import os
import pygame
from game.utils import load_image

# desired bomb sprite size (width, height)
# increased size for a visually larger bomb
BOMB_SIZE = 48

# try generic loader first
_BOMB_IMG = load_image("bomb.png")

# explicit fallback to src/assets/sprites/bomb.png
if not _BOMB_IMG:
    path = os.path.join("src", "assets", "sprites", "bomb.png")
    if os.path.exists(path):
        try:
            _BOMB_IMG = pygame.image.load(path).convert_alpha()
            print(f"[debug projectile] loaded bomb image from {path}")
        except Exception:
            try:
                _BOMB_IMG = pygame.image.load(path).convert()
                print(f"[debug projectile] loaded bomb image (no alpha) from {path}")
            except Exception:
                _BOMB_IMG = None
    else:
        print(f"[debug projectile] bomb image not found at {path}, using fallback circle")

if _BOMB_IMG:
    try:
        _BOMB_IMG = pygame.transform.smoothscale(_BOMB_IMG, (BOMB_SIZE, BOMB_SIZE))
    except Exception:
        pass

class Bomb:
    """Simple parabolic projectile using bomb.png when available."""
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
        if _BOMB_IMG:
            try:
                rect = _BOMB_IMG.get_rect(center=(int(self.x), int(self.y)))
                surface.blit(_BOMB_IMG, rect)
                return
            except Exception:
                pass
        # fallback: draw same-sized gray circle
        radius = max(4, BOMB_SIZE // 2)
        pygame.draw.circle(surface, (80, 80, 80), (int(self.x), int(self.y)), radius)

    def get_rect(self):
        if _BOMB_IMG:
            w, h = _BOMB_IMG.get_size()
            return pygame.Rect(int(self.x - w/2), int(self.y - h/2), w, h)
        r = max(4, BOMB_SIZE // 2)
        return pygame.Rect(int(self.x - r), int(self.y - r), r*2, r*2)

    def offscreen(self, width, height):
        return (self.x < -200) or (self.x > width + 200) or (self.y > height + 400)