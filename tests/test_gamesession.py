import asyncio
import unittest
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

from hqtrivia.gamesession import GameSession
from hqtrivia.messages import *


class GameSessionTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_run(self):
        """Tests that run() method calls execute_next_round() only once if it returns False.
        """
        game = GameSession(0, [])
        game.abort_game = AsyncMock()
        game.execute_next_round = AsyncMock(return_value=False)

        asyncio.run(game.run())

        game.abort_game.assert_not_called()
        game.execute_next_round.assert_called_once()

    def test_run_when_exception_thrown(self):
        """Tests that run() method calls execute_next_round() only once if it returns False.
        """
        self.assertRaises(Exception, GameSession.run)

        game = GameSession(0, [])
        game.abort_game = AsyncMock()
        game.execute_next_round = AsyncMock(
            return_value=True, side_effect=Exception)

        with self.assertRaises(Exception):
            asyncio.run(game.run())

        game.abort_game.assert_called_once()
        game.execute_next_round.assert_called_once()

    def test_abort_game(self):
        """Tests that abort_game() method calls handle_eliminated_players() once
        """

        player = MagicMock()
        sendMessage = AsyncMock()
        player.attach_mock(sendMessage, 'sendMessage')

        game = GameSession(0, [player])
        game.handle_eliminated_players = AsyncMock()

        asyncio.run(game.abort_game())

        game.handle_eliminated_players.assert_called_once()
        sendMessage.assert_called_once_with(MESSAGE_NETWORK_ERROR_OCCURRED)

    @patch('hqtrivia.question.Question.generate', new_callable=AsyncMock)
    def test_execute_next_round(self, generate):
        """Tests that execute_next_round() method calls the necessary sub methods.
        """

        player = MagicMock()
        sendMessage = AsyncMock()
        player.attach_mock(sendMessage, 'sendMessage')
        recvMessage = AsyncMock()
        recvMessage.return_value = 'my_answer'
        player.attach_mock(recvMessage, 'recvMessage')

        game = GameSession(0, [player])

        asyncio.run(game.execute_next_round())

        genearate.assert_called_once()

        # game.handle_eliminated_players.assert_called_once()
        # sendMessage.assert_called_once_with(MESSAGE_NETWORK_ERROR_OCCURRED)
