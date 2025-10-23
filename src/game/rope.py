import pygame
from game.utils import load_image

class Rope:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # rope travel limits (original baseline)
        self.min_x = 120
        self.max_x = width - 120
        self.pos = width // 2
        # vertical position: below characters (baseline)
        self.y = height // 2 + 80

        self.body_img = load_image("rope-body.png")
        self.knot_img = load_image("rope-knot.png")

        if self.body_img:
            try:
                # double the baseline body tile height (baseline 24 -> now 48)
                target_h = 24 * 2
                w, h = self.body_img.get_size()
                scale_w = max(1, int(w * (target_h / float(h))))
                self.body_tile = pygame.transform.smoothscale(self.body_img, (scale_w, target_h))
            except Exception:
                self.body_tile = self.body_img
        else:
            self.body_tile = None

        # revert knot sizing to baseline (clamp to max 48px tall)
        if self.knot_img:
            try:
                kw, kh = self.knot_img.get_size()
                max_kh = 48
                if kh > max_kh:
                    kscale = max_kh / float(kh)
                    self.knot_img = pygame.transform.smoothscale(self.knot_img, (int(kw * kscale), max_kh))
            except Exception:
                pass

        # vertical offset for the knot (positive moves knot downward)
        self.knot_offset = 5

    def apply_pull(self, left_pull, right_pull):
        self.pos += (right_pull - left_pull)
        self.pos = max(self.min_x, min(self.max_x, self.pos))

    def draw_body(self, surface):
        if self.body_tile:
            tile_w, tile_h = self.body_tile.get_size()
            y = int(self.y - tile_h // 2)
            x = 0
            while x < self.width:
                surface.blit(self.body_tile, (x, y))
                x += tile_w
        else:
            pygame.draw.line(surface, (220, 200, 60), (0, self.y), (self.width, self.y), 18)

    def draw_knot(self, surface):
        if self.knot_img:
            kw, kh = self.knot_img.get_size()
            kx = int(self.pos - kw // 2)
            ky = int(self.y - kh // 2 + self.knot_offset)
            surface.blit(self.knot_img, (kx, ky))
        else:
            # larger fallback circle so it's visible
            pygame.draw.circle(surface, (240, 240, 240), (int(self.pos), int(self.y + self.knot_offset)), 8)

    def reset(self):
        self.rope = Rope(self.width, self.height)
        # align rope to window center and move down 30px on reset
        try:
            self.rope.y = self.height // 2 + 30
        except Exception:
            pass
        self.left.pull = 0
        self.right.pull = 0

    def start(self):
        """Start the game (used by tests)."""
        self.rope = Rope(self.width, self.height)
        # align rope to window center and move down 30px on start
        try:
            self.rope.y = self.height // 2 + 30
        except Exception:
            pass
        self.left = Player('left', x=70, y=self.height//2 + 20)
        self.right = Player('right', x=self.width-130, y=self.height//2 + 20)