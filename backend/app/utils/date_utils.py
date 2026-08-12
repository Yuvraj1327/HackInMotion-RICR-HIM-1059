from datetime import date, timedelta
from typing import List


def date_range(start: date, days: int) -> List[date]:
    """Return `days` consecutive dates starting the day AFTER `start`."""
    return [start + timedelta(days=i + 1) for i in range(days)]


def is_weekend(d: date) -> bool:
    return d.weekday() >= 5  # Saturday=5, Sunday=6


def days_between(a: date, b: date) -> int:
    return (b - a).days
