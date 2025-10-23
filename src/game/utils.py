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
        img = pygame.image.load(path)
    except Exception:
        return None

    # prefer convert_alpha, but fall back to convert if needed
    try:
        img = img.convert_alpha()
    except Exception:
        try:
            img = img.convert()
        except Exception:
            pass

    if colorkey is not None:
        try:
            img.set_colorkey(colorkey)
        except Exception:
            pass

    return img

def play_sound(sound, volume=1.0):
    """Play a pygame Sound if available."""
    if sound is None:
        return
    try:
        sound.set_volume(volume)
        sound.play()
    except Exception:
        pass

# --- music helpers ---

def load_music(name):
    """Return full path to a music file in src/assets/music/ or None if missing."""
    path = os.path.join(ASSETS_DIR, "music", name)
    return path if os.path.isfile(path) else None

def play_music(path, loops=-1, volume=0.6):
    """Play background music from a file path (uses pygame.mixer.music)."""
    if path is None:
        return
    try:
        pygame.mixer.music.stop()
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loops)
    except Exception:
        pass

def stop_music():
    """Stop currently playing background music."""
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass