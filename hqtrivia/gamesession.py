import websockets
from .gamemanager import Player


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

    async def execute_next_round(self) -> bool:
        """
        Returns false if game is over.
        """

        # Generate the question for this round
        question = QuestionGenerator.generate()

        self.current_round += 1

        # Set the round ending time after getting the question in case
        # question generation was slow.

        # TODO: Breakdown the below tasks into separate functions for unit testing

        # TODO: Broadcast questions to the players and wait for the answers

        # TODO: Share the results to the players

        # TODO: Eliminate the players
