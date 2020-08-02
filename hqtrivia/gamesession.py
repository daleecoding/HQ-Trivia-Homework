import asyncio
from collections import Counter
import json
import logging
from typing import List
import websockets

from .messages import *
from .question import Question


class Player:
    """
    This represents a handle to a single remote player.

    The purpose of this class is to wrap the websocket calls so that the
    GameSession class can have a bi-directional communication without
    worrying about the protocol nor the low-level communication errors.

    Future object is used to signal that game is complete for the user.
    """

    def __init__(self, future: asyncio.Future, websocket: websockets.WebSocketServerProtocol):
        self.future = future
        self.websocket = websocket

    async def sendMessage(self, message: str):
        await self.websocket.send(message)
        # TypeError can be raised but that would be a bug on our part in
        # trying to send different types of data, and we want that to
        # propagate to the user

    async def recvMessage(self) -> str:
        try:
            return await self.websocket.recv()
        except ConnectionClosed as e:
            logging.warning(
                "Connection closed while waiting for recv(): %s", e)
            return None
        # RuntimeError can be raised if two coroutines call recv() concurrently.
        # That would be a bug and we want that to propagate to the user.


class GameSession:
    """
    Represents a single game consisting of multiple players.
    The game will continue until everyone is eliminated or only
    1 player is left.

    """

    ROUND_DURATION = 10

    def __init__(self, game_id: int, players: List[Player]):
        self.game_id = id
        self.players = players
        self.current_round = 0

    async def run(self):
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
            *[player.sendMessage(MESSAGE_NETWORK_ERROR_OCCURRED)
              for player in self.players]
        )

        await self.handle_eliminated_players(self.players)
        self.players.clear()

    async def execute_next_round(self) -> bool:
        """
        Returns false if game is over.
        """

        self.current_round += 1

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
        json_text = question.get_json_without_answer()

        return await asyncio.gather(
            *[self.send_question_and_get_answer(
                json_text, player) for player in self.players]
        )

    async def send_question_and_get_answer(self, question_json: str, player: Player) -> str:
        try:
            await player.sendMessage(question_json)
            return await asyncio.wait_for(player.recvMessage(), timeout=GameSession.ROUND_DURATION)

        except asyncio.TimeoutError as e:
            # Expected to occur if player doesn't answer in time
            pass

        except:
            logging.error(
                "Error occurred while sending and receiving answer", exc_info=True)

        return None

    async def broadcast_results(self, allplayers: List[Player], survivors: List[Player], eliminated: List[Player], choice_counts: List[int]):
        json_text = json.dumps(choice_counts)

        # Broadcast the statistics on how many players have chosen each answer.
        await asyncio.gather(
            *[player.sendMessage(json_text) for player in allplayers]
        )

        # Broadcast whether each player has survived or been eliminated from the game.
        coroutines = [player.sendMessage(
            MESSAGE_CORRECT_MOVING_TO_NEXT_ROUND) for player in survivors]
        coroutines.extend([player.sendMessage(
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
                                     eliminated, choice_counts)

        # Update the new players list to only the survivors
        self.players = survivors

        return eliminated

    def handle_eliminated_players(self, players: List[Player]):
        # Set the result so that the websocket handling can finish.
        for player in players:
            player.future.set_result(None)

    async def notify_winner_if_one_remaining(self):
        # Check if there's a winner
        if (len(self.players) == 1):
            await self.players[0].sendMessage(MESSAGE_YOU_ARE_THE_WINNER)

            # Notify that this player is done with the game
            self.players[0].future.set_result(None)
            del self.players[0]

        # Game will continue if there are still participants left
        return len(self.players) != 0
