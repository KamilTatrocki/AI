import sys
import time
from datetime import datetime, timedelta
from typing import List, Tuple
from itertools import combinations
import copy
from data_consumer import main_consumer
from utils.graph import Graph
from utils.route_finder import RouteFinder


class TabuSearch:
    def __init__(self, start_stop: str, intermediate_stops: str, criteria: str, start_time_str: str):
        self.start_stop = start_stop
        # Split and clean the list of stops L
        self.stops_to_visit = [stop.strip() for stop in intermediate_stops.split(';') if stop.strip()]
        self.criteria = criteria
        self.start_time_str = start_time_str
        
        main_consumer.load_data()
        self.graph = Graph(main_consumer)
        self.route_finder = RouteFinder(self.graph)
        
        # Cache for evaluated legs: (from_stop, to_stop, start_time_sec) -> (cost, arrival_time_sec, path, base_date)
        # To avoid recomputing A* for identical legs
        self.leg_cache = {}
        
        # Tabu search parameters
        self.max_iterations = 20 # Maximum iterations without improvement or overall
        self.tabu_list = [] # Store tabu moves as (stop_A, stop_B)
        self.tabu_tenure = 10 # Number of iterations a move stays tabu

    def evaluate_leg(self, stop_A: str, stop_B: str, current_time_str: str) -> Tuple:
        cache_key = (stop_A, stop_B, current_time_str)
        if cache_key in self.leg_cache:
            return self.leg_cache[cache_key]

        cost, path, arrival_time, base_date = self.route_finder.evaluate_a_star_route(
            stop_A, stop_B, current_time_str, self.criteria, upgraded_heuristic=False
        )
        
        if path is not None:
            self.leg_cache[cache_key] = (cost, arrival_time, path, base_date)
            return cost, arrival_time, path, base_date
        return float('inf'), None, None, None
        
    def _format_datetime(self, time_sec: int, base_date: datetime) -> str:
        days = time_sec // 86400
        seconds_within_day = time_sec % 86400
        h = seconds_within_day // 3600
        m = (seconds_within_day % 3600) // 60
        s = seconds_within_day % 60
        
        actual_date = base_date + timedelta(days=days)
        time_str = f"{actual_date.strftime('%Y-%m-%d')} {h:02d}:{m:02d}:{s:02d}"
        return time_str

    def evaluate_permutation(self, permutation: List[str]) -> Tuple[float, List]:
        """
        Evaluates the full sequence: start_stop -> perm[0] -> ... -> perm[-1] -> start_stop
        Returns total cost, and the combined paths/arrival data if valid, or float('inf') if invalid.
        """
        full_sequence = [self.start_stop] + permutation + [self.start_stop]
        
        current_time_str = self.start_time_str
        full_path = []
        
        for i in range(len(full_sequence) - 1):
            from_stop = full_sequence[i]
            to_stop = full_sequence[i+1]
            
            cost, arrival_time, path, base_date = self.evaluate_leg(from_stop, to_stop, current_time_str)
            
            if cost == float('inf') or path is None:
                # Disconnected leg
                return float('inf'), None
                
            full_path.append((from_stop, to_stop, path, arrival_time, base_date))
            
            # Update current_time_str for the next leg based on arrival time
            current_time_str_full = self._format_datetime(arrival_time, base_date)
            # convert to user format "%Y-%m-%d %H:%M"
            dt_obj = datetime.strptime(current_time_str_full, "%Y-%m-%d %H:%M:%S")
            current_time_str = dt_obj.strftime("%Y-%m-%d %H:%M")
            
        total_cost = 0
        if self.criteria == 'p':
            last_route = None
            for leg in full_path:
                path = leg[2]
                for step in path:
                    if step[0] == "RIDE":
                        # step[3] is route_short_name — same as print_route uses
                        if last_route is not None and last_route != step[3]:
                            total_cost += 1
                        last_route = step[3]
                    elif step[0] == "WALK":
                        # WALK is always a przesiadka (print_route shows [WALK + PRZESIADKA])
                        # Only count if we were already riding something
                        if last_route is not None:
                            total_cost += 1
                        last_route = None  # reset: next RIDE is a fresh boarding
        else:
            final_leg = full_path[-1]
            final_arrival_time = final_leg[3]
            final_base_date = final_leg[4]
            final_arrival_str = self._format_datetime(final_arrival_time, final_base_date)
            final_dt = datetime.strptime(final_arrival_str, "%Y-%m-%d %H:%M:%S")
            start_dt = datetime.strptime(self.start_time_str, "%Y-%m-%d %H:%M")
            total_cost = (final_dt - start_dt).total_seconds()
            
        return total_cost, full_path

    def get_neighbors(self, permutation: List[str]) -> List[Tuple[List[str], Tuple[str, str]]]:
        """
        Generate all neighbors by swapping two nodes in the permutation.
        Returns a list of (new_permutation, swapped_pair)
        """
        neighbors = []
        indices = list(range(len(permutation)))
        for i, j in combinations(indices, 2):
            neighbor = list(permutation)
            neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
            # Pair representing the move, sorted to treat (A,B) and (B,A) as the same move
            move = tuple(sorted([permutation[i], permutation[j]]))
            neighbors.append((neighbor, move))
        return neighbors

    def search(self):
        start_eval_time = time.time()
        
        # Initial solution: sequential from the list L
        current_solution = list(self.stops_to_visit)
        best_solution = list(current_solution)
        
        current_cost, current_path_info = self.evaluate_permutation(current_solution)
        best_cost = current_cost
        best_path_info = current_path_info
        
        if current_cost == float('inf'):
            print("Nie można znaleźć ścieżki początkowej.", file=sys.stderr)
            return

        iterations_without_improvement = 0
        tabu_moves = {} # move -> expiration_iteration
        
        print(f"Początkowy koszt: {best_cost} dla permutacji: {best_solution}", file=sys.stderr)
        
        for iteration in range(self.max_iterations):
            neighbors = self.get_neighbors(current_solution)
            best_neighbor_cost = float('inf')
            best_neighbor = None
            best_neighbor_path_info = None
            best_move = None
            
            for neighbor_solution, move in neighbors:
                # Check if move is Tabu
                if move in tabu_moves and tabu_moves[move] > iteration:
                    # Aspiration criteria could be added here (e.g. if cost < best_cost)
                    # We will simply skip tabu moves
                    continue
                    
                cost, path_info = self.evaluate_permutation(neighbor_solution)
                
                if cost < best_neighbor_cost:
                    best_neighbor_cost = cost
                    best_neighbor = neighbor_solution
                    best_neighbor_path_info = path_info
                    best_move = move
                    
            if best_neighbor is None:
                # No valid non-tabu neighbors
                break
                
            # Move to best neighbor
            current_solution = best_neighbor
            current_cost = best_neighbor_cost
            current_path_info = best_neighbor_path_info
            
            # Update Tabu list
            if best_move is not None:
                tabu_moves[best_move] = iteration + self.tabu_tenure
                
            # Update global best
            if current_cost < best_cost:
                best_cost = current_cost
                best_solution = list(current_solution)
                best_path_info = current_path_info
                iterations_without_improvement = 0
                print(f"Nowe najlepsze rozwiązanie w iteracji {iteration}: koszt {best_cost}, permutacja: {best_solution}", file=sys.stderr)
            else:
                iterations_without_improvement += 1
                
            # Stop if no improvement for 5 consecutive iterations
            if iterations_without_improvement >= 5:
                break
                
        eval_time = time.time() - start_eval_time
        
        # Output results
        self.print_solution(best_solution, best_path_info, best_cost, eval_time)

    def print_solution(self, best_solution, best_path_info, best_cost, eval_time):
        
        if best_path_info is None:
            print("Nie znaleziono pełnej trasy.", file=sys.stderr)
            return

        print(f"Najlepsza trasa: {best_solution}")
        
        for leg in best_path_info:
            from_stop_leg, to_stop_leg, path, arrival_time_sec, base_date = leg
            print(f"\nOdcinek: {from_stop_leg} -> {to_stop_leg}")
            self.route_finder.print_route(path, arrival_time_sec, base_date)

        # Wypisywanie na standardowe wyjście błędów wartość minimalizowanego kryterium oraz czas
        print(f"\nKryterium: {best_cost}", file=sys.stderr)
        print(f"Czas obliczeń: {eval_time}", file=sys.stderr)
