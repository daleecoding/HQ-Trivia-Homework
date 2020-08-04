import asyncio
import logging
import websockets

from .gamesession import GameSession
from .messages import *
from .player import Player
from .websocketserver import WebsocketServer
from .websocketserver import WebsocketCallbackInterface


class GameManager(WebsocketCallbackInterface):
    """
    Runs and manages the overall HQ Trivia game.

    TODO: Description of the overall logic.
    """

    PLAYERS_PER_GAME = 2
    WS_SERVER_PORT = 9999

    def __init__(self):
        # Players waiting for the game to start after quorum is reached
        self.waiting_players = []
        self.next_game_id = 1
        # TODO: Make the port configurable
        self.wsserver = WebsocketServer(GameManager.WS_SERVER_PORT, self)

    def main(self):
        # Start websocket server and wait forever
        event_loop = asyncio.get_event_loop()
        event_loop.run_until_complete(self.wsserver.start())
        event_loop.run_forever()

    async def handle_new_websocket(self, websocket: websockets.WebSocketServerProtocol):
        new_player = Player(
            asyncio.get_running_loop().create_future(), websocket)

        await self.wait_until_game_complete(new_player)

    async def wait_until_game_complete(self, player: Player):
        # Create future to await on and queue onto the waiting list
        self.waiting_players.append(player)

        # If there is a quorum, create a new game and schedule it as a task
        if (len(self.waiting_players) >= GameManager.PLAYERS_PER_GAME):
            game = GameSession(self.next_game_id, self.waiting_players)
            self.next_game_id += 1

            self.waiting_players.clear()

            # Use the last player's context to run the game.
            await game.run()
        else:
            logging.info(
                f"Waiting for more players: [players={len(self.waiting_players)} min_required={GameManager.PLAYERS_PER_GAME}]")
            await player.send_announcement(TEMPLATE_WAITING_FOR_PLAYERS.substitute(players=GameManager.PLAYERS_PER_GAME))

        # Wait until the game is complete for this player
        await player.future


if __name__ == '__main__':
    # TODO: Make the logging level configurable
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.INFO)

    try:
        gm = GameManager()
        gm.main()
    except KeyboardInterrupt:
        # User requested abort
        logging.warning("Received keyboard interrupt. Exiting")
