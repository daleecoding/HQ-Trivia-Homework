from string import Template

TEMPLATE_GAME_SESSION_ERROR = Template(
    'Error encountered in game session $gameid. Aborting game.')
MESSAGE_NETWORK_ERROR_OCCURRED = 'Network error encountered. Please try again later.'
MESSAGE_CORRECT_MOVING_TO_NEXT_ROUND = 'Correct! You are moving to the next round!'
MESSAGE_YOU_ARE_ELIMINATED = 'Did not receive a correct response! You have been eliminated from the game!'
MESSAGE_YOU_ARE_THE_WINNER = 'Congratulations, you are the winner!'
