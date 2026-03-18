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
    # A = "Wrocław Sołtysowice"   
    # B = "Oleśnica"
    # start_time_str = "2026-03-08 15:20" # czas rozpoczęcia podróży
    
    route_finder = RouteFinder(graph)
    
    print(f"Rozpoczęcie szukania A*: {A} -> {B} (Kryterium: {criteria}, Start: {start_time_str})")
    
    start_eval_time = time.time()
    cost, path, arrival_time, base_date = route_finder.evaluate_a_star_route(A, B, start_time_str, criteria, upgraded_heuristic=True)
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

