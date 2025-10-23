import sys
import pygame

WIDTH, HEIGHT = 800, 480
ROPE_Y = HEIGHT // 2

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tug Of War - Prototype")
    clock = pygame.time.Clock()

    rope_pos = WIDTH // 2
    pull_strength = 5

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            rope_pos -= pull_strength
        if keys[pygame.K_l]:
            rope_pos += pull_strength

        rope_pos = max(50, min(WIDTH - 50, rope_pos))

        screen.fill((30, 30, 30))
        pygame.draw.rect(screen, (150, 50, 50), (50, ROPE_Y-40, 60, 80))          # left team
        pygame.draw.rect(screen, (50, 50, 150), (WIDTH-110, ROPE_Y-40, 60, 80))  # right team
        pygame.draw.line(screen, (200, 180, 50), (50, ROPE_Y), (rope_pos, ROPE_Y), 6)
        pygame.draw.line(screen, (200, 180, 50), (rope_pos, ROPE_Y), (WIDTH-50, ROPE_Y), 6)
        pygame.draw.circle(screen, (255,255,255), (rope_pos, ROPE_Y), 8)

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
