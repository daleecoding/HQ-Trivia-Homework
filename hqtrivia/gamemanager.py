
class GameManager:

    def __init__(self):
        self.server = None
        self.waiting_players = []
        self.active_player_to_game = {}
        self.games = {}

    def start(self):
        self.server = WebsocketServer(9999, self)
