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

    def dijkstra(self, stop_A_name: str, stop_B_name: str, start_datetime_str: str) -> Tuple[Optional[List], Optional[int], Optional[datetime]]:
        """
        Znajduje najkrótszą ścieżkę z A do B minimalizując wyłącznie czas.
        """
        try:
            start_dt = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M")
        except ValueError:
            print("zla data, podaj w dobrym formacie")
            return None, None, None
            
        start_time_sec = start_dt.hour * 3600 + start_dt.minute * 60 + start_dt.second
        base_date = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        
        start_stops = self.find_stop_ids_by_name(stop_A_name)
        end_stops = self.find_stop_ids_by_name(stop_B_name)
        
        if not start_stops:
            print(f"Nie znaleziono przystanku początkowego: {stop_A_name}")
            return None, None, None
        if not end_stops:
            print(f"Nie znaleziono przystanku końcowego: {stop_B_name}")
            return None, None, None

        end_stops_set = set(end_stops)
        counter = itertools.count()
        
        # (current_time, counter_id, stop_id, current_trip_id, path)
        pq = []
        for start_stop in start_stops:
            heapq.heappush(pq, (start_time_sec, next(counter), start_stop, None, []))
            
        # (stop_id, current_trip) -> min_arrival_time
        visited_times = {}
        
        while pq:
            current_time, _, u, current_trip, path = heapq.heappop(pq)
            state_key = (u, current_trip)
            
            
            if state_key in visited_times and visited_times[state_key] <= current_time:
                continue
            visited_times[state_key] = current_time
            
            if u in end_stops_set:
                return path, current_time, base_date
                
            
            for edge in self.graph.adjacency_list.get(u, []):
                day_idx = current_time // 86400
                best_dep_time, best_arr_time, best_d_offset = None, None, None
                
                
                for d_offset in range(day_idx, day_idx + 1): #1 dzien do przodu patrze
                    dep_abs = d_offset * 86400 + edge.departure_time_sec
                    if dep_abs >= current_time:
                        check_date = base_date + timedelta(days=d_offset)
                        if self.calendar.check_if_route_is_active_on_day(edge.route_id, check_date):
                            if best_dep_time is None or dep_abs < best_dep_time:
                                best_dep_time = dep_abs
                                best_arr_time = d_offset * 86400 + edge.arrival_time_sec
                                best_d_offset = d_offset
                                
                if best_dep_time is not None:
                    trip_state = (edge.trip_id, best_d_offset)
                    new_path = path + [("RIDE", edge.from_stop, edge.to_stop, edge.route_short_name, best_dep_time, best_arr_time, edge.trip_id)]
                    heapq.heappush(pq, (best_arr_time, next(counter), edge.to_stop, trip_state, new_path))

            # przejscie po peronkach
            related_stops = self.graph.get_related_stops_for_transfers(u)
            for related_stop in related_stops:
                new_path = path + [("WALK", u, related_stop)]
                heapq.heappush(pq, (current_time, next(counter), related_stop, current_trip, new_path))

        return None, None, None

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

    def print_route(self, path: List, arrival_time: int, base_date: datetime):
        """Wypisuje sformatowaną trasę przejazdu"""
        if not path:
            print("Nie znaleziono trasy dopasowanej do podanych kryteriów i daty.")
            return

        print(f"Znaleziono trasę! Najszybszy czas przyjazdu na miejsce: {self.format_time(arrival_time, base_date)}")
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
                print(f"  [WALK] {step[1]} -> {step[2]} (przejście wewnątrz stacji)")
                pass 
