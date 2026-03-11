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
import heapq
import itertools
from datetime import datetime

# Dadaj główny folder projektu do sys.path żeby importy z utils działały poprawnie
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.graph import Graph
from utils.calendar import Calendar
from data_consumer import main_consumer


def find_stop_ids_by_name(graph: Graph, name: str):
    """Zwraca wszystkie stop_id zapisane na dany stop_name"""
    return [stop_id for stop_id, data in graph.nodes.items() if data['stop_name'] == name]


def dijkstra(graph: Graph, stop_A_name: str, stop_B_name: str, start_datetime_str: str, criterion: str = 't'):
    """
    Znajduje najkrótszą ścieżkę (czasowo lub przesiadkowo) z A do B.
    criterion: 't' (czas przejazdu), 'p' (liczba przesiadek)
    """
    try:
        start_dt = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M")
    except ValueError:
        print("Nieprawidłowy format daty/czasu. Oczekiwano: RRRR-MM-DD HH:MM")
        return None, None, None
        
    start_time_sec = start_dt.hour * 3600 + start_dt.minute * 60 + start_dt.second
    # Używamy start_dt do sprawdzania kalendarza dla tego dnia
    day = start_dt

    calendar = Calendar()
    
    start_stops = find_stop_ids_by_name(graph, stop_A_name)
    end_stops = find_stop_ids_by_name(graph, stop_B_name)
    
    if not start_stops:
        print(f"Nie znaleziono przystanku początkowego: {stop_A_name}")
        return None, None, None
    if not end_stops:
        print(f"Nie znaleziono przystanku końcowego: {stop_B_name}")
        return None, None, None

    end_stops_set = set(end_stops)

    # Kolejka priorytetowa dla algorytmu Dijkstry
    pq = []
    
    # Przechowujemy zbiór dominujących stanów (dla optymalizacji wielokryterialnej jeśli minimalizujemy przesiadki)
    # mapowanie: state_key -> [(koszt1, koszt2), ...]
    # gdzie state_key = (aktualny_przystanek, aktualny_trip_id)
    D = {}
    
    # Generowanie unikalnego ID żeby radzić sobie z konfliktami typów w samej kolejce
    counter = itertools.count()
    
    for start_stop in start_stops:
        # Tuple: (cost1, cost2, id, current_time, stop_id, current_trip_id, path)
        if criterion == 't':
            # Minimalizacja czasu (cost1 = czas)
            heapq.heappush(pq, (start_time_sec, 0, next(counter), start_time_sec, start_stop, None, []))
        else:
            # Minimalizacja przesiadek (cost1 = przesiadki)
            heapq.heappush(pq, (0, start_time_sec, next(counter), start_time_sec, start_stop, None, []))
            
    while pq:
        cost1, cost2, _, current_time, u, current_trip, path = heapq.heappop(pq)
        
        transfers = cost2 if criterion == 't' else cost1
        
        state_key = (u, current_trip)
        if state_key not in D:
            D[state_key] = []
            
        # Sprawdzenie czy osiągnęliśmy ten stan lepszą ścieżką wektorowo
        is_dominated = False
        for (c1, c2) in D[state_key]:
            if c1 <= cost1 and c2 <= cost2:
                is_dominated = True
                break
                
        if is_dominated:
            continue
            
        filtered = [(c1, c2) for (c1, c2) in D[state_key] if not (cost1 <= c1 and cost2 <= c2)]
        filtered.append((cost1, cost2))
        D[state_key] = filtered
        
        if u in end_stops_set:
            return path, current_time, transfers
            
        # 1. Trasy z aktualnego przystanku (krawędzie skierowane)
        active_edges = graph.get_active_edges_for_stop(u, day, calendar)
        for edge in active_edges:
            # Sprawdzamy, czy połączenie z danego peronu odjeżdża PO naszym aktualnym czasie
            if edge.departure_time_sec >= current_time:
                # Obliczanie ilości przesiadek
                is_transfer = (current_trip is not None) and (current_trip != edge.trip_id)
                new_transfers = transfers + (1 if is_transfer else 0)
                new_time = edge.arrival_time_sec
                
                new_path = path + [("RIDE", edge.from_stop, edge.to_stop, edge.route_short_name, edge.departure_time_sec, edge.arrival_time_sec, edge.trip_id)]
                
                if criterion == 't':
                    heapq.heappush(pq, (new_time, new_transfers, next(counter), new_time, edge.to_stop, edge.trip_id, new_path))
                else:
                    heapq.heappush(pq, (new_transfers, new_time, next(counter), new_time, edge.to_stop, edge.trip_id, new_path))
                    
        # 2. Przejścia piesze na tej samej stacji w poszukiwaniu alternatywnych peronów (transfers)
        related_stops = graph.get_related_stops_for_transfers(u)
        for related_stop in related_stops:
            # WAŻNE: nie zmieniamy current_trip na None. 
            # Dzięki temu, wsiadając do nowego pociągu na sąsiednim peronie od razu wyłapiemy zmianę trip_id jako przesiadkę z pociągu, z którym przyjechaliśmy.
            new_path = path + [("WALK", u, related_stop)]
            if criterion == 't':
                heapq.heappush(pq, (current_time, transfers, next(counter), current_time, related_stop, current_trip, new_path))
            else:
                heapq.heappush(pq, (transfers, current_time, next(counter), current_time, related_stop, current_trip, new_path))

    return None, None, None


def format_time(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    # Modulo 24 on hours just in case of times like 25:10
    days = h // 24
    h = h % 24
    time_str = f"{h:02d}:{m:02d}:{s:02d}"
    if days > 0:
        time_str += f" (+{days} dni)"
    return time_str


if __name__ == "__main__":
    print("Ładowanie danych...")
    main_consumer.load_data()
    print("Budowanie grafu połączeń...")
    graph = Graph(main_consumer)
    
    # ==== DANE WEJŚCIOWE APLIKACJI ====
    A = "Sobótka"   # (a) przystanek początkowy
    B = "Zgorzelec"          # (b) przystanek końcowy
    criterion = 't'        # (c) 't' - min czas przejazdu, 'p' - min liczba przesiadek
    start_time_str = "2026-03-11 21:00" # (d) czas rozpoczęcia podróży
    # ==================================
    
    print(f"Szukanie trasy z '{A}' do '{B}' (Kryterium: '{criterion}', Start: {start_time_str})")
    print("-" * 50)
    
    path, arrival_time, transfers = dijkstra(graph, A, B, start_time_str, criterion)
    
    if path:
        print(f"Znaleziono trasę! Czas przyjazdu na miejsce: {format_time(arrival_time)}, Liczba przesiadek: {transfers}")
        print("Trasa:")
        for step in path:
            if step[0] == "RIDE":
                _, f, t, route, dep, arr, trip = step
                print(f"  [{format_time(dep)} - {format_time(arr)}] {graph.nodes[f]['stop_name']} -> {graph.nodes[t]['stop_name']} [Linia {route}]")
            elif step[0] == "WALK":
                # Debugging - przejścia wewnątrz peronów na stacji
                pass 
    else:
        print("Nie znaleziono trasy dopasowanej do podanych kryteriów i daty.")