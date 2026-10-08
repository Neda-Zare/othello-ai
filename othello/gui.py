"""pygame front-end for Othello."""

from __future__ import annotations

import queue
import threading

import pygame

from .ai import DIFFICULTY_DEPTH, choose_move
from .logic import BLACK, EMPTY, SIZE, WHITE, Game

HUMAN, COMPUTER = BLACK, WHITE

SQUARE = 80
BOARD_PX = SQUARE * SIZE
BAR_H = 70
FOOTER_H = 36
WIDTH = BOARD_PX
HEIGHT = BAR_H + BOARD_PX + FOOTER_H
FPS = 30

BOARD_GREEN = (30, 120, 60)
LINE_COLOR = (15, 70, 35)
BAR_COLOR = (28, 30, 36)
TEXT_COLOR = (235, 235, 235)
MUTED_COLOR = (150, 155, 165)
DISC_BLACK = (20, 20, 20)
DISC_WHITE = (240, 240, 240)
HINT_COLOR = (200, 235, 210)
LAST_MOVE_COLOR = (220, 60, 60)
OVERLAY_COLOR = (0, 0, 0, 150)


class App:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Othello")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 24)
        self.small_font = pygame.font.SysFont("arial", 16)
        self.big_font = pygame.font.SysFont("arial", 56, bold=True)

        self.difficulty = "medium"
        self.results: queue.Queue = queue.Queue()
        self.generation = 0
        self.thinking = False
        self.game = Game()
        self.new_game()

    # ------------------------------------------------------------------ state
    def new_game(self) -> None:
        self.generation += 1  # invalidates any search still running
        self.thinking = False
        self.game = Game()

    def start_ai(self) -> None:
        self.thinking = True
        generation = self.generation
        board = self.game.board.copy()
        depth = DIFFICULTY_DEPTH[self.difficulty]

        def work() -> None:
            self.results.put((generation, choose_move(board, COMPUTER, depth)))

        threading.Thread(target=work, daemon=True).start()

    def update(self) -> None:
        while not self.results.empty():
            generation, move = self.results.get()
            if generation != self.generation:
                continue  # result of an old game
            self.thinking = False
            if move is not None:
                self.game.play(*move)

        if (
            not self.game.over
            and self.game.turn == COMPUTER
            and not self.thinking
        ):
            self.start_ai()

    # ----------------------------------------------------------------- events
    def handle_click(self, pos: tuple[int, int]) -> None:
        if self.game.over or self.game.turn != HUMAN or self.thinking:
            return
        x, y = pos
        row, col = (y - BAR_H) // SQUARE, x // SQUARE
        if y < BAR_H or not (0 <= row < SIZE and 0 <= col < SIZE):
            return
        self.game.play(row, col)

    def handle_key(self, key: int) -> None:
        if key == pygame.K_r:
            self.new_game()
        elif key == pygame.K_1:
            self.difficulty = "easy"
        elif key == pygame.K_2:
            self.difficulty = "medium"
        elif key == pygame.K_3:
            self.difficulty = "hard"

    # ---------------------------------------------------------------- drawing
    @staticmethod
    def _center(row: int, col: int) -> tuple[int, int]:
        return col * SQUARE + SQUARE // 2, BAR_H + row * SQUARE + SQUARE // 2

    def _draw_disc(self, center: tuple[int, int], player: int, radius: int) -> None:
        color = DISC_BLACK if player == BLACK else DISC_WHITE
        edge = (90, 90, 90) if player == BLACK else (170, 170, 170)
        pygame.draw.circle(self.screen, edge, center, radius + 1)
        pygame.draw.circle(self.screen, color, center, radius)

    def _status_text(self) -> str:
        game = self.game
        if game.over:
            winner = game.winner()
            if winner == EMPTY:
                return "Game over - it's a draw"
            return "Game over - you win!" if winner == HUMAN else "Game over - computer wins"
        prefix = ""
        if game.passed is not None:
            who = "You have" if game.passed == HUMAN else "Computer has"
            prefix = f"{who} no moves, turn skipped. "
        if game.turn == HUMAN:
            return prefix + "Your turn"
        return prefix + "Computer is thinking..."

    def draw(self) -> None:
        screen = self.screen
        screen.fill(BAR_COLOR)

        # Board
        for row in range(SIZE):
            for col in range(SIZE):
                rect = (col * SQUARE, BAR_H + row * SQUARE, SQUARE, SQUARE)
                pygame.draw.rect(screen, BOARD_GREEN, rect)
                pygame.draw.rect(screen, LINE_COLOR, rect, 1)
                cell = self.game.board.grid[row][col]
                if cell != EMPTY:
                    self._draw_disc(self._center(row, col), cell, SQUARE // 2 - 7)

        # Hints for the human player
        if not self.game.over and self.game.turn == HUMAN:
            for row, col in self.game.valid_moves():
                pygame.draw.circle(screen, HINT_COLOR, self._center(row, col), 8)

        # Last move marker
        if self.game.last_move:
            pygame.draw.circle(
                screen, LAST_MOVE_COLOR, self._center(*self.game.last_move), 6
            )

        self._draw_bar()
        self._draw_footer()
        if self.game.over:
            self._draw_game_over()
        pygame.display.flip()

    def _draw_bar(self) -> None:
        status = self.font.render(self._status_text(), True, TEXT_COLOR)
        self.screen.blit(status, (16, 12))
        level = self.small_font.render(
            f"Difficulty: {self.difficulty}", True, MUTED_COLOR
        )
        self.screen.blit(level, (16, 44))

        black, white = self.game.score()
        x = WIDTH - 190
        self._draw_disc((x, 35), BLACK, 14)
        self.screen.blit(self.font.render(str(black), True, TEXT_COLOR), (x + 24, 22))
        self._draw_disc((x + 90, 35), WHITE, 14)
        self.screen.blit(self.font.render(str(white), True, TEXT_COLOR), (x + 114, 22))

    def _draw_footer(self) -> None:
        text = "R: new game    1/2/3: difficulty (easy/medium/hard)    You are black"
        surf = self.small_font.render(text, True, MUTED_COLOR)
        self.screen.blit(surf, (16, BAR_H + BOARD_PX + 9))

    def _draw_game_over(self) -> None:
        overlay = pygame.Surface((BOARD_PX, BOARD_PX), pygame.SRCALPHA)
        overlay.fill(OVERLAY_COLOR)
        self.screen.blit(overlay, (0, BAR_H))

        winner = self.game.winner()
        if winner == EMPTY:
            title = "Draw"
        else:
            title = "You win!" if winner == HUMAN else "You lose"
        surf = self.big_font.render(title, True, TEXT_COLOR)
        self.screen.blit(surf, surf.get_rect(center=(WIDTH // 2, BAR_H + BOARD_PX // 2 - 20)))
        hint = self.font.render("Press R to play again", True, TEXT_COLOR)
        self.screen.blit(hint, hint.get_rect(center=(WIDTH // 2, BAR_H + BOARD_PX // 2 + 35)))

    # ------------------------------------------------------------------- loop
    def run(self) -> None:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    else:
                        self.handle_key(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_click(event.pos)
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()


def main() -> None:
    App().run()
