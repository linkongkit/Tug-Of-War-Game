import pygame

class Player:
    def __init__(self, side, x=0, y=0):
        self.side = side
        self.x = x
        self.y = y
        self.width = 60
        self.height = 80
        self.pull = 0
        self.pull_strength = 5

    def handle_input(self, keys):
        # left player uses A, right player uses L
        if self.side == 'left':
            self.pull = self.pull_strength if keys[pygame.K_a] else 0
        else:
            self.pull = self.pull_strength if keys[pygame.K_l] else 0

    def draw(self, surface):
        color = (150, 50, 50) if self.side == 'left' else (50, 50, 150)
        rect = pygame.Rect(self.x, self.y - self.height // 2, self.width, self.height)
        pygame.draw.rect(surface, color, rect)