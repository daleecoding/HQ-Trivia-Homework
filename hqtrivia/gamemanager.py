import asyncio
import logging
from .gamesession import GameSession
from .gamesession import Player
from .websocketserver import WebsocketServer
from .websocketserver import WebsocketCallbackInterface


class GameManager(WebsocketCallbackInterface):
    """
    Runs and manages the overall HQ Trivia game.

    TODO: Description of the overall logic.
    """

    PLAYERS_PER_GAME = 2
    WS_SERVER_PORT

    def __init__(self):
        # Players waiting for the game to start after quorum is reached
        self.waiting_players = []
        self.next_game_id = 1
        self.game_task_queue = asyncio.Queue()

    async def main(self):
        # TODO: Make the port configurable
        wsserver = WebsocketServer(WS_SERVER_PORT, self)

        await asyncio.create_task(self.run())
        await asyncio.create_task(wsserver.start())

    async def run(self):
        # Ensure that all game.run() tasks get tracked until they finish.
        while (True):
            task = await game_task_queue.get()
            # Eat up the exception if game.run() threw an exception
            await asyncio.gather(task, return_exceptions=False)

    async def handle_new_websocket(self, websocket: websockets.WebSocketServerProtocol):
        new_player = Player(
            asyncio.get_running_loop().create_future(), websocket)

        await self.wait_until_game_complete(new_player)

    async def wait_until_game_complete(self, player: Player):
        # Create future to await on and queue onto the waiting list
        waiting_players.append(player)

        # If there is a quorum, create a new game and schedule it as a task
        if (len(waiting_players) >= PLAYERS_PER_GAME):
            game = GameSession(next_game_id, waiting_players)
            next_game_id += 1

            waiting_players.clear()

            # Start the game.run() task and ensure task is kept track until
            # it finishes.
            game_task_queue.append(asyncio.create_task(game.run()))

        # Wait until the game is complete for this player
        await player.future


if __name__ == '__main__':
    # TODO: Make the logging level configurable
    logging.basicConfig(format='%(asctime)s %(message)s',
                        level=logging.WARNING)

    gm = GameManager()
    asyncio.run(gm.main())
