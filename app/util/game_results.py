class GameResults(object):
    def __init__(self):
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self.in_progress = 0

    def add_result(self, result: str):
        if result == 'win':
            self.wins += 1
        elif result == 'loss':
            self.losses += 1
        elif result == 'draw':
            self.draws += 1
        elif result == 'in_progress':
            self.in_progress += 1
        else:
            raise ValueError(f"Unknown result: {result}")

    def count(self):
        return self.wins + self.losses

    def win_loss_str(self):
        if self.wins + self.losses + self.draws + self.in_progress == 0:
            return ''
        else:
            return f"{self.wins}-{self.losses}"

    def __str__(self):
        return f"{self.wins}-{self.losses}-{self.draws}-{self.in_progress}"
