import sys
import pygame
from .player import Player
from .rope import Rope
from .utils import play_music, stop_music, load_image

class Game:
    def __init__(self, screen=None, width=800, height=480, ai=False):
        # allow tests to call Game() with no args; create a dummy surface if needed
        self.width = width
        self.height = height
        self.ai_enabled = ai
        self.current_music = None

        # ensure pygame subsystems needed here are initialized
        if not pygame.get_init():
            pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()

        # if no screen provided (e.g. in unit tests), create an offscreen Surface
        self.screen = screen if screen is not None else pygame.Surface((self.width, self.height))

        self.clock = pygame.time.Clock()
        self.rope = Rope(self.width, self.height)
        # align rope with window center and move down 20px
        try:
            self.rope.y = self.height // 2 + 20
        except Exception:
            pass
        self.left = Player('left', x=70, y=self.height//2 + 20)
        self.right = Player('right', x=self.width-130, y=self.height//2 + 20)

        # align rope with players so knot/body center with characters
        try:
            # Align rope to character center. If the sprite anchor makes the rope appear low,
            # apply a small upward offset. Tweak offset_pct to fine-tune.
            offset_pct = -0.15   # negative moves rope upward; adjust (e.g. -0.15 -> -15% of player height)
            rope_offset = int(self.left.height * offset_pct)
            self.rope.y = self.left.y + rope_offset
        except Exception:
            pass

        # fonts doubled for larger window
        self.font = pygame.font.SysFont(None, 48)
        self.title_font = pygame.font.SysFont(None, 72)
        self.small_font = pygame.font.SysFont(None, 28)
        self.game_over = False
        self.winner = None

        # track previous pull to detect start events
        self.left_prev_pull = 0
        self.right_prev_pull = 0

        # initial state expected by tests: "waiting"
        self.state = "waiting"

        # menu selection + flicker state
        self.menu_selected_choice = None      # '1' or '2' while flickering
        self.menu_flicker_timer = 0
        self.menu_flicker_duration = 120      # frames to flicker before starting (~2s at 60fps)
        self.menu_flicker_rate = 4           # frames per blink

        # try to start menu music if main.py attached it to the Game instance
        try:
            self._set_music("menu")
        except Exception:
            pass

        # load gameplay background (put file at src/assets/sprites/gameplay-bg.png)
        self.game_bg = load_image("gameplay-bg.png")
        if self.game_bg:
            try:
                self.game_bg = pygame.transform.smoothscale(self.game_bg, (self.width, self.height))
            except Exception:
                pass

    def _set_music(self, which):
        """Switch background music to 'menu' or 'gameplay' (safe if files missing)."""
        if which == "menu":
            path = getattr(self, "menu_music", None)
        elif which == "gameplay":
            path = getattr(self, "gameplay_music", None)
        else:
            path = None

        # if same music already playing, do nothing
        if path == self.current_music:
            return

        if path:
            play_music(path, loops=-1, volume=0.6)
            self.current_music = path
        else:
            stop_music()
            self.current_music = None

    def _maybe_play_select_sound(self):
        snd = getattr(self, "select_sound", None)
        if snd is None:
            return
        try:
            snd.play()
        except Exception:
            pass

    def start(self):
        """Start the game (used by tests)."""
        # set the state the tests expect
        self.state = "running"
        # reset gameplay state when starting a new round
        self.game_over = False
        self.winner = None
        self.rope = Rope(self.width, self.height)
        # align rope to window center and move down 20px on start
        try:
            self.rope.y = self.height // 2 + 20
        except Exception:
            pass

        # clear pulls and previous-pull trackers
        self.left.pull = 0
        self.right.pull = 0
        self.left_prev_pull = 0
        self.right_prev_pull = 0

        # reset player timers so no leftover tap/AI burst triggers a forced start
        self.left.tap_timer = 0
        self.right.tap_timer = 0
        self.left.ai_burst_timer = 0
        self.right.ai_burst_timer = 0
        self.left.ai_pause_timer = 0
        self.right.ai_pause_timer = 0

        # enforce symmetric parameters (keeps pulls fair)
        PULL_POWER = 6
        TAP_DURATION = 6
        MAX_STAMINA = 100.0
        STAMINA_DRAIN = 1.5
        STAMINA_REGEN = 0.8

        self.left.pull_strength = PULL_POWER
        self.right.pull_strength = PULL_POWER
        self.left.tap_duration = TAP_DURATION
        self.right.tap_duration = TAP_DURATION
        self.left.max_stamina = MAX_STAMINA
        self.right.max_stamina = MAX_STAMINA
        self.left.stamina = MAX_STAMINA
        self.right.stamina = MAX_STAMINA
        self.left.stamina_drain = STAMINA_DRAIN
        self.right.stamina_drain = STAMINA_DRAIN
        self.left.stamina_regen = STAMINA_REGEN
        self.right.stamina_regen = STAMINA_REGEN

        # give AI a short initial pause so it doesn't burst immediately on game start
        if self.ai_enabled:
            self.right.ai_pause_timer = 12  # ~0.2s at 60fps; increase if needed

        # switch to gameplay music if available
        try:
            self._set_music("gameplay")
        except Exception:
            pass

    def end(self):
        """End the current game (used by tests)."""
        self.game_over = True
        # set state the tests expect
        self.state = "ended"

    def reset(self):
        self.rope = Rope(self.width, self.height)
        # align rope to window center and move down 20px on reset
        try:
            self.rope.y = self.height // 2 + 20
        except Exception:
            pass
        self.left.pull = 0
        self.right.pull = 0
        self.game_over = False
        self.winner = None
        self.left_prev_pull = 0
        self.right_prev_pull = 0
        self.state = "waiting"

        # switch back to menu music
        try:
            self._set_music("menu")
        except Exception:
            pass

    def draw_menu(self):
        self.screen.fill((18, 18, 30))
        title = "Tug Of War"
        title_surf = self.title_font.render(title, True, (255, 230, 160))
        title_rect = title_surf.get_rect(center=(self.width//2, self.height//2 - 100))
        self.screen.blit(title_surf, title_rect)

        lines = [
            "Press 1 for Single-player (vs AI)",
            "Press 2 for Two-player (local)",
            "Controls: A = Left pull    L = Right pull",
            "Press Esc to quit"
        ]
        for i, line in enumerate(lines):
            # if a choice is flickering, compute visibility / color for that line
            visible = True
            color = (200, 200, 200)
            if self.menu_selected_choice is not None:
                # map '1' -> index 0, '2' -> index 1
                sel_index = 0 if self.menu_selected_choice == '1' else 1
                if i == sel_index:
                    # blink based on timer
                    blink_phase = (self.menu_flicker_timer // self.menu_flicker_rate) % 2
                    if blink_phase == 0:
                        # visible frame, highlight
                        color = (255, 250, 120)
                    else:
                        # hidden/dim frame
                        color = (70, 70, 70)
                else:
                    # other lines dim while selection flickers
                    color = (120, 120, 120)

            surf = self.small_font.render(line, True, color)
            rect = surf.get_rect(center=(self.width//2, self.height//2 - 20 + i*30))
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
            # capture previous pulls for sound detection
            prev_left = self.left.pull
            prev_right = self.right.pull

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

                    if self.state == "waiting":
                        # CHANGED: start flicker + sound, delay actual start until flicker finishes
                        if event.key == pygame.K_1:
                            # begin single-player selection flicker
                            self.menu_selected_choice = '1'
                            self.menu_flicker_timer = self.menu_flicker_duration
                            self._maybe_play_select_sound()
                        elif event.key == pygame.K_2:
                            # begin two-player selection flicker
                            self.menu_selected_choice = '2'
                            self.menu_flicker_timer = self.menu_flicker_duration
                            self._maybe_play_select_sound()
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                            # Enter starts immediately using current ai flag
                            self.start()
                    elif self.game_over:
                        if event.key == pygame.K_r:
                            self.reset()
                        elif event.key == pygame.K_ESCAPE:
                            pygame.quit()
                            sys.exit()
                    else:
                        # gameplay keydown -> trigger tap pulls (single press)
                        if event.key == pygame.K_a:
                            self.left.press_pull()
                        if event.key == pygame.K_l and not self.ai_enabled:
                            # only allow right human pull if not using AI
                            self.right.press_pull()

            # handle menu selection flicker countdown (if active)
            if self.menu_flicker_timer > 0:
                self.menu_flicker_timer -= 1
                # when timer reaches zero, finalize choice and start game
                if self.menu_flicker_timer == 0 and self.menu_selected_choice is not None:
                    if self.menu_selected_choice == '1':
                        self.ai_enabled = True
                    else:
                        self.ai_enabled = False
                    # clear selection state and actually start the game
                    self.menu_selected_choice = None
                    self.start()

            keys = pygame.key.get_pressed()  # still available if needed elsewhere

            if self.state == "waiting":
                self.draw_menu()
            elif not self.game_over:
                # Left human updates
                self.left.update()

                # Right: AI or human
                if self.ai_enabled:
                    self.right.ai_act(self.rope.pos, self.width // 2, opponent_pull=prev_left)
                    self.right.update()
                else:
                    self.right.update()

                # play pull-start sound if someone just started pulling
                if self.left.pull > 0 and prev_left == 0:
                    self._maybe_play_pull_sound()
                if self.right.pull > 0 and prev_right == 0:
                    self._maybe_play_pull_sound()

                # apply pulls to rope
                self.rope.apply_pull(self.left.pull, self.right.pull)

                # check win condition...
                if self.rope.pos <= self.rope.min_x:
                    self.game_over = True
                    self.winner = "Left team"
                    self._maybe_play_win_sound()
                elif self.rope.pos >= self.rope.max_x:
                    self.game_over = True
                    self.winner = "Right team"
                    self._maybe_play_win_sound()

            # draw: use background during gameplay, menu draws with draw_menu()
            if self.state == "waiting":
                # draw menu (draw_menu fills the screen)
                self.draw_menu()
            elif self.game_over:
                # final frame: keep background visible behind game over overlay
                if self.game_bg:
                    self.screen.blit(self.game_bg, (0, 0))
                else:
                    self.screen.fill((30, 30, 30))
                self.rope.draw_body(self.screen)
                self.left.draw(self.screen)
                self.right.draw(self.screen)
                self.rope.draw_knot(self.screen)
                self.draw_game_over()
            else:
                # gameplay: background -> rope body -> characters -> knot on top
                if self.game_bg:
                    self.screen.blit(self.game_bg, (0, 0))
                else:
                    self.screen.fill((30, 30, 30))
                self.rope.draw_body(self.screen)
                self.left.draw(self.screen)
                self.right.draw(self.screen)
                self.rope.draw_knot(self.screen)
 
            # (display flip / tick follows)
            pygame.display.flip()
            self.clock.tick(60)