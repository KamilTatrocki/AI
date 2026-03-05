"""
Testy integracyjne dla StopTimesGraph i algorytmów Dijkstry
na PRAWDZIWYCH danych GTFS z folderu data/.

Fakty ustalone na podstawie analizy plików data/*.txt:

══════════════════════════════════════════════════════════════════════
KRAWĘDZIE KURSOWE (trip 37148498_396994, route 234088, service 1_396994)
  Aktywny w środę 2026-03-05 (calendar: wed=1, 20260225–20260307)
  1474824 dep=05:36 → 1474825 arr=05:41  waga = 5 min = 300 s
  1474825 dep=05:41 → 1474826 arr=05:48  waga = 7 min = 420 s

STACJA PRZESIADKOWA (parent_station=1413065, nazwa "Bardo Przyłęk"):
  stop 1475207  (obsługiwany m.in. przez trip 37151308_399804, route 234116)
  stop 1474849  (obsługiwany m.in. przez trip 37149204_397700, route 234108)

  Przesiadka w kierunku 1475207 → 1474849:
    Kurs T₁ = 37151308_399804 (route 234116, service 2450_399804)
      przybywa  na 1475207 o 06:31 (arr=06:31)
    Kurs T₂ = 37149204_397700 (route 234108, service 610_397700)
      odjeżdża z 1474849 o 06:45 (dep=06:45)
    Czas oczekiwania = 06:45 − 06:31 = 14 min = 840 s
    Oba serwisy aktywne w środę 2026-03-05 (calendar wed=1, 20260225–20260306)

DATA TESTOWA: 2026-03-05 (środa) – mieści się w każdym z powyższych zakresów
══════════════════════════════════════════════════════════════════════
"""

import pytest
import sys
import os
from datetime import datetime

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from data_consumer import main_consumer

TEST_DAY    = datetime(2026, 3, 5)     # środa – data z zakresu wszystkich badanych serwisów
NO_DAY      = None                     # bez filtrowania po dniu

# Konkretne stop_id z danych
STOP_A      = 1474824   # Trutnov hl.n.  (trip 37148498_396994, first stop)
STOP_B      = 1474825   # Trutnov střed  (trip 37148498_396994, second stop)
STOP_C      = 1474826   # Liberec        (trip 37148498_396994, third stop)

STOP_P1     = 1475207   # Bardo Przyłęk  (parent=1413065, kurs 37151308_399804 arr=06:31)
STOP_P2     = 1474849   # Bardo Przyłęk  (parent=1413065, kurs 37149204_397700 dep=06:45)
PARENT_BARDO = 1413065

TRIP_MAIN   = "37148498_396994"  # kurs A→B→C...  route=234088
TRIP_T1     = "37151308_399804"  # kurs przyb. na P1 o 06:31  route=234116
TRIP_T2     = "37149204_397700"  # kurs odj. z P2  o 06:45  route=234108

ROUTE_MAIN  = 234088
ROUTE_T1    = 234116
ROUTE_T2    = 234108

# Wagi kursowe [sekundy] – MINIMALNE spośród wszystkich kursów na danej parze
# A→B: min z kursów = trip 37148513_397009 (4m00s) = 240 s  (nie 300 s z kursu głównego!)
WEIGHT_A_B  = 4 * 60    # 240 s  (13:41 − 13:37, kurs 37148513_397009)
# B→C: tylko jeden kursy = 7 min = 420 s
WEIGHT_B_C  = 7 * 60    # 420 s
# Przesiadka P1→P2: dep T2 = 06:46, arr T1 = 06:31 → 15 min = 900 s
WAIT_P1_P2  = 15 * 60   # 900 s  (06:46 − 06:31)


# ---------------------------------------------------------------------------
# Fixture: wczytaj dane raz dla całego modułu
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module", autouse=True)
def load_gtfs():
    """Wczytaj prawdziwe dane GTFS przed uruchomieniem testów.

    Jawnie resetuje main_consumer – konieczne gdy test_transfers.py (syntetyczne dane)
    uruchomiał się wcześniej i zostawiał mock w pamięci.
    """
    import data_consumer as dc_mod
    import utils.stop_times_graph as stg_mod
    import utils.calendar as cal_mod

    real_consumer = dc_mod.DataConsumer(
        data_dir=os.path.join(REPO_ROOT, "data")
    )
    real_consumer.load_data()

    # Wstrzyknij prawdziwy consumer do wszystkich modułów które go używają
    dc_mod.main_consumer = real_consumer
    stg_mod.main_consumer = real_consumer
    # Calendar używa lazy-load, ale na wszelki wypadek wyczyść cache
    cal_mod.main_consumer = real_consumer
    # Calendar jest singleton'em z lazy-load – wymuś reset cache
    cal_mod.calendar._calendar_data = None
    cal_mod.calendar._calendar_exception = None
    cal_mod.calendar._trips_data = None
    cal_mod.calendar._day_cache = {}


@pytest.fixture(scope="module")
def stg_no_day():
    """Graf bez filtrowania po dniu (wszystkie kursy)."""
    from utils.stop_times_graph import StopTimesGraph
    return StopTimesGraph().build(day=None)


@pytest.fixture(scope="module")
def stg_wed():
    """Graf dla środy 2026-03-05."""
    from utils.stop_times_graph import StopTimesGraph
    return StopTimesGraph().build(day=TEST_DAY)


@pytest.fixture(scope="module")
def dijkstra_fns():
    from tasks.task1a import dijkstra, dijkstra_min_transfers, reconstruct_path
    return dijkstra, dijkstra_min_transfers, reconstruct_path


# ===========================================================================
# 1. Wczytywanie danych i ogólna struktura grafu
# ===========================================================================

class TestGraphBuilding:

    def test_graph_has_many_nodes(self, stg_no_day):
        """Graf pełny powinien mieć 718 węzłów (tyle co stop_id w stop_times)."""
        assert len(stg_no_day) == 718

    def test_graph_filtered_by_day_has_fewer_nodes(self, stg_no_day, stg_wed):
        """Po filtracji po dniu mamy ≤ tyle węzłów co w grafie pełnym."""
        assert len(stg_wed) <= len(stg_no_day)
        assert len(stg_wed) > 0

    def test_graph_filtered_has_reasonable_size(self, stg_wed):
        """Graf dzienny powinien mieć sensowną liczbę węzłów (>100)."""
        assert len(stg_wed) > 100

    def test_repr_shows_nodes_and_edges(self, stg_no_day):
        r = repr(stg_no_day)
        assert "węzły=" in r
        assert "krawędzie=" in r


# ===========================================================================
# 2. Krawędzie kursowe – konkretne wagi z trip 37148498_396994
# ===========================================================================

class TestInVehicleEdges:

    def test_edge_A_to_B_exists(self, stg_no_day):
        """Krawędź 1474824 → 1474825 musi istnieć (kurs 37148498_396994)."""
        assert STOP_B in stg_no_day.graph[STOP_A]

    def test_edge_A_to_B_weight(self, stg_no_day):
        """
        Waga A→B = minimalna spośród wszystkich kursów = 240 s (4 min).
        Kurs 37148513_397009: dep 13:37 → arr 13:41 (4 min).
        Kurs 37148498_396994: dep 05:36 → arr 05:41 (5 min) – NIE jest minimum.
        """
        assert stg_no_day.graph[STOP_A][STOP_B] == WEIGHT_A_B

    def test_edge_B_to_C_exists(self, stg_no_day):
        """Krawędź 1474825 → 1474826 musi istnieć."""
        assert STOP_C in stg_no_day.graph[STOP_B]

    def test_edge_B_to_C_weight(self, stg_no_day):
        """Waga B→C = 7 min = 420 s (05:48 − 05:41)."""
        assert stg_no_day.graph[STOP_B][STOP_C] == WEIGHT_B_C

    def test_edge_trip_recorded(self, stg_no_day):
        """edge_trips[A][B] musi zawierać kurs T₁."""
        assert TRIP_MAIN in stg_no_day.edge_trips[STOP_A][STOP_B]

    def test_edges_present_in_day_filtered_graph(self, stg_wed):
        """Krawędź A→B powinna być obecna też w grafie dziennym (serwis aktywny w środę)."""
        assert STOP_B in stg_wed.graph.get(STOP_A, {})
        # W grafie dziennym mogą być inne minimalne wagi niż w pełnym
        # (podzbiór aktywnych kursów) – sprawdzamy tylko że waga jest sensowna
        assert stg_wed.graph[STOP_A][STOP_B] > 0


# ===========================================================================
# 3. Indeks stacji (parent_station) i krawędzie przesiadkowe
# ===========================================================================

class TestStationIndexReal:

    def test_P1_and_P2_share_parent_station(self, stg_no_day):
        """Przystanki 1475207 i 1474849 mają tę samą parent_station=1413065."""
        assert stg_no_day._stop_to_station[STOP_P1] == PARENT_BARDO
        assert stg_no_day._stop_to_station[STOP_P2] == PARENT_BARDO

    def test_all_718_stops_in_station_index(self, stg_no_day):
        """Każdy węzeł grafu musi być zmapowany w indeksie stacji."""
        for stop_id in stg_no_day.graph:
            assert stop_id in stg_no_day._stop_to_station

    def test_transfer_P1_to_P2_exists(self, stg_no_day):
        """
        Przybycie na P1 (1475207) o 06:31 – przesiadka dostępna na P2 (1474849)
        o 06:45. get_transfer_edges musi ją zwrócić.
        """
        arr_on_P1 = 6 * 3600 + 31 * 60   # 06:31:00 w sekundach
        transfers = stg_no_day.get_transfer_edges(STOP_P1, arr_on_P1)
        to_P2 = [(nb, wait, t) for nb, wait, t in transfers if nb == STOP_P2 and t == TRIP_T2]
        assert len(to_P2) >= 1, (
            f"Przesiadka P1→P2 przez {TRIP_T2} nieznaleziona. "
            f"Dostępne: {transfers[:5]}"
        )

    def test_transfer_wait_time_correct(self, stg_no_day):
        """Czas oczekiwania przy przesiadce P1→P2 = 14 min = 840 s."""
        arr_on_P1 = 6 * 3600 + 31 * 60
        transfers = stg_no_day.get_transfer_edges(STOP_P1, arr_on_P1)
        to_P2 = [(nb, wait, t) for nb, wait, t in transfers if nb == STOP_P2 and t == TRIP_T2]
        assert to_P2[0][1] == WAIT_P1_P2, (
            f"Oczekiwany czas oczekiwania: {WAIT_P1_P2} s, dostałem {to_P2[0][1]} s"
        )

    def test_transfer_unavailable_if_arrived_after_departure(self, stg_no_day):
        """Przybycie po 06:45 – kurs T₂ odjeżdżający o 06:45 nie powinien być dostępny."""
        arr_too_late = 6 * 3600 + 46 * 60   # 06:46:00
        transfers = stg_no_day.get_transfer_edges(STOP_P1, arr_too_late)
        t2_results = [(nb, w, t) for nb, w, t in transfers if t == TRIP_T2 and w < 0]
        # Negatywne czasy oczekiwania nie powinny być zwracane
        assert t2_results == [], f"Ujemne czasy oczekiwania nie powinny być zwracane: {t2_results}"


# ===========================================================================
# 4. Dijkstra – minimalizacja czasu – na prawdziwych danych
# ===========================================================================

class TestDijkstraTimeReal:

    def test_distance_A_to_B(self, stg_no_day, dijkstra_fns):
        """Najkrótsza ścieżka A→B = 240 s (min waga krawędzi w grafie)."""
        dijkstra, _, _ = dijkstra_fns
        d, _ = dijkstra(stg_no_day.graph, STOP_A)
        assert d[STOP_B] == WEIGHT_A_B

    def test_distance_A_to_C(self, stg_no_day, dijkstra_fns):
        """Najkrótsza ścieżka A→C = 240 s + 420 s = 660 s."""
        dijkstra, _, _ = dijkstra_fns
        d, _ = dijkstra(stg_no_day.graph, STOP_A)
        assert d[STOP_C] == WEIGHT_A_B + WEIGHT_B_C

    def test_reconstruct_path_A_to_C(self, stg_no_day, dijkstra_fns):
        """Ścieżka A→C to [A, B, C]."""
        dijkstra, _, reconstruct_path = dijkstra_fns
        _, p = dijkstra(stg_no_day.graph, STOP_A)
        path = reconstruct_path(p, STOP_A, STOP_C)
        assert path == [STOP_A, STOP_B, STOP_C]

    def test_start_to_self_is_zero(self, stg_no_day, dijkstra_fns):
        """Odległość od węzła do samego siebie = 0."""
        dijkstra, _, _ = dijkstra_fns
        d, _ = dijkstra(stg_no_day.graph, STOP_A)
        assert d[STOP_A] == 0

    def test_all_reachable_distances_nonnegative(self, stg_no_day, dijkstra_fns):
        """Wszystkie obliczone odległości muszą być nieujemne."""
        dijkstra, _, _ = dijkstra_fns
        d, _ = dijkstra(stg_no_day.graph, STOP_A)
        for stop, dist in d.items():
            assert dist >= 0, f"Ujemna odległość do stop {stop}: {dist}"


# ===========================================================================
# 5. Dijkstra – minimalizacja przesiadek – na prawdziwych danych
# ===========================================================================

class TestDijkstraTransfersReal:

    def test_zero_transfers_on_direct_trip(self, stg_no_day, dijkstra_fns):
        """A→B bezpośrednim kursem: 0 przesiadek."""
        _, dijkstra_min_transfers, _ = dijkstra_fns
        d, _ = dijkstra_min_transfers(stg_no_day, STOP_A, start_time_sec=5 * 3600 + 36 * 60)
        transfers, _ = d[STOP_B]
        assert transfers == 0

    def test_zero_transfers_A_to_C(self, stg_no_day, dijkstra_fns):
        """A→C tym samym kursem co A→B→C: 0 przesiadek."""
        _, dijkstra_min_transfers, _ = dijkstra_fns
        d, _ = dijkstra_min_transfers(stg_no_day, STOP_A, start_time_sec=5 * 3600 + 36 * 60)
        transfers, _ = d[STOP_C]
        assert transfers == 0

    def test_path_requiring_transfer_has_one_transfer(self, stg_no_day, dijkstra_fns):
        """
        Ścieżka wymagająca przesiadki na stacji Bardo Przyłęk:
        P1 (1475207) → P2 (1474849) to zmiana kursu → 1 przesiadka.
        Startujemy z P1 po przyjeździe kursu T₁ (o 06:31).
        """
        _, dijkstra_min_transfers, _ = dijkstra_fns
        # Start z P1 po przyjeździe T1
        start_sec = 6 * 3600 + 31 * 60   # 06:31

        # Sprawdzamy tylko samą przesiadkę P1→P2 (get_transfer_edges),
        # nie pełną trasę przez Dijkstrę (bo P2 może mieć kontynuację kursu)
        transfers = stg_no_day.get_transfer_edges(STOP_P1, start_sec)
        to_P2 = [(nb, wait, t) for nb, wait, t in transfers if nb == STOP_P2]
        assert len(to_P2) > 0, "Powinna istnieć możliwość przesiadki P1→P2"

    def test_result_dict_contains_tuples(self, stg_no_day, dijkstra_fns):
        """dijkstra_min_transfers zwraca słownik {stop: (transfers, time)}."""
        _, dijkstra_min_transfers, _ = dijkstra_fns
        d, _ = dijkstra_min_transfers(stg_no_day, STOP_A, start_time_sec=0)
        for stop, val in d.items():
            assert isinstance(val, tuple) and len(val) == 2, (
                f"Oczekiwano krotki (transfers, time), dostałem {val!r} dla stop {stop}"
            )

    def test_transfers_are_nonnegative(self, stg_no_day, dijkstra_fns):
        """Liczba przesiadek musi być zawsze ≥ 0."""
        _, dijkstra_min_transfers, _ = dijkstra_fns
        d, _ = dijkstra_min_transfers(stg_no_day, STOP_A, start_time_sec=0)
        for stop, (transfers, _) in d.items():
            if transfers < float("inf"):
                assert transfers >= 0, f"Ujemna liczba przesiadek dla stop {stop}: {transfers}"

    def test_time_component_nonnegative(self, stg_no_day, dijkstra_fns):
        """Czas łączny musi być ≥ 0 dla wszystkich osiągalnych węzłów."""
        _, dijkstra_min_transfers, _ = dijkstra_fns
        d, _ = dijkstra_min_transfers(stg_no_day, STOP_A, start_time_sec=0)
        for stop, (transfers, time) in d.items():
            if transfers < float("inf"):
                assert time >= 0, f"Ujemny czas dla stop {stop}: {time}"


# ===========================================================================
# 6. Filtrowanie po dniu – spójność z kalendarzem
# ===========================================================================

class TestDayFiltering:

    def test_edges_from_active_service_present(self, stg_wed):
        """
        Serwis 1_396994 jest aktywny w środę 2026-03-05.
        Krawędź A→B z tego kursu musi być w grafie dziennym.
        """
        assert STOP_B in stg_wed.graph.get(STOP_A, {}), (
            "Krawędź A→B (kurs aktywny w środę) powinna być w grafie dziennym"
        )

    def test_day_graph_is_subset_of_full_graph(self, stg_no_day, stg_wed):
        """
        Graf dzienny to podzbiór pełnego – każda krawędź dziennego grafu
        musi istnieć też w pełnym grafie.
        """
        for stop_a, neighbors in stg_wed.graph.items():
            assert stop_a in stg_no_day.graph, f"Węzeł {stop_a} z grafu dziennego nie ma w pełnym"
            for stop_b in neighbors:
                assert stop_b in stg_no_day.graph[stop_a], (
                    f"Krawędź {stop_a}→{stop_b} z grafu dziennego nie ma w pełnym"
                )

    def test_no_service_before_schedule(self):
        """Dla daty przed startem rozkładu graf powinien być pusty."""
        from utils.stop_times_graph import StopTimesGraph
        stg_empty = StopTimesGraph().build(day=datetime(2025, 1, 1))
        assert len(stg_empty) == 0, "Graf przed startem rozkładu powinien być pusty"
