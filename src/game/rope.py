import pygame

class Rope:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.y = height // 2
        self.pos = width // 2
        self.min_x = 50
        self.max_x = width - 50

    def apply_pull(self, left_pull, right_pull):
        # right_pull moves pos right, left_pull moves pos left
        self.pos += (right_pull - left_pull)
        self.pos = max(self.min_x, min(self.max_x, self.pos))

    def draw(self, surface):
        pygame.draw.line(surface, (200,180,50), (50, self.y), (int(self.pos), self.y), 6)
        pygame.draw.line(surface, (200,180,50), (int(self.pos), self.y), (self.width-50, self.y), 6)
        pygame.draw.circle(surface, (255,255,255), (int(self.pos), self.y), 8)