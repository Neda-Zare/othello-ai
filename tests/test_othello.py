import unittest

from othello.ai import choose_move
from othello.logic import BLACK, EMPTY, SIZE, WHITE, Board, Game


def board_from(rows):
    """Build a board from 8 strings using '.', 'B', 'W'."""
    mapping = {".": EMPTY, "B": BLACK, "W": WHITE}
    return Board([[mapping[ch] for ch in row] for row in rows])


class BoardTests(unittest.TestCase):
    def test_initial_position(self):
        board = Board()
        self.assertEqual(board.count(BLACK), 2)
        self.assertEqual(board.count(WHITE), 2)
        self.assertEqual(
            sorted(board.valid_moves(BLACK)), [(2, 3), (3, 2), (4, 5), (5, 4)]
        )

    def test_flips(self):
        board = Board()
        flips = board.play(2, 3, BLACK)
        self.assertEqual(flips, [(3, 3)])
        self.assertEqual(board.grid[3][3], BLACK)
        self.assertEqual(board.count(BLACK), 4)

    def test_illegal_move_raises(self):
        with self.assertRaises(ValueError):
            Board().play(0, 0, BLACK)

    def test_out_of_bounds_is_not_a_move(self):
        board = Board()
        self.assertEqual(board.get_flips(-1, 3, BLACK), [])
        self.assertEqual(board.get_flips(8, 8, BLACK), [])

    def test_occupied_square_is_not_a_move(self):
        self.assertEqual(Board().get_flips(3, 3, BLACK), [])

    def test_multi_direction_flip(self):
        board = board_from([
            "........",
            "........",
            "........",
            "........",
            ".....WB.",
            "....W...",
            "....B...",
            "........",
        ])
        flips = board.get_flips(4, 4, BLACK)
        self.assertEqual(sorted(flips), [(4, 5), (5, 4)])

    def test_disc_at_edge_is_not_flanked(self):
        board = board_from(["BW......"] + ["........"] * 7)
        self.assertEqual(board.get_flips(0, 2, BLACK), [(0, 1)])
        self.assertEqual(board.get_flips(0, 2, WHITE), [])


class GameTests(unittest.TestCase):
    def test_turn_alternates(self):
        game = Game()
        self.assertEqual(game.turn, BLACK)
        self.assertTrue(game.play(2, 3))
        self.assertEqual(game.turn, WHITE)
        self.assertFalse(game.play(0, 0))
        self.assertEqual(game.turn, WHITE)

    def test_pass_keeps_same_player(self):
        game = Game()
        game.board = board_from([
            "BW......",
            "........",
            "........",
            "BW......",
            "........",
            "........",
            "........",
            "........",
        ])
        game.turn = BLACK
        self.assertTrue(game.play(0, 2))  # black flips (0, 1)
        # White's last disc sits next to the edge disc and cannot flank anything.
        self.assertEqual(game.board.valid_moves(WHITE), [])
        self.assertEqual(game.turn, BLACK)
        self.assertEqual(game.passed, WHITE)
        self.assertFalse(game.over)
        self.assertEqual(game.valid_moves(), [(3, 2)])

    def test_game_over_when_nobody_can_move(self):
        game = Game()
        game.board = board_from(["BBBBBBBB"] * 4 + ["........"] * 4)
        game.turn = WHITE
        game._advance()
        self.assertTrue(game.over)
        self.assertEqual(game.winner(), BLACK)
        self.assertFalse(game.play(5, 5))

    def test_draw(self):
        game = Game()
        game.board = board_from(["BBBBBBBB"] * 4 + ["WWWWWWWW"] * 4)
        game.turn = BLACK
        game._advance()
        self.assertTrue(game.over)
        self.assertEqual(game.winner(), EMPTY)


class AITests(unittest.TestCase):
    def test_returns_legal_move(self):
        board = Board()
        move = choose_move(board, BLACK, depth=3)
        self.assertIn(move, board.valid_moves(BLACK))

    def test_no_move_returns_none(self):
        board = board_from(["BBBBBBBB"] * 8)
        self.assertIsNone(choose_move(board, WHITE, depth=2))

    def test_takes_corner(self):
        board = board_from([
            ".BW.....",
            "........",
            "........",
            "...BW...",
            "........",
            "........",
            "........",
            "...W..B.",
        ])
        # White can flank (0, 1) from the corner or (3, 3) from (3, 2).
        self.assertIn((0, 0), board.valid_moves(WHITE))
        self.assertIn((3, 2), board.valid_moves(WHITE))
        self.assertEqual(choose_move(board, WHITE, depth=2), (0, 0))

    def test_full_game_ai_vs_ai_terminates(self):
        game = Game()
        moves = 0
        while not game.over and moves < 200:
            move = choose_move(game.board, game.turn, depth=2)
            self.assertIsNotNone(move)
            self.assertTrue(game.play(*move))
            moves += 1
        self.assertTrue(game.over)
        black, white = game.score()
        self.assertEqual(black + white + game.board.empty_count(), SIZE * SIZE)


if __name__ == "__main__":
    unittest.main()
