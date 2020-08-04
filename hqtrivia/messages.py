import json
from string import Template

TEMPLATE_GAME_SESSION_ERROR = Template(
    'Error encountered in game session $gameid. Aborting game.')
TEMPLATE_WAITING_FOR_PLAYERS = Template(
    'Please be patient. Waiting for $players players to join.')
TEMPLATE_GAME_ROUND_STARTING = Template('Game round $round starting.')
MESSAGE_NETWORK_ERROR_OCCURRED = 'Network error encountered. Please try again later.'
MESSAGE_CORRECT_ANSWER = 'You answered correctly!'
MESSAGE_YOU_ARE_ELIMINATED = 'Did not receive a correct response! You have been eliminated from the game!'
MESSAGE_YOU_ARE_THE_WINNER = 'Congratulations, you are the winner!'
