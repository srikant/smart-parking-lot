from abc import ABC, abstractmethod
from datetime import timedelta
from decimal import Decimal
from typing import Optional

from parking.domain.enums import LoyaltyTier
from parking.domain.models import Money, ParkingSession, TimeWindow
from parking.policies.base import PricingPolicy

# Specials are strictly restricted to single-day or consecutive overnight stays.
MAX_SPECIAL_STAY = timedelta(hours=24)


class FlatRateSpecialPolicy(PricingPolicy, ABC):
    """
    Template for flat-rate specials (Early Bird, Night Owl).

    Encapsulates what is common: the >24h eligibility cap, time-window
    validation, vehicle multiplier, and loyalty discount application.
    Subclasses supply what varies: windows, base rate, day constraint.
    """

    def __init__(
        self,
        base_car_rate: Money,
        entry_window: TimeWindow,
        exit_window: TimeWindow,
    ) -> None:
        self._base_car_rate = base_car_rate
        self._entry_window = entry_window
        self._exit_window = exit_window

    def calculate(self, session: ParkingSession) -> Optional[Money]:
        if not self.is_applicable(session):
            return None
        fare = self._base_car_rate * session.ticket.vehicle.type.multiplier
        return self._apply_loyalty_discount(fare, session.loyalty_tier)

    def is_applicable(self, session: ParkingSession) -> bool:
        # Critical edge case: stays > 24h invalidate all specials.
        if session.duration > MAX_SPECIAL_STAY:
            return False
        if not self._entry_window.contains(session.ticket.entry_time):
            return False
        if not self._exit_window.contains(session.exit_time):
            return False
        return self._matches_day_constraint(session)

    @abstractmethod
    def _matches_day_constraint(self, session: ParkingSession) -> bool:
        """Calendar-day relationship between entry and exit."""

    @staticmethod
    def _apply_loyalty_discount(fare: Money, tier: LoyaltyTier) -> Money:
        return fare * (Decimal("1.00") - tier.discount_rate)