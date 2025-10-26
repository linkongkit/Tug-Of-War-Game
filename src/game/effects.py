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
    def __init__(self, x, y, frames, duration):
        self.frames = frames or []
        self.duration = max(1, float(duration or 1))
        self.frame_index = 0
        self.acc = 0.0
        # equal time per frame (float for smooth timing)
        self.per_frame = self.duration / max(1, len(self.frames))
        self.image = self.frames[0] if self.frames else None
        self.rect = self.image.get_rect(center=(x, y)) if self.image else pygame.Rect(x, y, 0, 0)
        self.alive = bool(self.frames)

    def update(self):
        if not self.alive:
            return
        self.acc += 1.0
        while self.acc >= self.per_frame:
            self.acc -= self.per_frame
            self.frame_index += 1
            if self.frame_index >= len(self.frames):
                self.alive = False
                return
            self.image = self.frames[self.frame_index]
            # keep center stable
            center = self.rect.center
            self.rect = self.image.get_rect(center=center)

    def draw(self, surface):
        if self.alive and self.image:
            surface.blit(self.image, self.rect)

class ExplosionAnim(Anim):
    def __init__(self, x, y, frames, duration, scale=None, target_size=None):
        # compute scale from target_size if provided
        if target_size and frames:
            fw, fh = frames[0].get_size()
            if fw > 0 and fh > 0:
                sx = float(target_size[0]) / fw
                sy = float(target_size[1]) / fh
                scale = max(sx, sy)
        if scale is not None and scale != 1.0 and frames:
            frames = [
                pygame.transform.scale(f, (int(f.get_width() * scale), int(f.get_height() * scale)))
                for f in frames
            ]
        super().__init__(x, y, frames, duration)