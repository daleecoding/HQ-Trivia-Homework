import unittest
from hqtrivia.gamesession import GameSession


class GameSessionTest(unittest.Testcase):

    def setUp(self):
        pass

    def test_sanity(self):
        game = GameSession(0, [])
        self.assertFalse(False, "Not Implemented")


if __name__ == '__main__':
    unittest.main()
