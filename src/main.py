import sys
import pygame
import random
import os
import warnings
warnings.filterwarnings("ignore", message="iCCP: known incorrect sRGB profile")
from game.utils import init_audio  # keep only init_audio here

WIDTH, HEIGHT = 800, 480

def main():
    # ensure mixer pre-init then init pygame
    init_audio()
    pygame.init()

    # Initialize the display early (must happen before convert_alpha())
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tug Of War - Prototype")

    # import modules that may load images/assets now that display exists
    from game.core import Game
    from game.utils import load_sound, load_music, load_image

    pull_sound = load_sound("pull.wav")
    win_sound = load_sound("win.wav")
    select_sound = load_sound("select.wav")
    menu_music = load_music("menu.wav")
    gameplay_music = load_music("gameplay.wav")
    clone_sound = load_sound("clone-smoke.wav")
    explosion_sound = load_sound("explosion.wav")  # Load explosion sound

    # per-track target volumes (0.0 .. 1.0)
    menu_volume = 0.4
    gameplay_volume = 0.6

    try:
        if menu_music:
            if isinstance(menu_music, pygame.mixer.Sound):
                menu_music.set_volume(menu_volume)
            else:
                pygame.mixer.music.set_volume(menu_volume)
    except Exception:
        pass

    if pull_sound:
        pull_sound.set_volume(0.6)
    if win_sound:
        win_sound.set_volume(0.7)
    if select_sound:
        select_sound.set_volume(1.0)
    if clone_sound:
        clone_sound.set_volume(1.0)
    if explosion_sound:
        explosion_sound.set_volume(1.0)

    game = Game(screen, WIDTH, HEIGHT, ai=True)
    game.pull_sound = pull_sound
    game.win_sound = win_sound
    game.select_sound = select_sound
    game.menu_music = menu_music
    game.gameplay_music = gameplay_music
    game.menu_volume = menu_volume
    game.gameplay_volume = gameplay_volume
    game.clone_sound = clone_sound
    game.explosion_sound = explosion_sound

    try:
        game._set_music("menu")
    except Exception:
        pass

    game.run()

if __name__ == "__main__":
    main()
