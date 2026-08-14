from datetime import datetime

from parking.domain.calendar import StandardCalendar
from parking.domain.peak import PeakHourDetector


def _detector():
    return PeakHourDetector(StandardCalendar())


class TestMorningPeak:
    def test_block_fully_inside_morning_peak(self):
        # Wed 2024-03-06 08:00-09:00
        assert _detector().is_peak(datetime(2024, 3, 6, 8, 0), datetime(2024, 3, 6, 9, 0))

    def test_partial_overlap_at_peak_start(self):
        # Wed 06:30-07:30 overlaps 07:00 -> peak (partial-overlap rule)
        assert _detector().is_peak(datetime(2024, 3, 6, 6, 30), datetime(2024, 3, 6, 7, 30))

    def test_block_ending_exactly_at_peak_start_is_not_peak(self):
        # Wed 06:00-07:00 ends exactly when peak begins (exclusive boundary)
        assert not _detector().is_peak(datetime(2024, 3, 6, 6, 0), datetime(2024, 3, 6, 7, 0))

    def test_block_starting_exactly_at_peak_end_is_not_peak(self):
        # Wed 10:00-11:00 starts exactly when peak ends (exclusive boundary)
        assert not _detector().is_peak(datetime(2024, 3, 6, 10, 0), datetime(2024, 3, 6, 11, 0))


class TestEveningPeak:
    def test_block_fully_inside_evening_peak(self):
        # Wed 17:00-18:00
        assert _detector().is_peak(datetime(2024, 3, 6, 17, 0), datetime(2024, 3, 6, 18, 0))

    def test_partial_overlap_at_evening_peak_start(self):
        # Wed 15:30-16:30 overlaps 16:00 -> peak
        assert _detector().is_peak(datetime(2024, 3, 6, 15, 30), datetime(2024, 3, 6, 16, 30))


class TestOffPeak:
    def test_midday_is_not_peak(self):
        assert not _detector().is_peak(datetime(2024, 3, 6, 12, 0), datetime(2024, 3, 6, 13, 0))

    def test_night_is_not_peak(self):
        assert not _detector().is_peak(datetime(2024, 3, 6, 21, 0), datetime(2024, 3, 6, 22, 0))


class TestWeekendsAndDayBoundaries:
    def test_weekend_peak_window_is_not_peak(self):
        # Sat 2024-03-09 08:00-09:00 falls in the window but it's a weekend
        assert not _detector().is_peak(datetime(2024, 3, 9, 8, 0), datetime(2024, 3, 9, 9, 0))

    def test_block_crossing_midnight_without_peak_times(self):
        # Fri 23:30 -> Sat 00:30 touches no peak window
        assert not _detector().is_peak(datetime(2024, 3, 8, 23, 30), datetime(2024, 3, 9, 0, 30))


class TestCalendarInjection:
    def test_holiday_suppresses_peak(self):
        class NoPeakCalendar:
            def is_weekday(self, day):
                return False

        detector = PeakHourDetector(NoPeakCalendar())
        assert not detector.is_peak(datetime(2024, 3, 6, 8, 0), datetime(2024, 3, 6, 9, 0))