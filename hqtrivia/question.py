import asyncio
from aiohttp import ClientSession


class Question:
    """
    Represents 1 multiple question that will be used in a game round.
    """

    HTTP_TIMEOUT = 10
    QUESTION_GENERATOR_API = 'http://opentdb.com/api.php?amount=1&type=multiple'

    def __init__(self, question: str, choices: List[str], answer: str):
        self.question = question
        self.choices = choices
        self.answer = answer

    @staticmethod
    async def generate() -> Question:
        pass
