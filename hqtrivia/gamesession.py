
class RoundResult:

    def __init__(self, winner: Player, question: Question, count_per_choice: List[int]):
        self.winner = winner
        self.question = question
        self.count_per_choice = count_per_choice


class GameSession:

    def __init__(self, game_id: str, players: List[Player]):
        self.game_id = id
        self.players = players
        self.current_round = 0
        self.current_question = None

    def on_round_started_get_question(self) -> Question:
        pass

    def on_player_submit_answer(self, player_id: str, answer: str):
        pass

    def on_round_ended_get_result(self) -> RoundResult:
        pass

    def on_player_leave_game(self, player_id: str):
        pass
