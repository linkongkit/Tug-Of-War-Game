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
        self.title_font = pygame.font.SysFont(None, 72)
        self.small_font = pygame.font.SysFont(None, 28)
        self.game_over = False
        self.winner = None

        # track previous pull to detect start events
        self.left_prev_pull = 0
        self.right_prev_pull = 0

        # initial state: show menu until Enter pressed
        self.state = "menu"

    def reset(self):
        self.rope = Rope(self.width, self.height)
        self.left.pull = 0
        self.right.pull = 0
        self.game_over = False
        self.winner = None
        self.left_prev_pull = 0
        self.right_prev_pull = 0
        self.state = "menu"

    def draw_menu(self):
        self.screen.fill((18, 18, 30))
        title = "Tug Of War"
        title_surf = self.title_font.render(title, True, (255, 230, 160))
        title_rect = title_surf.get_rect(center=(self.width//2, self.height//2 - 80))
        self.screen.blit(title_surf, title_rect)

        lines = [
            "Press Enter to Start",
            "Controls: A = Left pull    L = Right pull",
            "Press Esc to quit"
        ]
        for i, line in enumerate(lines):
            surf = self.small_font.render(line, True, (200, 200, 200))
            rect = surf.get_rect(center=(self.width//2, self.height//2 - 20 + i*32))
            self.screen.blit(surf, rect)

    def draw_game_over(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0,0,0,160))
        self.screen.blit(overlay, (0,0))

        text = f"{self.winner} wins!"
        txt_surf = self.font.render(text, True, (255,255,255))
        rect = txt_surf.get_rect(center=(self.width//2, self.height//2 - 20))
        self.screen.blit(txt_surf, rect)

        hint = "Press R to restart or Esc to quit"
        hint_surf = self.small_font.render(hint, True, (200,200,200))
        hint_rect = hint_surf.get_rect(center=(self.width//2, self.height//2 + 40))
        self.screen.blit(hint_surf, hint_rect)

    def _maybe_play_pull_sound(self):
        # safe-play attached pull_sound from main.py if present
        snd = getattr(self, "pull_sound", None)
        if snd is None:
            return
        try:
            snd.play()
        except Exception:
            pass

    def _maybe_play_win_sound(self):
        snd = getattr(self, "win_sound", None)
        if snd is None:
            return
        try:
            snd.play()
        except Exception:
            pass

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if self.state == "menu":
                        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                            self.state = "playing"
                    elif self.game_over:
                        if event.key == pygame.K_r:
                            self.reset()
                        elif event.key == pygame.K_ESCAPE:
                            pygame.quit()
                            sys.exit()

            keys = pygame.key.get_pressed()

            if self.state == "menu":
                self.draw_menu()
            elif not self.game_over:
                # store previous pulls to detect start
                prev_left = self.left.pull
                prev_right = self.right.pull

                self.left.handle_input(keys)
                self.right.handle_input(keys)

                # if a player just started pulling, play sound
                if self.left.pull > 0 and prev_left == 0:
                    self._maybe_play_pull_sound()
                if self.right.pull > 0 and prev_right == 0:
                    self._maybe_play_pull_sound()

                # apply pulls to rope
                self.rope.apply_pull(self.left.pull, self.right.pull)

                # check win condition (left boundary => Left team wins)
                if self.rope.pos <= self.rope.min_x:
                    self.game_over = True
                    self.winner = "Left team"
                    self._maybe_play_win_sound()   # play win sound
                elif self.rope.pos >= self.rope.max_x:
                    self.game_over = True
                    self.winner = "Right team"
                    self._maybe_play_win_sound()   # play win sound

            # draw
            self.screen.fill((30, 30, 30))
            self.left.draw(self.screen)
            self.right.draw(self.screen)
            self.rope.draw(self.screen)

            if self.game_over:
                self.draw_game_over()
            elif self.state == "menu":
                self.draw_menu()

            pygame.display.flip()
            self.clock.tick(60)