import asyncio
import unittest
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch
from websockets.exceptions import ConnectionClosed

from hqtrivia.gamesession import GameSession
from hqtrivia.messages import *
from hqtrivia.question import Question
from hqtrivia.player import Player


class GameSessionTest(unittest.TestCase):

    def setUp(self):
        # Set to a shorter time for faster test
        self.original_round_duration = GameSession.ROUND_DURATION
        GameSession.ROUND_DURATION = min(2, GameSession.ROUND_DURATION)

    def tearDown(self):
        GameSession.ROUND_DURATION = self.original_round_duration

    def get_mocked_player(self, answer):
        """Helper method to get a mocked up player for use
        """
        player = MagicMock()
        send_announcement = AsyncMock()
        player.attach_mock(send_announcement, 'send_announcement')
        send_question = AsyncMock()
        player.attach_mock(send_question, 'send_question')
        send_answers = AsyncMock()
        player.attach_mock(send_answers, 'send_answers')
        recv_answer = AsyncMock()
        player.attach_mock(recv_answer, 'recv_answer')
        recv_answer.return_value = answer
        return (player, send_announcement, send_question, send_answers, recv_answer)

    def test_run(self):
        """Tests that run() method calls execute_next_round() only once if it returns False.
        """
        game = GameSession(0, [])
        game.abort_game = AsyncMock()
        game.execute_next_round = AsyncMock()
        # First time returns True. On second time returns False.
        game.execute_next_round.side_effect = [True, False]

        asyncio.run(game.run())

        game.abort_game.assert_not_called()
        game.execute_next_round.assert_has_calls([call(), call()])

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
        send_announcement = AsyncMock()
        player.attach_mock(send_announcement, 'send_announcement')

        game = GameSession(0, [player])
        game.handle_eliminated_players = MagicMock()

        asyncio.run(game.abort_game())

        game.handle_eliminated_players.assert_called_once()
        send_announcement.assert_called_once_with(
            MESSAGE_NETWORK_ERROR_OCCURRED)

    @patch('hqtrivia.question.Question.generate', new_callable=AsyncMock)
    def test_execute_next_round_identifies_winner(self, generate):
        """Tests that execute_next_round() method correctly identifies winner from the game.
        """
        question = Question('Question 1', ['A', 'B', 'C', 'D'], 'C')
        generate.return_value = question

        # Create player 1 with wrong answer, and player 2 with the right answer
        (player1, send_announcement1, send_question1,
         send_answers1, recv_answer1) = self.get_mocked_player('D')

        (player2, send_announcement2, send_question2,
         send_answers2, recv_answer2) = self.get_mocked_player('C')

        game = GameSession(0, [player1, player2])

        result = asyncio.run(game.execute_next_round())

        self.assertFalse(
            result, "execute_next_round() should return False since game ended with a winner.")

        self.assertEqual(len(game.players), 0,
                         "No player should remain in the game")

        # Check that the question was sent to the players
        send_question1.assert_any_call(question)
        send_question2.assert_any_call(question)

        # Check that the count of the answers from each participant was sent
        send_answers1.assert_any_call(question, [0, 0, 1, 1])
        send_answers2.assert_any_call(question, [0, 0, 1, 1])

        # Check that these message were sent last
        send_announcement1.assert_called_with(MESSAGE_YOU_ARE_ELIMINATED)
        send_announcement2.assert_called_with(MESSAGE_YOU_ARE_THE_WINNER)

    @patch('hqtrivia.question.Question.generate', new_callable=AsyncMock)
    def test_execute_next_round_player_times_out(self, generate):
        """Tests that execute_next_round() eliminates player who did not respond within timeout.
        """
        question = Question('Question 1', ['A', 'B', 'C', 'D'], 'C')
        generate.return_value = question

        # Create player 1 with the wrong answer, and player 2 will timeout
        (player1, send_announcement1, send_question1,
         send_answers1, recv_answer1) = self.get_mocked_player('D')

        async def over_sleep():
            await asyncio.sleep(GameSession.ROUND_DURATION+1)

        (player2, send_announcement2, send_question2,
         send_answers2, recv_answer2) = self.get_mocked_player(None)

        player2.attach_mock(over_sleep, 'recv_answer')

        game = GameSession(0, [player1, player2])

        result = asyncio.run(game.execute_next_round())

        self.assertFalse(
            result, "execute_next_round() should return False since game ended.")

        self.assertEqual(len(game.players), 0,
                         "No player should remain in the game")

        # Check that the question was sent to the players
        # Check that the question was sent to the players
        send_question1.assert_any_call(question)
        send_question2.assert_any_call(question)

        # Check that the count of the answers from each participant was sent
        send_answers1.assert_any_call(question, [0, 0, 0, 1])
        send_answers2.assert_any_call(question, [0, 0, 0, 1])

        # Check that these message were sent last
        send_announcement1.assert_called_with(MESSAGE_YOU_ARE_ELIMINATED)
        send_announcement1.assert_called_with(MESSAGE_YOU_ARE_ELIMINATED)

    @patch('hqtrivia.question.Question.generate', new_callable=AsyncMock)
    def test_execute_next_round_player_recvMessage_exception(self, generate):
        """Tests that execute_next_round() eliminates player who did not respond within timeout.
        """
        question = Question('Question 1', ['A', 'B', 'C', 'D'], 'C')
        generate.return_value = question

        # Create player 1 with wrong answer, and player 2 with the right answer
        (player1, send_announcement1, send_question1,
         send_answers1, recv_answer1) = self.get_mocked_player('D')

        (player2, send_announcement2, send_question2,
         send_answers2, recv_answer2) = self.get_mocked_player('C')

        recv_answer2 = AsyncMock(side_effect=Exception(
            'General Error during recv_answer()'))
        player2.attach_mock(recv_answer2, 'recv_answer')

        game = GameSession(0, [player1, player2])

        result = asyncio.run(game.execute_next_round())

        self.assertFalse(
            result, "execute_next_round() should return False since game ended.")

        self.assertEqual(len(game.players), 0,
                         "No player should remain in the game")

        # Check that the question was sent to the players
        send_question1.assert_any_call(question)
        send_question2.assert_any_call(question)

        # Check that the count of the answers from each participant was sent
        send_answers1.assert_any_call(question, [0, 0, 0, 1])
        send_answers2.assert_any_call(question, [0, 0, 0, 1])

        # Check that these message were sent last
        send_announcement1.assert_called_with(MESSAGE_YOU_ARE_ELIMINATED)
        send_announcement1.assert_called_with(MESSAGE_YOU_ARE_ELIMINATED)

    @patch('hqtrivia.question.Question.generate', new_callable=AsyncMock)
    def test_execute_next_round_move_to_next_round(self, generate):
        """Tests that execute_next_round() method has to continue to the next round.
        """
        question = Question('Question 1', ['A', 'B', 'C', 'D'], 'C')
        generate.return_value = question

        # Both players gives the correct answer
        (player1, send_announcement1, send_question1,
         send_answers1, recv_answer1) = self.get_mocked_player('C')

        (player2, send_announcement2, send_question2,
         send_answers2, recv_answer2) = self.get_mocked_player('C')

        game = GameSession(0, [player1, player2])

        result = asyncio.run(game.execute_next_round())

        self.assertTrue(
            result, "execute_next_round() should return True since no single winner yet.")

        self.assertEqual(len(game.players), 2,
                         "Two players should still be in the game")

        # Check that the question was sent to the players
        send_question1.assert_any_call(question)
        send_question2.assert_any_call(question)

        # Check that the count of the answers from each participant was sent
        send_answers1.assert_any_call(question, [0, 0, 2, 0])
        send_answers2.assert_any_call(question, [0, 0, 2, 0])

        # Check that these message were sent last
        send_announcement1.assert_called_with(MESSAGE_CORRECT_ANSWER)
        send_announcement1.assert_called_with(MESSAGE_CORRECT_ANSWER)

    @patch('hqtrivia.question.Question.generate', new_callable=AsyncMock)
    def test_execute_next_round_all_eliminated(self, generate):
        """Tests that execute_next_round() method eliminates everyone without winner
        """
        question = Question('Question 1', ['A', 'B', 'C', 'D'], 'C')
        generate.return_value = question

        # Both players gives wrong answer
        (player1, send_announcement1, send_question1,
         send_answers1, recv_answer1) = self.get_mocked_player('A')

        (player2, send_announcement2, send_question2,
         send_answers2, recv_answer2) = self.get_mocked_player('B')

        game = GameSession(0, [player1, player2])

        result = asyncio.run(game.execute_next_round())

        self.assertFalse(
            result, "execute_next_round() should return False since everyone eliminated.")

        self.assertEqual(len(game.players), 0,
                         "No one should remain in the game")

        # Check that the question was sent to the players
        send_question1.assert_any_call(question)
        send_question2.assert_any_call(question)

        # Check that the count of the answers from each participant was sent
        send_answers1.assert_any_call(question, [1, 1, 0, 0])
        send_answers2.assert_any_call(question, [1, 1, 0, 0])

        # Check that these message were sent last
        send_announcement1.assert_called_with(MESSAGE_YOU_ARE_ELIMINATED)
        send_announcement1.assert_called_with(MESSAGE_YOU_ARE_ELIMINATED)

    @patch('hqtrivia.question.Question.generate', new_callable=AsyncMock)
    def test_run_exception_question_generator(self, generate):
        """Tests that run() method eliminates everyone without winner
        """
        question = Question('Question 1', ['A', 'B', 'C', 'D'], 'C')
        generate.return_value = question
        generate.side_effect = Exception("Network Error!!!")

        # Both players give wrong answer, but not important since Question.generate will throw exception
        (player1, send_announcement1, send_question1,
         send_answers1, recv_answer1) = self.get_mocked_player('A')

        (player2, send_announcement2, send_question2,
         send_answers2, recv_answer2) = self.get_mocked_player('B')

        game = GameSession(0, [player1, player2])

        with self.assertRaises(Exception):
            asyncio.run(game.run())

        self.assertEqual(len(game.players), 0,
                         "No one should remain in the game")

        # Check that these message were sent last
        send_announcement1.assert_called_once_with(
            MESSAGE_NETWORK_ERROR_OCCURRED)
        send_announcement2.assert_called_once_with(
            MESSAGE_NETWORK_ERROR_OCCURRED)
