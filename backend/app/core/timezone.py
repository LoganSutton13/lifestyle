from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def validate_timezone(value: str) -> str:
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        msg = "Invalid timezone"
        raise ValueError(msg) from exc
    return value


def date_range_to_utc_bounds(start: date, end: date, timezone: str) -> tuple[datetime, datetime]:
    tz = ZoneInfo(timezone)
    start_dt = datetime.combine(start, time.min, tzinfo=tz).astimezone(UTC)
    end_dt = datetime.combine(end, time.max, tzinfo=tz).astimezone(UTC)
    return start_dt, end_dt


def default_date_range(timezone: str, days: int = 30) -> tuple[date, date]:
    now = datetime.now(ZoneInfo(timezone))
    end = now.date()
    start = end - timedelta(days=days)
    return start, end
