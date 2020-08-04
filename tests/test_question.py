import aiohttp
import asyncio
import logging
import unittest
from unittest.mock import AsyncMock
from unittest.mock import patch

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

        string = "Question is " + str([question])

        self.assertGreater(len(question.choices), 1,
                           "Choices returned must be greater than 1")

        self.assertEqual(len(question.choices), len(
            set(question.choices)), "Choices returned are not unique")

        self.assertIsNotNone(
            question.answer, "Answer returned must not be None")

        count = 0

        for c in question.choices:
            if (c == question.answer):
                count += 1

        self.assertEqual(count, 1, "Only one choice must be an answer")

    def test_question_when_http_request_gets_400(self):
        """Test when the HTTP GET returns 400 from the Trivia server
        """

        # Point to a server that always returns 400
        self.backup_api = Question.QUESTION_GENERATOR_API
        Question.QUESTION_GENERATOR_API = 'http://httpbin.org/status/400'

        try:
            with self.assertRaises(Exception):
                asyncio.run(Question.generate())

        finally:
            Question.QUESTION_GENERATOR_API = self.backup_api
