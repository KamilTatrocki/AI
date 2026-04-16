from __future__ import annotations
from abc import ABC, abstractmethod
from board import Board

class Heuristic(ABC):
    @abstractmethod
    def evaluate(self, board: Board, player: str) -> float:
        """
        im wyzej tym lepiej
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """nazwa"""

class MaterialAdvantage(Heuristic):
    @property
    def name(self) -> str:
        return "material_advantage"

    def evaluate(self, board: Board, player: str) -> float:
        opponent = Board.W if player == Board.B else Board.B
        return float(board.count(player) - board.count(opponent))




class PositionalAdvance(Heuristic):
    def __init__(self, alpha: float = 1.5) -> None:
        self._alpha = alpha

    @property
    def name(self) -> str:
        return "positional_advance"

    def evaluate(self, board: Board, player: str) -> float:
        n = board.n
        score = 0.0

        for r in range(n):
            for c in range(board.m):
                piece = board.cell(r, c)
                if piece == Board.B:
                    advance = r  
                    advance *= self._alpha
                    score += advance if player == Board.B else -advance
                elif piece == Board.W:
                    advance = n - 1 - r  
                    advance *= self._alpha
                    score += advance if player == Board.W else -advance
        return score



class DefensiveAggressiveMix(Heuristic):
    """
    alpha · materiał  +  beta · zaawansowanie  +  gamma · bezpieczeństwo
    """

    def __init__(
        self,
        alpha: float = 3.0,
        beta: float = 1.5,
        gamma: float = 0.5,
    ) -> None:
        self._alpha = alpha
        self._beta = beta
        self._gamma = gamma

    @property
    def name(self) -> str:
        return "defensive_aggressive_mix"

    @staticmethod
    def _safety_score(board: Board, player: str) -> float:
        direction = Board._direction(player)
        protected = 0
        for r in range(board.n):
            for c in range(board.m):
                if board.cell(r, c) != player:
                    continue
                back_row = r - direction
                if not (0 <= back_row < board.n):
                    continue
                for dc in (-1, 1):
                    bc = c + dc
                    if 0 <= bc < board.m and board.cell(back_row, bc) == player:
                        protected += 1
                        break
        return float(protected)

    def _evaluate_params_value(self, board: Board) -> None:
        board_cells = board.n * board.m
        current_pieces = board.count(Board.B) + board.count(Board.W)
        
        progress = 1.0 - (current_pieces / board_cells) if board_cells > 0 else 1.0
        progress = max(0.0, min(1.0, progress))
        
        self._alpha = 3.0 - (1.0 * progress)  
        self._beta = 1.5 + (2.5 * progress)   
        self._gamma = 0.5 - (0.4 * progress)  

    def evaluate(self, board: Board, player: str) -> float:
        self._evaluate_params_value(board)

        opponent = Board.W if player == Board.B else Board.B

        mat = MaterialAdvantage().evaluate(board, player)
        pos = PositionalAdvance().evaluate(board, player)
        safety = self._safety_score(board, player) - self._safety_score(board, opponent)

        return self._alpha * mat + self._beta * pos + self._gamma * safety



HEURISTICS: dict[str, Heuristic] = {
    "1": MaterialAdvantage(),
    "2": PositionalAdvance(),
    "3": DefensiveAggressiveMix(),
    "material":   MaterialAdvantage(),
    "positional": PositionalAdvance(),
    "mixed":      DefensiveAggressiveMix(),
}
