from decimal import Decimal

import pytest

from parking.domain.enums import VehicleType
from parking.domain.models import Money
from parking.domain.peak import PeakHourDetector
from parking.policies.standard_hourly import StandardHourlyPolicy


@pytest.fixture
def policy():
    return StandardHourlyPolicy()


class TestSpecExample:
    def test_weekday_morning_peak_two_hours(self, policy, make_session):
        # The worked example from the spec: $7.50 + $4.50 = $12.00
        session = make_session("2024-03-05T06:30", "2024-03-05T08:30")
        assert policy.calculate(session) == Money(Decimal("12.00"))


class TestProgressiveRates:
    def test_single_off_peak_hour(self, policy, make_session):
        session = make_session("2024-03-05T11:00", "2024-03-05T12:00")
        assert policy.calculate(session) == Money(Decimal("5.00"))

    def test_two_hours_off_peak(self, policy, make_session):
        # 5 + 3 = 8
        session = make_session("2024-03-05T11:00", "2024-03-05T13:00")
        assert policy.calculate(session) == Money(Decimal("8.00"))

    def test_three_hours_off_peak(self, policy, make_session):
        # 5 + 3 + 2 = 10
        session = make_session("2024-03-05T11:00", "2024-03-05T14:00")
        assert policy.calculate(session) == Money(Decimal("10.00"))

    def test_four_hours_off_peak(self, policy, make_session):
        # 5 + 3 + 2 + 2 = 12
        session = make_session("2024-03-05T11:00", "2024-03-05T15:00")
        assert policy.calculate(session) == Money(Decimal("12.00"))


class TestRoundingUp:
    def test_partial_hour_rounds_up(self, policy, make_session):
        # 1h1m -> 2 blocks -> 5 + 3 = 8 (off-peak)
        session = make_session("2024-03-05T11:00", "2024-03-05T12:01")
        assert policy.calculate(session) == Money(Decimal("8.00"))

    def test_rounded_up_block_catches_peak(self, policy, make_session):
        # 30-min stay 06:30-07:00 -> rounded block 06:30-07:30 overlaps peak
        # -> 5 * 1.5 = 7.50 (documents the floating-block interpretation)
        session = make_session("2024-03-05T06:30", "2024-03-05T07:00")
        assert policy.calculate(session) == Money(Decimal("7.50"))


class TestPeakWindows:
    def test_evening_peak_two_hours(self, policy, make_session):
        # Wed 16:30-18:30 -> both blocks peak: 7.5 + 4.5 = 12
        session = make_session("2024-03-06T16:30", "2024-03-06T18:30")
        assert policy.calculate(session) == Money(Decimal("12.00"))

    def test_entry_exactly_at_peak_end_is_off_peak(self, policy, make_session):
        # Wed 10:00-11:00 -> morning peak ended (exclusive) -> 5.00
        session = make_session("2024-03-06T10:00", "2024-03-06T11:00")
        assert policy.calculate(session) == Money(Decimal("5.00"))

    def test_weekend_has_no_peak_surcharge(self, policy, make_session):
        # Sat 08:00-09:00 would be peak on a weekday -> 5.00 flat
        session = make_session("2024-03-09T08:00", "2024-03-09T09:00")
        assert policy.calculate(session) == Money(Decimal("5.00"))


class TestVehicleMultipliers:
    def test_bus_off_peak(self, policy, make_session):
        session = make_session("2024-03-05T11:00", "2024-03-05T12:00", VehicleType.BUS)
        assert policy.calculate(session) == Money(Decimal("10.00"))  # 5 * 2

    def test_motorcycle_peak(self, policy, make_session):
        # Wed 08:00-09:00 peak: 5 * 1.5 * 0.8 = 6.00
        session = make_session("2024-03-06T08:00", "2024-03-06T09:00", VehicleType.MOTORCYCLE)
        assert policy.calculate(session) == Money(Decimal("6.00"))

    def test_bus_peak_two_hours(self, policy, make_session):
        # weekday 06:30-08:30: (7.5 + 4.5) * 2 = 24.00
        session = make_session("2024-03-05T06:30", "2024-03-05T08:30", VehicleType.BUS)
        assert policy.calculate(session) == Money(Decimal("24.00"))


class TestMultiDay:
    def test_multi_day_progressive_without_peak(self, make_session):
        # Inject an always-off-peak calendar to verify progressive rates over 26h:
        # 5 + 3 + (24 * 2) = 56
        class NeverPeakCalendar:
            def is_weekday(self, day):
                return False

        policy = StandardHourlyPolicy(PeakHourDetector(NeverPeakCalendar()))
        session = make_session("2024-03-05T11:00", "2024-03-06T13:00")  # 26 hours
        assert policy.calculate(session) == Money(Decimal("56.00"))