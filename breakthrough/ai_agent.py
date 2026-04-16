from __future__ import annotations

import math
from typing import Optional

from board import Board, Move
from heuristics import Heuristic


class AiAgent:
    WIN_SCORE  =  10_000_000.0
    LOSS_SCORE = -10_000_000.0

    def __init__(self, player: str, depth: int, heuristic: Heuristic, use_alpha_beta: bool = True) -> None:
        assert player in (Board.B, Board.W), f"Nieznany gracz: {player}"
        self.player         = player
        self.opponent       = Board.W if player == Board.B else Board.B
        self.depth          = depth
        self.heuristic      = heuristic
        self.use_alpha_beta = use_alpha_beta
        self.nodes_visited: int = 0

    def minimax(self, board: Board, depth: int, is_maximizing: bool) -> float:
        self.nodes_visited += 1

        winner = board.get_winner()
        if winner is not None:
            return self.WIN_SCORE if winner == self.player else self.LOSS_SCORE
        if depth == 0:
            return self.heuristic.evaluate(board, self.player)

        current_player = self.player if is_maximizing else self.opponent
        moves = board.get_legal_moves(current_player)

        if not moves:
            return self.LOSS_SCORE if is_maximizing else self.WIN_SCORE

        if is_maximizing:
            best = -math.inf
            for move in moves:
                best = max(best, self.minimax(board.make_move(move), depth - 1, False))
            return best
        else:
            best = math.inf
            for move in moves:
                best = min(best, self.minimax(board.make_move(move), depth - 1, True))
            return best


    def alpha_beta(
        self,
        board: Board,
        depth: int,
        alpha: float,
        beta: float,
        is_maximizing: bool,
    ) -> float:
 
        self.nodes_visited += 1

        winner = board.get_winner()
        if winner is not None:
            return self.WIN_SCORE if winner == self.player else self.LOSS_SCORE
        if depth == 0:
            return self.heuristic.evaluate(board, self.player)

        current_player = self.player if is_maximizing else self.opponent
        moves = board.get_legal_moves(current_player)

        if not moves:
            return self.LOSS_SCORE if is_maximizing else self.WIN_SCORE

        if is_maximizing:
            value = -math.inf
            for move in moves:
                value = max(value, self.alpha_beta(board.make_move(move), depth - 1, alpha, beta, False))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break  
            return value
        else:
            value = math.inf
            for move in moves:
                value = min(value, self.alpha_beta(board.make_move(move), depth - 1, alpha, beta, True))
                beta = min(beta, value)
                if beta <= alpha:
                    break  
            return value



    def choose_move(self, board: Board) -> Optional[Move]:
        self.nodes_visited = 0
        moves = board.get_legal_moves(self.player)
        if not moves:
            return None

        best_move: Optional[Move] = None
        best_val = -math.inf

        for move in moves:
            if self.use_alpha_beta:
                val = self.alpha_beta(
                    board.make_move(move),
                    self.depth - 1,
                    -math.inf,
                    math.inf,
                    False,
                )
            else:
                val = self.minimax(
                    board.make_move(move),
                    self.depth - 1,
                    False,
                )
            if val > best_val:
                best_val = val
                best_move = move

        return best_move

    @property
    def algorithm_name(self) -> str:
        return "Alpha-Beta" if self.use_alpha_beta else "Minimax"
