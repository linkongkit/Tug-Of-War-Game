import sys
import pygame
import random
import os
from game.core import Game
from game.utils import init_audio, load_sound, load_music, load_image

WIDTH, HEIGHT = 800, 480

def main():
    # ensure mixer pre-init then init pygame
    init_audio()
    pygame.init()

    pull_sound = load_sound("pull.wav")
    win_sound = load_sound("win.wav")
    select_sound = load_sound("select.wav")
    menu_music = load_music("menu.wav")
    gameplay_music = load_music("gameplay.wav")
    clone_sound = load_sound("clone-smoke.wav")

    print(f"[debug] menu_music loaded: {menu_music is not None}, type: {type(menu_music)}")
    print(f"[debug] gameplay_music loaded: {gameplay_music is not None}, type: {type(gameplay_music)}")

    # per-track target volumes (0.0 .. 1.0)
    menu_volume = 0.4      # tune menu music
    gameplay_volume = 0.6   # tune gameplay music

    # reduce menu music volume (0.0 = silent .. 1.0 = full). adjust as desired.
    try:
        if menu_music:
            # if load_music returned a Sound object
            if isinstance(menu_music, pygame.mixer.Sound):
                menu_music.set_volume(menu_volume)
            else:
                # if load_music returned a filename/path used with pygame.mixer.music
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

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tug Of War - Prototype")

    game = Game(screen, WIDTH, HEIGHT, ai=True)  # default to 1 player mode
    game.pull_sound = pull_sound
    game.win_sound = win_sound
    game.select_sound = select_sound
    game.menu_music = menu_music
    game.gameplay_music = gameplay_music
    # expose desired volumes to the Game instance
    game.menu_volume = menu_volume
    game.gameplay_volume = gameplay_volume
    game.clone_sound = clone_sound

    # debug: verify pull_strength parity
    try:
        print(f"[debug] pull_strength -> left: {game.left.pull_strength}, right: {game.right.pull_strength}")
    except Exception:
        pass

    # start menu music if available
    try:
        game._set_music("menu")
    except Exception:
        pass

    game.run()

if __name__ == "__main__":
    main()
