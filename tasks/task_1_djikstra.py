"""
Wersja wykorzystująca uproszczoną klasę RouteFinderSimple optymalizującą
wyłącznie najszybszy czas przyjazdu (bez wgłębiania się w przesiadki).
"""
import sys
import os

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
    start_time_str = "2026-03-11 21:00" # czas rozpoczęcia podróży

    #inne
    A= "Forst (Lausitz)"
    B= "Jerzmanki"
    start_time_str = "2026-03-08 8:00"
    
    print(f"Szukanie trasy z '{A}' do '{B}' (Tylko optymalizacja czasu przejazdu, Start: {start_time_str})")
    print("-" * 50)
    
    route_finder = RouteFinder(graph)
    path, arrival_time, base_date = route_finder.dijkstra(A, B, start_time_str)
    route_finder.print_route(path, arrival_time, base_date)
