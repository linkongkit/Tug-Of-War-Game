import pygame
from .utils import load_image

def load_sequence(name, num_frames):
    """
    Load a sequence of images. Supports two common patterns:
      - name + index + .png   (e.g. "explosion" -> explosion0.png)
      - name + index padded   (e.g. "clone-smoke/frame_" -> clone-smoke/frame_000.png)
    Tries both index and zero-padded (3 digits).
    """
    frames = []
    for i in range(num_frames):
        tried = []
        candidates = [
            f"{name}{i}.png",
            f"{name}{i:03d}.png",
            # also support if caller passed base without trailing separator
            f"{name}/{i}.png",
            f"{name}/{i:03d}.png",
        ]
        found = None
        for fname in candidates:
            tried.append(fname)
            img = load_image(fname)
            if img:
                found = img
                break
        if found:
            frames.append(found)
        else:
            print(f"[debug] Failed to load sequence frame for index {i}, tried: {tried}")
    print(f"[debug] load_sequence('{name}', {num_frames}) -> {len(frames)} frames")
    return frames

class Anim:
    """
    Time-based animation. duration_ms is total animation length in milliseconds.
    If duration_ms is None, default is 100 ms per frame.
    """
    def __init__(self, x, y, frames, duration_ms=None):
        self.frames = list(frames or [])
        self.n_frames = len(self.frames)
        if self.n_frames == 0:
            self.alive = False
            self.image = None
            self.rect = pygame.Rect(int(x), int(y), 0, 0)
            return

        if not duration_ms or duration_ms <= 0:
            duration_ms = self.n_frames * 100.0  # default 100 ms/frame

        self.duration_ms = float(duration_ms)
        self.per_frame_ms = max(1.0, self.duration_ms / float(self.n_frames))

        self.start_time = pygame.time.get_ticks()
        self.frame_index = 0
        self.image = self.frames[0]
        self.center = (int(x), int(y))
        self.rect = self.image.get_rect(center=self.center)
        self.alive = True

    def update(self):
        if not self.alive:
            return
        now = pygame.time.get_ticks()
        elapsed = now - self.start_time
        idx = int(elapsed // self.per_frame_ms)
        if idx >= self.n_frames:
            self.alive = False
            return
        if idx != self.frame_index:
            self.frame_index = idx
            self.image = self.frames[self.frame_index]
            self.rect = self.image.get_rect(center=self.center)

    def draw(self, surface):
        if self.alive and self.image:
            surface.blit(self.image, self.rect)

class ExplosionAnim(Anim):
    def __init__(self, x, y, frames, duration_ms=None, scale=None, target_size=None):
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

class CloneSmokeAnim(Anim):
    """
    Anim subclass forcing 50 ms per frame unless caller supplies explicit duration_ms.
    """
    def __init__(self, x, y, frames, per_frame_ms=50, duration_ms=None, scale=None, target_size=None):
        # same scaling logic as ExplosionAnim
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

        if duration_ms is None:
            duration_ms = per_frame_ms * len(frames) if frames else 0

        super().__init__(x, y, frames, duration_ms)