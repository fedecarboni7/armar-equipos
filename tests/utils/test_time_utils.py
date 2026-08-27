from datetime import datetime
from zoneinfo import ZoneInfo

from app.utils.time_utils import get_calendar_week_bounds

BA_TZ = ZoneInfo("America/Argentina/Buenos_Aires")
UTC = ZoneInfo("UTC")


def test_mid_week_returns_monday_to_sunday_bounds():
    wednesday = datetime(2026, 8, 19, 15, 30, 45, tzinfo=BA_TZ)

    start, end = get_calendar_week_bounds(wednesday)

    assert start == datetime(2026, 8, 17, 0, 0, 0, 0, tzinfo=BA_TZ)
    assert end == datetime(2026, 8, 23, 23, 59, 59, 999999, tzinfo=BA_TZ)


def test_sunday_belongs_to_its_week_and_next_monday_starts_new_one():
    sunday_night = datetime(2026, 8, 23, 22, 0, tzinfo=BA_TZ)
    start_sunday, _ = get_calendar_week_bounds(sunday_night)
    assert start_sunday == datetime(2026, 8, 17, 0, 0, tzinfo=BA_TZ)

    monday_morning = datetime(2026, 8, 24, 0, 0, tzinfo=BA_TZ)
    start_monday, _ = get_calendar_week_bounds(monday_morning)
    assert start_monday == monday_morning


def test_naive_input_treated_as_buenos_aires_wall_time():
    naive_monday_midnight = datetime(2026, 8, 17, 0, 0)

    start, _ = get_calendar_week_bounds(naive_monday_midnight)

    assert start == datetime(2026, 8, 17, 0, 0, tzinfo=BA_TZ)


def test_naive_input_is_not_interpreted_as_utc():
    # Si se interpretara como UTC y se convirtiera a BA, caeria el domingo
    # anterior (21:00) y devolveria la semana previa.
    naive_monday_midnight = datetime(2026, 8, 17, 0, 0)

    start, _ = get_calendar_week_bounds(naive_monday_midnight)

    assert start.date().isoformat() == "2026-08-17"


def test_aware_input_in_other_timezone_converts_to_buenos_aires():
    utc_equivalent = datetime(2026, 8, 19, 18, 30, tzinfo=UTC)

    start, end = get_calendar_week_bounds(utc_equivalent)

    assert start == datetime(2026, 8, 17, 0, 0, 0, 0, tzinfo=BA_TZ)
    assert end == datetime(2026, 8, 23, 23, 59, 59, 999999, tzinfo=BA_TZ)


def test_sunday_last_microsecond_and_monday_first_microsecond_differ():
    sunday_end = datetime(2026, 8, 23, 23, 59, 59, 999999, tzinfo=BA_TZ)
    monday_start = datetime(2026, 8, 24, 0, 0, 0, 0, tzinfo=BA_TZ)

    _, end_of_week = get_calendar_week_bounds(sunday_end)
    start_of_week, _ = get_calendar_week_bounds(monday_start)

    assert end_of_week == sunday_end
    assert start_of_week == monday_start
    assert start_of_week > end_of_week
