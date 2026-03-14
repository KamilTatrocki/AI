"""
1. Wykorzystuj ˛ac dostarczony zbiór danych GTFS od Kolei Dolno´sl ˛askich, zaimplementuj algorytm wy
szukiwania najkrótszych ´scie˙zek mi˛edzy podanymi przystankami A i B. Jako funkcj˛e kosztu zastosuj (w
zale˙zno´sci od decyzji u˙zytkownika) czas przejazdu z A do B lub liczb˛e przesiadek.
Aplikacja powinna przyjmowa´c dane wej´sciowe w postaci 4 zmiennych:
(a) przystanek pocz ˛atkowy A
(b) przystanek ko´ncowy B
(c) kryterium optymalizacji: warto´s´c t oznacza minimalizacj˛e czasu przejazdu, warto´s´c p oznacza
minimalizacj˛e liczby przesiadek
(d) czas rozpocz˛ecia podró˙zy
Rozwi ˛azanie powinno wypisywa´c na standardowe wyj´scie w kolejnych wierszach szczegółowe infor
macje o ´scie˙zce, w tym przystanek pocz ˛atkowy, przystanek ko´ncowy, nazw˛e wykorzystanej linii, czas
rozpocz˛ecia, czas zako´nczenia, a na standardowe wyj´scie bł˛edów warto´s´c minimalizowanego kryte
rium oraz czas potrzebny do obliczenia najkrótszej ´scie˙zki.
Punktacja:
(b) wyszukiwanie najkrótszej ´scie˙zki z A do B za pomoc ˛aalgorytmu A*, na podstawie kryterium czasu
przejazdu (25 punktów).
(c) wyszukiwanie najkrótszej ´scie˙zki z A do B za pomoc ˛aalgorytmu A*, na podstawie kryterium liczby
przesiadek (25 punktów).
"""

import sys
import os
import time
from datetime import datetime


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.graph import Graph
from utils.route_finder import RouteFinder
from data_consumer import main_consumer

if __name__ == "__main__":
    """
    uv run tasks/task_1_a_start.py
    """
    main_consumer.load_data()
    graph = Graph(main_consumer)
    
    criteria = "p" # t - czas lub p - przesiadki
    start_time_str = "2026-03-15 14:00"

    # B = "Zduny"   
    # A = "Lubawka"

    #inne
    A= "Forst (Lausitz)"
    B= "Jerzmanki"
    start_time_str = "2026-03-08 8:00"

    # start_time_str = "2026-03-11 13:00"

    # A = "Sobótka"   
    # B = "Smolec"
    # A = "Legnica"   
    # B = "Zgorzelec" 
    # start_time_str = "2026-03-15 21:00" # czas rozpoczęcia podróży
    # A = "Sobótka"   
    # B = "Zgorzelec"
    # start_time_str = "2026-03-15 21:00" # czas rozpoczęcia podróży
    
    route_finder = RouteFinder(graph)
    
    print(f"Rozpoczęcie szukania A*: {A} -> {B} (Kryterium: {criteria}, Start: {start_time_str})")
    
    start_eval_time = time.time()
    cost, path, arrival_time, base_date = route_finder.evaluate_a_star_route(A, B, start_time_str, criteria, upgraded_heuristic=False)
    eval_time = time.time() - start_eval_time
    
    if path:
        route_finder.print_route(path, arrival_time, base_date)
        
        # standard error
        if criteria == 't':
            print(f"\nKryterium (czas podróży w sek.): {cost}", file=sys.stderr)
        else:
            print(f"\nKryterium (przesiadki): {cost}", file=sys.stderr)
            
        print(f"Czas obliczeń: {eval_time:.4f} s", file=sys.stderr)
    else:
        print("Nie znaleziono trasy.")

