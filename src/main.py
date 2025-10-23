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

    if pull_sound:
        pull_sound.set_volume(0.6)
    if win_sound:
        win_sound.set_volume(0.9)
    if select_sound:
        select_sound.set_volume(0.8)

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tug Of War - Prototype")

    game = Game(screen, WIDTH, HEIGHT, ai=False)
    game.pull_sound = pull_sound
    game.win_sound = win_sound
    game.select_sound = select_sound
    game.menu_music = menu_music
    game.gameplay_music = gameplay_music

    # start menu music if available
    try:
        game._set_music("menu")
    except Exception:
        pass

    game.run()

if __name__ == "__main__":
    main()
