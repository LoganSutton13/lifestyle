from datetime import date

import pytest

from app.services.task_recurrence import task_occurs_on_date


def test_daily_every_day() -> None:
    active_from = date(2026, 7, 1)
    assert task_occurs_on_date(active_from, None, "daily", 1, [], date(2026, 7, 1))
    assert task_occurs_on_date(active_from, None, "daily", 1, [], date(2026, 7, 2))
    assert task_occurs_on_date(active_from, None, "daily", 1, [], date(2026, 7, 10))


def test_daily_every_other_day() -> None:
    active_from = date(2026, 7, 1)
    assert task_occurs_on_date(active_from, None, "daily", 2, [], date(2026, 7, 1))
    assert not task_occurs_on_date(active_from, None, "daily", 2, [], date(2026, 7, 2))
    assert task_occurs_on_date(active_from, None, "daily", 2, [], date(2026, 7, 3))


def test_weekly_wednesday() -> None:
    active_from = date(2026, 7, 1)  # Wednesday
    days = [2]
    assert task_occurs_on_date(active_from, None, "weekly", 1, days, date(2026, 7, 1))
    assert not task_occurs_on_date(active_from, None, "weekly", 1, days, date(2026, 7, 2))
    assert task_occurs_on_date(active_from, None, "weekly", 1, days, date(2026, 7, 8))


def test_biweekly_wednesday() -> None:
    active_from = date(2026, 7, 1)  # Wednesday
    days = [2]
    assert task_occurs_on_date(active_from, None, "weekly", 2, days, date(2026, 7, 1))
    assert not task_occurs_on_date(active_from, None, "weekly", 2, days, date(2026, 7, 8))
    assert task_occurs_on_date(active_from, None, "weekly", 2, days, date(2026, 7, 15))


def test_weekly_anchor_when_active_from_not_on_selected_day() -> None:
    active_from = date(2026, 7, 7)  # Tuesday
    days = [2]  # Wednesday
    assert not task_occurs_on_date(active_from, None, "weekly", 1, days, date(2026, 7, 7))
    assert task_occurs_on_date(active_from, None, "weekly", 1, days, date(2026, 7, 8))
    assert task_occurs_on_date(active_from, None, "weekly", 1, days, date(2026, 7, 15))


def test_weekly_multiple_days() -> None:
    active_from = date(2026, 7, 6)  # Monday
    days = [0, 2, 4]
    assert task_occurs_on_date(active_from, None, "weekly", 1, days, date(2026, 7, 6))
    assert not task_occurs_on_date(active_from, None, "weekly", 1, days, date(2026, 7, 7))
    assert task_occurs_on_date(active_from, None, "weekly", 1, days, date(2026, 7, 8))


def test_before_active_from() -> None:
    active_from = date(2026, 7, 5)
    assert not task_occurs_on_date(active_from, None, "daily", 1, [], date(2026, 7, 4))


def test_after_active_until() -> None:
    active_from = date(2026, 7, 1)
    active_until = date(2026, 7, 10)
    assert task_occurs_on_date(active_from, active_until, "daily", 1, [], date(2026, 7, 10))
    assert not task_occurs_on_date(active_from, active_until, "daily", 1, [], date(2026, 7, 11))
