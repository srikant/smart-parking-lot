from decimal import Decimal

import pytest

from parking.domain.enums import LoyaltyTier, VehicleType
from parking.domain.models import Money
from parking.policies.early_bird import EarlyBirdPolicy


@pytest.fixture
def policy():
    return EarlyBirdPolicy()


class TestApplicability:
    def test_applies_for_valid_same_day_commuter_window(self, policy, make_session):
        session = make_session("2024-03-05T06:30", "2024-03-05T16:00")
        assert policy.calculate(session) == Money(Decimal("15.00"))

    def test_entry_at_6am_is_inclusive(self, policy, make_session):
        session = make_session("2024-03-05T06:00", "2024-03-05T16:00")
        assert policy.calculate(session) is not None

    def test_entry_before_6am_is_not_applicable(self, policy, make_session):
        session = make_session("2024-03-05T05:59", "2024-03-05T16:00")
        assert policy.calculate(session) is None

    def test_entry_at_9am_is_exclusive(self, policy, make_session):
        session = make_session("2024-03-05T09:00", "2024-03-05T16:00")
        assert policy.calculate(session) is None

    def test_exit_at_1530_is_inclusive(self, policy, make_session):
        session = make_session("2024-03-05T06:30", "2024-03-05T15:30")
        assert policy.calculate(session) is not None

    def test_exit_before_1530_is_not_applicable(self, policy, make_session):
        session = make_session("2024-03-05T06:30", "2024-03-05T15:29")
        assert policy.calculate(session) is None

    def test_exit_at_1900_is_exclusive(self, policy, make_session):
        session = make_session("2024-03-05T06:30", "2024-03-05T19:00")
        assert policy.calculate(session) is None

    def test_exit_on_next_day_is_not_applicable(self, policy, make_session):
        session = make_session("2024-03-05T06:30", "2024-03-06T16:00")
        assert policy.calculate(session) is None


class TestFareCalculation:
    def test_car_base_rate(self, policy, make_session):
        session = make_session("2024-03-05T06:30", "2024-03-05T16:00")
        assert policy.calculate(session) == Money(Decimal("15.00"))

    def test_motorcycle_multiplier(self, policy, make_session):
        session = make_session("2024-03-05T06:30", "2024-03-05T16:00", VehicleType.MOTORCYCLE)
        assert policy.calculate(session) == Money(Decimal("12.00"))  # 15 * 0.8

    def test_bus_multiplier(self, policy, make_session):
        session = make_session("2024-03-05T06:30", "2024-03-05T16:00", VehicleType.BUS)
        assert policy.calculate(session) == Money(Decimal("30.00"))  # 15 * 2.0

    @pytest.mark.parametrize(
        "tier, expected",
        [
            (LoyaltyTier.SILVER, "13.50"),     # 15 * 0.90
            (LoyaltyTier.GOLD, "12.00"),       # 15 * 0.80
            (LoyaltyTier.PLATINUM, "10.50"),   # 15 * 0.70
        ],
    )
    def test_loyalty_discounts_for_car(self, policy, make_session, tier, expected):
        session = make_session("2024-03-05T06:30", "2024-03-05T16:00", tier=tier)
        assert policy.calculate(session) == Money(Decimal(expected))

    def test_multiplier_and_discount_compose(self, policy, make_session):
        # Motorcycle + SILVER: 15 * 0.8 * 0.9 = 10.80
        session = make_session(
            "2024-03-05T06:30", "2024-03-05T16:00", VehicleType.MOTORCYCLE, LoyaltyTier.SILVER
        )
        assert policy.calculate(session) == Money(Decimal("10.80"))