"""
Testy dla stop_times_graph.StopTimesGraph i task1a.dijkstra_min_transfers.

Strategia:
  - Tworzymy syntetyczne (mini) dane GTFS jako pandas DataFrame-y
    i wstrzykujemy je w miejsce main_consumer – dzięki temu testy są
    deterministyczne i nie zależą od pliku stop_times.txt.
  - Następnie testujemy dijkstra_min_transfers() i dijkstra() z poznanymi,
    ręcznie wyliczonymi wynikami.

Topologia sieci testowej
────────────────────────
Przystanki (stop_id → parent_station):
    A=1  →  stacja X (parent=10)
    B=2  →  stacja X (parent=10)   ← A i B są na tej samej stacji X!
    C=3  →  stacja Y (parent=20)
    D=4  →  stacja Z (brak parent)

Kursy:
    trip "T1" (route 100): A(dep=00:00) → C(arr=00:20)
    trip "T2" (route 101): B(dep=00:30) → D(arr=00:50)

Oczekiwana sieć połączeń:
    Krawędzie kursowe:
        A → C  (T1, 20 min = 1200 s)
        B → D  (T2, 20 min = 1200 s)

    Krawędzie przesiadkowe (A i B są na stacji X):
        A → B  (przesiadka, czeka się aż T2 odjedzie: 30 min − 0 min = 30 min = 1800 s)
        B → A  (symetrycznie, ale T1 już odjechał więc brak w tym oknie)

Ścieżka A → D:
    Jedź T1 do C  → niemożliwe dalej bez przesiadki
    Lepiej: wsiądź na T1 na A, ale... A→C to kurs. D jest poza tym kursem.
    Więc: A → (przesiadka na stacji X) → B → D
      przesiadki = 1
      czas       = czekanie 30 min + jazda B→D 20 min = 50 min = 3000 s
"""

import pytest
import sys
import os
import importlib
import types
import pandas as pd

# ---------------------------------------------------------------------------
# sys.path: repo root musi być dostępny zarówno jako pakiet jak i bezpośrednio
# ---------------------------------------------------------------------------

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# ---------------------------------------------------------------------------
# Syntetyczne dane GTFS
# ---------------------------------------------------------------------------

def _make_stops() -> pd.DataFrame:
    """
    stop_id  parent_station
      1(A)       10              ← stacja X
      2(B)       10              ← stacja X (ta sama co A → przesiadka możliwa)
      3(C)       20              ← stacja Y
      4(D)       NaN             ← brak parent (samodzielny)
    """
    return pd.DataFrame({
        "stop_id":        [1,    2,    3,    4],
        "stop_name":      ["A",  "B",  "C",  "D"],
        "stop_lat":       [0.0,  0.0,  0.0,  0.0],
        "stop_lon":       [0.0,  0.0,  0.0,  0.0],
        "location_type":  [0,    0,    0,    0],
        "parent_station": [10.0, 10.0, 20.0, float("nan")],
    })


def _make_trips() -> pd.DataFrame:
    """
    trip_id  route_id  service_id
    T1       100       S1
    T2       101       S1
    """
    return pd.DataFrame({
        "trip_id":    ["T1", "T2"],
        "route_id":   [100,  101],
        "service_id": ["S1", "S1"],
    })


def _make_stop_times() -> pd.DataFrame:
    """
    T1: A(1) dep=00:00 → C(3) arr=00:20
    T2: B(2) dep=00:30 → D(4) arr=00:50
    """
    return pd.DataFrame({
        "trip_id":        ["T1", "T1", "T2", "T2"],
        "stop_id":        [1,    3,    2,    4   ],
        "stop_sequence":  [0,    1,    0,    1   ],
        "arrival_time":   ["00:00:00", "00:20:00", "00:30:00", "00:50:00"],
        "departure_time": ["00:00:00", "00:20:00", "00:30:00", "00:50:00"],
    })


# ---------------------------------------------------------------------------
# Fixture: StopTimesGraph z syntetycznymi danymi (bez filtrowania po dniu)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def stg():
    """
    Buduje StopTimesGraph z minimalnym, syntetycznym zestawem danych.
    Wstrzykuje dane do main_consumer przed wywołaniem build().
    """
    import data_consumer as dc_mod
    consumer = dc_mod.DataConsumer()
    consumer.stops      = _make_stops()
    consumer.trips      = _make_trips()
    consumer.stop_times = _make_stop_times()

    original = dc_mod.main_consumer
    dc_mod.main_consumer = consumer

    from utils.stop_times_graph import StopTimesGraph
    # Reimportuj moduł żeby pobrał nowy main_consumer
    import utils.stop_times_graph as stg_mod
    stg_mod.main_consumer = consumer

    graph = StopTimesGraph().build(day=None)  # bez filtrowania kalendarza

    dc_mod.main_consumer = original
    return graph


# ---------------------------------------------------------------------------
# Fixture: dijkstra_min_transfers i dijkstra ze stg
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def dijkstra_fns():
    from tasks.task1a import dijkstra, dijkstra_min_transfers, reconstruct_path
    return dijkstra, dijkstra_min_transfers, reconstruct_path


# ===========================================================================
# 1. Testy struktury grafu kursowego
# ===========================================================================

class TestGraphStructure:

    def test_all_stops_are_nodes(self, stg):
        """Każdy stop_id z stop_times musi być węzłem w grafie."""
        assert 1 in stg.graph   # A
        assert 2 in stg.graph   # B
        assert 3 in stg.graph   # C
        assert 4 in stg.graph   # D

    def test_in_vehicle_edge_T1(self, stg):
        """Krawędź kursowa T1: A(1) → C(3), waga = 20 min = 1200 s."""
        assert 3 in stg.graph[1]
        assert stg.graph[1][3] == 20 * 60

    def test_in_vehicle_edge_T2(self, stg):
        """Krawędź kursowa T2: B(2) → D(4), waga = 20 min = 1200 s."""
        assert 4 in stg.graph[2]
        assert stg.graph[2][4] == 20 * 60

    def test_no_direct_edge_A_to_B(self, stg):
        """A i B są na tej samej stacji, ale NIE ma między nimi krawędzi kursowej."""
        assert 2 not in stg.graph.get(1, {})

    def test_no_direct_edge_A_to_D(self, stg):
        """Brak bezpośredniego połączenia A→D (różne kursy)."""
        assert 4 not in stg.graph.get(1, {})

    def test_edge_trips_T1_recorded(self, stg):
        """edge_trips[A][C] powinno zawierać trip_id 'T1'."""
        assert "T1" in stg.edge_trips[1][3]

    def test_edge_trips_T2_recorded(self, stg):
        """edge_trips[B][D] powinno zawierać trip_id 'T2'."""
        assert "T2" in stg.edge_trips[2][4]


# ===========================================================================
# 2. Testy indeksu stacji (parent_station)
# ===========================================================================

class TestStationIndex:

    def test_A_and_B_share_station(self, stg):
        """Stop A(1) i B(2) mają tę samą parent_station (10)."""
        assert stg._stop_to_station[1] == stg._stop_to_station[2] == 10

    def test_C_has_own_station(self, stg):
        """Stop C(3) ma parent_station=20."""
        assert stg._stop_to_station[3] == 20

    def test_D_without_parent_maps_to_itself(self, stg):
        """Stop D(4) bez parent_station mapuje na swój własny stop_id."""
        assert stg._stop_to_station[4] == 4


# ===========================================================================
# 3. Testy krawędzi przesiadkowych (get_transfer_edges)
# ===========================================================================

class TestTransferEdges:

    def test_transfer_from_A_to_B_exists(self, stg):
        """
        Przychodząc na stację X (stop A) o 00:00, powinniśmy widzieć
        kurs T2 odjeżdżający z B o 00:30 → czas oczekiwania 30 min = 1800 s.
        """
        arr_at_A = 0  # 00:00:00 w sekundach
        transfers = stg.get_transfer_edges(stop_id=1, arrival_sec=arr_at_A)

        # Musi istnieć opcja: neighbor=B(2), wait=1800, trip=T2
        found = [(nb, wait, t) for nb, wait, t in transfers if nb == 2 and t == "T2"]
        assert len(found) == 1, f"Brak przesiadki A→B przez T2. Znalezione: {transfers}"
        assert found[0][1] == 30 * 60, f"Czas oczekiwania powinien być 1800s, jest {found[0][1]}"

    def test_no_transfer_to_same_stop(self, stg):
        """get_transfer_edges nie zwraca przesiadki na TEN SAM stop_id."""
        transfers = stg.get_transfer_edges(stop_id=1, arrival_sec=0)
        same_stop = [nb for nb, _, _ in transfers if nb == 1]
        assert same_stop == []

    def test_no_transfer_if_too_late(self, stg):
        """Przychodząc po 00:30 na stację X, kurs T2 już odjechał → brak przesiadki."""
        arr_after_T2 = 31 * 60  # 00:31:00
        transfers = stg.get_transfer_edges(stop_id=1, arrival_sec=arr_after_T2)
        t2_transfers = [(nb, wait, t) for nb, wait, t in transfers if t == "T2"]
        assert t2_transfers == [], f"T2 nie powinien być dostępny po 00:31. Znalezione: {t2_transfers}"

    def test_no_transfer_between_different_stations(self, stg):
        """
        C(3) jest na stacji Y, D(4) jest samodzielna → brak wspólnej stacji.
        get_transfer_edges z C nie powinna zwracać D.
        """
        transfers = stg.get_transfer_edges(stop_id=3, arrival_sec=0)
        to_D = [nb for nb, _, _ in transfers if nb == 4]
        assert to_D == []


# ===========================================================================
# 4. Testy dijkstra_min_transfers – liczba przesiadek
# ===========================================================================

class TestDijkstraMinTransfers:

    def test_direct_path_zero_transfers(self, stg, dijkstra_fns):
        """
        Start: A(1), cel: C(3).
        Trasa: A → C kursem T1, bez żadnej przesiadki.
        Oczekiwane przesiadki = 0.
        """
        _, dijkstra_min_transfers, _ = dijkstra_fns
        d, _ = dijkstra_min_transfers(stg, s=1, start_time_sec=0)
        transfers_to_C, _ = d[3]
        assert transfers_to_C == 0, f"A→C powinno być 0 przesiadek, jest {transfers_to_C}"

    def test_direct_path_correct_time(self, stg, dijkstra_fns):
        """
        A → C kursem T1: czas jazdy = 20 min = 1200 s.
        """
        _, dijkstra_min_transfers, _ = dijkstra_fns
        d, _ = dijkstra_min_transfers(stg, s=1, start_time_sec=0)
        _, time_to_C = d[3]
        assert time_to_C == 20 * 60, f"Czas A→C powinien być 1200 s, jest {time_to_C}"

    def test_path_with_one_transfer(self, stg, dijkstra_fns):
        """
        Start: A(1), cel: D(4).
        Jedyna trasa: A →(przesiadka na stacji X)→ B →(T2)→ D.
        Oczekiwane przesiadki = 1.
        """
        _, dijkstra_min_transfers, _ = dijkstra_fns
        d, _ = dijkstra_min_transfers(stg, s=1, start_time_sec=0)
        assert 4 in d, "D(4) powinno być osiągalne z A(1)"
        transfers_to_D, _ = d[4]
        assert transfers_to_D == 1, f"A→D powinno wymagać 1 przesiadki, jest {transfers_to_D}"

    def test_path_with_one_transfer_total_time(self, stg, dijkstra_fns):
        """
        A → B (czekanie 30 min = 1800 s) → D (jazda 20 min = 1200 s).
        Łączny czas = 3000 s.
        """
        _, dijkstra_min_transfers, _ = dijkstra_fns
        d, _ = dijkstra_min_transfers(stg, s=1, start_time_sec=0)
        _, time_to_D = d[4]
        assert time_to_D == 30 * 60 + 20 * 60, (
            f"Łączny czas A→D powinien być 3000 s, jest {time_to_D}"
        )

    def test_unreachable_stop_is_inf(self, stg, dijkstra_fns):
        """
        A(1) nie ma połączenia z D(4) bez przesiadki przez B.
        Jeśli zaczniemy od C(3) – nie ma żadnego kursu wychodzącego z C.
        """
        _, dijkstra_min_transfers, _ = dijkstra_fns
        d, _ = dijkstra_min_transfers(stg, s=3, start_time_sec=0)
        # Z C nie ma jak dotrzeć do D (C→A→B→D wymaga wstecznego kursu, którego nie ma)
        transfers_to_D, time_to_D = d.get(4, (float("inf"), float("inf")))
        assert transfers_to_D == float("inf"), f"D powinno być nieosiągalne z C, jest {transfers_to_D}"

    def test_reconstruct_path_via_transfer(self, stg, dijkstra_fns):
        """
        Ścieżka A→D musi przechodzić przez B (przesiadka na stacji X).
        """
        _, dijkstra_min_transfers, reconstruct_path = dijkstra_fns
        _, p = dijkstra_min_transfers(stg, s=1, start_time_sec=0)
        path = reconstruct_path(p, start=1, end=4)
        assert path != [], "Ścieżka A→D nie powinna być pusta"
        assert path[0] == 1, "Ścieżka powinna zaczynać się od A(1)"
        assert path[-1] == 4, "Ścieżka powinna kończyć się na D(4)"
        assert 2 in path, f"Ścieżka A→D musi przechodzić przez B(2), dostałem {path}"


# ===========================================================================
# 5. Testy dijkstra (minimalizacja czasu) – porównanie z dijkstra_min_transfers
# ===========================================================================

class TestDijkstraTime:

    def test_time_A_to_C(self, stg, dijkstra_fns):
        """dijkstra() (czas): A→C = 1200 s."""
        dijkstra, _, _ = dijkstra_fns
        d, _ = dijkstra(stg.graph, 1)
        assert d[3] == 20 * 60

    def test_time_B_to_D(self, stg, dijkstra_fns):
        """dijkstra() (czas): B→D = 1200 s."""
        dijkstra, _, _ = dijkstra_fns
        d, _ = dijkstra(stg.graph, 2)
        assert d[4] == 20 * 60

    def test_C_unreachable_from_A_by_time(self, stg, dijkstra_fns):
        """
        Graf kursowy nie ma krawędzi A→B ani A→D bezpośrednio.
        Dijkstra (czas) nie obsługuje przesiadek – D powinno być nieosiągalne.
        """
        dijkstra, _, _ = dijkstra_fns
        d, _ = dijkstra(stg.graph, 1)
        assert d[4] == float("inf"), (
            f"D(4) powinno być nieosiągalne przez sam graf kursowy z A, jest {d[4]}"
        )
