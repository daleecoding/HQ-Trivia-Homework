import json
import logging

# Configuration variables with default values assigned
CONFIG_LOG_LEVEL = logging.INFO
CONFIG_PLAYERS_PER_GAME = 2
CONFIG_WS_SERVER_PORT = 9999
CONFIG_ROUND_DURATION = 10
CONFIG_QUESTION_GENERATOR_API = 'http://opentdb.com/api.php?amount=1&type=multiple&difficulty=easy'


def load_config(config_file: str):
    global CONFIG_LOG_LEVEL
    global CONFIG_PLAYERS_PER_GAME
    global CONFIG_WS_SERVER_PORT
    global CONFIG_ROUND_DURATION
    global CONFIG_QUESTION_GENERATOR_API

    with open(config_file) as config_file:
        data = json.load(config_file)

        if ('log_level' in data):
            CONFIG_LOG_LEVEL = data['log_level']

        if ('players_per_game' in data):
            CONFIG_PLAYERS_PER_GAME = data['players_per_game']

        if ('ws_server_port' in data):
            CONFIG_WS_SERVER_PORT = data['ws_server_port']

        if ('round_duration' in data):
            CONFIG_ROUND_DURATION = data['round_duration']

        if ('question_generator_api' in data):
            CONFIG_QUESTION_GENERATOR_API = data['question_generator_api']
