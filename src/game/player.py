import pygame

class Player:
    def __init__(self, side, x=0, y=0):
        self.side = side
        self.x = x
        self.y = y
        self.width = 60
        self.height = 80

        # pull and stamina
        self.pull = 0
        self.pull_strength = 5
        self.max_stamina = 100.0
        self.stamina = self.max_stamina
        self.stamina_drain = 1.5   # per frame while pulling
        self.stamina_regen = 0.8    # per frame when not pulling

    def handle_input(self, keys):
        # Determine desired pull based on side keys
        wanting_pull = False
        if self.side == 'left':
            wanting_pull = bool(keys[pygame.K_a])
        else:
            wanting_pull = bool(keys[pygame.K_l])

        # If player wants to pull and has stamina, apply pull and drain
        if wanting_pull and self.stamina > 0:
            self.pull = self.pull_strength
            self.stamina -= self.stamina_drain
            if self.stamina < 0:
                self.stamina = 0
        else:
            self.pull = 0
            # regenerate stamina when not pulling
            self.stamina += self.stamina_regen
            if self.stamina > self.max_stamina:
                self.stamina = self.max_stamina

    def draw(self, surface):
        color = (150, 50, 50) if self.side == 'left' else (50, 50, 150)
        rect = pygame.Rect(self.x, self.y - self.height // 2, self.width, self.height)
        pygame.draw.rect(surface, color, rect)

        # draw stamina bar above player
        bar_w = self.width
        bar_h = 8
        bar_x = self.x
        bar_y = self.y - self.height // 2 - 12
        # background
        pygame.draw.rect(surface, (40,40,40), (bar_x, bar_y, bar_w, bar_h))
        # fill based on stamina ratio
        ratio = max(0.0, min(1.0, self.stamina / self.max_stamina))
        fill_w = int(bar_w * ratio)
        fill_color = (60,200,80) if ratio > 0.4 else (220,160,60) if ratio > 0.15 else (200,60,60)
        if fill_w > 0:
            pygame.draw.rect(surface, fill_color, (bar_x, bar_y, fill_w, bar_h))