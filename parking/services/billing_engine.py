from dataclasses import dataclass
from typing import Optional, Sequence

from parking.domain.models import Money, ParkingSession
from parking.policies.base import PricingPolicy
from parking.policies.early_bird import EarlyBirdPolicy
from parking.policies.night_owl import NightOwlPolicy
from parking.policies.standard_hourly import StandardHourlyPolicy


class NoApplicablePolicyError(Exception):
    """Raised when no registered policy yields a valid fare for a session."""


@dataclass(frozen=True)
class FareQuote:
    """
    One policy's evaluation of a session.
    amount is None when the policy was evaluated but does not apply.
    """
    policy_name: str
    amount: Optional[Money]


@dataclass(frozen=True)
class FareResult:
    """Final charge plus the full audit trail of policy evaluations."""
    amount: Money
    applied_policy: str
    quotes: Sequence[FareQuote]


class BillingEngine:
    """
    Exhaustively evaluates all registered rate policies against a parking
    session and applies the Best Value Logic: the minimum derived fare wins.

    The engine is policy-agnostic (Open/Closed Principle): new policies can
    be registered without modifying this class. The >24h invalidation of
    specials is enforced inside the policies themselves, so the engine
    naturally falls back to Standard Hourly for extended stays.
    """

    def __init__(self, policies: Sequence[PricingPolicy]) -> None:
        if not policies:
            raise ValueError("BillingEngine requires at least one pricing policy")
        self._policies = tuple(policies)

    @classmethod
    def with_active_policies(cls) -> "BillingEngine":
        """Wires the three active policies from the spec, in spec order."""
        return cls((StandardHourlyPolicy(), EarlyBirdPolicy(), NightOwlPolicy()))

    def calculate(self, session: ParkingSession) -> FareResult:
        quotes = tuple(
            FareQuote(
                policy_name=type(policy).__name__,
                amount=policy.calculate(session),
            )
            for policy in self._policies
        )

        applicable = [quote for quote in quotes if quote.amount is not None]
        if not applicable:
            raise NoApplicablePolicyError(
                f"No pricing policy applicable to session: {session!r}"
            )

        # min() is stable: on exact fare ties, the first registered policy wins.
        best = min(applicable, key=lambda quote: quote.amount)
        return FareResult(
            amount=best.amount,
            applied_policy=best.policy_name,
            quotes=quotes,
        )