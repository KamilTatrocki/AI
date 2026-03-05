from ..data_consumer import main_consumer
from datetime import datetime

class Calendar:
    def __init__(self):
        self.calendar_data = main_consumer.calendar
        self.calendar_exception = main_consumer.calendar_dates
        self.trips_data = main_consumer.trips

        self._day_cache = {}
    
    def get_Active_service_id_for_day(self, day: datetime):
        """
        return list service_id check if it is correct TODO vibecoded
        """
        day_val = int(day.strftime('%Y%m%d'))
        day_name = day.strftime('%A').lower()
        
        regular = self.calendar_data[
            (self.calendar_data['start_date'].astype(int) <= day_val) & 
            (self.calendar_data['end_date'].astype(int) >= day_val) & 
            (self.calendar_data[day_name] == 1)
        ]['service_id'].tolist()
        
        exceptions = self.calendar_exception[self.calendar_exception['date'].astype(int) == day_val]
        
        added = exceptions[exceptions['exception_type'] == 1]['service_id'].tolist()
        removed = exceptions[exceptions['exception_type'] == 2]['service_id'].tolist()
        
        active_services = set(regular + added) - set(removed)
        
        return list(active_services)
    
    def get_routes_for_services(self, service_ids: list):
        active_routes = self.trips_data[
            self.trips_data['service_id'].isin(service_ids)
        ]['route_id'].unique().tolist()
        
        return active_routes

    def get_all_active_routes_in_day(self, day: datetime):
        active_services = self.get_Active_service_id_for_day(day)
        return self.get_routes_for_services(active_services)
    
    def check_if_route_is_active_on_day(self, route_id: str, day: datetime):
        active_routes = self.get_all_active_routes_in_day(day)
        return route_id in active_routes