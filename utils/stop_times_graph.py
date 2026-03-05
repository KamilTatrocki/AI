import heapq
from collections import defaultdict
from datetime import datetime

from data_consumer import main_consumer


def _time_to_seconds(t: str) -> int:
    """
    GTFS dopuszcza (np. "25:10:00").
    """
    h, m, s = t.strip().split(":")
    return int(h) * 3600 + int(m) * 60 + int(s)


class StopTimesGraph:
    """
    Buduje skierowany, ważony, zależny od dnia graf komunikacji miejskiej z GTFS.

    ═══════════════════════════════════════════════════════════════════
    WĘZŁY: stop_id (przystanki z location_type=0)

    KRAWĘDZIE – dwa rodzaje:

      1. Krawędzie kursowe (in-vehicle)
         stop_A → stop_B gdy stop_B następuje bezpośrednio po stop_A
         w tym samym kursie (trip_id) aktywnym w danym dniu.
         Wagi:
           • time      = arrival[B] − departure[A]  [sekundy]
           • transfers = 0  (nie ma zmiany pojazdu)

      2. Krawędzie przesiadkowe (transfer)
         stop_A ↔ stop_B gdy oba mają tę samą parent_station
         (lub ten sam stop_id jeśli brak hierarchii).
         Tworzone dynamicznie podczas Dijkstry na podstawie
         czasu oczekiwania między kursami na tej samej stacji:
           • time      = departure[nowy_kurs] − arrival[obecny_kurs]  [sekundy]
           • transfers = +1

    ═══════════════════════════════════════════════════════════════════
    Użycie:
        stg = StopTimesGraph().build(day=datetime(2024, 3, 5))

        # Minimalizacja czasu
        d, p = dijkstra(stg.graph, start)

        # Minimalizacja przesiadek
        d, p = dijkstra_min_transfers(stg.edge_trips, start)
    """

    def __init__(self) -> None:
        self._graph: dict = {}       # {stop_A: {stop_B: min_czas_sek}}
        self._edge_trips: dict = {}  # {stop_A: {stop_B: frozenset(trip_ids)}}
        self._stop_to_station: dict = {}
        self._station_events: dict = {}
        self._transfer_graph: dict = {}  # leniwie budowany: kursowy + przesiadkowy


    # ------------------------------------------------------------------
    # Budowanie grafu
    # ------------------------------------------------------------------

    def build(self, day: datetime | None = None) -> "StopTimesGraph":
        """
        Buduje graf dla konkretnego dnia.

        Parametry
        ----------
        day : datetime | None
            Dzień dla którego budujemy graf.
            None → brak filtrowania po dniu (wszystkie kursy).

        Przed wywołaniem upewnij się, że dane zostały wczytane:
            main_consumer.load_data()
        """
        self._build_station_index()
        self._build_graph(day)
        return self

    def _build_station_index(self) -> None:
        """
        Buduje indeks stop_id → parent_station.

        Jeśli stop ma parent_station → używamy parent_station jako klucza węzła stacji.
        Jeśli nie ma (samodzielny) → używamy własnego stop_id.
        """
        stops_df = main_consumer.stops
        if stops_df is None:
            raise RuntimeError("Dane stops nie istnieją. Wywołaj main_consumer.load_data().")

        stop_to_station = {}
        for _, row in stops_df.iterrows():
            sid = row["stop_id"]
            parent = row["parent_station"]
            # parent_station bywa floatem (NaN lub np. 1413064.0) – normalizuj
            if parent != parent:  # NaN check (szybsze niż pd.isna)
                stop_to_station[sid] = sid
            else:
                stop_to_station[sid] = int(parent)

        self._stop_to_station = stop_to_station

    def _build_graph(self, day: datetime | None) -> None:
        """Buduje krawędzie kursowe i indeks zdarzeń na stacjach."""
        st_df = main_consumer.stop_times
        trips_df = main_consumer.trips

        if st_df is None or trips_df is None:
            raise RuntimeError("Dane nie istnieją. Wywołaj main_consumer.load_data().")

        # ── Filtrowanie po dniu (przez route_id kursów) ─────────────────────
        active_trip_ids: set | None = None
        if day is not None:
            from utils.calendar import calendar as cal
            # Pobierz aktywne route_id dla danego dnia (jeden call, z cache'em)
            active_route_ids = cal.get_all_active_routes_in_day(day)  # set of int
            # Wybierz trip_id których route_id jest aktywna
            active_trip_ids = set(
                trips_df[trips_df["route_id"].isin(active_route_ids)]["trip_id"]
            )


        # ── Sortujemy stop_times i filtrujemy aktywne kursy ─────────────────
        df = st_df.sort_values(["trip_id", "stop_sequence"]).reset_index(drop=True)
        if active_trip_ids is not None:
            df = df[df["trip_id"].isin(active_trip_ids)].reset_index(drop=True)

        arr_secs = df["arrival_time"].map(_time_to_seconds).tolist()
        dep_secs = df["departure_time"].map(_time_to_seconds).tolist()
        trip_ids = df["trip_id"].tolist()
        stop_ids = df["stop_id"].tolist()

        graph: dict = defaultdict(dict)
        edge_trips: dict = defaultdict(lambda: defaultdict(set))
        # station_events: {station_id: [(arr_sec, dep_sec, stop_id, trip_id), ...]}
        station_events: dict = defaultdict(list)

        prev_trip = None
        prev_stop = None
        prev_dep = None

        for i in range(len(trip_ids)):
            trip_id = trip_ids[i]
            stop_id = stop_ids[i]
            arr_sec = arr_secs[i]
            dep_sec = dep_secs[i]

            # Węzeł musi istnieć
            if stop_id not in graph:
                graph[stop_id] = {}
                edge_trips[stop_id] = defaultdict(set)

            # Krawędź kursowa: poprzedni → obecny
            if prev_trip == trip_id:
                weight = max(0, arr_sec - prev_dep)

                existing = graph[prev_stop].get(stop_id)
                if existing is None or weight < existing:
                    graph[prev_stop][stop_id] = weight

                edge_trips[prev_stop][stop_id].add(trip_id)

            # Zapamiętaj zdarzenie stacji (do budowania przesiadek)
            station_id = self._stop_to_station.get(stop_id, stop_id)
            station_events[station_id].append((arr_sec, dep_sec, stop_id, trip_id))

            prev_trip = trip_id
            prev_stop = stop_id
            prev_dep = dep_sec

        self._graph = dict(graph)
        self._edge_trips = {
            a: {b: frozenset(trips) for b, trips in neighbors.items()}
            for a, neighbors in edge_trips.items()
        }
        # Sortuj zdarzenia po czasie przyjazdu – przyda się przy przesiadkach
        self._station_events = {
            sid: sorted(events, key=lambda e: e[0])
            for sid, events in station_events.items()
        }

    # ------------------------------------------------------------------
    # Krawędzie przesiadkowe (generowane na żądanie)
    # ------------------------------------------------------------------

    def get_transfer_edges(self, stop_id, arrival_sec: int) -> list[tuple]:
        """
        Zwraca możliwe przesiadki z danego przystanku po przyjeździe o `arrival_sec`.

        Szuka kursów odjeżdżających ze WSZYSTKICH przystanków tej samej stacji
        (parent_station) po czasie arrival_sec.

        Zwraca listę krotek:
            (neighbor_stop_id, wait_seconds, trip_id)
            gdzie wait_seconds = departure[nowy_kurs] − arrival_sec
        """
        station_id = self._stop_to_station.get(stop_id, stop_id)
        events = self._station_events.get(station_id, [])

        transfers = []
        for arr, dep, ev_stop, ev_trip in events:
            # Kurs musi odjeżdżać po naszym przyjeździe
            # i nie może to być ten sam przystanek (to byłoby kontynuowanie kursu,
            # nie przesiadka) – ale stop_id może się różnić w obrębie tej stacji
            wait = dep - arrival_sec
            if wait >= 0 and ev_stop != stop_id:
                transfers.append((ev_stop, wait, ev_trip))

        return transfers

    # ------------------------------------------------------------------
    # Dostęp do danych
    # ------------------------------------------------------------------

    @property
    def graph(self) -> dict:
        """
        Graf z wagami = min czas przejazdu [sekundy].
        Format: {stop_id: {sąsiad: sekundy}}
        Kompatybilny z dijkstra().
        """
        self._assert_built()
        return self._graph

    @property
    def edge_trips(self) -> dict:
        """
        Krawędzie kursowe z zestawem trip_ids.
        Format: {stop_A: {stop_B: frozenset({trip_id, ...})}}
        Używany przez dijkstra_min_transfers().
        """
        self._assert_built()
        return self._edge_trips

    @property
    def station_events(self) -> dict:
        """
        Zdarzenia na stacjach do obsługi przesiadek.
        Format: {station_id: [(arr_sec, dep_sec, stop_id, trip_id), ...]}
        """
        self._assert_built()
        return self._station_events

    @property
    def graph_with_transfers(self) -> dict:
        """
        Graf rozszerzony: krawędzie kursowe + krawędzie przesiadkowe.

        Pozwala zwykłej dijkstra() znajdować trasy wymagające przesiadki.
        Waga krawędzi przesiadkowej = MINIMALNY czas oczekiwania
        między danym pař przystanków na tej samej stacji,
        liczony pośród wszystkich możliwych połączeń
        (min dep[T2] − arr[T1] > 0).

        Graf jest buforowany (liczony tylko raz po build()).
        """
        self._assert_built()
        if self._transfer_graph:
            return self._transfer_graph

        import copy
        # Zacznij od kopii grafu kursowego
        extended: dict = {stop: dict(nb) for stop, nb in self._graph.items()}

        # Iteruj po stacjach z wieloma przystankami
        for station_id, events in self._station_events.items():
            # Zbierz unikalne stop_id na tej stacji
            stops_at_station = {ev_stop for _, _, ev_stop, _ in events}
            if len(stops_at_station) < 2:
                continue   # stacja ma tylko jeden przystanek – brak przesiadek

            # Dla każdej pary (stop_A → stop_B) na tej stacji
            # policz minimalny czas oczekiwania spośród wszystkich kombinacji
            # arr[T1 na stop_A] i dep[T2 na stop_B] gdzie dep[T2] > arr[T1]
            for stop_a in stops_at_station:
                arr_times_A = [
                    arr for arr, dep, ev_stop, ev_trip in events
                    if ev_stop == stop_a
                ]
                for stop_b in stops_at_station:
                    if stop_a == stop_b:
                        continue
                    dep_times_B = [
                        dep for arr, dep, ev_stop, ev_trip in events
                        if ev_stop == stop_b
                    ]
                    # Znajdź minimalny dodatni czas oczekiwania
                    min_wait = float("inf")
                    for arr_a in arr_times_A:
                        for dep_b in dep_times_B:
                            wait = dep_b - arr_a
                            if 0 < wait < min_wait:
                                min_wait = wait

                    if min_wait < float("inf"):
                        # Dodaj krawędź przesiadkową jeśli lepsza niż istniejąca
                        existing = extended.get(stop_a, {}).get(stop_b)
                        if existing is None or min_wait < existing:
                            extended.setdefault(stop_a, {})[stop_b] = min_wait

        self._transfer_graph = extended
        return self._transfer_graph

    def neighbors(self, stop_id) -> dict:
        """Sąsiedzi przystanku z wagami czasowymi (tylko krawędzie kursowe)."""
        return self._graph.get(stop_id, {})

    def _assert_built(self):
        if not self._graph:
            raise RuntimeError("Graf jest pusty. Wywołaj najpierw build().")

    def __len__(self) -> int:
        return len(self._graph)

    def __repr__(self) -> str:
        edges = sum(len(v) for v in self._graph.values())
        return f"StopTimesGraph(węzły={len(self._graph)}, krawędzie={edges})"
