import os
import pandas as pd

class DataConsumer:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.agency = None
        self.routes = None
        self.stops = None
        self.trips = None
        self.stop_times = None
        self.calendar = None
        self.calendar_dates = None
        self.feed_info = None

    def load_data(self):
        self.agency = pd.read_csv(os.path.join(self.data_dir, "agency.txt"))
        self.routes = pd.read_csv(os.path.join(self.data_dir, "routes.txt"))
        self.stops = pd.read_csv(os.path.join(self.data_dir, "stops.txt"))
        self.trips = pd.read_csv(os.path.join(self.data_dir, "trips.txt"))
        self.stop_times = pd.read_csv(os.path.join(self.data_dir, "stop_times.txt"))
        self.calendar = pd.read_csv(os.path.join(self.data_dir, "calendar.txt"))
        self.calendar_dates = pd.read_csv(os.path.join(self.data_dir, "calendar_dates.txt"))
        self.feed_info = pd.read_csv(os.path.join(self.data_dir, "feed_info.txt"))

    def print_info(self):
        print("Agency:")
        print(self.agency.head())
        print("\nRoutes:")
        print(self.routes.head())
        print("\nStops:")
        print(self.stops.head())
        print("\nTrips:")
        print(self.trips.head())
        print("\nStop Times:")
        print(self.stop_times.head())
        print("\nCalendar:")
        print(self.calendar.head())
        print("\nCalendar Dates:")
        print(self.calendar_dates.head())
        print("\nFeed Info:")
        print(self.feed_info.head())

        
if __name__ == "__main__":
    consumer = DataConsumer()
    consumer.load_data()
    consumer.print_info()