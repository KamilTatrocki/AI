from data_consumer import main_consumer
from datetime import datetime

class Calendar:
    def __init__(self):
        self.calendar_data = main_consumer.calendar
        self.calendar_exception = main_consumer.calendar_dates
        self.trips_data = main_consumer.trips
        self._day_cache = {}
        self._service_cache = {}

    _DAY_ABBR_TO_FULL = {
        'mon': 'monday', 'tue': 'tuesday', 'wed': 'wednesday',
        'thu': 'thursday', 'fri': 'friday', 'sat': 'saturday', 'sun': 'sunday',
    }

    def get_Active_service_id_for_day(self, day: datetime):
        cache_key = day.strftime('%Y%m%d')
        if cache_key in self._service_cache:
            return self._service_cache[cache_key]
            
        day_val = int(cache_key)
        day_name = self._DAY_ABBR_TO_FULL[day.strftime('%a').lower()]
        
        mask = (
            (self.calendar_data['start_date'].astype(int) <= day_val) & 
            (self.calendar_data['end_date'].astype(int) >= day_val)
        )
        
        regular = self.calendar_data[mask & (self.calendar_data[day_name] == 1)]['service_id'].tolist()
        
        exceptions = self.calendar_exception[self.calendar_exception['date'].astype(int) == day_val]
        
        added = exceptions[exceptions['exception_type'] == 1]['service_id'].unique().tolist()
        removed = set(exceptions[exceptions['exception_type'] == 2]['service_id'])
        
        active_services = list((set(regular) | set(added)) - removed)
        self._service_cache[cache_key] = active_services
        
        return active_services



    # def check_if_route_is_active_on_day(self, route_id: str, day: datetime):
    #     active_routes = self.get_all_active_routes_in_day(day)
    #     return route_id in active_routes

    def check_if_service_is_active_on_day(self, service_id: str, day: datetime):
        active_services = self.get_Active_service_id_for_day(day)
        return service_id in active_services