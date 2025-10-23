class Player:
    def __init__(self, name):
        self.name = name
        self.strength = 100  # Initial strength of the player
        self.position = 0    # Position on the rope

    def pull(self):
        # Logic for pulling the rope
        pass

    def release(self):
        # Logic for releasing the pull
        pass

    def get_status(self):
        return {
            'name': self.name,
            'strength': self.strength,
            'position': self.position
        }