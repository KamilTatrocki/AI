from ..data_consumer import main_consumer
import math

class Stops:
    def __init__(self):
        self.data = main_consumer.stops

    def calculate_distance_between_station(self, stop_id):
        """
        return {"stop_id": distance}
        """
        stop = self.data[self.data['stop_id'] == stop_id]
        if stop.empty:
            raise ValueError(f"Stop with id {stop_id} not found.")
        
        stop_lat = stop['stop_lat'].values[0]
        stop_lon = stop['stop_lon'].values[0]

        res = {}
        
        for index, row in self.data.iterrows():
            if row['stop_id'] != stop_id:
                distance = self.__calculate_distance_based_on_lan_lat(stop_lat, row['stop_lat'], stop_lon, row['stop_lon'])
                res[row['stop_id']] = distance
                
        return res

    def __calculate_distance_based_on_lan_lat(self, lat1, lat2, lon1, lon2):
        #aproksymacji euklidesowej na rzutowanych współrzednych
        earth_radius = 6371000
    
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        mean_phi = (phi1 + phi2) / 2
        
        x = delta_lambda * math.cos(mean_phi)
        y = delta_phi
        
        return math.sqrt(x**2 + y**2) * earth_radius
    