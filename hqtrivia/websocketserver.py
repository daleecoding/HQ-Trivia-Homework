import asyncio
import logging
import websockets


class WebsocketCallbackInterface:
    """
    WebsocketServer callback interface.

    Any events of user's interest will be notified through the callback
    implementation provided by the user.
    """

    async def handle_new_websocket(self, websocket: websockets.WebSocketServerProtocol):
        """Notifies that there is a new client websocket connection.

        This is an asyncio coroutine.

        Parameters
        ----------
        websocket : websocket
            The new websocket object associated with the new client connection.
        """
        pass


class WebsocketServer:
    """
    WebsocketServer implementation based on websockets library.

    Purpose of this class is to provide a simple websocket server
    implementation where the user is only interested in implementing
    a coroutine for handling a new client websocket.
    """

    def __init__(self, port: int, callback: WebsocketCallbackInterface):
        """
        Parameters
        ----------
        port: int
            websocket TCP accept port
        callback: WebsocketCallbackInterface
            User's callback implementation
        """

        self.port = port
        self.callback = callback

    async def ws_handler_impl(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """ws_handler implementation for use with the Python websockets serve().

        Parameters
        ----------
        websocket: WebSocketServerProtocol
            The websocket for the new connection
        path: str
            The wss request URI that created the websocket connection
        """
        try:
            await self.callback.handle_new_websocket(websocket)

        except Exception as e:
            logging.error("Exception occurred", exc_info=True)

        # websocket library will ensure that the websockets gets closed,
        # and I do not have to close it here.

    async def start(self):
        # Do not specify the host so that I'm not bound to a specific NIC
        await websockets.serve(
            self.ws_handler_impl, port=self.port)
