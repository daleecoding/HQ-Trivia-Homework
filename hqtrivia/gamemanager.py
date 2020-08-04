import argparse
import asyncio
import logging
import websockets

import hqtrivia.config as config
from .gamesession import GameSession
from .messages import *
from .player import Player
from .websocketserver import WebsocketServer
from .websocketserver import WebsocketCallbackInterface

"""
Provides the main execution entry and the overall logic for the hqtrivia package.
"""


class GameManager(WebsocketCallbackInterface):
    """
    Runs and manages the overall HQ Trivia game.

    The rule of the game:
    - Each player connects through a separate websocket connection
    - When N number of players are connected and waiting, game session commences.
    - Game session can have 1 or more rounds. Each round consists of:
        - Players are given the same questions
        - If the player provides an incorrect answer or does not provide an
          answer within the timeout, the player is eliminated from the game.
        - If there are two more or players left in the game, go to the next round.
          Otherwise if 1 player is remaining, that player is the winner and game ends.
          Otherwise there is no winner and the game ends.

    The main entry for this class is main().  In main(), websocketserver is
    started and is blocked on the current event loop until it is stopped.

    Events are driven by the call from the websocketserver when a new websocket
    is connected.  Websocket is abstracted by wrapping it in the Player instance.
    The Player is then put on the waiting list. If the waiting list meets the
    minimum number of players, a GameSession is created and is run using await.

    All Player instances wait on a future instance so that the underly websocket
    connection is kept alive until the game is over for the Player. The future
    instance is set by the GameSession when it determines that the Player is
    either eliminated or declared a winner.
    """

    def __init__(self):
        # Players waiting for the game to start after quorum is reached
        self.waiting_players = []
        self.next_game_id = 1
        self.wsserver = WebsocketServer(config.CONFIG_WS_SERVER_PORT, self)

    def main(self):
        """Start websocket server and wait forever
        """

        event_loop = asyncio.get_event_loop()
        event_loop.run_until_complete(self.wsserver.start())
        event_loop.run_forever()

    async def handle_new_websocket(self, websocket: websockets.WebSocketServerProtocol):
        """Callback from the websocketserver to handle a new websocket.
           Websocket connection is kept alive by waiting on the future until the game is over for the player.

        Parameters
        ----------
        websocket: websockets.WebSocketServerProtocol
            New websocket
        """
        new_player = Player(
            asyncio.get_running_loop().create_future(), websocket)

        await self.wait_until_game_complete(new_player)

    async def wait_until_game_complete(self, player: Player):
        """Waits until the game is complete for the given player.
           Player will wait on the future, and the future will be set by the gamesession when the game is
           over by the player.

        Parameters
        ----------
        player: Player
            Player who just connected to the server
        """

        # Create future to await on and queue onto the waiting list
        self.waiting_players.append(player)

        # If there is a quorum, create a new game and schedule it as a task
        if (len(self.waiting_players) >= config.CONFIG_PLAYERS_PER_GAME):
            game = GameSession(self.next_game_id, self.waiting_players)
            self.next_game_id += 1

            self.waiting_players.clear()

            # Use the last player's context to run the game.
            await game.run()
        else:
            logging.info(
                f"Waiting for more players: [players={len(self.waiting_players)} min_required={config.CONFIG_PLAYERS_PER_GAME}]")
            await player.send_announcement(TEMPLATE_WAITING_FOR_PLAYERS.substitute(players=config.CONFIG_PLAYERS_PER_GAME))

        # Wait until the game is complete for this player
        await player.future


if __name__ == '__main__':
    """main execution entry for the hqtrivia package
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', metavar='path',
                        required=False, help='path to the config.json file')
    args = parser.parse_args()

    if (args.config != None):
        # Load config into the config module
        config.load_config(args.config)

    # Setup logging
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=config.CONFIG_LOG_LEVEL)

    try:
        gm = GameManager()
        gm.main()
    except KeyboardInterrupt:
        # User requested abort
        logging.warning("Received keyboard interrupt. Exiting")
