import unittest
from hqtrivia.gamemanager import GameManager


class GameManagerTest(unittest.Testcase):

    def setUp(self):
        pass

    def test_sanity(self):
        game_manager = GameManager()
        self.assertFalse(False, "Not Implemented")


if __name__ == '__main__':
    unittest.main()
