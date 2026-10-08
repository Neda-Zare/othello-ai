"""Pure game logic for Othello (no pygame dependency)."""

from __future__ import annotations

EMPTY, BLACK, WHITE = 0, 1, -1
SIZE = 8
DIRECTIONS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)


def in_bounds(row: int, col: int) -> bool:
    return 0 <= row < SIZE and 0 <= col < SIZE


class Board:
    """An 8x8 board stored as a list of lists (fast enough for tree search)."""

    __slots__ = ("grid",)

    def __init__(self, grid: list[list[int]] | None = None) -> None:
        if grid is not None:
            self.grid = grid
            return
        self.grid = [[EMPTY] * SIZE for _ in range(SIZE)]
        mid = SIZE // 2
        self.grid[mid - 1][mid - 1] = self.grid[mid][mid] = WHITE
        self.grid[mid - 1][mid] = self.grid[mid][mid - 1] = BLACK

    def copy(self) -> "Board":
        return Board([row[:] for row in self.grid])

    def get_flips(self, row: int, col: int, player: int) -> list[tuple[int, int]]:
        """Return the discs that would be flipped if `player` played at (row, col).

        An empty list means the move is illegal.
        """
        if not in_bounds(row, col) or self.grid[row][col] != EMPTY:
            return []
        grid = self.grid
        flips: list[tuple[int, int]] = []
        for d_row, d_col in DIRECTIONS:
            r, c = row + d_row, col + d_col
            line: list[tuple[int, int]] = []
            while in_bounds(r, c) and grid[r][c] == -player:
                line.append((r, c))
                r += d_row
                c += d_col
            if line and in_bounds(r, c) and grid[r][c] == player:
                flips.extend(line)
        return flips

    def valid_moves(self, player: int) -> list[tuple[int, int]]:
        return [
            (r, c)
            for r in range(SIZE)
            for c in range(SIZE)
            if self.get_flips(r, c, player)
        ]

    def has_moves(self, player: int) -> bool:
        return any(
            self.get_flips(r, c, player)
            for r in range(SIZE)
            for c in range(SIZE)
        )

    def play(self, row: int, col: int, player: int) -> list[tuple[int, int]]:
        """Play a move in place and return the flipped discs."""
        flips = self.get_flips(row, col, player)
        if not flips:
            raise ValueError(f"Illegal move for {player}: {(row, col)}")
        self.grid[row][col] = player
        for r, c in flips:
            self.grid[r][c] = player
        return flips

    def count(self, player: int) -> int:
        return sum(row.count(player) for row in self.grid)

    def empty_count(self) -> int:
        return sum(row.count(EMPTY) for row in self.grid)


class Game:
    """Game state: handles turns, passes and the end of the game."""

    def __init__(self) -> None:
        self.board = Board()
        self.turn = BLACK  # Black moves first
        self.over = False
        self.last_move: tuple[int, int] | None = None
        self.passed: int | None = None  # player who had to pass last turn

    def valid_moves(self) -> list[tuple[int, int]]:
        return [] if self.over else self.board.valid_moves(self.turn)

    def play(self, row: int, col: int) -> bool:
        """Try to play for the current player. Returns True if the move was legal."""
        if self.over:
            return False
        try:
            self.board.play(row, col, self.turn)
        except ValueError:
            return False
        self.last_move = (row, col)
        self._advance()
        return True

    def _advance(self) -> None:
        self.passed = None
        opponent = -self.turn
        if self.board.has_moves(opponent):
            self.turn = opponent
        elif self.board.has_moves(self.turn):
            self.passed = opponent  # opponent must pass, same player moves again
        else:
            self.over = True

    def score(self) -> tuple[int, int]:
        """Return (black, white)."""
        return self.board.count(BLACK), self.board.count(WHITE)

    def winner(self) -> int | None:
        """BLACK / WHITE, EMPTY for a draw, or None while the game is running."""
        if not self.over:
            return None
        black, white = self.score()
        if black == white:
            return EMPTY
        return BLACK if black > white else WHITE
