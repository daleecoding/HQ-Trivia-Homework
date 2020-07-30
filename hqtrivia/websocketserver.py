

class WebsocketCallbackInterface:
    def on_connected(self, id: int):
        pass

    def on_disconnected(self, id: int):
        pass


class WebsocketServer:

    def __init__(self, port: int, callback: WebsocketCallbackInterface):
        self.port = port
        self.callback = callback
