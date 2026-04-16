from __future__ import annotations
import copy
from typing import List, Optional, Tuple

Move = Tuple[Tuple[int, int], Tuple[int, int]]

class Board:
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
        self.n = n
        self.m = m
        self._last_from: Optional[Tuple[int, int]] = last_from

        if initial_state is not None:
            self._grid: List[List[str]] = copy.deepcopy(initial_state)
        else:
            self._grid = self._default_grid()



    def _default_grid(self) -> List[List[str]]:
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
        """1 dla B, -1 dla W"""
        return 1 if player == Board.B else -1

    def get_legal_moves(self, player: str) -> List[Move]:
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
                        # ruch prosty
                        if dest == self.EMPTY:
                            moves.append(((row, col), (new_row, new_col)))
                    else:
                        # ruch skośny
                        if dest != player:
                            moves.append(((row, col), (new_row, new_col)))
        return moves

    def make_move(self, move: Move) -> "Board":
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
        return self.get_winner() is not None

    def get_winner(self) -> Optional[str]:
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
        rows = []
        for line in text.strip().splitlines():
            cells = [char for char in line if not char.isspace()]
            row = [c if c in ('B', 'W') else Board.EMPTY for c in cells]
            
            while len(row) < m:
                row.append(Board.EMPTY)
            
            rows.append(row[:m])
            
        while len(rows) < n:
            rows.append([Board.EMPTY] * m)
            
        return Board(n=n, m=m, initial_state=rows[:n])
