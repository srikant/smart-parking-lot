from datetime import time
from decimal import Decimal

from parking.domain.models import Money, ParkingSession, TimeWindow
from parking.policies.flat_rate import FlatRateSpecialPolicy


class EarlyBirdPolicy(FlatRateSpecialPolicy):
    """
    Commuter special: entry 06:00-09:00, exit 15:30-19:00, same calendar day.
    Flat $15.00 car rate, subject to vehicle multiplier and loyalty discount.
    """

    def __init__(self) -> None:
        super().__init__(
            base_car_rate=Money(Decimal("15.00")),
            entry_window=TimeWindow(start=time(6, 0), end=time(9, 0)),
            exit_window=TimeWindow(start=time(15, 30), end=time(19, 0)),
        )

    def _matches_day_constraint(self, session: ParkingSession) -> bool:
        return session.is_same_day