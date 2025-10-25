import pygame

class Bomb:
    """Simple parabolic projectile."""
    def __init__(self, x, y, vx, vy, gravity=0.4):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.gravity = gravity
        self.alive = True
        self.exploded = False

    def update(self):
        if not self.alive or self.exploded:
            return
        self.vy += self.gravity
        self.x += self.vx
        self.y += self.vy

    def draw(self, surface):
        if not self.alive or self.exploded:
            return
        pygame.draw.circle(surface, (80, 80, 80), (int(self.x), int(self.y)), 8)

    def get_rect(self):
        return pygame.Rect(int(self.x - 8), int(self.y - 8), 16, 16)

    def offscreen(self, width, height):
        return (self.x < -200) or (self.x > width + 200) or (self.y > height + 400)