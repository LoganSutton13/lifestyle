from datetime import date, timedelta

from app.api.error_handlers import ValidationError

VALID_FREQUENCIES = frozenset({"daily", "weekly"})
WEEKDAY_MIN = 0
WEEKDAY_MAX = 6


def validate_recurrence(frequency: str, interval: int, days: list[int]) -> None:
    if frequency not in VALID_FREQUENCIES:
        raise ValidationError("recurrenceFrequency must be 'daily' or 'weekly'")
    if interval < 1:
        raise ValidationError("recurrenceInterval must be at least 1")
    if frequency == "weekly":
        if not days:
            raise ValidationError("recurrenceDays must include at least one weekday for weekly tasks")
        for day in days:
            if day < WEEKDAY_MIN or day > WEEKDAY_MAX:
                raise ValidationError("recurrenceDays values must be between 0 (Monday) and 6 (Sunday)")


def normalize_recurrence_days(frequency: str, days: list[int]) -> list[int]:
    if frequency == "daily":
        return []
    return sorted(set(days))


def task_occurs_on_date(
    active_from: date,
    active_until: date | None,
    frequency: str,
    interval: int,
    days: list[int],
    target_date: date,
) -> bool:
    if target_date < active_from:
        return False
    if active_until is not None and target_date > active_until:
        return False

    if frequency == "daily":
        return (target_date - active_from).days % interval == 0

    if frequency == "weekly":
        if target_date.weekday() not in days:
            return False
        anchor = active_from
        while anchor.weekday() != target_date.weekday():
            anchor += timedelta(days=1)
        if anchor > target_date:
            return False
        weeks_since = (target_date - anchor).days // 7
        return weeks_since % interval == 0

    return False
