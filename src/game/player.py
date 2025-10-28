import pygame
import random
from game.utils import load_image
from game.effects import ExplosionAnim, load_sequence

class Player:
    def __init__(self, x, y, width, height, side, push_img_path, pull_img_path):
        self.side = side
        self.x = x
        self.y = y
        # doubled character size (120x160)
        self.width = 60
        self.height = 80

        # pulling / stamina
        self.pull = 0
        self.pull_strength = 5
        self.tap_duration = 6
        self.tap_timer = 0

        self.max_stamina = 100
        self.stamina = self.max_stamina
        self.stamina_drain = 1
        self.stamina_regen = 0.6

        # AI timers / params
        # Keep pull strength identical for both players so pulls are fair.
        # Side-specific difficulty should be expressed via ai_aggressiveness and timers only.
        self.ai_aggressiveness = 0.95
        self.ai_burst_timer = 0
        self.ai_pause_timer = 0

        # clone / special
        self.clone_active = False
        self.clone_timer = 0
        self.clone_duration = 60
        self.clone_used = False
        self.clone_cooldown = 180
        self.clone_cooldown_timer = 0

        # bomb
        self.bomb_used = False

        # freeze when hit by bomb
        self.freeze_timer = 0
        self.freeze_duration_frames = 120

        # --- LOAD SIDE-SPECIFIC SPRITES (explicit, prefer exact files) ---
        if self.side == "left":
            push_name = "girl-push.png"
            pull_name = "girl-pull.png"
        else:
            push_name = "boy-push.png"
            pull_name = "boy-pull.png"

        self.push_img = load_image(push_name)
        self.pull_img = load_image(pull_name)

        # If preferred files are missing, log warning and attempt fallback but do NOT
        # let fallback override a successfully loaded preferred image.
        if self.push_img is None:
            fallback = "boy-push.png" if self.side == "left" else "girl-push.png"
            alt = load_image(fallback)
            if alt:
                # flip fallback for left side so it faces correct direction
                if self.side == "left":
                    alt = pygame.transform.flip(alt, True, False)
                self.push_img = alt
                print(f"[player] {self.side}: using fallback push image {fallback}")
            else:
                print(f"[player] WARNING: no push image for {self.side} (tried {push_name} and {fallback})")

        if self.pull_img is None:
            fallback = "boy-pull.png" if self.side == "left" else "girl-pull.png"
            alt = load_image(fallback)
            if alt:
                if self.side == "left":
                    alt = pygame.transform.flip(alt, True, False)
                self.pull_img = alt
                print(f"[player] {self.side}: using fallback pull image {fallback}")
            else:
                print(f"[player] WARNING: no pull image for {self.side} (tried {pull_name} and {fallback})")
        else:
            if self.pull_img is None:
                # Load default pull image or handle error
                pass  # Add your code here if needed

        # scale images to player size
        if self.push_img and self.push_img.get_size() != (self.width, self.height):
            try:
                self.push_img = pygame.transform.smoothscale(self.push_img, (self.width, self.height))
            except Exception:
                self.push_img = pygame.transform.scale(self.push_img, (self.width, self.height))
        if self.pull_img and self.pull_img.get_size() != (self.width, self.height):
            try:
                self.pull_img = pygame.transform.smoothscale(self.pull_img, (self.width, self.height))
            except Exception:
                self.pull_img = pygame.transform.scale(self.pull_img, (self.width, self.height))

        # preload clone smoke frames (folder: src/assets/sprites/clone-smoke/)
        try:
            self.clone_smoke_frames = load_sequence("clone-smoke")
        except Exception:
            self.clone_smoke_frames = []

        # active particle/effect list
        self.effects = []
        # explicit total explosion time in milliseconds (set small so frames advance)
        # 300 ms total for 6 frames -> 50 ms per frame
        # total explosion time in milliseconds: 6 frames * 100ms = 600ms
        self.explosion_duration_ms = 600
        self.explosion_frames = load_sequence("explosion", 6)
        self.explosion_anim = None

    def press_pull(self):
        # cannot pull if frozen
        if self.freeze_timer > 0:
            return
        if self.stamina > 0:
            self.tap_timer = self.tap_duration

    def activate_clone(self, frames=None):
        """Trigger a temporary clone in front of the player (visual) that doubles pull.
           Only activates once per round (clone_used prevents re-use).
        """
        if self.clone_active or self.clone_used:
            return False
        self.clone_active = True
        self.clone_timer = frames if frames is not None else self.clone_duration
        self.clone_used = True
        # start cooldown after activation
        self.clone_cooldown_timer = self.clone_cooldown
        return True

    def apply_bomb_hit(self, freeze_frames=120):
        self.freeze_timer = freeze_frames
        self.spawn_explosion()

    def spawn_explosion(self, y_offset=-30):
        """
        Spawn explosion centered on the player's rect center.
        y_offset moves it vertically (negative moves up).
        """
        if not getattr(self, "explosion_frames", None):
            return

        # use player rect if available
        if hasattr(self, "rect") and self.rect:
            cx, cy = self.rect.center
        else:
            cx = int(self.x + self.width / 2)
            cy = int(self.y + self.height / 2)

        cy += int(y_offset)

        size = int(max(self.width, self.height) * 1.6)
        # pass explicit duration in milliseconds
        self.explosion_anim = ExplosionAnim(cx, cy, self.explosion_frames, duration_ms=self.explosion_duration_ms, target_size=(size, size))

    def update(self, *args, **kwargs):
        # always update explosion animation first
        if getattr(self, "explosion_anim", None):
            self.explosion_anim.update()
            if not self.explosion_anim.alive:
                self.explosion_anim = None

        # clone timer
        if self.clone_timer > 0:
            self.clone_timer -= 1
            if self.clone_timer <= 0:
                self.clone_active = False

        # cooldowns
        if self.clone_cooldown_timer > 0:
            self.clone_cooldown_timer -= 1

        # freeze handling
        if self.freeze_timer > 0:
            self.freeze_timer -= 1
            # while frozen, clear action timers and force pull=0
            self.tap_timer = 0
            self.ai_burst_timer = 0
            self.ai_pause_timer = max(self.ai_pause_timer, self.freeze_timer)
            self.pull = 0
            return

        # tap (player input)
        if self.tap_timer > 0:
            self.tap_timer -= 1
            multiplier = 2 if self.clone_active else 1
            self.pull = self.pull_strength * multiplier
            self.stamina -= self.stamina_drain
            if self.stamina < 0:
                self.stamina = 0
            return

        # AI burst (when ai_act set burst)
        if self.ai_burst_timer > 0:
            self.ai_burst_timer -= 1
            multiplier = 2 if self.clone_active else 1
            self.pull = self.pull_strength * multiplier
            self.stamina -= self.stamina_drain
            if self.stamina < 0:
                self.stamina = 0
            return

        # idle
        self.pull = 0
        self.stamina += self.stamina_regen
        if self.stamina > self.max_stamina:
            self.stamina = self.max_stamina

        # update effects
        for e in list(self.effects):
            e.update()
            if e.finished:
                try:
                    self.effects.remove(e)
                except Exception:
                    pass

    def ai_act(self, rope_pos, rope_center, opponent_pull=0, threshold=10):
        # do nothing while frozen
        if self.freeze_timer > 0:
            return

        if self.ai_pause_timer > 0:
            self.ai_pause_timer -= 1

        if self.side == 'left':
            condition = rope_pos > (rope_center + threshold)
        else:
            condition = rope_pos < (rope_center - threshold)

        # higher base chance to start bursts, but keep bursts short so no long holds
        respond_bias = 0.45 if opponent_pull == 0 else 0.7

        if self.ai_pause_timer == 0:
            chance = min(1.0, self.ai_aggressiveness + respond_bias)
            if condition and random.random() < chance:
                # SHORT burst lengths, very brief pauses => frequent short pulls
                self.ai_burst_timer = random.randint(1, 4)   # very short bursts
                self.ai_pause_timer = random.randint(1, 6)   # short pause
                return

        # higher opportunistic short-burst chance when opponent not pulling
        if opponent_pull == 0 and random.random() < 0.18:
            self.ai_burst_timer = random.randint(1, 4)
            self.ai_pause_timer = random.randint(1, 6)
            return

        # small increased chance for specials (still single-use per round)
        if not getattr(self, "clone_used", False) and not getattr(self, "clone_active", False):
            if random.random() < (0.012 if self.side == "right" else 0.008):
                self.ai_wants_clone = True

        if not getattr(self, "bomb_used", False):
            if random.random() < (0.008 if self.side == "right" else 0.003):
                self.ai_wants_bomb = True

    def draw(self, surface):
        # draw player sprite
        # show pull frame when actively pulling, else ready/push frame if available
        if self.pull > 0 and self.pull_img:
            img = self.pull_img
        elif self.push_img:
            img = self.push_img

        if img:
            rect = img.get_rect(center=(self.x + self.width // 2, self.y))
            surface.blit(img, rect)
        else:
            # fallback rectangle (red for left, blue for right)
            color = (180, 60, 60) if self.side == 'left' else (60, 90, 180)
            rect = pygame.Rect(self.x, self.y - self.height // 2, self.width, self.height)
            pygame.draw.rect(surface, color, rect)

        # draw clone (semi-transparent copy) in front if active
        if self.clone_active and img:
            try:
                clone_img = img.copy()
                # semi-transparent
                clone_img.set_alpha(160)
            except Exception:
                clone_img = img
            # offset in front toward center: left clone appears to the right, right clone to the left
            offset_x = int(self.width * 0.8)
            # small manual nudges: left clone 2px left, right clone 2px right
            if self.side == "left":
                cx = self.x + self.width // 2 + offset_x - 2
            else:
                cx = self.x + self.width // 2 - offset_x + 2
            crect = clone_img.get_rect(center=(cx, self.y))
            surface.blit(clone_img, crect)

        # draw local effects
        for e in self.effects:
            e.draw(surface)

        # draw explosion on top even if player frozen
        if getattr(self, "explosion_anim", None):
            self.explosion_anim.draw(surface)

    def spawn_effect(self, x, y, kind="clone-smoke", frame_rate=12):
        if kind == "clone-smoke" and self.clone_smoke_frames:
            eff = SpriteEffect(x, y, self.clone_smoke_frames, frame_rate=frame_rate)
            self.effects.append(eff)

    def reset(self):
        # reset player for a new round
        self.stamina = self.max_stamina
        self.tap_timer = 0
        self.clone_active = False
        self.clone_timer = 0
        self.clone_used = False
        self.clone_cooldown_timer = 0
        self.bomb_used = False
        self.freeze_timer = 0
        self.ai_burst_timer = 0
        self.ai_pause_timer = 0
        self.pull = 0
        self.effects = []

class Game:
    def run(self):
        clock = pygame.time.Clock()
        fps_timer = pygame.time.get_ticks()
        frame_count = 0

        while self.running:
            # ...existing event/update/draw code...

            pygame.display.flip()
            # cap FPS
            dt = clock.tick(60)
            frame_count += 1

            # optional: print FPS once per second
            now = pygame.time.get_ticks()
            if now - fps_timer >= 1000:
                fps = frame_count / ((now - fps_timer) / 1000.0)
                print(f"[dbg-core] approx fps={fps:.1f} tick_dt={dt}ms")
                fps_timer = now
                frame_count = 0