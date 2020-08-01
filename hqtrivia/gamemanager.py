import asyncio
import logging

from .gamesession import GameSession
from .websocketserver import WebsocketServer


class Player:
    """
    This represents a handle to a single remote player.

    The purpose of this class is to wrap the websocket calls so that the
    GameSession class can have a bi-directional communication without
    worrying about the protocol nor the low-level communication errors.
    """

    def __init__(self, websocket: websockets.protocol.websocket):
        self.websocket = websocket

    async def sendMessage(self, message: str):
        try:
            await self.websocket.send(message)
        except:
            logging.warning("sendMessage failed %s", sys.exc_info()[0])

    async def recvMessage(self) -> str:
        try:
            return await self.websocket.recv()
        except:
            logging.warning("recvMessage failed %s", sys.exc_info()[0])
            return None


class GameManager:
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

    async def main(self):
        # TODO: Make the port configurable
        wsserver = WebsocketServer(WS_SERVER_PORT, self)

        await asyncio.create_task(self.run())
        await asyncio.create_task(wsserver.start())

    async def run(self):
        # TODO: I may not need this coroutine if I can do all house
        # keeping through the handle_new_websocket.
        pass

    async def handle_new_websocket(self, websocket: websockets.WebSocketServerProtocol):
        # TODO: Break down into small functions for unit testing

        new_player = Player(websocket)

        waiting_players.append(new_player)

        if (len(waiting_players) >= PLAYERS_PER_GAME):
            # Got a quorum. Create a new game with all the players who has been waiting
            game = GameSession(next_game_id, waiting_players)
            waiting_players.clear()

            # Increment next game id to use by 1 for uniqueness
            next_game_id += 1

            # Keep going to the next round until the game is over
            while (await game.execute_next_round()):
                pass
        else:
            # TODO: Handle players waiting for other players to join
            # Need to use future to notify the waiting players
            pass


if __name__ == '__main__':
    # TODO: Make the logging level configurable
    logging.basicConfig(format='%(asctime)s %(message)s',
                        level=logging.WARNING)

    gm = GameManager()
    asyncio.run(gm.main())
