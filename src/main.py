import sys
import pygame
from game.core import Game
from game.utils import init_audio, load_sound

WIDTH, HEIGHT = 800, 480

def main():
    pygame.init()

    # initialize audio (safe) and try to load a pull sound
    init_audio()
    pull_sound = load_sound("pull.wav")  # optional
    win_sound = load_sound("win.wav")    # new win sound
    if pull_sound:
        pull_sound.set_volume(0.6)
    if win_sound:
        win_sound.set_volume(0.9)

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tug Of War - Prototype")

    game = Game(screen, WIDTH, HEIGHT)
    game.pull_sound = pull_sound
    game.win_sound = win_sound   # attach win sound

    game.run()

if __name__ == "__main__":
    main()
