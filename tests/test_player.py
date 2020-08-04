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


class PlayerTest(unittest.TestCase):

    def test_player_send_json_rpc_request(self):
        """Tests that Player.send_json_rpc_request() calls websocket send()
        """
        websocket = MagicMock()
        send = AsyncMock()
        websocket.attach_mock(send, 'send')

        player = Player(None, websocket)
        string = "Player is " + str([player])

        params = dict()
        params['a'] = 'x'
        asyncio.run(player.send_json_rpc_request("general_request", params))

        send.assert_called_once_with(
            '{"id": 1, "method": "general_request", "params": {"a": "x"}}')

    def test_player_send_json_rpc_request_throws_connection_closed(self):
        """Tests Player.send_json_rpc_request() when websocket send() throws a ConnectionClosed exception
        """
        websocket = MagicMock()
        send = AsyncMock(side_effect=ConnectionClosed(0, 'Connection Closed'))
        websocket.attach_mock(send, 'send')

        player = Player(None, websocket)
        string = "Player is " + str([player])

        params = dict()
        params['a'] = 'x'
        asyncio.run(player.send_json_rpc_request("general_request", params))
        # No exception should propage as expected
        send.assert_called_once()

    def test_player_receive_json_rpc_response(self):
        """Tests that Player.receive_json_rpc_response() calls websocket recv()
        """
        websocket = MagicMock()
        recv = AsyncMock()
        recv.return_value = '{"id":2323, "error":"noerror", "result":"nothing"}'
        websocket.attach_mock(recv, 'recv')

        player = Player(None, websocket)
        (reqid, error, result) = asyncio.run(
            player.receive_json_rpc_response())

        self.assertEqual(reqid, 2323,
                         "receive_json_rpc_response(() returned unexpected 'id'")

        self.assertEqual(error, 'noerror',
                         "receive_json_rpc_response(() returned unexpected 'error'")

        self.assertEqual(result, 'nothing',
                         "receive_json_rpc_response(() returned unexpected 'result''")

    def test_player_receive_json_rpc_response_connection_closed(self):
        """Tests that Player.receive_json_rpc_response_connection_closed() returns None when websocket throws ConnectionClosed exception
        """
        websocket = MagicMock()
        recv = AsyncMock(side_effect=ConnectionClosed(0, 'Connection Closed'))
        websocket.attach_mock(recv, 'recv')

        player = Player(None, websocket)
        (x, y, z) = asyncio.run(player.receive_json_rpc_response())

        self.assertEqual(
            (x, y, z), (None, None, None), '(None, None, None) expected for receive_json_rpc_response() when connection is closed')

    def test_player_receive_json_rpc_response_exception(self):
        """Tests that Player.receive_json_rpc_response_connection_closed() throws Exception when websocket throws Exception
        """
        websocket = MagicMock()
        recv = AsyncMock()
        recv.return_value = "test1"
        recv.side_effect = Exception("System Error")
        websocket.attach_mock(recv, 'recv')

        player = Player(None, websocket)

        with self.assertRaises(Exception):
            asyncio.run(player.receive_json_rpc_response_connection_closed())

    def test_send_question(self):
        """Tests that Player.send_question() calls websocket send()
        """
        question = Question('Question 1', ['A', 'B', 'C', 'D'], 'C')

        websocket = MagicMock()
        send = AsyncMock()
        websocket.attach_mock(send, 'send')

        player = Player(None, websocket)
        asyncio.run(player.send_question(question))

        send.assert_called_once_with(
            '{"id": 1, "method": "ask_question", "params": {"question": "Question 1", "choices": ["A", "B", "C", "D"]}}')

    def test_send_answers(self):
        """Tests that Player.send_answers() calls websocket send()
        """
        question = Question('Question 1', ['A', 'B', 'C', 'D'], 'C')

        websocket = MagicMock()
        send = AsyncMock()
        websocket.attach_mock(send, 'send')

        player = Player(None, websocket)
        counts = [1, 0, 1, 0]
        asyncio.run(player.send_answers(question, counts))

        send.assert_called_once_with(
            '{"id": 1, "method": "answers", "params": {"question": {"question": "Question 1", "choices": ["A", "B", "C", "D"], "answer": "C"}, "choice_counts": [1, 0, 1, 0]}}')

    def test_send_announcement(self):
        """Tests that Player.send_announcement() calls websocket send()
        """
        websocket = MagicMock()
        send = AsyncMock()
        websocket.attach_mock(send, 'send')

        player = Player(None, websocket)
        asyncio.run(player.send_announcement("Breaking News!!!"))

        send.assert_called_once_with(
            '{"id": 1, "method": "announcement", "params": {"message": "Breaking News!!!"}}')

    def test_player_recv_answer(self):
        """Tests that Player.recv_answer() calls websocket recv()
        """
        websocket = MagicMock()
        recv = AsyncMock()
        recv.return_value = '{"id":2323, "error":"noerror", "result":"nothing"}'
        websocket.attach_mock(recv, 'recv')

        player = Player(None, websocket)
        answer = asyncio.run(player.recv_answer())

        self.assertEqual(answer, "nothing",
                         "recv_answer() did not return 'result'")
