import pygame
from game.utils import load_image

def load_sequence(folder_name, pad=3):
    """Load frames from src/assets/sprites/{folder_name}/frame_###.png.
    Returns list of Surfaces. Stops when a frame is missing.
    """
    frames = []
    i = 0
    while True:
        name = f"{folder_name}/frame_{i:0{pad}d}.png"
        img = load_image(name)
        if img is None:
            break
        frames.append(img)
        i += 1
    return frames

class SpriteEffect:
    """Simple sprite-sequence effect. x,y are center position on screen. frame_rate is FPS."""
    def __init__(self, x, y, frames, frame_rate=12):
        self.x = int(x)
        self.y = int(y)
        self.frames = frames or []
        self.frame_rate = max(1, int(frame_rate))
        # game runs ~60 FPS -> how many game-frames each animation frame lasts
        self.frame_duration = max(1, int(60 / self.frame_rate))
        self.timer = 0
        self.index = 0
        self.finished = False

    def update(self):
        if self.finished or not self.frames:
            return
        self.timer += 1
        if self.timer >= self.frame_duration:
            self.timer = 0
            self.index += 1
            if self.index >= len(self.frames):
                self.finished = True

    def draw(self, surface):
        if self.finished or not self.frames:
            return
        img = self.frames[self.index]
        rect = img.get_rect(center=(self.x, self.y))
        surface.blit(img, rect)