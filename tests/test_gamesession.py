import asyncio
import unittest
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

from hqtrivia.gamesession import GameSession
from hqtrivia.messages import *
from hqtrivia.question import Question
from hqtrivia.gamesession import Player


class GameSessionTest(unittest.TestCase):

    def setUp(self):
        # Set to a shorter time for faster test
        self.original_round_duration = GameSession.ROUND_DURATION
        GameSession.ROUND_DURATION = min(2, GameSession.ROUND_DURATION)

    def tearDown(self):
        GameSession.ROUND_DURATION = self.original_round_duration

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
    def test_execute_next_round_identifies_winner(self, generate):
        """Tests that execute_next_round() method correctly identifies winner from the game.
        """
        generate.return_value = Question(
            'Question 1', ['A', 'B', 'C', 'D'], 'C')

        # Create player 1 with wrong answer, and player 2 with the right answer
        player1 = MagicMock()
        sendMessage1 = AsyncMock()
        player1.attach_mock(sendMessage1, 'sendMessage')
        recvMessage1 = AsyncMock()
        recvMessage1.return_value = "D"
        player1.attach_mock(recvMessage1, 'recvMessage')

        player2 = MagicMock()
        sendMessage2 = AsyncMock()
        player2.attach_mock(sendMessage2, 'sendMessage')
        recvMessage2 = AsyncMock()
        recvMessage2.return_value = "C"
        player2.attach_mock(recvMessage2, 'recvMessage')

        game = GameSession(0, [player1, player2])

        result = asyncio.run(game.execute_next_round())

        self.assertFalse(
            result, "execute_next_round() should return False since game ended with a winner.")

        self.assertEqual(len(game.players), 0,
                         "No player should remain in the game")

        # Check that the question was sent to the players
        sendMessage1.assert_any_call(
            '{"question": "Question 1", "choices": ["A", "B", "C", "D"]}')

        sendMessage2.assert_any_call(
            '{"question": "Question 1", "choices": ["A", "B", "C", "D"]}')

        # Check that the count of the answers from each participant was sent
        sendMessage1.assert_any_call('[0, 0, 1, 1]')
        sendMessage2.assert_any_call('[0, 0, 1, 1]')

        # Check that these message were sent last
        sendMessage1.assert_called_with(MESSAGE_YOU_ARE_ELIMINATED)
        sendMessage2.assert_called_with(MESSAGE_YOU_ARE_THE_WINNER)

    @patch('hqtrivia.question.Question.generate', new_callable=AsyncMock)
    def test_execute_next_round_player_times_out(self, generate):
        """Tests that execute_next_round() eliminates player who did not respond within timeout.
        """
        generate.return_value = Question(
            'Question 1', ['A', 'B', 'C', 'D'], 'C')

        # Create player 1 with wrong answer, and player 2 with the right answer
        player1 = MagicMock()
        sendMessage1 = AsyncMock()
        player1.attach_mock(sendMessage1, 'sendMessage')
        recvMessage1 = AsyncMock()
        recvMessage1.return_value = "D"
        player1.attach_mock(recvMessage1, 'recvMessage')

        async def over_sleep():
            await asyncio.sleep(GameSession.ROUND_DURATION+1)

        websocket = MagicMock()
        player2 = Player(MagicMock(), None)
        sendMessage2 = AsyncMock()
        player2.sendMessage = sendMessage2
        player2.recvMessage = over_sleep

        game = GameSession(0, [player1, player2])

        result = asyncio.run(game.execute_next_round())

        self.assertFalse(
            result, "execute_next_round() should return False since game ended.")

        self.assertEqual(len(game.players), 0,
                         "No player should remain in the game")

        # Check that the question was sent to the players
        sendMessage1.assert_any_call(
            '{"question": "Question 1", "choices": ["A", "B", "C", "D"]}')

        sendMessage2.assert_any_call(
            '{"question": "Question 1", "choices": ["A", "B", "C", "D"]}')

        # Check that the count of the answers from each participant was sent
        sendMessage1.assert_any_call('[0, 0, 0, 1]')
        sendMessage2.assert_any_call('[0, 0, 0, 1]')

        # Check that these message were sent last
        sendMessage1.assert_called_with(MESSAGE_YOU_ARE_ELIMINATED)
        sendMessage2.assert_called_with(MESSAGE_YOU_ARE_ELIMINATED)

    @patch('hqtrivia.question.Question.generate', new_callable=AsyncMock)
    def test_execute_next_round_move_to_next_round(self, generate):
        """Tests that execute_next_round() method has to continue to the next round.
        """
        generate.return_value = Question(
            'Question 1', ['A', 'B', 'C', 'D'], 'C')

        # Both players gives the correct answer
        player1 = MagicMock()
        sendMessage1 = AsyncMock()
        player1.attach_mock(sendMessage1, 'sendMessage')
        recvMessage1 = AsyncMock()
        recvMessage1.return_value = "C"
        player1.attach_mock(recvMessage1, 'recvMessage')

        player2 = MagicMock()
        sendMessage2 = AsyncMock()
        player2.attach_mock(sendMessage2, 'sendMessage')
        recvMessage2 = AsyncMock()
        recvMessage2.return_value = "C"
        player2.attach_mock(recvMessage2, 'recvMessage')

        game = GameSession(0, [player1, player2])

        result = asyncio.run(game.execute_next_round())

        self.assertTrue(
            result, "execute_next_round() should return True since no single winner yet.")

        self.assertEqual(len(game.players), 2,
                         "Two players should still be in the game")

        # Check that the question was sent to the players
        sendMessage1.assert_any_call(
            '{"question": "Question 1", "choices": ["A", "B", "C", "D"]}')

        sendMessage2.assert_any_call(
            '{"question": "Question 1", "choices": ["A", "B", "C", "D"]}')

        # Check that the count of the answers from each participant was sent
        sendMessage1.assert_any_call('[0, 0, 2, 0]')
        sendMessage2.assert_any_call('[0, 0, 2, 0]')

        # Check that these message were sent last
        sendMessage1.assert_called_with(MESSAGE_CORRECT_MOVING_TO_NEXT_ROUND)
        sendMessage2.assert_called_with(MESSAGE_CORRECT_MOVING_TO_NEXT_ROUND)

    @patch('hqtrivia.question.Question.generate', new_callable=AsyncMock)
    def test_execute_next_round_all_eliminated(self, generate):
        """Tests that execute_next_round() method eliminates everyone without winner
        """
        generate.return_value = Question(
            'Question 1', ['A', 'B', 'C', 'D'], 'C')

        # Both players gives wrong answer
        player1 = MagicMock()
        sendMessage1 = AsyncMock()
        player1.attach_mock(sendMessage1, 'sendMessage')
        recvMessage1 = AsyncMock()
        recvMessage1.return_value = "A"
        player1.attach_mock(recvMessage1, 'recvMessage')

        player2 = MagicMock()
        sendMessage2 = AsyncMock()
        player2.attach_mock(sendMessage2, 'sendMessage')
        recvMessage2 = AsyncMock()
        recvMessage2.return_value = "B"
        player2.attach_mock(recvMessage2, 'recvMessage')

        game = GameSession(0, [player1, player2])

        result = asyncio.run(game.execute_next_round())

        self.assertFalse(
            result, "execute_next_round() should return False since everyone eliminated.")

        self.assertEqual(len(game.players), 0,
                         "No one should remain in the game")

        # Check that the question was sent to the players
        sendMessage1.assert_any_call(
            '{"question": "Question 1", "choices": ["A", "B", "C", "D"]}')

        sendMessage2.assert_any_call(
            '{"question": "Question 1", "choices": ["A", "B", "C", "D"]}')

        # Check that the count of the answers from each participant was sent
        sendMessage1.assert_any_call('[1, 1, 0, 0]')
        sendMessage2.assert_any_call('[1, 1, 0, 0]')

        # Check that these message were sent last
        sendMessage1.assert_called_with(MESSAGE_YOU_ARE_ELIMINATED)
        sendMessage2.assert_called_with(MESSAGE_YOU_ARE_ELIMINATED)

    @patch('hqtrivia.question.Question.generate', new_callable=AsyncMock)
    def test_run_exception_question_generator(self, generate):
        """Tests that run() method eliminates everyone without winner
        """
        generate.return_value = Question(
            'Question 1', ['A', 'B', 'C', 'D'], 'C')
        generate.side_effect = Exception("Network Error!!!")

        player1 = MagicMock()
        sendMessage1 = AsyncMock()
        player1.attach_mock(sendMessage1, 'sendMessage')
        recvMessage1 = AsyncMock()
        recvMessage1.return_value = "A"
        player1.attach_mock(recvMessage1, 'recvMessage')

        player2 = MagicMock()
        sendMessage2 = AsyncMock()
        player2.attach_mock(sendMessage2, 'sendMessage')
        recvMessage2 = AsyncMock()
        recvMessage2.return_value = "B"
        player2.attach_mock(recvMessage2, 'recvMessage')

        game = GameSession(0, [player1, player2])

        with self.assertRaises(Exception):
            asyncio.run(game.run())

        self.assertEqual(len(game.players), 0,
                         "No one should remain in the game")

        # Check that these message were sent last
        sendMessage1.assert_called_once_with(MESSAGE_NETWORK_ERROR_OCCURRED)
        sendMessage2.assert_called_once_with(MESSAGE_NETWORK_ERROR_OCCURRED)
