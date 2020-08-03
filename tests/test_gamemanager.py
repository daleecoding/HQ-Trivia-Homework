import asyncio
import unittest
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch
import websockets

from hqtrivia.gamemanager import GameManager
from hqtrivia.gamesession import Player


class GameManagerTest(unittest.TestCase):

    def test_main(self):
        """Tests whether main() starts up the websockets server and game manager main coroutines
        """
        gm = GameManager()
        gm.wsserver.start = AsyncMock()

        asyncio.run(gm.main())

        gm.wsserver.start.assert_called_once()

    def test_handle_new_websocket(self):
        """Tests whether handle_new_websocket() calls wait_until_game_complete().
        """

        gm = GameManager()
        gm.wait_until_game_complete = AsyncMock()
        ws = websockets.WebSocketServerProtocol(None, None)

        asyncio.run(gm.handle_new_websocket(ws))

        gm.wait_until_game_complete.assert_called_once()

    def test_wait_until_game_complete_not_enough_players(self):
        """Tests whether wait_until_game_complete() waits upon the future when there are not enough players
        """

        async def my_coroutine():
            gm = GameManager()
            future = asyncio.get_running_loop().create_future()
            player = Player(future, None)

            # Do not set result on purpose so that we know that it's blocking on this.
            # future.set_result(None)

            # Indirectly I can be confident that it timed out waiting for future.
            with self.assertRaises(asyncio.TimeoutError):
                await asyncio.wait_for(gm.wait_until_game_complete(player), timeout=1)

            self.assertEqual(len(gm.waiting_players), 1,
                             "Number of waiting players must be 1")

            gm.waiting_players.clear()

            # Now let's see if it's not blocked.
            future = asyncio.get_running_loop().create_future()
            player = Player(future, None)
            future.set_result(None)

            await asyncio.wait_for(gm.wait_until_game_complete(player), timeout=1)

            self.assertEqual(len(gm.waiting_players), 1,
                             "Number of waiting players must be 1")

        asyncio.run(my_coroutine())

    @patch('hqtrivia.gamesession.GameSession.run', new_callable=AsyncMock)
    def test_wait_until_game_complete_enough_players(self, run):
        """Tests whether wait_until_game_complete() runs a game if there are enough players
        """

        async def my_coroutine():
            gm = GameManager()

            for i in range(0, GameManager.PLAYERS_PER_GAME):
                future = asyncio.get_running_loop().create_future()
                player = Player(future, None)
                future.set_result(None)

                await asyncio.wait_for(gm.wait_until_game_complete(player), timeout=1)

            self.assertEqual(len(gm.waiting_players), 0,
                             "Number of waiting players must be 0")

            run.assert_called_once()

        asyncio.run(my_coroutine())
