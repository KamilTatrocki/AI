"""
board.py – reprezentacja planszy gry Breakthrough.

Symbole:
    B  – pionek gracza pierwszego (porusza się w dół, wiersz 0 → N-1)
    W  – pionek gracza drugiego   (porusza się w górę, wiersz N-1 → 0)
    _  – pole puste
    o  – pole, z którego wykonano ostatni ruch (tylko w wypisywaniu)

Ruch: krotka ((from_row, from_col), (to_row, to_col))
"""
from __future__ import annotations

import copy
from typing import List, Optional, Tuple

Move = Tuple[Tuple[int, int], Tuple[int, int]]


class Board:
    """
    Niemutowalna reprezentacja stanu planszy Breakthrough.

    Plansza przechowywana jako lista list znaków: 'B', 'W', '_'.
    _last_from przechowuje współrzędne pola, z którego wykonano ruch –
    służy do wypisywania znaku 'o'.

    Gracze:
        'B' (Black) – porusza się z wiersza 0 w kierunku wiersza N-1
        'W' (White) – porusza się z wiersza N-1 w kierunku wiersza 0
    """

    EMPTY = '_'
    B = 'B'
    W = 'W'

    def __init__(
        self,
        n: int = 8,
        m: int = 8,
        initial_state: Optional[List[List[str]]] = None,
        last_from: Optional[Tuple[int, int]] = None,
    ) -> None:
        self.n = n  # wiersze
        self.m = m  # kolumny
        self._last_from: Optional[Tuple[int, int]] = last_from

        if initial_state is not None:
            self._grid: List[List[str]] = copy.deepcopy(initial_state)
        else:
            self._grid = self._default_grid()



    def _default_grid(self) -> List[List[str]]:
        """Dwa pierwsze rzędy = B, dwa ostatnie = W, reszta pusta."""
        grid = [[self.EMPTY] * self.m for _ in range(self.n)]
        for row in range(2):
            for col in range(self.m):
                grid[row][col] = self.B
        for row in range(self.n - 2, self.n):
            for col in range(self.m):
                grid[row][col] = self.W
        return grid


    @staticmethod
    def _direction(player: str) -> int:
        """Kierunek ruchu: B idzie w dół (+1), W idzie w górę (-1)."""
        return 1 if player == Board.B else -1

    def get_legal_moves(self, player: str) -> List[Move]:
        """
        Zwraca listę wszystkich legalnych ruchów dla gracza ('B' lub 'W').

        Zasady:
        - Pionek przesuwa się o 1 pole do przodu (prosto lub po skosie).
        - Ruch prosto: dozwolony tylko na puste pole.
        - Ruch po skosie: dozwolony na puste pole LUB na pole zajęte przez
          przeciwnika (bicie).
        """
        assert player in (self.B, self.W), f"Nieznany gracz: {player}"
        direction = self._direction(player)
        moves: List[Move] = []

        for row in range(self.n):
            for col in range(self.m):
                if self._grid[row][col] != player:
                    continue
                new_row = row + direction
                if not (0 <= new_row < self.n):
                    continue
                for dc in (-1, 0, 1):
                    new_col = col + dc
                    if not (0 <= new_col < self.m):
                        continue
                    dest = self._grid[new_row][new_col]
                    if dc == 0:
                        # ruch prosty – tylko puste pole
                        if dest == self.EMPTY:
                            moves.append(((row, col), (new_row, new_col)))
                    else:
                        # ruch skośny – puste LUB bicie przeciwnika
                        if dest != player:
                            moves.append(((row, col), (new_row, new_col)))
        return moves

    def make_move(self, move: Move) -> "Board":
        """
        Tworzy nowy, niemutowalny obiekt Board z wykonanym ruchem.
        Rzuca ValueError dla ruchów nielegalnych.
        """
        (fr, fc), (tr, tc) = move

        if not (0 <= fr < self.n and 0 <= fc < self.m):
            raise ValueError(f"Pole źródłowe ({fr},{fc}) poza planszą.")
        if not (0 <= tr < self.n and 0 <= tc < self.m):
            raise ValueError(f"Pole docelowe ({tr},{tc}) poza planszą.")

        player = self._grid[fr][fc]
        if player not in (self.B, self.W):
            raise ValueError(f"Brak pionka gracza na polu ({fr},{fc}).")

        if move not in self.get_legal_moves(player):
            raise ValueError(f"Nielegalny ruch: {move} dla gracza {player}.")

        new_grid = copy.deepcopy(self._grid)
        new_grid[tr][tc] = new_grid[fr][fc]
        new_grid[fr][fc] = self.EMPTY
        return Board(n=self.n, m=self.m, initial_state=new_grid, last_from=(fr, fc))


    def is_game_over(self) -> bool:
        """Sprawdza, czy gra się skończyła."""
        return self.get_winner() is not None

    def get_winner(self) -> Optional[str]:
        """
        Zwraca 'B' lub 'W' jeśli któryś gracz wygrał, None w przeciwnym razie.

        Warunki wygranej:
        - B wygrywa, gdy jakiś pionek B dotrze do ostatniego rzędu (n-1).
        - W wygrywa, gdy jakiś pionek W dotrze do wiersza 0.
        - Gracz wygrywa też, gdy przeciwnik nie ma żadnych ruchów.
        """
        for col in range(self.m):
            if self._grid[self.n - 1][col] == self.B:
                return self.B
        for col in range(self.m):
            if self._grid[0][col] == self.W:
                return self.W
        if not self.get_legal_moves(self.B):
            return self.W
        if not self.get_legal_moves(self.W):
            return self.B
        return None



    def get_board_string(self) -> str:
        """Zwraca string z reprezentacją planszy (z literami kolumn i numerami wierszy)."""
        lines = []
        col_labels = "  " + " ".join(chr(ord('A') + c) for c in range(self.m))
        lines.append(col_labels)
        for r in range(self.n):
            cells = []
            for c in range(self.m):
                if self._last_from is not None and (r, c) == self._last_from:
                    cells.append('o')
                else:
                    cells.append(self._grid[r][c])
            lines.append(f"{r + 1} " + " ".join(cells))
        return "\n".join(lines)

    def print_board(self) -> None:
        """Wypisuje planszę z literami kolumn (A-Z) i numerami wierszy."""
        print(self.get_board_string())



    def cell(self, row: int, col: int) -> str:
        return self._grid[row][col]

    def count(self, player: str) -> int:
        return sum(
            self._grid[r][c] == player
            for r in range(self.n)
            for c in range(self.m)
        )

    def to_text(self) -> str:
        """Reprezentacja tekstowa zgodna ze specyfikacją (B/W/_/o, spacje)."""
        lines = []
        for r in range(self.n):
            cells = []
            for c in range(self.m):
                if self._last_from is not None and (r, c) == self._last_from:
                    cells.append('o')
                else:
                    cells.append(self._grid[r][c])
            lines.append(" ".join(cells))
        return "\n".join(lines)

    @staticmethod
    def from_text(text: str, n: int = 8, m: int = 8) -> "Board":
        """
        Wczytuje planszę z tekstu (n linii po m tokenów).
        Symbole 'o' (ostatni ruch) zastępowane są przez '_'.
        """
        rows = []
        for line in text.strip().splitlines():
            cells = line.split()
            row = [c if c in ('B', 'W') else Board.EMPTY for c in cells]
            rows.append(row)
        actual_n = len(rows)
        actual_m = max(len(r) for r in rows) if rows else m
        return Board(n=actual_n, m=actual_m, initial_state=rows)
