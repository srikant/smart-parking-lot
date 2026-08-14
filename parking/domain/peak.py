from datetime import datetime, time, timedelta

from parking.domain.calendar import Calendar
from parking.domain.models import TimeWindow


class PeakHourDetector:
    """
    Determines whether an hourly block overlaps any peak window.

    Peak windows: 07:00-10:00 and 16:00-19:00 (half-open: start inclusive,
    end exclusive), weekdays only. A block is 'peak' if ANY part of it
    falls within a window on a weekday (partial-overlap rule). Handles
    blocks that cross midnight by evaluating each touched calendar day.
    """

    def __init__(self, calendar: Calendar) -> None:
        self._calendar = calendar
        self._windows = [
            TimeWindow(start=time(7, 0), end=time(10, 0)),
            TimeWindow(start=time(16, 0), end=time(19, 0)),
        ]

    def is_peak(self, block_start: datetime, block_end: datetime) -> bool:
        day = block_start.date()
        last_day = block_end.date()
        while day <= last_day:
            if self._calendar.is_weekday(day) and self._overlaps_peak_on_day(
                block_start, block_end, day
            ):
                return True
            day += timedelta(days=1)
        return False

    def _overlaps_peak_on_day(
        self, block_start: datetime, block_end: datetime, day
    ) -> bool:
        day_start = datetime.combine(day, time(0, 0))
        day_end_exclusive = datetime.combine(day + timedelta(days=1), time(0, 0))

        seg_start = max(block_start, day_start)
        seg_end = min(block_end, day_end_exclusive)
        if seg_start >= seg_end:
            return False

        for window in self._windows:
            peak_start = datetime.combine(day, window.start)
            peak_end = datetime.combine(day, window.end)
            if seg_start < peak_end and seg_end > peak_start:
                return True
        return False