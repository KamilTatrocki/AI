import heapq
import itertools
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

from .graph import Graph
from .calendar import Calendar

class RouteFinder:
    def __init__(self, graph: Graph):
        self.graph = graph
        self.calendar = Calendar()

    def find_stop_ids_by_name(self, name: str) -> List[str]:
        """Zwraca wszystkie stop_id zapisane na dany stop_name"""
        return [stop_id for stop_id, data in self.graph.nodes.items() if data['stop_name'] == name]

    def _initialize_priority_queue(self, start_stops: List[str], start_time_sec: int, criterion: str, counter: itertools.count) -> List[Tuple]:
        """Inicjalizuje kolejkę priorytetową dla przystanków początkowych"""
        pq = []
        for start_stop in start_stops:
            # Format: (primary_cost, secondary_cost, counter_id, current_time, stop_id, current_trip_id, path)
            if criterion == 't':
                heapq.heappush(pq, (start_time_sec, 0, next(counter), start_time_sec, start_stop, None, []))
            else:
                heapq.heappush(pq, (0, start_time_sec, next(counter), start_time_sec, start_stop, None, []))
        return pq

    def _is_state_dominated(self, D: dict, state_key: Tuple, cost1: int, cost2: int) -> bool:
        """Sprawdza czy stan jest zdominowany przez wcześniej znalezione optymalniejsze dojścia (Pareto frontier)"""
        if state_key not in D:
            D[state_key] = []
            
        for (c1, c2) in D[state_key]:
            if c1 <= cost1 and c2 <= cost2:
                return True
        return False

    def _update_pareto_front(self, D: dict, state_key: Tuple, cost1: int, cost2: int):
        """Aktualizuje front Pareto dla danego stanu o nowe, nie zdominowane rozwiązanie"""
        filtered = [(c1, c2) for (c1, c2) in D[state_key] if not (cost1 <= c1 and cost2 <= c2)]
        filtered.append((cost1, cost2))
        D[state_key] = filtered

    def _process_ride_edges(self,
                            u: str,
                            current_time: int,
                            transfers: int,
                            current_trip,
                            path: List,
                            base_date: datetime,
                            criterion: str,
                            counter: itertools.count,
                            pq: List):
        """Przetwarza krawędzie reprezentujące bezpośrednie przejazdy pojazdem (RIDE)"""
        for edge in self.graph.adjacency_list.get(u, []):
            day_idx = current_time // 86400
            best_dep_time, best_arr_time, best_d_offset = None, None, None
            
            # Sprawdź dni od dzisiaj do max 4 dni w przód
            for d_offset in range(day_idx, day_idx + 4):
                dep_abs = d_offset * 86400 + edge.departure_time_sec
                if dep_abs >= current_time:
                    check_date = base_date + timedelta(days=d_offset)
                    if self.calendar.check_if_route_is_active_on_day(edge.route_id, check_date):
                        if best_dep_time is None or dep_abs < best_dep_time:
                            best_dep_time = dep_abs
                            # Dla tripów, które lądują po północy, GTFS podaje czasy > 24h
                            best_arr_time = d_offset * 86400 + edge.arrival_time_sec
                            best_d_offset = d_offset
                            
            if best_dep_time is not None:
                trip_state = (edge.trip_id, best_d_offset)
                is_transfer = (current_trip is not None) and (current_trip != trip_state)
                new_transfers = transfers + (1 if is_transfer else 0)
                new_path = path + [("RIDE", edge.from_stop, edge.to_stop, edge.route_short_name, best_dep_time, best_arr_time, edge.trip_id)]
                
                if criterion == 't':
                    heapq.heappush(pq, (best_arr_time, new_transfers, next(counter), best_arr_time, edge.to_stop, trip_state, new_path))
                else:
                    heapq.heappush(pq, (new_transfers, best_arr_time, next(counter), best_arr_time, edge.to_stop, trip_state, new_path))

    def _process_walk_edges(self,
                            u: str,
                            current_time: int,
                            transfers: int,
                            current_trip,
                            path: List,
                            criterion: str,
                            counter: itertools.count,
                            pq: List):
        """Przetwarza krawędzie reprezentujące przejścia piesze wewnątrz obszaru tego samego przystanku (WALK)"""
        related_stops = self.graph.get_related_stops_for_transfers(u)
        for related_stop in related_stops:
            new_path = path + [("WALK", u, related_stop)]
            if criterion == 't':
                heapq.heappush(pq, (current_time, transfers, next(counter), current_time, related_stop, current_trip, new_path))
            else:
                heapq.heappush(pq, (transfers, current_time, next(counter), current_time, related_stop, current_trip, new_path))

    def dijkstra(self, stop_A_name: str, stop_B_name: str, start_datetime_str: str, criterion: str = 't') -> Tuple[Optional[List], Optional[int], Optional[int], Optional[datetime]]:

        try:
            start_dt = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M")
        except ValueError:
            print("zla data, podaj w dobrym formacie")
            return None, None, None, None
            
        start_time_sec = start_dt.hour * 3600 + start_dt.minute * 60 + start_dt.second
        base_date = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        
        start_stops = self.find_stop_ids_by_name(stop_A_name)
        end_stops = self.find_stop_ids_by_name(stop_B_name)
        
        if not start_stops:
            print(f"Nie znaleziono przystanku początkowego: {stop_A_name}")
            return None, None, None, None
        if not end_stops:
            print(f"Nie znaleziono przystanku końcowego: {stop_B_name}")
            return None, None, None, None

        end_stops_set = set(end_stops)
        counter = itertools.count()
        
        pq = self._initialize_priority_queue(start_stops, start_time_sec, criterion, counter)
        D = {}
        
        while pq:
            cost1, cost2, _, current_time, u, current_trip, path = heapq.heappop(pq)
            transfers = cost2 if criterion == 't' else cost1
            state_key = (u, current_trip)
            
            if self._is_state_dominated(D, state_key, cost1, cost2):
                continue
                
            self._update_pareto_front(D, state_key, cost1, cost2)
            
            if u in end_stops_set:
                return path, current_time, transfers, base_date
                
            self._process_ride_edges(u, current_time, transfers, current_trip, path, base_date, criterion, counter, pq)
            self._process_walk_edges(u, current_time, transfers, current_trip, path, criterion, counter, pq)

        return None, None, None, None

    @staticmethod
    def format_time(seconds: int, base_date: datetime = None) -> str:
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

    def print_route(self, path: List, arrival_time: int, transfers: int, base_date: datetime):
        """Wypisuje sformatowaną trasę przejazdu"""
        if not path:
            print("Nie znaleziono trasy dopasowanej do podanych kryteriów.")
            return

        print(f"Znaleziono trasę! Czas przyjazdu na miejsce: {self.format_time(arrival_time, base_date)}, Liczba przesiadek: {transfers}")
        print("Trasa:")
        for step in path:
            if step[0] == "RIDE":
                _, f, t, route, dep, arr, trip = step
                dep_str = self.format_time(dep, base_date)
                arr_str = self.format_time(arr, base_date)
                stop_A = self.graph.nodes[f]['stop_name']
                stop_B = self.graph.nodes[t]['stop_name']
                print(f"  [{dep_str} - {arr_str}] {stop_A} -> {stop_B} [Linia {route}]")
            elif step[0] == "WALK":
                # Przejścia wewnątrz peronów na stacji
                pass 
