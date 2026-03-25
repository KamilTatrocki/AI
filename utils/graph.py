import pandas as pd
from collections import defaultdict
from .calendar import Calendar

class Edge:
    def __init__(self, from_stop, to_stop, departure_time_sec, arrival_time_sec, route_short_name, route_long_name, route_id, service_id, trip_id):
        self.from_stop = from_stop
        self.to_stop = to_stop
        self.departure_time_sec = departure_time_sec
        self.arrival_time_sec = arrival_time_sec
        self.travel_time = arrival_time_sec - departure_time_sec
        self.route_short_name = route_short_name
        self.route_long_name = route_long_name
        self.route_id = route_id
        self.service_id = service_id
        self.trip_id = trip_id

    def __repr__(self):
        name = self.route_short_name if pd.notna(self.route_short_name) else self.route_long_name
        return f"Edge({self.from_stop} -> {self.to_stop}, route={name}, trip={self.trip_id})"

class Graph:
    def __init__(self, data_consumer):
        self.data_consumer = data_consumer
        self.nodes = {}
        self.adjacency_list = defaultdict(list)
        self.parent_station_map = defaultdict(list)
        
        self.build_nodes()
        self.build_edges()
        
    def build_nodes(self):
        """przystanek lub peron"""
        for _, row in self.data_consumer.stops.iterrows():
            stop_id = row['stop_id']
            parent_station = row['parent_station'] if pd.notna(row['parent_station']) else stop_id
            
            self.nodes[stop_id] = {
                'stop_name': row['stop_name'],
                'stop_lat': row['stop_lat'],
                'stop_lon': row['stop_lon'],
                'parent_station': parent_station
            }
            self.parent_station_map[parent_station].append(stop_id)

    def build_edges(self):
        """połączenia bezpośrednie"""
        stops_times_df = self.data_consumer.stop_times.copy()
        trips_df = self.data_consumer.trips[['trip_id', 'route_id', 'service_id']].copy()
        routes_df = self.data_consumer.routes[['route_id', 'route_short_name', 'route_long_name']].copy()

        trips_routes = trips_df.merge(routes_df, on='route_id', how='left')
        st_merged = stops_times_df.merge(trips_routes, on='trip_id', how='left')
        st_merged = st_merged.sort_values(by=['trip_id', 'stop_sequence'])

        st_merged['next_stop_id'] = st_merged.groupby('trip_id')['stop_id'].shift(-1)
        st_merged['next_arrival_time'] = st_merged.groupby('trip_id')['arrival_time'].shift(-1)

        edges_df = st_merged.dropna(subset=['next_stop_id']).copy()
        edges_df = edges_df[edges_df['pickup_type'] == 0]
        
        def convert_time(t):
            try:
                h, m, s = map(int, str(t).split(':'))
                return h * 3600 + m * 60 + s
            except:
                return 0
                
        edges_df['departure_time_sec'] = edges_df['departure_time'].apply(convert_time)
        edges_df['arrival_time_sec'] = edges_df['next_arrival_time'].apply(convert_time)
        
        for row in edges_df.to_dict('records'):
            edge = Edge(
                from_stop=row['stop_id'],
                to_stop=row['next_stop_id'],
                departure_time_sec=row['departure_time_sec'],
                arrival_time_sec=row['arrival_time_sec'],
                route_short_name=row['route_short_name'],
                route_long_name=row['route_long_name'],
                route_id=row['route_id'],
                service_id=row['service_id'],
                trip_id=row['trip_id']
            )
            self.adjacency_list[row['stop_id']].append(edge)

    def get_related_stops_for_transfers(self, stop_id):
        """
        Zwraca listę przystanków, do których można dojść w ramach tego samego parenta
        """
        if stop_id not in self.nodes:
            return []
        parent = self.nodes[stop_id]['parent_station']
        transfers = [s for s in self.parent_station_map[parent] if s != stop_id]
        return transfers
        
 