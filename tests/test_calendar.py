"""
Tests for utils/calendar.py - Calendar class.

Uses real GTFS data (data/*.txt) without modifying it.
All service_id / route_id values are sourced directly from the actual files.
"""

import pytest
from datetime import datetime
import sys
import os
import importlib

# ---------------------------------------------------------------------------
# Import strategy
#
# calendar.py uses a relative import:  from ..data_consumer import main_consumer
# That requires the repo root to be a Python package.  Empty __init__.py files
# exist in AI/, AI/utils/, and AI/tests/.  We insert the *parent* of the repo
# root into sys.path so that `AI` is importable as a top-level package, then
# patch CalendarModule.main_consumer (the binding inside the calendar module's
# own namespace) with a fully-loaded DataConsumer before Calendar() is built.
# ---------------------------------------------------------------------------

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPO_PARENT = os.path.abspath(os.path.join(REPO_ROOT, ".."))
PACKAGE_NAME = os.path.basename(REPO_ROOT)  # "AI"

# REPO_PARENT pozwala importować AI.utils.calendar (stary styl)
if REPO_PARENT not in sys.path:
    sys.path.insert(0, REPO_PARENT)

# REPO_ROOT jest potrzebny bo calendar.py używa: from data_consumer import ...
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

dc_module = importlib.import_module(f"{PACKAGE_NAME}.data_consumer")
DataConsumer = dc_module.DataConsumer

CalendarModule = importlib.import_module(f"{PACKAGE_NAME}.utils.calendar")
Calendar = CalendarModule.Calendar



# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def calendar():
    """Load real GTFS data once and return a ready Calendar instance."""
    data_dir = os.path.join(REPO_ROOT, "data")
    consumer = DataConsumer(data_dir=data_dir)
    consumer.load_data()
    # Patch the local name binding inside calendar.py's namespace
    CalendarModule.main_consumer = consumer
    return Calendar()


# ---------------------------------------------------------------------------
# Test dates – derived from actual data files
#
# calendar.txt earliest start_date: 20260225
#
# Services from data/calendar.txt:
#   1_396994  : monday-sunday=1  20260225–20260307  (every day)
#   10_397004 : saturday=1, sunday=1, others=0;  20260225–20260307
#   33_397029 : saturday=1, sunday=1, others=0;  20260225–20260307
#
# Trips from data/trips.txt:
#   route_id 234088 ← service_id 1_396994  (and many others)
#   route_id 234089 ← service_id 33_397029 (and others)
#
# Exceptions from data/calendar_dates.txt for date 20260309 (Monday):
#   33_397029    exception_type=1  → added on that day
#   2808_400204  exception_type=2  → removed on that day
# ---------------------------------------------------------------------------

DATE_PRE_SCHEDULE    = datetime(2026, 2, 1)   # Sunday before any service starts
WEEKDAY_IN_RANGE     = datetime(2026, 3, 5)   # Thursday – inside first schedule block
SATURDAY_IN_RANGE    = datetime(2026, 3, 7)   # Saturday – inside first schedule block
DATE_WITH_EXCEPTIONS = datetime(2026, 3, 9)   # Monday – has calendar_dates entries


# ===========================================================================
# Tests for get_Active_service_id_for_day
# ===========================================================================

class TestGetActiveServiceIdForDay:

    def test_return_type_is_list(self, calendar):
        result = calendar.get_Active_service_id_for_day(WEEKDAY_IN_RANGE)
        assert isinstance(result, list)

    def test_empty_before_schedule_starts(self, calendar):
        """No services have start_date <= 20260201, so result must be []."""
        result = calendar.get_Active_service_id_for_day(DATE_PRE_SCHEDULE)
        assert result == []

    def test_all_day_service_active_on_thursday(self, calendar):
        """Service 1_396994 runs every day 20260225–20260307 → present on Thu."""
        result = calendar.get_Active_service_id_for_day(WEEKDAY_IN_RANGE)
        assert "1_396994" in result

    def test_weekend_service_absent_on_thursday(self, calendar):
        """Service 10_397004 (sat+sun only) must NOT appear on Thursday."""
        result = calendar.get_Active_service_id_for_day(WEEKDAY_IN_RANGE)
        assert "10_397004" not in result

    def test_weekend_service_present_on_saturday(self, calendar):
        """Service 10_397004 (sat+sun) must appear on Saturday."""
        result = calendar.get_Active_service_id_for_day(SATURDAY_IN_RANGE)
        assert "10_397004" in result

    def test_exception_type1_adds_service(self, calendar):
        """
        33_397029 has exception_type=1 for 20260309 in calendar_dates.txt.
        Even if not in the regular schedule for Monday, it must be included.
        """
        result = calendar.get_Active_service_id_for_day(DATE_WITH_EXCEPTIONS)
        assert "33_397029" in result

    def test_exception_type2_removes_service(self, calendar):
        """
        2808_400204 has exception_type=2 for 20260309 in calendar_dates.txt.
        It must NOT appear in the active set on that day.
        """
        result = calendar.get_Active_service_id_for_day(DATE_WITH_EXCEPTIONS)
        assert "2808_400204" not in result

    def test_no_duplicate_service_ids(self, calendar):
        """Each service_id should appear at most once in the returned list."""
        result = calendar.get_Active_service_id_for_day(WEEKDAY_IN_RANGE)
        assert len(result) == len(set(result))


# ===========================================================================
# Tests for get_routes_for_services
# ===========================================================================

class TestGetRoutesForServices:

    def test_empty_input_returns_empty_list(self, calendar):
        assert calendar.get_routes_for_services([]) == []

    def test_return_type_is_list(self, calendar):
        result = calendar.get_routes_for_services(["1_396994"])
        assert isinstance(result, list)

    def test_known_service_maps_to_correct_route(self, calendar):
        """Service 1_396994 appears on route 234088 in trips.txt."""
        result = [str(r) for r in calendar.get_routes_for_services(["1_396994"])]
        assert "234088" in result

    def test_second_known_service_maps_to_correct_route(self, calendar):
        """Service 33_397029 appears on route 234089 in trips.txt."""
        result = [str(r) for r in calendar.get_routes_for_services(["33_397029"])]
        assert "234089" in result

    def test_unknown_service_returns_empty(self, calendar):
        assert calendar.get_routes_for_services(["NO_SUCH_SERVICE_XYZ"]) == []

    def test_multiple_services_yield_union_of_routes(self, calendar):
        """Combined call must return at least the union of individual calls."""
        r1 = {str(r) for r in calendar.get_routes_for_services(["1_396994"])}
        r2 = {str(r) for r in calendar.get_routes_for_services(["33_397029"])}
        combined = {str(r) for r in calendar.get_routes_for_services(["1_396994", "33_397029"])}
        assert combined >= r1 | r2

    def test_no_duplicate_route_ids(self, calendar):
        """The method uses .unique() so no route_id must appear twice."""
        result = calendar.get_routes_for_services(["1_396994"])
        assert len(result) == len(set(result))

    def test_list_of_services_returns_nonempty(self, calendar):
        """Several real service IDs should yield a non-empty route list."""
        services = ["1_396994", "2_396995", "3_396996", "33_397029", "13_397007"]
        result = calendar.get_routes_for_services(services)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_single_trip_service_returns_its_route(self, calendar):
        """Service 13_397007 (trips.txt) maps to route 234088."""
        result = [str(r) for r in calendar.get_routes_for_services(["13_397007"])]
        assert "234088" in result


# ===========================================================================
# Tests for get_all_active_routes_in_day
# ===========================================================================

class TestGetAllActiveRoutesInDay:

    def test_return_type_is_set(self, calendar):
        result = calendar.get_all_active_routes_in_day(WEEKDAY_IN_RANGE)
        assert isinstance(result, set)

    def test_pre_schedule_returns_empty_set(self, calendar):
        result = calendar.get_all_active_routes_in_day(DATE_PRE_SCHEDULE)
        assert isinstance(result, set)
        assert len(result) == 0

    def test_route_234088_active_on_weekday(self, calendar):
        """Route 234088 should be active on a Thursday in range."""
        result = {str(r) for r in calendar.get_all_active_routes_in_day(WEEKDAY_IN_RANGE)}
        assert "234088" in result

    def test_caching_returns_same_object(self, calendar):
        """Two calls with the same date must return the exact same set object."""
        r1 = calendar.get_all_active_routes_in_day(WEEKDAY_IN_RANGE)
        r2 = calendar.get_all_active_routes_in_day(WEEKDAY_IN_RANGE)
        assert r1 is r2

    def test_different_dates_produce_different_results(self, calendar):
        """
        Weekday vs Saturday – weekend-only services differ, so the sets
        must not be identical.
        """
        weekday = calendar.get_all_active_routes_in_day(WEEKDAY_IN_RANGE)
        saturday = calendar.get_all_active_routes_in_day(SATURDAY_IN_RANGE)
        assert isinstance(weekday, set)
        assert isinstance(saturday, set)
        assert weekday != saturday


# ===========================================================================
# Tests for check_if_route_is_active_on_day
# ===========================================================================

class TestCheckIfRouteIsActiveOnDay:

    def test_return_type_is_bool(self, calendar):
        # Use a route in its correct representation (int or str) by peeking at cache
        active = calendar.get_all_active_routes_in_day(WEEKDAY_IN_RANGE)
        sample = next(iter(active))
        route_id = type(sample)(234088)
        result = calendar.check_if_route_is_active_on_day(route_id, WEEKDAY_IN_RANGE)
        assert isinstance(result, bool)

    def test_known_route_active_on_weekday(self, calendar):
        """Route 234088 must be active on 2026-03-05 (Thursday)."""
        active = calendar.get_all_active_routes_in_day(WEEKDAY_IN_RANGE)
        sample = next(iter(active))
        route_id = type(sample)(234088)
        assert calendar.check_if_route_is_active_on_day(route_id, WEEKDAY_IN_RANGE) is True

    def test_nonexistent_route_returns_false(self, calendar):
        """A route_id that doesn't exist in any trip must return False."""
        assert calendar.check_if_route_is_active_on_day("NO_SUCH_ROUTE_XYZ", WEEKDAY_IN_RANGE) is False

    def test_pre_schedule_returns_false(self, calendar):
        """Before the schedule starts no route should be reported as active."""
        assert calendar.check_if_route_is_active_on_day(234088, DATE_PRE_SCHEDULE) is False

    def test_consistent_with_get_all_active_routes(self, calendar):
        """Every route from get_all_active_routes_in_day must pass the check."""
        active = calendar.get_all_active_routes_in_day(WEEKDAY_IN_RANGE)
        for route in active:
            assert calendar.check_if_route_is_active_on_day(route, WEEKDAY_IN_RANGE) is True
