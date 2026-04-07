import argparse
import random
import sys

import pygame

WIDTH, HEIGHT = 800, 600
TARGET_RADIUS = 35
GAME_TIME_SECONDS = 30
BG_COLOR = (20, 24, 32)
TARGET_COLOR = (255, 120, 80)
TEXT_COLOR = (235, 240, 255)


def spawn_target():
    x = random.randint(TARGET_RADIUS, WIDTH - TARGET_RADIUS)
    y = random.randint(TARGET_RADIUS + 70, HEIGHT - TARGET_RADIUS)
    return x, y


def make_font(size: int) -> pygame.font.Font:
    # Try a Korean-capable font first, then fallback safely.
    preferred = ["malgungothic", "맑은 고딕", "arial", "sans"]
    for name in preferred:
        font = pygame.font.SysFont(name, size)
        if font:
            return font
    return pygame.font.Font(None, size)


def run_game(test_seconds: float = 0.0) -> int:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Simple Click Game")
    clock = pygame.time.Clock()
    font = make_font(28)

    score = 0
    target_x, target_y = spawn_target()
    start_ticks = pygame.time.get_ticks()
    test_quit_ms = int(test_seconds * 1000) if test_seconds > 0 else None

    running = True
    while running:
        elapsed_ms = pygame.time.get_ticks() - start_ticks
        elapsed_s = elapsed_ms / 1000
        time_left = max(0, GAME_TIME_SECONDS - int(elapsed_s))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if (mx - target_x) ** 2 + (my - target_y) ** 2 <= TARGET_RADIUS**2:
                    score += 1
                    target_x, target_y = spawn_target()

        if elapsed_s >= GAME_TIME_SECONDS:
            running = False
        if test_quit_ms is not None and elapsed_ms >= test_quit_ms:
            running = False

        screen.fill(BG_COLOR)
        pygame.draw.circle(screen, TARGET_COLOR, (target_x, target_y), TARGET_RADIUS)
        screen.blit(font.render(f"Score: {score}", True, TEXT_COLOR), (20, 16))
        screen.blit(font.render(f"Time Left: {time_left}s", True, TEXT_COLOR), (20, 48))
        screen.blit(font.render("Click the circle!", True, TEXT_COLOR), (WIDTH - 230, 16))
        pygame.display.flip()
        clock.tick(60)

    if test_quit_ms is None:
        screen.fill(BG_COLOR)
        end_text = font.render(f"Game Over! Final Score: {score}", True, TEXT_COLOR)
        hint_text = font.render("Press ESC or close window.", True, TEXT_COLOR)
        screen.blit(end_text, (WIDTH // 2 - end_text.get_width() // 2, HEIGHT // 2 - 30))
        screen.blit(hint_text, (WIDTH // 2 - hint_text.get_width() // 2, HEIGHT // 2 + 10))
        pygame.display.flip()

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    waiting = False
            clock.tick(30)

    pygame.quit()
    return score


def parse_args():
    parser = argparse.ArgumentParser(description="Simple pygame click game")
    parser.add_argument(
        "--test-seconds",
        type=float,
        default=0.0,
        help="Auto-quit after N seconds for non-interactive test runs.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        run_game(test_seconds=args.test_seconds)
    except pygame.error as exc:
        print(f"Pygame runtime error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
