"""
Wykorzystując dostarczony zbiór danych GTFS od Kolei Dolnośląskich, zaimplementuj algorytm wy-
szukiwania najkrótszych ścieżek między podanymi przystankami A i B. Jako funkcję kosztu zastosuj (w
zależności od decyzji użytkownika) czas przejazdu z A do B lub liczbę przesiadek.
Aplikacja powinna przyjmować dane wejściowe w postaci 4 zmiennych:
(a) przystanek początkowy A
(b) przystanek końcowy B
(c) kryterium optymalizacji: warto ́s ́c t oznacza minimalizacj  ̨e czasu przejazdu, warto ́s ́c p oznacza
minimalizacj  ̨e liczby przesiadek (to zrób jako parametr ustawiany w kodzie, domyślnie ustaw czas przejazdu)
(d) czas rozpocz ̨ecia podró ̇zy ( godzina oraz data np 13:37 )
"""
import sys
import os

# Dadaj główny folder projektu do sys.path żeby importy z utils działały poprawnie
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.graph import Graph
from utils.route_finder import RouteFinder
from data_consumer import main_consumer


if __name__ == "__main__":
    """
 uv run tasks/task_1_djikstra.py
    """
    
    main_consumer.load_data()
    
    graph = Graph(main_consumer)
    
    # inputy
    A = "Sobótka"   
    B = "Zgorzelec"
    criterion = 'p'        #  't'   czas przejazdu 'p'  liczba przesiadek
    start_time_str = "2026-03-11 21:00" # czas rozpoczęcia podróży
    
    print(f"Szukanie trasy z '{A}' do '{B}' (Kryterium: '{criterion}', Start: {start_time_str})")
    print("-" * 50)
    
    route_finder = RouteFinder(graph)
    path, arrival_time, transfers, base_date = route_finder.dijkstra(A, B, start_time_str, criterion)
    route_finder.print_route(path, arrival_time, transfers, base_date)