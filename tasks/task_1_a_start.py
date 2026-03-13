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
    
    criteria = "t" # t - czas lub p - przesiadki
    start_time_str = "2026-03-15 14:00"

    A = "Wrocław Główny"   
    B = "Sobótka"

    #inne
    # A= "Forst (Lausitz)"
    # B= "Jerzmanki"
    # start_time_str = "2026-03-08 5:00"

    
   
    
    route_finder = RouteFinder(graph)
    
    print(f"Rozpoczęcie szukania A*: {A} -> {B} (Kryterium: {criteria}, Start: {start_time_str})")
    
    start_eval_time = time.time()
    path, arrival_time, base_date = route_finder.a_star(A, B, start_time_str, criterion=criteria)
    eval_time = time.time() - start_eval_time
    
    if path:
        route_finder.print_route(path, arrival_time, base_date)
        
        # standard error
        if criteria == 't':
            start_dt = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M")
            start_sec = start_dt.hour * 3600 + start_dt.minute * 60 + start_dt.second
            travel_time = arrival_time - start_sec
            print(f"\nKryterium (czas podróży w sek.): {travel_time}", file=sys.stderr)
        else:
            transfers = 0
            last_trip = None
            for step in path:
                if step[0] == "RIDE":
                    if last_trip is not None and last_trip != step[6]:
                        transfers += 1
                    last_trip = step[6]
            print(f"\nKryterium (przesiadki): {transfers}", file=sys.stderr)
            
        print(f"Czas obliczeń: {eval_time:.4f} s", file=sys.stderr)
    else:
        print("Nie znaleziono trasy.")