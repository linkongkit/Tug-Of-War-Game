import pygame
import random
from game.utils import load_image

class SpriteEffect:
    """
    Minimal effect/animation wrapper used by Player.spawn_effect.
    Holds a list of frames (surfaces), a frame rate and exposes update/draw.
    """
    def __init__(self, x, y, frames, frame_rate=12):
        self.x = x
        self.y = y
        self.frames = frames or []
        self.frame_rate = frame_rate
        # timer counts ticks; advance every ticks_per_frame
        self.ticks_per_frame = max(1, int(60 / max(1, frame_rate)))
        self.timer = 0
        self.index = 0
        self.finished = not bool(self.frames)

    def update(self):
        if self.finished:
            return
        self.timer += 1
        if self.timer >= self.ticks_per_frame:
            self.timer = 0
            self.index += 1
            if self.index >= len(self.frames):
                self.finished = True
                self.index = max(0, len(self.frames) - 1)

    def draw(self, surface):
        if self.finished or not self.frames:
            return
        img = self.frames[self.index]
        rect = img.get_rect(center=(self.x, self.y))
        surface.blit(img, rect)

class Player:
    def __init__(self, side, x=0, y=0):
        self.side = side
        self.x = x
        self.y = y
        # doubled character size (120x160)
        self.width = 60
        self.height = 80

        # pull state
        self.pull = 0
        self.pull_strength = 5

        # tap behaviour
        self.tap_duration = 6
        self.tap_timer = 0

        # AI
        self.ai_aggressiveness = 0.75
        self.ai_burst_timer = 0
        self.ai_pause_timer = 0

        # clone / special move
        self.clone_active = False
        self.clone_timer = 0
        self.clone_duration = 60  # frames (60 = 1 second at 60fps)

        # single-use flag (one clone per round)
        self.clone_used = False

        # allow repeated uses with cooldown (frames)
        self.clone_cooldown = 180   # 3 seconds at 60fps
        self.clone_cooldown_timer = 0

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
        else:
            print(f"[player] {self.side}: loaded push image {push_name}")

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
            print(f"[player] {self.side}: loaded pull image {pull_name}")

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

    def press_pull(self):
        if self.stamina > 0:
            self.tap_timer = self.tap_duration

    def activate_clone(self, frames=None):
        """Trigger a temporary clone in front of the player (visual) that doubles pull.
           Only activates once per round (clone_used prevents re-use).
        """
        if self.clone_active:
            return False
        # block if already used this round
        if self.clone_used:
            return False
        if frames is None:
            frames = self.clone_duration
        self.clone_active = True
        self.clone_timer = frames
        # mark as used (one chance only)
        self.clone_used = True
        return True

    def update(self):
        # handle clone timer
        if self.clone_timer > 0:
            self.clone_timer -= 1
            if self.clone_timer <= 0:
                self.clone_active = False

        # cooldown tick down
        if self.clone_cooldown_timer > 0:
            self.clone_cooldown_timer -= 1

        if self.tap_timer > 0:
            self.tap_timer -= 1
            # double pull if clone active
            multiplier = 2 if self.clone_active else 1
            self.pull = self.pull_strength * multiplier
            self.stamina -= self.stamina_drain
            if self.stamina < 0:
                self.stamina = 0
            return

        if self.ai_burst_timer > 0:
            self.ai_burst_timer -= 1
            multiplier = 2 if self.clone_active else 1
            self.pull = self.pull_strength * multiplier
            self.stamina -= self.stamina_drain
            if self.stamina < 0:
                self.stamina = 0
            return

        self.pull = 0
        self.stamina += self.stamina_regen
        if self.stamina > self.max_stamina:
            self.stamina = self.max_stamina

    def ai_act(self, rope_pos, rope_center, opponent_pull=0, threshold=10):
        if self.ai_pause_timer > 0:
            self.ai_pause_timer -= 1

        if self.side == 'left':
            condition = rope_pos > (rope_center + threshold)
        else:
            condition = rope_pos < (rope_center - threshold)

        respond_bias = 0.15 if opponent_pull == 0 else 0.35

        if self.ai_pause_timer == 0:
            chance = self.ai_aggressiveness + respond_bias
            if condition and random.random() < chance:
                self.ai_burst_timer = random.randint(4, 12)
                self.ai_pause_timer = random.randint(8, 24)
                return

        if opponent_pull == 0 and random.random() < 0.02:
            self.ai_burst_timer = random.randint(3, 8)
            self.ai_pause_timer = random.randint(6, 20)
            return

    def draw(self, surface):
        img = None
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
            if self.side == "left":
                cx = self.x + self.width // 2 + offset_x
            else:
                cx = self.x + self.width // 2 - offset_x
            crect = clone_img.get_rect(center=(cx, self.y))
            surface.blit(clone_img, crect)

    def spawn_effect(self, x, y, kind="clone-smoke", frame_rate=12):
        if kind == "clone-smoke":
            frames = self.clone_smoke_frames
            if not frames:
                return
            eff = SpriteEffect(x, y, frames, frame_rate=frame_rate)
            self.effects.append(eff)

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:
                    try:
                        if self.left.activate_clone():
                            # spawn effect slightly in front of player (toward center)
                            fx = self.left.x + self.left.width // 2 + int(self.left.width * 0.6)
                            fy = self.left.y
                            self.spawn_effect(fx, fy)
                            if getattr(self, "clone_sound", None):
                                self.clone_sound.play()
                    except Exception:
                        pass

                if event.key == pygame.K_h:
                    try:
                        if self.right.activate_clone():
                            fx = self.right.x + self.right.width // 2 - int(self.right.width * 0.6)
                            fy = self.right.y
                            self.spawn_effect(fx, fy)
                            if getattr(self, "clone_sound", None):
                                self.clone_sound.play()
                    except Exception:
                        pass