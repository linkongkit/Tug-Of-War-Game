class Rope:
    def __init__(self, length):
        self.length = length
        self.tension = 0

    def pull(self, force):
        self.tension += force

    def release(self, force):
        self.tension = max(0, self.tension - force)

    def get_tension(self):
        return self.tension

    def reset(self):
        self.tension = 0