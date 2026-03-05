from ..data_consumer import main_consumer
from datetime import datetime

class Calendar:
    def __init__(self):
        self.calendar_data = main_consumer.calendar
        self.calendar_exception = main_consumer.calendar_dates
    
    def get_stops_in_proper_day(self, day: datetime):
        """
        return service_id list maybe? but than i will have to connect via trips.txt get route_id bcs stops have only route_id
        """
        pass