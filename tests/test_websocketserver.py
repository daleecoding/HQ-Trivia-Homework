import asyncio
import unittest
import unittest
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch
import websockets

from hqtrivia.websocketserver import WebsocketServer


class WebsocketServerTest(unittest.TestCase):

    @patch('websockets.serve', new_callable=AsyncMock)
    def test_start(self, serve):
        """Tests whether start() calls serve() on websockets with correct arguments
        """

        wss = WebsocketServer(64823, None)

        asyncio.run(wss.start())

        serve.assert_called_once_with(wss.ws_handler_impl, port=64823)

    def test_ws_handler_impl(self):
        """Tests whether ws_handler_impl() calls callback with correct arguments
        """

        callback = MagicMock()
        wss = WebsocketServer(64823, callback)
        handle_new_websocket = AsyncMock()
        wss.callback.attach_mock(handle_new_websocket, 'handle_new_websocket')

        ws = MagicMock()

        asyncio.run(wss.ws_handler_impl(ws, None))

        handle_new_websocket.assert_called_once_with(ws)

    def test_ws_handler_impl_throws_exception(self):
        """Tests when ws_handler_impl() encounters exception thrown from the callback. It is expected to eat up the exception.
        """

        callback = MagicMock()
        wss = WebsocketServer(64823, callback)
        handle_new_websocket = AsyncMock(
            side_effect=Exception("Error Occurred"))
        wss.callback.attach_mock(handle_new_websocket, 'handle_new_websocket')

        ws = MagicMock()

        asyncio.run(wss.ws_handler_impl(ws, None))

        handle_new_websocket.assert_called_once_with(ws)
