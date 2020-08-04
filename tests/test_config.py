import aiohttp
import asyncio
import logging
import unittest
from unittest.mock import AsyncMock
from unittest.mock import patch

import hqtrivia.config as config


class ConfigTest(unittest.TestCase):

    def test_load_config(self):
        """Tests load_config method
        """
        config.load_config('tests/test_config.json')

        self.assertEqual(config.CONFIG_LOG_LEVEL, 40)
        self.assertEqual(config.CONFIG_PLAYERS_PER_GAME, 100)
        self.assertEqual(config.CONFIG_WS_SERVER_PORT, 8080)
        self.assertEqual(config.CONFIG_ROUND_DURATION, 60)
        self.assertEqual(config.CONFIG_QUESTION_GENERATOR_API,
                         'http://httpbin.org/status/400')
