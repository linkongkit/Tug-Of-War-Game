import pygame
import random
from game.utils import load_image

class Player:
    def __init__(self, side, x=0, y=0):
        self.side = side
        self.x = x
        self.y = y
        # doubled character size (120x160)
        self.width = 120
        self.height = 160

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

    def press_pull(self):
        self.tap_timer = self.tap_duration

    def update(self):
        if self.tap_timer > 0:
            self.tap_timer -= 1
            self.pull = self.pull_strength
            return

        if self.ai_burst_timer > 0:
            self.ai_burst_timer -= 1
            self.pull = self.pull_strength
            return

        self.pull = 0

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
        if self.pull > 0 and self.pull_img:
            img = self.pull_img
        elif self.push_img:
            img = self.push_img

        if img:
            rect = img.get_rect(center=(self.x + self.width // 2, self.y))
            surface.blit(img, rect)
        else:
            color = (180, 60, 60) if self.side == 'left' else (60, 90, 180)
            rect = pygame.Rect(self.x, self.y - self.height // 2, self.width, self.height)
            pygame.draw.rect(surface, color, rect)