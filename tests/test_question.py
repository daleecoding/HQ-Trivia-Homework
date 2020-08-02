import asyncio
import unittest
from hqtrivia.question import Question


class QuestionTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_question(self):
        """Test the actual question retrieval and checks the validity of the Question instance.
        """

        question = asyncio.run(Question.generate())

        self.assertGreater(len(question.choices), 1,
                           "Choices returned must be greater than 1")
        self.assertIsNotNone(
            question.answer, "Answer returned must not be None")

        count = 0

        for c in question.choices:
            if (c == question.answer):
                count += 1

        self.assertEqual(count, 1, "Only one choice must be an answer")
