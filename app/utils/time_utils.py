from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

BUENOS_AIRES_TZ = ZoneInfo("America/Argentina/Buenos_Aires")


def get_calendar_week_bounds(
    dt: datetime | None = None,
) -> tuple[datetime, datetime]:
    """Lunes 00:00:00 a domingo 23:59:59.999999 de la semana calendario de dt.

    Naive datetimes se interpretan como hora de pared de Buenos Aires
    (así se almacenan en las columnas DateTime del proyecto).
    """
    tz = BUENOS_AIRES_TZ

    if dt is None:
        reference = datetime.now(tz)
    elif dt.tzinfo is None:
        reference = dt.replace(tzinfo=tz)
    else:
        reference = dt.astimezone(tz)

    monday_date = reference.date() - timedelta(days=reference.weekday())
    week_start = datetime.combine(monday_date, time.min, tzinfo=tz)
    week_end = week_start + timedelta(days=7) - timedelta(microseconds=1)
    return week_start, week_end
