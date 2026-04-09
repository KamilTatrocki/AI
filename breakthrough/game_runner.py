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
        print("╔══════════════════════════════════════════╗")
        print("║        BREAKTHROUGH – konfiguracja       ║")
        print("╚══════════════════════════════════════════╝\n")

        print("Tryb gry:")
        print("  basic    – obaj agenci używają tych samych heurystyk")
        print("  extended – dwa niezależne agenty z różnymi ustawieniami")
        mode_raw = input("Podaj tryb [basic/extended] (Enter = basic): ").strip().lower()
        self.mode = mode_raw if mode_raw in ('basic', 'extended') else 'basic'
        print("Wybrales: ", self.mode)
        print()

        print("Algorytm przeszukiwania:")
        print("  1 / alpha-beta – Minimax z przycinaniem Alpha-Beta (szybszy)")
        print("  2 / minimax    – Czysty Minimax (wolniejszy, bez przycinania)")
        algo_raw = input("Wybierz algorytm [1/2] (Enter = 1, czyli Alpha-Beta): ").strip()
        use_alpha_beta = (algo_raw != '2')
        print("Wybrales:", "Alpha-Beta" if use_alpha_beta else "Minimax")
        print()

        print("Wymiary planszy (min. 4x4, domyślnie 8x8):")
        dims_raw = input("Podaj n m (np. '8 8', Enter = 8 8): ").strip().split()
        if len(dims_raw) >= 2:
            n, m = int(dims_raw[0]), int(dims_raw[1])
        else:
            n, m = 8, 8
        print()

        print("═══ Agent B (Czarny – startuje od góry) ═══")
        d_b_raw = input("Głębokość przeszukiwania d [1-6] (Enter = 3): ").strip()
        d_b = int(d_b_raw) if d_b_raw.isdigit() else 3

        print("Heurystyka:")
        print("  1 / material   – przewaga materiałowa (liczba pionków)")
        print("  2 / positional – zaawansowanie pozycyjne (odległość od mety)")
        print("  3 / mixed      – kombinacja materiału, pozycji i bezpieczeństwa")
        heur_b_key = input("Wybierz heurystykę [1/2/3] (Enter = 1): ").strip() or '1'
        heur_b = HEURISTICS.get(heur_b_key, MaterialAdvantage())
        self.agent_b = AiAgent(Board.B, d_b, heur_b, use_alpha_beta)
        print()

        if self.mode == 'extended':
            print("═══ Agent W (Biały – startuje od dołu) ═══")
            d_w_raw = input("Głębokość przeszukiwania d [1-6] (Enter = 3): ").strip()
            d_w = int(d_w_raw) if d_w_raw.isdigit() else 3

            print("Heurystyka:")
            print("  1 / material   – przewaga materiałowa")
            print("  2 / positional – zaawansowanie pozycyjne")
            print("  3 / mixed      – kombinacja (materiał + pozycja + bezpieczeństwo)")
            heur_w_key = input("Wybierz heurystykę [1/2/3] (Enter = 1): ").strip() or '1'
            heur_w = HEURISTICS.get(heur_w_key, MaterialAdvantage())
            self.agent_w = AiAgent(Board.W, d_w, heur_w, use_alpha_beta)
        else:
            # W trybie basic agent W używa tych samych ustawień co B
            self.agent_w = AiAgent(Board.W, d_b, heur_b, use_alpha_beta)
        print()

        print("Stan początkowy planszy:")
        print("  Enter        – domyślny układ startowy")
        print("  własny układ – wpisz n linii po m tokenów (B/W/_). Możesz zostawić puste (Enter). Wpisz 'q' by skończyć szybciej.")
        custom = input("Czy chcesz podać własny układ? [t/N]: ").strip().lower()
        print()

        if custom == 't':
            print(f"Wpisz {n} wierszy po {m} tokenów (B W _), 'q' kończy wczytywanie:")
            board_lines = []
            while len(board_lines) < n:
                line = input(f"  wiersz {len(board_lines) + 1}/{n}: ").strip()
                if line.lower() == 'q':
                    break
                board_lines.append(line)
            self.board = Board.from_text("\n".join(board_lines), n=n, m=m)
        else:
            self.board = Board(n=n, m=m)

        print("Konfiguracja zakończona. Startujemy!\n")

    def play_game(self) -> None:
        assert self.board is not None, "Wywołaj parse_input() przed play_game()."

        current_player = Board.B  # B zaczyna
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
