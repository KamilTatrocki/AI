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
from datetime import datetime, timedelta

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
        return None, None, None, None
        
    start_time_sec = start_dt.hour * 3600 + start_dt.minute * 60 + start_dt.second
    base_date = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)

    calendar = Calendar()
    
    start_stops = find_stop_ids_by_name(graph, stop_A_name)
    end_stops = find_stop_ids_by_name(graph, stop_B_name)
    
    if not start_stops:
        print(f"Nie znaleziono przystanku początkowego: {stop_A_name}")
        return None, None, None, None
    if not end_stops:
        print(f"Nie znaleziono przystanku końcowego: {stop_B_name}")
        return None, None, None, None

    end_stops_set = set(end_stops)

    # Kolejka priorytetowa dla algorytmu Dijkstry
    pq = []
    
    # Przechowujemy zbiór dominujących stanów (dla optymalizacji wielokryterialnej jeśli minimalizujemy przesiadki)
    # mapowanie: state_key -> [(koszt1, koszt2), ...]
    # gdzie state_key = (aktualny_przystanek, aktualny_trip_id_i_dzień)
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
            return path, current_time, transfers, base_date
            
        # 1. Trasy z aktualnego przystanku (krawędzie skierowane)
        for edge in graph.adjacency_list.get(u, []):
            day_idx = current_time // 86400
            
            best_dep_time = None
            best_arr_time = None
            best_d_offset = None
            
            # Sprawdź dni od dzisiaj do max 4 dni w przód (zabezpieczenie przed weekendami i czekaniem do rana)
            for d_offset in range(day_idx, day_idx + 4):
                dep_abs = d_offset * 86400 + edge.departure_time_sec
                if dep_abs >= current_time:
                    check_date = base_date + timedelta(days=d_offset)
                    if calendar.check_if_route_is_active_on_day(edge.route_id, check_date):
                        if best_dep_time is None or dep_abs < best_dep_time:
                            best_dep_time = dep_abs
                            # Dla tripów, które lądują po północy, GTFS podaje czasy > 24h, 
                            # więc arrival_time_sec to już obejmie automatycznie.
                            best_arr_time = d_offset * 86400 + edge.arrival_time_sec
                            best_d_offset = d_offset
                            
            if best_dep_time is not None:
                # trip identyfikujemy po trip_id ORAZ offsecie dnia jako unikalny stan
                trip_state = (edge.trip_id, best_d_offset)
                is_transfer = (current_trip is not None) and (current_trip != trip_state)
                new_transfers = transfers + (1 if is_transfer else 0)
                new_time = best_arr_time
                
                new_path = path + [("RIDE", edge.from_stop, edge.to_stop, edge.route_short_name, best_dep_time, best_arr_time, edge.trip_id)]
                
                if criterion == 't':
                    heapq.heappush(pq, (new_time, new_transfers, next(counter), new_time, edge.to_stop, trip_state, new_path))
                else:
                    heapq.heappush(pq, (new_transfers, new_time, next(counter), new_time, edge.to_stop, trip_state, new_path))
                    
        # 2. Przejścia piesze na tej samej stacji w poszukiwaniu alternatywnych peronów (transfers)
        related_stops = graph.get_related_stops_for_transfers(u)
        for related_stop in related_stops:
            # WAŻNE: nie zmieniamy current_trip na None. 
            # Dzięki temu, wsiadając do nowego pociągu na sąsiednim peronie od razu wyłapiemy zmianę jako przesiadkę.
            new_path = path + [("WALK", u, related_stop)]
            if criterion == 't':
                heapq.heappush(pq, (current_time, transfers, next(counter), current_time, related_stop, current_trip, new_path))
            else:
                heapq.heappush(pq, (transfers, current_time, next(counter), current_time, related_stop, current_trip, new_path))

    return None, None, None, None


def format_time(seconds, base_date: datetime = None):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    days = h // 24
    h = h % 24
    
    time_str = f"{h:02d}:{m:02d}:{s:02d}"
    if base_date and days > 0:
        actual_date = base_date + timedelta(days=days)
        time_str = f"{actual_date.strftime('%Y-%m-%d')} " + time_str
    elif days > 0:
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
    
    path, arrival_time, transfers, base_date = dijkstra(graph, A, B, start_time_str, criterion)
    
    if path:
        print(f"Znaleziono trasę! Czas przyjazdu na miejsce: {format_time(arrival_time, base_date)}, Liczba przesiadek: {transfers}")
        print("Trasa:")
        for step in path:
            if step[0] == "RIDE":
                _, f, t, route, dep, arr, trip = step
                print(f"  [{format_time(dep, base_date)} - {format_time(arr, base_date)}] {graph.nodes[f]['stop_name']} -> {graph.nodes[t]['stop_name']} [Linia {route}]")
            elif step[0] == "WALK":
                # Debugging - przejścia wewnątrz peronów na stacji
                pass 
    else:
        print("Nie znaleziono trasy dopasowanej do podanych kryteriów i daty.")