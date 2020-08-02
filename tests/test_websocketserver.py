import unittest
from hqtrivia.websocketserver import WebsocketServer


class WebsocketServerTest(unittest.Testcase):

    def setUp(self):
        pass

    def test_sanity(self):
        game = WebsocketServer(9999, None)
        self.assertFalse(False, "Not Implemented")
