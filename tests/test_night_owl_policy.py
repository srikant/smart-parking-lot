from decimal import Decimal

import pytest

from parking.domain.enums import LoyaltyTier, VehicleType
from parking.domain.models import Money
from parking.policies.night_owl import NightOwlPolicy


@pytest.fixture
def policy():
    return NightOwlPolicy()


class TestApplicability:
    def test_applies_for_valid_overnight_window(self, policy, make_session):
        session = make_session("2024-03-05T20:00", "2024-03-06T07:00")
        assert policy.calculate(session) == Money(Decimal("8.00"))

    def test_entry_at_1800_is_inclusive(self, policy, make_session):
        session = make_session("2024-03-05T18:00", "2024-03-06T07:00")
        assert policy.calculate(session) is not None

    def test_entry_before_1800_is_not_applicable(self, policy, make_session):
        session = make_session("2024-03-05T17:59", "2024-03-06T07:00")
        assert policy.calculate(session) is None

    def test_entry_at_235959_is_applicable(self, policy, make_session):
        session = make_session("2024-03-05T23:59:59", "2024-03-06T07:00")
        assert policy.calculate(session) is not None

    def test_exit_at_5am_is_inclusive(self, policy, make_session):
        session = make_session("2024-03-05T20:00", "2024-03-06T05:00")
        assert policy.calculate(session) is not None

    def test_exit_before_5am_is_not_applicable(self, policy, make_session):
        session = make_session("2024-03-05T20:00", "2024-03-06T04:59")
        assert policy.calculate(session) is None

    def test_exit_at_10am_is_exclusive(self, policy, make_session):
        session = make_session("2024-03-05T20:00", "2024-03-06T10:00")
        assert policy.calculate(session) is None

    def test_exit_two_days_later_is_not_applicable(self, policy, make_session):
        session = make_session("2024-03-05T20:00", "2024-03-07T07:00")
        assert policy.calculate(session) is None

    def test_applies_on_weekends(self, policy, make_session):
        # Assumption: specials are not restricted to weekdays.
        session = make_session("2024-03-09T21:00", "2024-03-10T06:00")  # Sat -> Sun
        assert policy.calculate(session) == Money(Decimal("8.00"))


class TestFareCalculation:
    def test_bus_with_gold_loyalty(self, policy, make_session):
        # 8 * 2.0 * 0.80 = 12.80
        session = make_session(
            "2024-03-05T20:00", "2024-03-06T07:00", VehicleType.BUS, LoyaltyTier.GOLD
        )
        assert policy.calculate(session) == Money(Decimal("12.80"))

    def test_motorcycle_with_platinum_loyalty(self, policy, make_session):
        # 8 * 0.8 * 0.70 = 4.48
        session = make_session(
            "2024-03-05T20:00", "2024-03-06T07:00", VehicleType.MOTORCYCLE, LoyaltyTier.PLATINUM
        )
        assert policy.calculate(session) == Money(Decimal("4.48"))