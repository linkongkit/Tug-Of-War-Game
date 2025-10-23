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
        self.font = pygame.font.SysFont(None, 48)
        self.game_over = False
        self.winner = None

    def reset(self):
        self.rope = Rope(self.width, self.height)
        self.left.pull = 0
        self.right.pull = 0
        self.game_over = False
        self.winner = None

    def draw_game_over(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0,0,0,160))
        self.screen.blit(overlay, (0,0))

        text = f"{self.winner} wins!"
        txt_surf = self.font.render(text, True, (255,255,255))
        rect = txt_surf.get_rect(center=(self.width//2, self.height//2 - 20))
        self.screen.blit(txt_surf, rect)

        hint = "Press R to restart or Esc to quit"
        hint_surf = self.font.render(hint, True, (200,200,200))
        hint_rect = hint_surf.get_rect(center=(self.width//2, self.height//2 + 40))
        self.screen.blit(hint_surf, hint_rect)

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and self.game_over:
                    if event.key == pygame.K_r:
                        self.reset()
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

            keys = pygame.key.get_pressed()

            if not self.game_over:
                self.left.handle_input(keys)
                self.right.handle_input(keys)

                # apply pulls to rope
                self.rope.apply_pull(self.left.pull, self.right.pull)

                # check win condition
                if self.rope.pos <= self.rope.min_x:
                    self.game_over = True
                    self.winner = "Left team"
                elif self.rope.pos >= self.rope.max_x:
                    self.game_over = True
                    self.winner = "Right team"

            # draw
            self.screen.fill((30, 30, 30))
            self.left.draw(self.screen)
            self.right.draw(self.screen)
            self.rope.draw(self.screen)

            if self.game_over:
                self.draw_game_over()

            pygame.display.flip()
            self.clock.tick(60)