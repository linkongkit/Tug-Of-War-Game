import sys
import pygame
from .player import Player
from .rope import Rope
from .utils import load_image, load_sound, load_music
from game.projectile import Bomb
import random
import os
import pygame

# Minimal SpriteEffect implementation used by spawn_effect.
# Provides update(), draw() and finished flag so effects list in Game works.
class SpriteEffect:
    def __init__(self, x, y, frames, frame_rate=12):
        # x,y are screen coordinates (center)
        self.x = int(x)
        self.y = int(y)
        # store frames (list of pygame.Surface)
        self.frames = list(frames) if frames is not None else []
        # frame_rate is number of game ticks per frame (must be >=1)
        try:
            self.frame_rate = max(1, int(frame_rate))
        except Exception:
            self.frame_rate = 12
        self._tick = 0
        self._index = 0
        self.finished = False

    def update(self):
        if self.finished or not self.frames:
            return
        self._tick += 1
        if self._tick >= self.frame_rate:
            self._tick = 0
            self._index += 1
            if self._index >= len(self.frames):
                # mark finished and clamp index to last frame
                self.finished = True
                self._index = max(0, len(self.frames) - 1)

    def draw(self, surface):
        if not self.frames or surface is None:
            return
        try:
            img = self.frames[self._index]
            rect = img.get_rect(center=(self.x, self.y))
            surface.blit(img, rect)
        except Exception:
            # safe no-op on any drawing error
            pass

def load_sequence(folder_name, pad=3):
    """Load frames named folder_name/frame_###.png from sprites folder."""
    frames = []
    i = 0
    while True:
        name = f"{folder_name}/frame_{i:0{pad}d}.png"
        img = load_image(name)
        if img is None:
            break
        frames.append(img)
        i += 1
    return frames

class Game:
    def __init__(self, screen, width, height, ai=False):
        self.screen = screen
        self.width = width
        self.height = height

        # try common filename variants for the menu background
        bg_candidates = ["homepage bg.jpg", "homepage-bg.jpg", "homepage_bg.jpg", "homepage.jpg"]
        self.menu_bg = None
        for name in bg_candidates:
            img = load_image(name)
            if img:
                self.menu_bg = img
                print(f"[debug] menu background loaded: {name}")
                break
        if self.menu_bg:
            try:
                self.menu_bg = pygame.transform.smoothscale(self.menu_bg, (self.width, self.height))
            except Exception:
                self.menu_bg = pygame.transform.scale(self.menu_bg, (self.width, self.height))
        else:
            print("[debug] menu background not found; checked:", bg_candidates)

        # -------- Determination font (robust lookup + debug) --------
        pygame.font.init()
        font_candidates = [
            os.path.join(os.path.dirname(__file__), "..", "assets", "fonts", "determination.ttf"),
            os.path.join(os.path.dirname(__file__), "..", "..", "src", "assets", "fonts", "determination.ttf"),
            os.path.join(os.getcwd(), "src", "assets", "fonts", "determination.ttf"),
            os.path.join(os.getcwd(), "assets", "fonts", "determination.ttf"),
            os.path.normpath("src/assets/fonts/determination.ttf"),
            os.path.normpath("assets/fonts/determination.ttf"),
        ]
        font_path = None
        for p in font_candidates:
            p = os.path.abspath(p)
            if os.path.isfile(p):
                font_path = p
                break
        if font_path:
            try:
                # even smaller sizes
                self.menu_font = pygame.font.Font(font_path, 28)
                self.menu_small_font = pygame.font.Font(font_path, 14)
                self.menu_hint_font = pygame.font.Font(font_path, 12)
                self.menu_label_font = pygame.font.Font(font_path, 12)
                self.determination_hint_font = pygame.font.Font(font_path, 10)
                print(f"[debug] loaded determination.ttf from: {font_path}")
            except Exception as e:
                print(f"[debug] failed to load determination.ttf from {font_path}: {e}")
                self.menu_font = pygame.font.SysFont(None, 28)
                self.menu_small_font = pygame.font.SysFont(None, 14)
                self.menu_hint_font = pygame.font.SysFont(None, 12)
                self.menu_label_font = pygame.font.SysFont(None, 12)
                self.determination_hint_font = pygame.font.SysFont(None, 10)
        else:
            print("[debug] determination.ttf not found. Checked:", font_candidates)
            self.menu_font = pygame.font.SysFont(None, 28)
            self.menu_small_font = pygame.font.SysFont(None, 14)
            self.menu_hint_font = pygame.font.SysFont(None, 12)
            self.menu_label_font = pygame.font.SysFont(None, 12)
            self.determination_hint_font = pygame.font.SysFont(None, 10)
        # ------------------------------------------------------------

        # create clock and players first so we can align rope to their center
        self.clock = pygame.time.Clock()

        # create players (use self.height for vertical center)
        player_width = 80
        player_height = 120
        left_margin = 100
        right_margin = width - 100 - player_width
        self.left = Player(left_margin, self.height // 2 + 20, player_width, player_height, 'left', 'boy-push.png', 'boy-pull.png')
        self.right = Player(right_margin, self.height // 2 + 20, player_width, player_height, 'right', 'girl-push.png', 'girl-pull.png')
        left_center = left_margin + (self.left.width // 2)
        right_center = self.width - left_center
        self.right.x = int(right_center - (self.right.width // 2))

        # create rope and align it to player center
        self.rope = Rope(self.width, self.height)
        try:
            self.rope.y = self.left.y
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

        # preload clone smoke frames (folder: src/assets/sprites/clone-smoke/)
        try:
            self.clone_smoke_frames = load_sequence("clone-smoke")
        except Exception:
            self.clone_smoke_frames = []

        # active particle/effect list
        self.effects = []

        # active projectiles (bombs)
        self.projectiles = []

        clone_sound = load_sound("clone-smoke.wav")
        if clone_sound:
            clone_sound.set_volume(0.9)

        # attach clone sound to this Game instance instead of creating a nested Game
        self.clone_sound = clone_sound

        self.running = True  # add this line

    def _set_music(self, which):
        """Set background music for 'menu' or 'gameplay' reliably.

        Stops any playing pygame.mixer.music and any previously played Sound object
        before starting the requested track to avoid overlap.
        """
        try:
            music_obj = getattr(self, f"{which}_music", None)
        except Exception:
            music_obj = None
        vol = getattr(self, f"{which}_volume", None)

        

        # stop mixer music first
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

        # stop any previously played Sound-based music we tracked
        try:
            prev = getattr(self, "_playing_music_sound", None)
            if prev:
                try:
                    prev.stop()
                except Exception:
                    pass
                self._playing_music_sound = None
        except Exception:
            pass

        if not music_obj:
            return

        # If load_music returned a filename/path, use pygame.mixer.music
        if isinstance(music_obj, str):
            try:
                pygame.mixer.music.load(music_obj)
                if vol is not None:
                    pygame.mixer.music.set_volume(vol)
                pygame.mixer.music.play(-1)
                self._playing_music_mode = "mixer"
            except Exception as e:
                print(f"[music] failed to load/play {which} ({music_obj}): {e}")
            return

        # Otherwise assume it's a pygame.mixer.Sound — play but track it so we can stop later
        try:
            if vol is not None:
                try:
                    music_obj.set_volume(vol)
                except Exception:
                    pass
            music_obj.play(-1)
            self._playing_music_sound = music_obj
            self._playing_music_mode = "sound"
        except Exception as e:
            print(f"[music] failed to play Sound for {which}: {e}")

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

        # align rope with player center on start
        try:
            self.rope.y = self.left.y
        except Exception:
            pass

        # reset clone state so players get their one chance this round
        try:
            self.left.clone_active = False
            self.left.clone_timer = 0
            self.left.clone_used = False
            self.right.clone_active = False
            self.right.clone_timer = 0
            self.right.clone_used = False
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

        # --- enforce strict symmetry so each tap moves the rope equally ---
        # make each pull half strength to increase difficulty
        PULL_POWER = 3          # single canonical pull strength for both sides (halved)
        TAP_DURATION = 6        # frames a tap lasts
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
        # reset game state for new round and return to menu
        try:
            self.game_over = False
            self.winner = None
            self.state = "waiting"  # return to menu
            try:
                self.rope.reset()
            except Exception:
                pass
            try:
                self.left.reset()
            except Exception:
                pass
            try:
                self.right.reset()
            except Exception:
                pass

            # reset bomb and freeze states
            try:
                self.left.bomb_used = False
                self.left.freeze_timer = 0
            except Exception:
                pass
            try:
                self.right.bomb_used = False
                self.right.freeze_timer = 0
            except Exception:
                pass

            # reset projectiles and effects
            self.projectiles = []
            self.effects = []

            # switch back to menu music
            try:
                self._set_music("menu")
            except Exception:
                pass

        except Exception:
            # ensure we at least go back to menu to avoid quitting
            self.state = "waiting"

    def draw_menu(self):
        if getattr(self, "menu_bg", None):
            self.screen.blit(self.menu_bg, (0, 0))
        else:
            self.screen.fill((20, 30, 40))

        # ...existing menu title / logo drawing code ...

        # Draw the 1P / 2P labels (replace with flicker-aware blit)
        t1 = "Press 1 for 1P"
        t2 = "Press 2 for 2P"
        s1 = self.menu_small_font.render(t1, True, (255, 255, 255))
        s2 = self.menu_small_font.render(t2, True, (255, 255, 255))

        spacing = 40
        total_w = s1.get_width() + spacing + s2.get_width()
        left_shift = 15
        start_x = (self.width - total_w) // 2 - left_shift
        start_x = max(10, start_x)
        bottom_margin = 20
        y = self.height - bottom_margin - s1.get_height()

        # Blit the 1P / 2P labels (replace with flicker-aware blit)
        s2_x = start_x + s1.get_width() + spacing

        # determine flicker visibility (guarded so missing attrs won't crash)
        mf_timer = getattr(self, "menu_flicker_timer", 0)
        mf_rate = getattr(self, "menu_flicker_rate", 4) or 4
        mf_choice = getattr(self, "menu_selected_choice", None)

        # default visible
        vis1 = True
        vis2 = True

        # if flicker active for a choice, toggle visibility every mf_rate frames
        if mf_timer > 0 and mf_choice == '1':
            vis1 = ((mf_timer // mf_rate) % 2) == 0
        if mf_timer > 0 and mf_choice == '2':
            vis2 = ((mf_timer // mf_rate) % 2) == 0

        if vis1:
            self.screen.blit(s1, (start_x, y))
        if vis2:
            self.screen.blit(s2, (s2_x, y))

        # stacked control hints (three rows) using the smaller hint font
        left_lines = ["A = Pull", "D = Bomb", "F = Clone"]
        right_lines = ["L = Pull", "J = Bomb", "H = Clone"]
        hint_color = (200, 200, 200)
        v_spacing = 4

        # render left hint surfaces with smaller font and align to left window edge (x=10)
        left_surfs = [self.menu_hint_font.render(t, True, hint_color) for t in left_lines]
        left_max_w = max(s.get_width() for s in left_surfs)
        left_x = 10  # flush to left frame with 10px padding

        # render right hint surfaces and align to right window edge (width - pad)
        right_surfs = [self.menu_hint_font.render(t, True, hint_color) for t in right_lines]
        right_max_w = max(s.get_width() for s in right_surfs)
        right_x = self.width - right_max_w - 10  # flush to right frame with 10px padding

        # vertical centering of the stacked hints relative to the label baseline y
        n = len(left_surfs)
        line_h = left_surfs[0].get_height()
        total_h = n * line_h + (n - 1) * v_spacing
        top_y = y - total_h // 2

        # blit left stacked hints
        ty = top_y
        for surf in left_surfs:
            self.screen.blit(surf, (left_x, ty))
            ty += line_h + v_spacing

        # blit right stacked hints
        ty = top_y
        for surf in right_surfs:
            # for right alignment of each line, shift by its width so text is flush to right_x
            self.screen.blit(surf, (right_x, ty))
            ty += line_h + v_spacing

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

    def spawn_effect(self, x, y, kind="clone-smoke", frame_rate=12, target_h=None):
        """Spawn a short-lived sprite-sequence effect at screen coords (x,y).
           If target_h is provided, scale the effect frames so their height matches target_h.
        """
        if kind == "clone-smoke":
            frames = getattr(self, "clone_smoke_frames", [])
            if not frames:
                return

            # if target height requested, create scaled copies of frames
            if target_h is not None:
                scaled = []
                for f in frames:
                    fw, fh = f.get_size()
                    if fh == 0:
                        scaled.append(f)
                        continue
                    scale = float(target_h) / float(fh)
                    nw = max(1, int(fw * scale))
                    nh = max(1, int(fh * scale))
                    try:
                        scaled.append(pygame.transform.smoothscale(f, (nw, nh)))
                    except Exception:
                        scaled.append(f)
                frames_used = scaled
            else:
                frames_used = frames

            eff = SpriteEffect(x, y, frames_used, frame_rate=frame_rate)
            self.effects.append(eff)

    def spawn_bomb(self, thrower, target, travel_time_frames=60):
        """Spawn a bomb from thrower aimed at target."""
        if not thrower or not target or getattr(thrower, "bomb_used", False):
            return
        sx = thrower.x + thrower.width // 2
        sy = thrower.y - (thrower.height * 0.1)
        tx = target.x + target.width // 2
        ty = target.y
        dx = tx - sx
        dy = ty - sy
        T = float(max(10, travel_time_frames))
        g = 0.4
        vx = dx / T
        vy = (dy - 0.5 * g * T * T) / T
        bomb = Bomb(sx, sy, vx, vy, gravity=g)
        self.projectiles.append(bomb)
        thrower.bomb_used = True

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
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
                        # left clone special (F)
                        if event.key == pygame.K_f:
                            try:
                                if self.left.activate_clone():
                                    # spawn smoke in front of left player
                                    fx = self.left.x + self.left.width // 2 + int(self.left.width * 0.6) + 5
                                    fy = self.left.y
                                    self.spawn_effect(fx, fy, target_h=self.left.height)
                                    if getattr(self, "clone_sound", None):
                                        self.clone_sound.play()
                            except Exception:
                                pass

                        # right clone special (H)
                        if event.key == pygame.K_h:
                            try:
                                if self.right.activate_clone():
                                    # spawn smoke in front of right player
                                    fx = self.right.x + self.right.width // 2 - int(self.right.width * 0.6) - 5
                                    fy = self.right.y
                                    self.spawn_effect(fx, fy, target_h=self.right.height)
                                    if getattr(self, "clone_sound", None):
                                        self.clone_sound.play()
                            except Exception:
                                pass

                    # bomb throw: D -> left throws to right; J -> right throws to left
                    if event.key == pygame.K_d:
                        try:
                            if not getattr(self.left, "bomb_used", False) and getattr(self.left, "freeze_timer", 0) == 0:
                                self.spawn_bomb(self.left, self.right, travel_time_frames=60)
                        except Exception:
                            pass

                    if event.key == pygame.K_j:
                        try:
                            if not getattr(self.right, "bomb_used", False) and getattr(self.right, "freeze_timer", 0) == 0:
                                self.spawn_bomb(self.right, self.left, travel_time_frames=60)
                        except Exception:
                            pass

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
                # ---- AI decision step: call ai_act BEFORE update so bursts apply immediately ----
                if getattr(self, "ai_enabled", False):
                    try:
                        rope_pos = getattr(self.rope, "pos", 0.5)
                        rope_center = 0.5
                        # call ai_act on right player (1-player mode)
                        if getattr(self.right, "ai_act", None):
                            self.right.ai_act(rope_pos, rope_center, opponent_pull=getattr(self.left, "pull", 0))
                    except Exception:
                        pass

                # update players
                self.left.update()
                self.right.update()

                # Spawn clone effect + sound when a player activates clone (both human & AI)
                try:
                    for player in (self.left, self.right):
                        if getattr(player, "clone_active", False) and not getattr(player, "clone_effect_spawned", False):
                            # place effect at the clone's position (match Player.draw clone offset),
                            # not at the main character center.
                            try:
                                center_x = player.x + player.width // 2
                                offset_x = int(player.width * 0.8)
                                if getattr(player, "side", "") == "left":
                                    fx = center_x + offset_x - 2
                                else:
                                    fx = center_x - offset_x + 2
                                fy = player.y

                                # spawn effect scaled to player height if supported
                                try:
                                    self.spawn_effect(fx, fy, target_h=player.height)
                                except TypeError:
                                    self.spawn_effect(fx, fy)
                            except Exception:
                                # fallback to player center if anything fails
                                try:
                                    self.spawn_effect(player.x + player.width // 2, player.y, target_h=player.height)
                                except Exception:
                                    pass

                            if getattr(self, "clone_sound", None):
                                try:
                                    self.clone_sound.play()
                                except Exception:
                                    pass
                            player.clone_effect_spawned = True
                except Exception:
                    pass

                # DEBUG: compare pull values, strengths, stamina and timers
                try:
                    # gather debug info without printing to avoid spamming tests;
                    # keep as a local tuple so the block is not empty and safe to run.
                    left_info = (self.left.pull, getattr(self.left, "pull_strength", None), getattr(self.left, "stamina", None))
                    right_info = (self.right.pull, getattr(self.right, "pull_strength", None), getattr(self.right, "stamina", None))
                    # assign to a temporary variable to avoid lint warnings
                    _debug_snapshot = (left_info, right_info)
                except Exception:
                    pass

                # --- SIMPLE AI RANDOM ACTIONS (1-player only) ---
                if getattr(self, "ai_enabled", False):
                    try:
                        # AI random clone
                        if (not getattr(self.right, "clone_used", False)
                                and getattr(self.right, "clone_cooldown_timer", 0) == 0
                                and getattr(self.right, "freeze_timer", 0) == 0
                                and random.random() < 0.004):
                            try:
                                if self.right.activate_clone():
                                    fx = self.right.x + self.right.width // 2 - int(self.right.width * 0.6) - 5
                                    fy = self.right.y
                                    try:
                                        self.spawn_effect(fx, fy, target_h=self.right.height)
                                    except Exception:
                                        pass
                                    if getattr(self, "clone_sound", None):
                                        try:
                                            self.clone_sound.play()
                                        except Exception:
                                            pass
                            except Exception:
                                pass

                        # AI random bomb
                        if (not getattr(self.right, "bomb_used", False)
                                and getattr(self.right, "freeze_timer", 0) == 0
                                and random.random() < 0.002):
                            try:
                                self.spawn_bomb(self.right, self.left, travel_time_frames=60)
                            except Exception:
                                pass

                    except Exception:
                        pass
                # --- end AI random actions ---

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

                # draw effects on top (smoke)
                for e in self.effects:
                    e.draw(self.screen)

                # draw projectiles (bombs) - invisible for now
                for p in self.projectiles:
                    p.draw(self.screen)

            # update effects
            for e in self.effects:
                e.update()
            # remove finished
            self.effects = [e for e in self.effects if not e.finished]

            # update projectiles and handle collisions
            for p in list(self.projectiles):
                p.update()
                if p.alive and not p.exploded:
                    r = p.get_rect()
                    if p.vx > 0:
                        target = pygame.Rect(self.right.x, self.right.y - self.right.height, self.right.width, self.right.height)
                        if r.colliderect(target):
                            self.right.apply_bomb_hit(freeze_frames=120)
                            if getattr(self, "explosion_sound", None):
                                self.explosion_sound.play()
                            p.exploded = True
                            p.alive = False
                    else:
                        target = pygame.Rect(self.left.x, self.left.y - self.left.height, self.left.width, self.left.height)
                        if r.colliderect(target):
                            self.left.apply_bomb_hit(freeze_frames=120)
                            if getattr(self, "explosion_sound", None):
                                self.explosion_sound.play()
                            p.exploded = True
                            p.alive = False
                if not p.alive or p.offscreen(self.width, self.height):
                    try:
                        self.projectiles.remove(p)
                    except Exception:
                        pass

            # (display flip / tick follows)
            pygame.display.flip()
            clock.tick(60)  # cap at 60 FPS

class Projectile:
    def __init__(self, x, y, vx, vy):
        import os
        import pygame
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.alive = True
        self.exploded = False
        self._image_name = None
        self.image = None

        # candidates to try
        sprites_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets", "sprites"))
        candidates = [
            os.path.join(sprites_dir, "bomb.png"),
            os.path.join(sprites_dir, "bomb0.png"),
            os.path.join(sprites_dir, "projectile.png"),
            os.path.join(sprites_dir, "missile.png"),
            "bomb.png",
        ]

        # try each candidate and print debug info about existence + load error
        for path in candidates:
            try:
                exists = os.path.exists(path)
            except Exception:
                exists = False
            print(f"[debug] Projectile: trying path={path} exists={exists}")
            if not exists:
                continue
            try:
                img = pygame.image.load(path)
                try:
                    img = img.convert_alpha()
                except Exception:
                    img = img.convert()
                self.image = img
                self._image_name = path
                print(f"[debug] Projectile: loaded image {path}")
                break
            except Exception as e:
                print(f"[debug] Projectile: failed to load {path}: {e}")

        # fallback: try helper load_image (may search by basename)
        if not self.image:
            try:
                img = load_image("bomb.png")
                if img:
                    self.image = img
                    self._image_name = "bomb.png (via load_image)"
                    print(f"[debug] Projectile: loaded bomb.png via load_image")
            except Exception as e:
                print(f"[debug] Projectile: load_image raised: {e}")

        # final fallback placeholder
        if not self.image:
            print("[debug] Projectile: using placeholder gray circle")
            surf = pygame.Surface((16, 16), pygame.SRCALPHA)
            pygame.draw.circle(surf, (180, 180, 180), (8, 8), 6)
            self.image = surf
            self._image_name = "<placeholder>"

        # set rect centered on spawn pos
        try:
            self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))
        except Exception:
            self.rect = pygame.Rect(int(self.x), int(self.y), 12, 12)

# helper used in debug print to avoid NameError if not defined elsewhere
def _safe(s):
    try:
        return s
    except Exception:
        return "<unknown>"