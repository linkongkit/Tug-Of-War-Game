import os
import pygame

# assets folder: src/assets/
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")

def init_audio():
    """Initialize the mixer safely (call once at startup)."""
    try:
        pygame.mixer.init()
    except Exception:
        # ignore if audio backend is not available
        pass

def load_sound(name):
    """Load a sound from src/assets/sfx/, return a Sound or None."""
    path = os.path.join(ASSETS_DIR, "sfx", name)
    if not os.path.isfile(path):
        return None
    try:
        return pygame.mixer.Sound(path)
    except Exception:
        return None

def load_image(name, colorkey=None):
    """Load an image from src/assets/sprites/, return Surface or None."""
    path = os.path.join(ASSETS_DIR, "sprites", name)
    if not os.path.isfile(path):
        return None
    try:
        img = pygame.image.load(path).convert_alpha()
        if colorkey is not None:
            img.set_colorkey(colorkey)
        return img
    except Exception:
        return None

def play_sound(sound, volume=1.0):
    """Play a pygame Sound if available."""
    if sound is None:
        return
    try:
        sound.set_volume(volume)
        sound.play()
    except Exception:
        pass