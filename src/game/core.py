import sys
import pygame
from .player import Player
from .rope import Rope

class Game:
    def __init__(self, screen, width, height):
        self.screen = screen
        self.width = width
        self.height = height
        self.clock = pygame.time.Clock()
        self.rope = Rope(width, height)
        self.left = Player('left', x=70, y=height//2)
        self.right = Player('right', x=width-130, y=height//2)

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            keys = pygame.key.get_pressed()
            self.left.handle_input(keys)
            self.right.handle_input(keys)

            # apply pulls to rope
            self.rope.apply_pull(self.left.pull, self.right.pull)

            # draw
            self.screen.fill((30, 30, 30))
            self.left.draw(self.screen)
            self.right.draw(self.screen)
            self.rope.draw(self.screen)

            pygame.display.flip()
            self.clock.tick(60)