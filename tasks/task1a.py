def dijkstra(graph, s):
    d = {v: float('inf') for v in graph}
    p = {v: None for v in graph}
    d[s] = 0
    
    Q = set(graph.keys())
    
    while Q:
        u = min(Q, key=lambda k: d[k])
        Q.remove(u)
        
        for v, weight in graph[u].items():
            if d[v] > d[u] + weight:
                d[v] = d[u] + weight
                p[v] = u
                
    return d, p