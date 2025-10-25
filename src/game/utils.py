import os
import pygame

ASSET_ROOT = os.path.join("src", "assets")

# optional global bomb image; set to a Surface when available to avoid NameError
_BOMB_IMG = None

def init_audio():
    try:
        # safe pre-init and init
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.mixer.init()
    except Exception:
        pass

def _find_asset(subpaths):
    for p in subpaths:
        path = os.path.join(ASSET_ROOT, p)
        if os.path.exists(path):
            return path
    return None

def load_sound(filename):
    """Return a pygame.mixer.Sound or None. Searches common asset folders."""
    try:
        candidates = [
            os.path.join("sfx", filename),
            os.path.join("sounds", filename),
            os.path.join("sound", filename),
            os.path.join("", filename),
        ]
        for c in candidates:
            path = os.path.join(ASSET_ROOT, c)
            if os.path.exists(path):
                try:
                    return pygame.mixer.Sound(path)
                except Exception:
                    return None
        # fallback: try direct path
        if os.path.exists(filename):
            try:
                return pygame.mixer.Sound(filename)
            except Exception:
                return None
    except Exception:
        pass
    return None

def load_music(filename):
    """Return a file path for pygame.mixer.music.load or None."""
    try:
        path = os.path.join(ASSET_ROOT, "music", filename)
        if os.path.exists(path):
            return path
        # also try src/assets/ (fallback)
        path = os.path.join(ASSET_ROOT, filename)
        if os.path.exists(path):
            return path
    except Exception:
        pass
    print(f"[load_music] File not found: {os.path.join(ASSET_ROOT, 'music', filename)}")
    return None

def load_image(filename):
    """Return a pygame.Surface or None. Searches images and sprites folders."""
    try:
        candidates = [
            os.path.join("images", filename),
            os.path.join("sprites", filename),
            filename,
        ]
        for c in candidates:
            path = os.path.join(ASSET_ROOT, c)
            if os.path.exists(path) and os.path.isfile(path):
                try:
                    surf = pygame.image.load(path)
                    try:
                        return surf.convert_alpha()
                    except Exception:
                        return surf  # return raw surface if convert fails
                except Exception:
                    return None
        # fallback: try direct path
        if os.path.exists(filename):
            try:
                surf = pygame.image.load(filename)
                try:
                    return surf.convert_alpha()
                except Exception:
                    return surf
            except Exception:
                return None
    except Exception:
        pass
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

# --- music helpers ---

def load_music(filename):
    """Load music file path for pygame.mixer.music."""
    try:
        path = os.path.join("src", "assets", "music", filename)
        if os.path.exists(path):
            return path  # return path for pygame.mixer.music
        else:
            print(f"[load_music] File not found: {path}")
            return None
    except Exception as e:
        print(f"[load_music] Error loading {filename}: {e}")
        return None

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