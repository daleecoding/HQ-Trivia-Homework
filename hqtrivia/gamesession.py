import asyncio
from collections import Counter
import json
import logging
from typing import List
import websockets
from websockets.exceptions import ConnectionClosed

import hqtrivia.config as config
from .messages import *
from .player import Player
from .question import Question


class GameSession:
    """
    Represents a single game consisting of multiple players.
    The game will continue until everyone is eliminated or only
    1 player is left.

    """

    def __init__(self, game_id: int, players: List[Player]):
        self.game_id = game_id
        self.players = players.copy()
        self.current_round = 0

    async def run(self):
        logging.info(
            f"Game has started: [game_id={self.game_id}, players={str(self.players)}]")

        try:
            # Continue going to the next round as long as there's a player not eliminated yet
            while(await self.execute_next_round()):
                pass
        except:
            logging.error(TEMPLATE_GAME_SESSION_ERROR.substitute(
                gameid=self.game_id), exc_info=True)
            await self.abort_game()
            raise

    async def abort_game(self):
        """
        Aborts the game if an unrecoverable error is encountered
        """
        await asyncio.gather(
            *[player.send_announcement(MESSAGE_NETWORK_ERROR_OCCURRED)
              for player in self.players]
        )

        self.handle_eliminated_players(self.players)
        self.players.clear()

    async def execute_next_round(self) -> bool:
        """
        Returns false if game is over.
        """
        self.current_round += 1

        logging.info(
            f"Executing round: [game_id={self.game_id} round={self.current_round}]")

        # Generate the question for this round
        question = await Question.generate()

        # Start the duration for receiving now so that question
        # generation time is not taken into the timeout for the
        # user to answer the question.

        # Broadcast questions to the players and wait for the answers
        answers = await self.broadcast_question_and_wait_for_answers(question)

        # Broadcast the result to the players
        eliminated_players = await self.broadcast_results_and_eliminate_players(question, answers)

        # Eliminate players with wrong answers
        self.handle_eliminated_players(eliminated_players)

        # If only 1 remaining, notify the winner.
        # Return true if game should continue
        return await self.notify_winner_if_one_remaining()

    async def broadcast_question_and_wait_for_answers(self, question: Question) -> List[str]:
        logging.info(
            f"Sending questions players: [game_id={self.game_id} round={self.current_round} players={len(self.players)} question={str(question)}]")

        return await asyncio.gather(
            *[self.send_question_and_get_answer(
                question, player) for player in self.players]
        )

    async def send_question_and_get_answer(self, question: str, player: Player) -> str:
        try:
            # Announce that the round is starting
            await player.send_announcement(TEMPLATE_GAME_ROUND_STARTING.substitute(round=self.current_round))
            # Send the questions
            await player.send_question(question)
            # Give the player the round duration amount of time to answer
            answer = await asyncio.wait_for(player.recv_answer(), timeout=config.CONFIG_ROUND_DURATION)
            logging.info(f"Player answered: [player={player} answer={answer}]")
            return answer

        except asyncio.TimeoutError as e:
            logging.info(
                f"player did not respond within timeout: [player={player} timeout={config.CONFIG_ROUND_DURATION}]")
            pass

        except:
            logging.error(
                f"Error occurred while sending and receiving answer: [player={player}]", exc_info=True)

        return None

    async def broadcast_results(self, allplayers: List[Player], survivors: List[Player], eliminated: List[Player], question: Question, choice_counts: List[int]):
        logging.info(
            f"Sending round stats to players: [game_id={self.game_id} round={self.current_round} players={len(self.players)}, counts={choice_counts}]")

        # Broadcast the statistics on how many players have chosen each answer.
        await asyncio.gather(
            *[player.send_answers(question, choice_counts) for player in allplayers]
        )

        logging.info(
            f"Game round survivors: [game_id={self.game_id} round={self.current_round} players={survivors}]")

        # Broadcast whether each player has survived or been eliminated from the game.
        coroutines = [player.send_announcement(
            MESSAGE_CORRECT_ANSWER) for player in survivors]
        coroutines.extend([player.send_announcement(
            MESSAGE_YOU_ARE_ELIMINATED) for player in eliminated])

        await asyncio.gather(*coroutines)

    async def broadcast_results_and_eliminate_players(self, question: Question, answers: List[str]) -> List[Player]:
        counter = Counter()
        eliminated = []
        survivors = []

        for i in range(0, len(self.players)):
            if (question.answer == answers[i]):
                # More efficient to construct new players than deleting from array list each time.
                survivors.append(self.players[i])
            else:
                eliminated.append(self.players[i])

            # Gather the number of players who chose this answer
            counter[answers[i]] += 1

        choice_counts = [0] * len(question.choices)

        for i in range(0, len(question.choices)):
            choice_counts[i] = counter[question.choices[i]]

        # Send the results to the players
        await self.broadcast_results(self.players, survivors,
                                     eliminated, question, choice_counts)

        # Update the new players list to only the survivors
        self.players = survivors

        return eliminated

    def handle_eliminated_players(self, players: List[Player]):
        # Set the result so that the websocket handling can finish.
        for player in players:
            logging.info(
                f"Player eliminated from the game: [game_id={self.game_id} round={self.current_round} player={player}]")

            player.future.set_result(None)

    async def notify_winner_if_one_remaining(self):
        # Check if there's a winner
        if (len(self.players) == 1):
            await self.players[0].send_announcement(MESSAGE_YOU_ARE_THE_WINNER)

            # Notify that this player is done with the game
            self.players[0].future.set_result(None)
            del self.players[0]

        # Game will continue if there are still participants left
        return len(self.players) != 0
