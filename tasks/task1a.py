import heapq
from datetime import datetime

from utils.stop_times_graph import StopTimesGraph
from data_consumer import main_consumer


# ---------------------------------------------------------------------------
# Dijkstra – funkcja kosztu: CZAS PRZEJAZDU
# ---------------------------------------------------------------------------

def dijkstra(graph: dict, s) -> tuple[dict, dict]:
    """
    Algorytm Dijkstry – minimalizuje łączny czas przejazdu.

    Parametry
    ----------
    graph : dict
        {stop_id: {sąsiad_stop_id: waga_sekundy, ...}, ...}
        Pobierz z: StopTimesGraph().build(day).graph
    s :
        Węzeł startowy.

    Zwraca
    -------
    d : dict  {stop_id: min_czas_sekundy}   (inf = nieosiągalne)
    p : dict  {stop_id: poprzednik_stop_id}
    """
    d = {v: float("inf") for v in graph}
    p = {v: None for v in graph}
    d[s] = 0

    Q = set(graph.keys())

    while Q:
        u = min(Q, key=lambda k: d[k])
        Q.remove(u)

        if d[u] == float("inf"):
            break

        for v, weight in graph[u].items():
            if d[v] > d[u] + weight:
                d[v] = d[u] + weight
                p[v] = u

    return d, p


# ---------------------------------------------------------------------------
# Nazwy stacji
# ---------------------------------------------------------------------------

def get_stop_names() -> dict:
    """
    Buduje słownik {stop_id: stop_name} z danych GTFS.

    Przykład użycia:
        names = get_stop_names()
        path  = reconstruct_path(p, start, end, stop_names=names)
        # →  ['Trutnov hl.n.', 'Trutnov střed', 'Liberec']
    """
    stops_df = main_consumer.stops
    if stops_df is None:
        raise RuntimeError("Dane stops nie istnieją. Wywołaj main_consumer.load_data().")
    return dict(zip(stops_df["stop_id"], stops_df["stop_name"]))


# ---------------------------------------------------------------------------
# Odtwarzanie ścieżki
# ---------------------------------------------------------------------------

def reconstruct_path(p: dict, start, end, stop_names: dict | None = None) -> list:
    """
    Odtwarza ścieżkę [start, ..., end] ze słownika poprzedników.
    Zwraca pustą listę jeśli end jest nieosiągalny.

    Parametry
    ----------
    p : dict
        Słownik poprzedników zwrócony przez dijkstra() lub dijkstra_min_transfers().
    start, end :
        Węzły startowy i docelowy (stop_id).
    stop_names : dict | None
        Opcjonalnie słownik {stop_id: nazwa_stacji}.
        Jeśli podany, ścieżka zwraca nazwy zamiast stop_id.
        Pobierz przez: get_stop_names()

    Zwraca
    ------
    list
        [start, ..., end]  – stop_id lub nazwy stacji (zależnie od stop_names).
        Pusta lista gdy end jest nieosiągalny.
    """
    path = []
    node = end
    while node is not None:
        path.append(node)
        node = p[node]
        if node == start:
            path.append(start)
            break
    else:
        return []

    path = list(reversed(path))

    if stop_names is not None:
        path = [stop_names.get(sid, sid) for sid in path]

    return path


if __name__ == "__main__":
    print("Wczytywanie danych GTFS...")
    main_consumer.load_data()

    day = datetime(2026, 3, 5)
    print(f"Budowanie grafu dla dnia {day.strftime('%Y-%m-%d')} ...")
    stg = StopTimesGraph().build(day=day)
    print(stg)

    names = get_stop_names()
    start_stop = 1474667
    print(f"\nStart: stop_id={start_stop}  ({names.get(start_stop, '?')})")

    # Graf z przesiadkami, ścieżki z nazwami stacji
    print(f"\n[CZAS, z przesiadkami] Dijkstra ze stop_id={start_stop}...")
    d_wtf, p_wtf = dijkstra(stg.graph_with_transfers, start_stop)
    reachable_wtf = sorted(
        ((k, v) for k, v in d_wtf.items() if v < float("inf") and k != start_stop),
        key=lambda x: x[1],
    )[:100]
    print("50 najbliższych (z możliwymi przesiadkami):")
    for stop_id, sec in reachable_wtf:
        m, s = divmod(int(sec), 60)
        path_named = reconstruct_path(p_wtf, start_stop, stop_id, stop_names=names)
        print(f"  {names.get(stop_id, stop_id):<30}  czas={m}m{s:02d}s  ścieżka={path_named}")
