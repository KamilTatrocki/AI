import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.graph import Graph
from data_consumer import main_consumer
import datetime
import time

print("Loading data...")
main_consumer.load_data()
print("Data loaded")

start = time.time()
print("Building graph...")
g = Graph(main_consumer)
print(f"Graph built in {time.time() - start:.2f} seconds")
print(f"Total nodes: {len(g.nodes)}")
total_edges = sum(len(edges) for edges in g.adjacency_list.values())
print(f"Total edges: {total_edges}")

test_stop = list(g.adjacency_list.keys())[0] if g.adjacency_list else "None"
print(f"Sample edges for stop {test_stop}:")
if test_stop != "None":
    for e in g.adjacency_list[test_stop][:2]:
        print("  ", e)
        
print("Graph processing test completed.")
