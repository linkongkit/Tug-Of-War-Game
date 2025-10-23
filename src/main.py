import sys
import pygame
from game.core import Game

WIDTH, HEIGHT = 800, 480

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tug Of War - Prototype")
    game = Game(screen, WIDTH, HEIGHT)
    game.run()

if __name__ == "__main__":
    main()
