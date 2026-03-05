from data_consumer import main_consumer
from datetime import datetime

class Calendar:
    def __init__(self):
        self._calendar_data = None
        self._calendar_exception = None
        self._trips_data = None
        self._day_cache = {}

    def _ensure_loaded(self):
        """Ładuje dane z main_consumer przy pierwszym użyciu (lazy init)."""
        if self._calendar_data is None:
            self._calendar_data = main_consumer.calendar
            self._calendar_exception = main_consumer.calendar_dates
            self._trips_data = main_consumer.trips
            if self._calendar_data is None:
                raise RuntimeError(
                    "Dane nie zostały wczytane. Wywołaj main_consumer.load_data() przed użyciem Calendar."
                )

    @property
    def calendar_data(self):
        self._ensure_loaded()
        return self._calendar_data

    @property
    def calendar_exception(self):
        self._ensure_loaded()
        return self._calendar_exception

    @property
    def trips_data(self):
        self._ensure_loaded()
        return self._trips_data


    _DAY_ABBR_TO_FULL = {
        'mon': 'monday', 'tue': 'tuesday', 'wed': 'wednesday',
        'thu': 'thursday', 'fri': 'friday', 'sat': 'saturday', 'sun': 'sunday',
    }

    def get_Active_service_id_for_day(self, day: datetime):
        day_val = int(day.strftime('%Y%m%d'))
        day_name = self._DAY_ABBR_TO_FULL[day.strftime('%a').lower()]
        
        mask = (
            (self.calendar_data['start_date'].astype(int) <= day_val) & 
            (self.calendar_data['end_date'].astype(int) >= day_val)
        )
        
        regular = self.calendar_data[mask & (self.calendar_data[day_name] == 1)]['service_id'].tolist()
        
        exceptions = self.calendar_exception[self.calendar_exception['date'].astype(int) == day_val]
        
        added = exceptions[exceptions['exception_type'] == 1]['service_id'].unique().tolist()
        removed = set(exceptions[exceptions['exception_type'] == 2]['service_id'])
        
        active_services = (set(regular) | set(added)) - removed
        
        return list(active_services)

    def get_routes_for_services(self, service_ids: list):
        if not service_ids:
            return []
            
        return self.trips_data[
            self.trips_data['service_id'].isin(service_ids)
        ]['route_id'].unique().tolist()

    def get_all_active_routes_in_day(self, day: datetime):
        cache_key = day.strftime('%Y%m%d')
        
        if cache_key not in self._day_cache:
            active_services = self.get_Active_service_id_for_day(day)
            self._day_cache[cache_key] = set(self.get_routes_for_services(active_services))
            
        return self._day_cache[cache_key]

    def check_if_route_is_active_on_day(self, route_id, day: datetime):
        active_routes = self.get_all_active_routes_in_day(day)
        # active_routes zawiera int-y (z pandas), route_id może być str lub int
        try:
            return int(route_id) in active_routes
        except (ValueError, TypeError):
            return route_id in active_routes


calendar = Calendar()