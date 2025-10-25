import sys
import pygame
from .player import Player
from .rope import Rope
from .utils import load_image, load_sound, load_music
from game.projectile import Bomb
import random

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
    def __init__(self, screen=None, width=800, height=480, ai=False):
        self.screen = screen
        # store passed sizes
        self.width = width
        self.height = height
        self.ai_enabled = ai

        # create clock and players first so we can align rope to their center
        self.clock = pygame.time.Clock()

        # create players (use self.height for vertical center)
        left_margin = 70
        self.left = Player('left', x=left_margin, y=self.height // 2 + 20)
        # create right player then set its x so its center mirrors the left player's center
        self.right = Player('right', x=0, y=self.height // 2 + 20)
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

        print(f"[debug music] request set {which}: obj={music_obj}, vol={vol}")

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
            print(f"[music] no {which}_music loaded")
            return

        # If load_music returned a filename/path, use pygame.mixer.music
        if isinstance(music_obj, str):
            try:
                pygame.mixer.music.load(music_obj)
                if vol is not None:
                    pygame.mixer.music.set_volume(vol)
                pygame.mixer.music.play(-1)
                self._playing_music_mode = "mixer"
                print(f"[debug music] Loaded and playing {which}: {music_obj}")
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
            print(f"[debug music] Playing Sound for {which}")
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

            print("[debug core] reset called - switching to menu and clearing flags")
            # switch back to menu music
            try:
                self._set_music("menu")
            except Exception:
                pass

        except Exception:
            # ensure we at least go back to menu to avoid quitting
            self.state = "waiting"

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
        print(f"[debug core] spawn_bomb from={thrower.side} to={target.side} vx={vx:.2f} vy={vy:.2f} travel_frames={T}")

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
                                    print(f"[debug core] AI clone executed for right player")
                            except Exception:
                                pass

                        # AI random bomb
                        if (not getattr(self.right, "bomb_used", False)
                                and getattr(self.right, "freeze_timer", 0) == 0
                                and random.random() < 0.002):
                            try:
                                self.spawn_bomb(self.right, self.left, travel_time_frames=60)
                                print(f"[debug core] AI bomb spawned from right")
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
                try:
                    p.update()
                    if p.alive and not p.exploded:
                        r = p.get_rect()
                        if p.vx > 0:
                            # collision with right player
                            target_rect = pygame.Rect(self.right.x, self.right.y - self.right.height//2, self.right.width, self.right.height)
                            if r.colliderect(target_rect):
                                self.right.apply_bomb_hit(freeze_frames=120)
                                p.exploded = True
                                p.alive = False
                        else:
                            # collision with left player
                            target_rect = pygame.Rect(self.left.x, self.left.y - self.left.height//2, self.left.width, self.left.height)
                            if r.colliderect(target_rect):
                                self.left.apply_bomb_hit(freeze_frames=120)
                                p.exploded = True
                                p.alive = False
                    # remove offscreen or exploded
                    if not p.alive or p.offscreen(self.width, self.height):
                        try:
                            self.projectiles.remove(p)
                        except Exception:
                            pass
                except Exception:
                    pass

            # (display flip / tick follows)
            pygame.display.flip()
            self.clock.tick(60)