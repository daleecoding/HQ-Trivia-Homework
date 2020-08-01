import unittest
from hqtrivia.question import Question


class QuestionTest(unittest.Testcase):

    def setUp(self):
        pass

    def test_sanity(self):
        question = Question.generate()
        self.assertFalse(False, "Not Implemented")


if __name__ == '__main__':
    unittest.main()
