"""
heuristics.py – interfejs Heuristic i trzy jego implementacje.

Wynik evaluate() jest zawsze z perspektywy podanego gracza:
    dodatni  → stan korzystny dla 'player'
    ujemny   → stan niekorzystny dla 'player'
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from board import Board


class Heuristic(ABC):
    """Interfejs heurystyki oceniającej stan planszy."""

    @abstractmethod
    def evaluate(self, board: Board, player: str) -> float:
        """
        Zwraca ocenę stanu `board` z perspektywy `player`.
        Wyższy wynik = lepszy stan dla `player`.
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """Zwraca nazwę heurystyki."""




class MaterialAdvantage(Heuristic):
    """
    Najprostsza ocena – różnica w liczbie pionków gracza i przeciwnika.
    """

    @property
    def name(self) -> str:
        return "material_advantage"

    def evaluate(self, board: Board, player: str) -> float:
        opponent = Board.W if player == Board.B else Board.B
        return float(board.count(player) - board.count(opponent))




class PositionalAdvance(Heuristic):
    """
    Sumuje odległość pionków od linii mety.
    Im bliżej krawędzi przeciwnika, tym wyższa ocena.

    B dąży do rzędu n-1  → zaawansowanie = r        (0 … n-1)
    W dąży do rzędu 0    → zaawansowanie = (n-1 - r) (0 … n-1)
    """

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
                    advance = r  # im wyższy wiersz, tym bliżej mety dla B
                    score += advance if player == Board.B else -advance
                elif piece == Board.W:
                    advance = n - 1 - r  # im niższy wiersz, tym bliżej mety dla W
                    score += advance if player == Board.W else -advance
        return score



class DefensiveAggressiveMix(Heuristic):
    """
    Kombinacja liczby pionków oraz ich "bezpieczeństwa".

    Składniki:
        α · materiał  +  β · zaawansowanie  +  γ · bezpieczeństwo

    Bezpieczeństwo: pionek jest chroniony, gdy co najmniej jeden sojusznik
    stoi skośnie z tyłu (osłania go przed biciem).
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
        """Liczba własnych pionków osłanianych przez sojusznika."""
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

    def evaluate(self, board: Board, player: str) -> float:
        opponent = Board.W if player == Board.B else Board.B

        mat = board.count(player) - board.count(opponent)
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
