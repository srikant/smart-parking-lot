from datetime import date
from typing import Protocol


class Calendar(Protocol):
    """Abstraction over day classification so holiday rules can be injected."""

    def is_weekday(self, day: date) -> bool: ...


class StandardCalendar:
    """
    Monday-Friday are weekdays.

    The spec excludes public holidays but supplies no holiday calendar,
    so holidays are treated as ordinary weekdays (documented assumption).
    Swap in a holiday-aware implementation via the Calendar protocol if needed.
    """

    def is_weekday(self, day: date) -> bool:
        return day.weekday() < 5  # Monday=0 ... Friday=4