from decimal import Decimal

import pytest

from parking.domain.enums import LoyaltyTier
from parking.domain.models import Money
from parking.policies.base import PricingPolicy
from parking.services.billing_engine import (
    BillingEngine,
    NoApplicablePolicyError,
)


class TestSpecConflictScenario:
    """
    The exact scenario from the spec's 'Conflict Resolution: Best Value Logic':
    A Car enters on a weekday at 6:30 AM and leaves at 4:00 PM. The session
    satisfies both Standard Hourly and Early Bird; the minimum fare wins.
    """

    @pytest.fixture
    def result(self, make_session):
        session = make_session("2024-03-05T06:30", "2024-03-05T16:00")  # Tuesday
        return BillingEngine.with_active_policies().calculate(session)

    def test_early_bird_wins_over_standard(self, result):
        assert result.amount == Money(Decimal("15.00"))
        assert result.applied_policy == "EarlyBirdPolicy"

    def test_standard_was_evaluated_at_31(self, result):
        # 7.50 + 4.50 + 3.00 + 3.00 + (5 * 2.00) + 3.00 = 31.00
        standard = next(
            q for q in result.quotes if q.policy_name == "StandardHourlyPolicy"
        )
        assert standard.amount == Money(Decimal("31.00"))

    def test_night_owl_evaluated_but_not_applicable(self, result):
        night_owl = next(
            q for q in result.quotes if q.policy_name == "NightOwlPolicy"
        )
        assert night_owl.amount is None

    def test_all_three_policies_are_exhaustively_evaluated(self, result):
        assert [q.policy_name for q in result.quotes] == [
            "StandardHourlyPolicy",
            "EarlyBirdPolicy",
            "NightOwlPolicy",
        ]


class TestBestValueSelection:
    def test_standard_wins_when_no_special_applies(self, make_session):
        session = make_session("2024-03-05T11:00", "2024-03-05T12:00")
        result = BillingEngine.with_active_policies().calculate(session)
        assert result.amount == Money(Decimal("5.00"))
        assert result.applied_policy == "StandardHourlyPolicy"

    def test_discounted_early_bird_beats_standard(self, make_session):
        session = make_session(
            "2024-03-05T06:30", "2024-03-05T16:00", tier=LoyaltyTier.GOLD
        )
        result = BillingEngine.with_active_policies().calculate(session)
        # Early Bird GOLD: 15 * 0.80 = 12.00 < Standard 31.00
        assert result.amount == Money(Decimal("12.00"))
        assert result.applied_policy == "EarlyBirdPolicy"

    def test_night_owl_beats_standard(self, make_session):
        session = make_session("2024-03-05T18:30", "2024-03-06T06:30")
        result = BillingEngine.with_active_policies().calculate(session)
        # Night Owl 8.00 < Standard 30.50 (7.50 + 3.00 + 10 * 2.00)
        assert result.amount == Money(Decimal("8.00"))
        assert result.applied_policy == "NightOwlPolicy"


class TestExtendedStays:
    def test_over_24_hours_falls_back_to_standard_exclusively(self, make_session):
        # 25 hours: Tue 06:30 -> Wed 07:30. Both specials must be invalid.
        session = make_session("2024-03-05T06:30", "2024-03-06T07:30")
        result = BillingEngine.with_active_policies().calculate(session)

        assert result.applied_policy == "StandardHourlyPolicy"
        # 9 peak blocks (Tue morning x4, Tue evening x4, Wed morning x1)
        # = 7.50 + 4.50 + 7*3.00 ; 16 off-peak blocks = 16 * 2.00 -> 65.00
        assert result.amount == Money(Decimal("65.00"))
        assert all(
            q.amount is None
            for q in result.quotes
            if q.policy_name != "StandardHourlyPolicy"
        )


class StubPolicyA(PricingPolicy):
    def calculate(self, session):
        return Money(Decimal("10.00"))


class StubPolicyB(PricingPolicy):
    def calculate(self, session):
        return Money(Decimal("10.00"))


class NeverApplicablePolicy(PricingPolicy):
    def calculate(self, session):
        return None


class TestEngineBehavior:
    def test_fare_ties_are_broken_deterministically_by_registration_order(
        self, make_session
    ):
        session = make_session("2024-03-05T11:00", "2024-03-05T12:00")
        engine = BillingEngine((StubPolicyB(), StubPolicyA()))
        result = engine.calculate(session)
        assert result.applied_policy == "StubPolicyB"  # first registered wins

    def test_raises_when_no_policy_applies(self, make_session):
        session = make_session("2024-03-05T11:00", "2024-03-05T12:00")
        engine = BillingEngine((NeverApplicablePolicy(),))
        with pytest.raises(NoApplicablePolicyError):
            engine.calculate(session)

    def test_requires_at_least_one_policy(self):
        with pytest.raises(ValueError):
            BillingEngine(())