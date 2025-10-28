import pygame
from .utils import load_image

def load_sequence(name, num_frames):
    frames = []
    for i in range(num_frames):
        fname = f"{name}{i}.png"
        img = load_image(fname)
        if img:
            frames.append(img)
        else:
            print(f"[debug] Failed to load {fname}")
    print(f"[debug] load_sequence('{name}', {num_frames}) -> {len(frames)} frames")
    return frames

class Anim:
    def __init__(self, x, y, frames, duration_ms):
        # frames: list of Surfaces, duration_ms = total animation length in milliseconds
        self.frames = frames or []
        self.n_frames = max(1, len(self.frames))
        # ensure duration passed as milliseconds; fallback to 100ms/frame if caller used seconds
        if duration_ms is None:
            duration_ms = self.n_frames * 100.0
        # guard: if caller passed seconds (<=10), treat as seconds -> convert to ms
        if duration_ms <= 10:
            duration_ms = float(duration_ms) * 1000.0
        self.duration_ms = float(max(1.0, duration_ms))
        self.per_frame_ms = max(1.0, self.duration_ms / self.n_frames)
        self.start_time = pygame.time.get_ticks()
        self.frame_index = 0
        self.image = self.frames[0] if self.frames else None
        self.center = (int(x), int(y))
        self.rect = self.image.get_rect(center=self.center) if self.image else pygame.Rect(int(x), int(y), 0, 0)
        self.alive = bool(self.frames)

    def update(self):
        if not self.alive:
            return
        now = pygame.time.get_ticks()
        elapsed = now - self.start_time
        idx = int(elapsed / self.per_frame_ms)
        if idx >= self.n_frames:
            self.alive = False
            return
        if idx != self.frame_index:
            self.frame_index = idx
            self.image = self.frames[self.frame_index]
            # keep animation centered where it started
            self.rect = self.image.get_rect(center=self.center)

    def draw(self, surface):
        if self.alive and self.image:
            surface.blit(self.image, self.rect)

class ExplosionAnim(Anim):
    def __init__(self, x, y, frames, duration_ms, scale=None, target_size=None):
        # compute scale from target_size if provided and scale frames up-front
        if target_size and frames:
            fw, fh = frames[0].get_size()
            if fw > 0 and fh > 0:
                sx = float(target_size[0]) / fw
                sy = float(target_size[1]) / fh
                scale = max(sx, sy)
        if scale is not None and scale != 1.0 and frames:
            scaled = []
            for f in frames:
                nw = max(1, int(f.get_width() * scale))
                nh = max(1, int(f.get_height() * scale))
                try:
                    nf = pygame.transform.smoothscale(f, (nw, nh))
                except Exception:
                    nf = pygame.transform.scale(f, (nw, nh))
                scaled.append(nf)
            frames = scaled
        super().__init__(x, y, frames, duration_ms)