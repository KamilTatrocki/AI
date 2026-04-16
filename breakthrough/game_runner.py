from __future__ import annotations

import sys
import time
from typing import Optional

from board import Board
from ai_agent import AiAgent
from heuristics import HEURISTICS, MaterialAdvantage


class GameRunner:
    def __init__(self) -> None:
        self.mode: str = 'basic'
        self.board: Optional[Board] = None
        self.agent_b: Optional[AiAgent] = None
        self.agent_w: Optional[AiAgent] = None
        self.rounds: int = 0
        self.total_nodes: int = 0
        self.elapsed: float = 0.0

    def parse_input(self) -> None:
        mode_raw = input("Tryb gry [basic/extended]: ").strip().lower()
        self.mode = mode_raw if mode_raw in ('basic', 'extended') else 'extended'

        algo_raw = input("Algorytm [1-AlphaBeta/2-Minimax]: ").strip()
        use_alpha_beta = (algo_raw != '2')

        dims_raw = input("Wymiary planszy [n m]: ").strip().split()
        if len(dims_raw) >= 2:
            n, m = int(dims_raw[0]), int(dims_raw[1])
        else:
            n, m = 8, 8

        d_b_raw = input("Głębokość Agent B: ").strip()
        d_b = int(d_b_raw) if d_b_raw.isdigit() else 3

        heur_b_key = input("Heurystyka B [1-mat/2-pos/3-mix]: ").strip() or '3'
        heur_b = HEURISTICS.get(heur_b_key, MaterialAdvantage())
        self.agent_b = AiAgent(Board.B, d_b, heur_b, use_alpha_beta)

        if self.mode == 'extended':
            d_w_raw = input("Głębokość Agent W: ").strip()
            d_w = int(d_w_raw) if d_w_raw.isdigit() else 3

            heur_w_key = input("Heurystyka W [1-mat/2-pos/3-mix]: ").strip() or '1'
            heur_w = HEURISTICS.get(heur_w_key, MaterialAdvantage())
            self.agent_w = AiAgent(Board.W, d_w, heur_w, use_alpha_beta)
        else:
            self.agent_w = AiAgent(Board.W, d_b, heur_b, use_alpha_beta)

        custom = input("Własna plansza? [t/N]: ").strip().lower()
        if custom == 't':
            board_lines = []
            while len(board_lines) < n:
                line = input().strip()
                if line.lower() == 'q':
                    break
                board_lines.append(line)
            self.board = Board.from_text("\n".join(board_lines), n=n, m=m)
        else:
            self.board = Board(n=n, m=m)

    def play_game(self) -> None:
        assert self.board is not None, "Wywołaj parse_input() przed play_game()."

        current_player = Board.W  
        self.rounds = 0
        self.total_nodes = 0
        start_time = time.perf_counter()

        with open("last_game.txt", "w", encoding="utf-8") as f:
            f.write("=== POCZĄTEK GRY ===\n")
            f.write(self.board.get_board_string() + "\n\n")

        while not self.board.is_game_over():
            agent = self.agent_b if current_player == Board.B else self.agent_w
            move = agent.choose_move(self.board)
            self.total_nodes += agent.nodes_visited

            if move is None:
                break  # brak ruchów = przegrana tego gracza

            
            (fr, fc), (tr, tc) = move
            from_pos = f"{chr(ord('A') + fc)}{fr + 1}"
            to_pos = f"{chr(ord('A') + tc)}{tr + 1}"
            player_name = "Agent B (Czarny)" if current_player == Board.B else "Agent W (Biały)"

            self.board = self.board.make_move(move)
            self.rounds += 1

     
            with open("last_game.txt", "a", encoding="utf-8") as f:
                f.write(f"--- RUNDA {self.rounds} ---\n")
                f.write(f"Ruch wykonał: {player_name}\n")
                f.write(f"Ruch: {from_pos} -> {to_pos} (z {fr},{fc} do {tr},{tc})\n")
                f.write("Plansza po ruchu:\n")
                f.write(self.board.get_board_string() + "\n\n")

            current_player = Board.W if current_player == Board.B else Board.B

        self.elapsed = time.perf_counter() - start_time


    def print_results(self) -> None:
        assert self.board is not None

        print("=== KOŃCOWY STAN PLANSZY ===")
        self.board.print_board()
        winner = self.board.get_winner()
        player_name = {"B": "Czarny (B)", "W": "Biały (W)"}.get(winner or '', "?")
        print(f"\nRundy:     {self.rounds}")
        print(f"Zwycięzca: {player_name}")

        
        print("\n[STATYSTYKI]")
        print(f"Odwiedzone węzły: {self.total_nodes}")
        print(f"Czas gry:         {self.elapsed:.4f} s")
        print(f"Tryb:             {self.mode}")
        if self.agent_b:
            print(
                f"Agent B: głębokość={self.agent_b.depth}, "
                f"heurystyka={self.agent_b.heuristic.name}, "
                f"algorytm={self.agent_b.algorithm_name}",
                file=sys.stderr,
            )
        if self.agent_w:
            print(
                f"Agent W: głębokość={self.agent_w.depth}, "
                f"heurystyka={self.agent_w.heuristic.name}, "
                f"algorytm={self.agent_w.algorithm_name}"
            )
