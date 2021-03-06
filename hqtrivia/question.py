from aiohttp import ClientSession
import asyncio
import json
import random
from typing import List

import hqtrivia.config as config

"""
Abstracts the multiple question to be used in the trivia game.
"""


class Question:
    """
    Represents 1 multiple question that will be used in a game round.
    """

    def __init__(self, question: str, choices: List[str], answer: str):
        self.question = question
        self.choices = choices
        self.answer = answer

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return str(self.__dict__)

    @staticmethod
    async def generate() -> 'Question':
        """Generates a new question by calling a RESTful API on an open trivia internet server.

        Returns
        -------
        Returns the new question if successful.  If error was encountered or response is not 200 OK,
        an exception will be thrown.
        """
        async with ClientSession() as session:
            async with session.get(config.CONFIG_QUESTION_GENERATOR_API) as resp:
                if (resp.status != 200):
                    raise Exception(
                        f"Received response {resp.status} from {config.CONFIG_QUESTION_GENERATOR_API}")

                # Convert JSON to our Question and return it
                text = await resp.text()
                return opentdb_json_to_question(text)


def opentdb_json_to_question(json_text: str) -> Question:
    """A quick "hack" for converting opentdb json result to our Question instance.

    Example JSON from opentdb.com:

    {
        "response_code": 0,
        "results": [{
            "category": "General Knowledge",
            "type": "multiple",
            "difficulty": "medium",
            "question": "What is real haggis made of?",
            "correct_answer": "Sheep&#039;s Heart, Liver and Lungs",
            "incorrect_answers": ["Sheep&#039;s Heart, Kidneys and Lungs", "Sheep&#039;s Liver, Kidneys and Eyes", "Whole Sheep"]
        }]
    }
    """

    result = json.loads(json_text)['results'][0]
    incorrect_choices = result['incorrect_answers']
    answer = result['correct_answer']

    # Insert correct answer randomly into the middle of incorrect answers
    random_index = random.randint(0, len(incorrect_choices))

    choices = incorrect_choices.copy()
    choices.insert(random_index, answer)

    return Question(result['question'], choices, answer)
