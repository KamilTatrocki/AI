import heapq
import itertools
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from collections import defaultdict
from utils.graph import Graph
from utils.calendar import Calendar

class RouteFinder:
    def __init__(self, graph: Graph):
        self.graph = graph
        self.calendar = Calendar()

    def find_stop_ids_by_name(self, name: str) -> List[str]:
        """Zwraca wszystkie stop_id zapisane na dany stop_name"""
        return [stop_id for stop_id, data in self.graph.nodes.items() if data['stop_name'] == name]

    def a_star(self, stop_A_name: str, stop_B_name: str, start_datetime_str: str, criterion: str = 't', upgraded_heuristic: bool = False) -> Tuple[Optional[List], Optional[int], Optional[datetime]]:
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
        
        # Priority queue z elementami: (f_score, current_cost, current_time, counter_id, stop_id, current_trip, path)
        pq = []
        for start_stop in start_stops:
            h = self._heuristic(start_stop, end_stops_set, criterion, upgraded_heuristic)
            # Na start oba koszty to 0
            heapq.heappush(pq, (h, 0, start_time_sec, next(counter), start_stop, None, []))
            
        # visited states: state_key -> min_cost
        visited_states = {}
        
        while pq:
            f, current_cost, current_time, _, u, current_trip, path = heapq.heappop(pq)
            state_key = (u, current_trip)
            
            if state_key in visited_states and visited_states[state_key] <= current_cost:
                continue
            visited_states[state_key] = current_cost
            
            if u in end_stops_set:
                return path, current_time, base_date
                
            for edge in self.graph.adjacency_list.get(u, []):
                day_idx = current_time // 86400
                best_dep_time, best_arr_time, best_d_offset = None, None, None
                
                for d_offset in range(day_idx, day_idx + 1):
                    dep_abs = d_offset * 86400 + edge.departure_time_sec
                    if dep_abs >= current_time:
                        check_date = base_date + timedelta(days=d_offset)
                        if self.calendar.check_if_service_is_active_on_day(edge.service_id, check_date):
                            if best_dep_time is None or dep_abs < best_dep_time:
                                best_dep_time = dep_abs
                                best_arr_time = d_offset * 86400 + edge.arrival_time_sec
                                best_d_offset = d_offset
                                
                if best_dep_time is not None:
                    trip_state = (edge.trip_id, best_d_offset)
                    
                    if criterion == 't':
                        new_cost = best_arr_time - start_time_sec
                    else:
                        is_transfer = 1 if (current_trip is not None and current_trip[0] != edge.trip_id) else 0
                        new_cost = current_cost + is_transfer
                        
                    h_val = self._heuristic(edge.to_stop, end_stops_set, criterion, upgraded_heuristic)
                    new_f = new_cost + h_val
                    
                    new_path = path + [("RIDE", edge.from_stop, edge.to_stop, edge.route_short_name, best_dep_time, best_arr_time, edge.trip_id)]
                    heapq.heappush(pq, (new_f, new_cost, best_arr_time, next(counter), edge.to_stop, trip_state, new_path))

            # przejścia piesze po peronach
            related_stops = self.graph.get_related_stops_for_transfers(u)
            for related_stop in related_stops:

                new_path = path + [("WALK", u, related_stop)]
                h_val = self._heuristic(related_stop, end_stops_set, criterion, upgraded_heuristic)
                new_f = current_cost + h_val
                
                heapq.heappush(pq, (new_f, current_cost, current_time, next(counter), related_stop, current_trip, new_path))

        return None, None, None

    def evaluate_a_star_route(self, stop_A_name: str, stop_B_name: str, start_datetime_str: str, criterion: str = 't', upgraded_heuristic: bool = True) -> Tuple[Optional[int], Optional[List], Optional[int], Optional[datetime]]:
        path, arrival_time, base_date = self.a_star(stop_A_name, stop_B_name, start_datetime_str, criterion, upgraded_heuristic)
        
        if not path:
            return None, None, None, None
            
        if criterion == 't':
            start_dt = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M")
            start_sec = start_dt.hour * 3600 + start_dt.minute * 60 + start_dt.second
            cost = arrival_time - start_sec
        else:
            cost = 0
            last_trip = None
            for step in path:
                if step[0] == "RIDE":
                    if last_trip is not None and last_trip != step[6]:
                        cost += 1
                    last_trip = step[6]
                    
        return cost, path, arrival_time, base_date

    def dijkstra(self, stop_A_name: str, stop_B_name: str, start_datetime_str: str) -> Tuple[Optional[List], Optional[int], Optional[datetime]]:
        """
        minimalizuje tylko czas
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
                        if self.calendar.check_if_service_is_active_on_day(edge.service_id, check_date):
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

    def _heuristic(self, curr_stop: str, end_stops_set: set, criterion: str, upgraded_heuristic: bool = False) -> float:
        if criterion == 'p':
            if upgraded_heuristic:
                return self._heuristic_p_upgraded(curr_stop, end_stops_set)
            return self._heuristic_p(curr_stop, end_stops_set)
        return self._heuristic_t(curr_stop, end_stops_set)

    def _build_routes_per_stop(self):
        if hasattr(self, '_routes_per_stop'):
            return
        self._routes_per_stop = {}
        for u, edges in self.graph.adjacency_list.items():
            if u not in self._routes_per_stop:
                self._routes_per_stop[u] = set()
            for e in edges:
                self._routes_per_stop[u].add(e.route_id)
                #gdyby byla stacja do ktorej mozna tylko przyjechac ale nie mozna z niej odjechac to 3 linie ponizej bylyby potrzebne
                # if e.to_stop not in self._routes_per_stop:
                #     self._routes_per_stop[e.to_stop] = set()
                # self._routes_per_stop[e.to_stop].add(e.route_id)

    def _heuristic_p(self, curr_stop: str, end_stops_set: set) -> float:
        if curr_stop in end_stops_set:
            return 0.0
            
        self._build_routes_per_stop()
        curr_routes = self._routes_per_stop.get(curr_stop, set())
        
        for end_stop in end_stops_set:
            if curr_routes.intersection(self._routes_per_stop.get(end_stop, set())):
                return 0.0
                
        return 1.0

    def _build_route_graph(self):
        if hasattr(self, '_route_neighbors'):
            return
            
        self._build_routes_per_stop()
        
        self._station_routes = defaultdict(set)
        #cel - _station_routes = przystanki ktore sa z max 1 przesiadka
        for stop_id, routes in self._routes_per_stop.items():
            self._station_routes[stop_id].update(routes)
            for related in self.graph.get_related_stops_for_transfers(stop_id):
                self._station_routes[stop_id].update(self._routes_per_stop.get(related, set()))
                
        self._route_neighbors = defaultdict(set)
        for stop_id, routes in self._station_routes.items():
            for r in routes:
                self._route_neighbors[r].update(routes)

    def _heuristic_p_upgraded(self, curr_stop: str, end_stops_set: set) -> float:
        if curr_stop in end_stops_set:
            return 0.0
            
        self._build_route_graph()
        
        curr_routes = self._station_routes.get(curr_stop, set())
        if not curr_routes:
            return 2.0
            
        cache_key = frozenset(end_stops_set)
        if hasattr(self, '_end_routes_cache') and cache_key in self._end_routes_cache:
            end_routes = self._end_routes_cache[cache_key]
            end_neighbors = self._end_neighbors_cache[cache_key]
        else:
            if not hasattr(self, '_end_routes_cache'):
                self._end_routes_cache = {}
                self._end_neighbors_cache = {}
                
            end_routes = set()
            for end_stop in end_stops_set:
                end_routes.update(self._station_routes.get(end_stop, set()))
            self._end_routes_cache[cache_key] = end_routes
            
            end_neighbors = set()
            for r in end_routes:
                end_neighbors.update(self._route_neighbors.get(r, set()))
            self._end_neighbors_cache[cache_key] = end_neighbors
            
        if curr_routes.intersection(end_routes):
            return 0.0
            
        if curr_routes.intersection(end_neighbors):
            return 1.0
            
        return 2.0

    def _heuristic_t(self, curr_stop: str, end_stops_set: set) -> float:
        min_dist = float('inf')
        lat1 = self.graph.nodes[curr_stop]['stop_lat']
        lon1 = self.graph.nodes[curr_stop]['stop_lon']
        
        import math
        for end_stop in end_stops_set:
            lat2 = self.graph.nodes[end_stop]['stop_lat']
            lon2 = self.graph.nodes[end_stop]['stop_lon']
            
            earth_radius = 6371000
            phi1 = math.radians(lat1)
            phi2 = math.radians(lat2)
            delta_phi = math.radians(lat2 - lat1)
            delta_lambda = math.radians(lon2 - lon1)
            
            mean_phi = (phi1 + phi2) / 2
            
            x = delta_lambda * math.cos(mean_phi)
            y = delta_phi
            
            dist = math.sqrt(x**2 + y**2) * earth_radius
            if dist < min_dist:
                min_dist = dist
                
        if min_dist == float('inf'):
            return 0.0
            
        # 50 m/s ~ 180 km/h - optymistyczna bo pociagi jezdza do 160 (model kd sprinter)
        return min_dist / 50.0

  

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
        prev_route = None
        for step in path:
            if step[0] == "RIDE":
                _, f, t, route, dep, arr, trip = step
                
                if prev_route is not None and prev_route != route:
                    stop_A = self.graph.nodes[f]['stop_name']
                    print(f"  --> [PRZESIADKA] Zmiana linii na stacji {stop_A} z {prev_route} na {route} <--")
                    
                dep_str = self.format_time(dep, base_date)
                arr_str = self.format_time(arr, base_date)
                stop_A = self.graph.nodes[f]['stop_name']
                stop_B = self.graph.nodes[t]['stop_name']
                print(f"  [{dep_str} - {arr_str}] {stop_A} -> {stop_B} [Linia {route}]")
                
                prev_route = route
            elif step[0] == "WALK":
                print(f"  [WALK + PRZESIADKA] {step[1]} -> {step[2]} (przejście wewnątrz stacji)")
                prev_route = None
