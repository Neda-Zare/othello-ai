"""Computer player: negamax search with alpha-beta pruning."""

from __future__ import annotations

from .logic import SIZE, Board

# Positional weights: corners are great, squares next to corners are dangerous.
WEIGHTS = [
    [100, -20, 10,  5,  5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [ 10,  -2,  5,  1,  1,  5,  -2,  10],
    [  5,  -2,  1,  0,  0,  1,  -2,   5],
    [  5,  -2,  1,  0,  0,  1,  -2,   5],
    [ 10,  -2,  5,  1,  1,  5,  -2,  10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10,  5,  5, 10, -20, 100],
]

WIN_SCORE = 10_000
MOBILITY_FACTOR = 8
ENDGAME_EMPTIES = 8
ENDGAME_DISC_FACTOR = 10

DIFFICULTY_DEPTH = {"easy": 2, "medium": 4, "hard": 5}


def evaluate(board: Board, player: int) -> int:
    """Heuristic value of `board` from the point of view of `player`."""
    grid = board.grid
    positional = 0
    for r in range(SIZE):
        weights = WEIGHTS[r]
        row = grid[r]
        for c in range(SIZE):
            positional += weights[c] * row[c]
    score = positional * player

    mobility = len(board.valid_moves(player)) - len(board.valid_moves(-player))
    score += MOBILITY_FACTOR * mobility

    if board.empty_count() <= ENDGAME_EMPTIES:
        score += ENDGAME_DISC_FACTOR * (board.count(player) - board.count(-player))
    return score


def _ordered(moves: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Try promising moves first so alpha-beta prunes more."""
    return sorted(moves, key=lambda m: WEIGHTS[m[0]][m[1]], reverse=True)


def negamax(board: Board, player: int, depth: int, alpha: int, beta: int) -> int:
    """Value of the position for `player`, who is to move."""
    moves = board.valid_moves(player)

    if not moves:
        if not board.has_moves(-player):
            # Game over: exact disc difference decides.
            diff = board.count(player) - board.count(-player)
            if diff == 0:
                return 0
            return WIN_SCORE + diff if diff > 0 else -WIN_SCORE + diff
        # `player` must pass; the opponent moves again (no depth consumed).
        return -negamax(board, -player, depth, -beta, -alpha)

    if depth == 0:
        return evaluate(board, player)

    best = -10 * WIN_SCORE
    for row, col in _ordered(moves):
        child = board.copy()
        child.play(row, col, player)
        value = -negamax(child, -player, depth - 1, -beta, -alpha)
        if value > best:
            best = value
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best


def choose_move(board: Board, player: int, depth: int = 4) -> tuple[int, int] | None:
    """Pick the best move for `player`, or None if there is no legal move."""
    moves = board.valid_moves(player)
    if not moves:
        return None

    alpha, beta = -10 * WIN_SCORE, 10 * WIN_SCORE
    best_move = None
    for row, col in _ordered(moves):
        child = board.copy()
        child.play(row, col, player)
        value = -negamax(child, -player, depth - 1, -beta, -alpha)
        if best_move is None or value > alpha:
            alpha = max(alpha, value)
            best_move = (row, col)
    return best_move
