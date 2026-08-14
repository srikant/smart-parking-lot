from datetime import time
from decimal import Decimal

from parking.domain.models import Money, ParkingSession, TimeWindow
from parking.policies.flat_rate import FlatRateSpecialPolicy


class NightOwlPolicy(FlatRateSpecialPolicy):
    """
    Overnight special: entry 18:00-23:59:59, exit 05:00-10:00,
    next consecutive calendar day. Flat $8.00 car rate.
    """

    def __init__(self) -> None:
        super().__init__(
            base_car_rate=Money(Decimal("8.00")),
            entry_window=TimeWindow(start=time(18, 0), end=time.max),
            exit_window=TimeWindow(start=time(5, 0), end=time(10, 0)),
        )

    def _matches_day_constraint(self, session: ParkingSession) -> bool:
        return session.is_consecutive_day