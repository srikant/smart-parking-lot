from datetime import time
from decimal import Decimal

from parking.domain.models import Money, TimeWindow
from parking.policies.flat_rate import FlatRateSpecialPolicy


class AnyTimePolicy(FlatRateSpecialPolicy):
    """
    Test double with full-day windows and no day constraint,
    so the >24h eligibility guard can be verified in isolation.
    """

    def __init__(self) -> None:
        super().__init__(
            base_car_rate=Money(Decimal("10.00")),
            entry_window=TimeWindow(start=time(0, 0), end=time.max),
            exit_window=TimeWindow(start=time(0, 0), end=time.max),
        )

    def _matches_day_constraint(self, session):
        return True


def test_stay_of_exactly_24_hours_is_still_eligible(make_session):
    session = make_session("2024-03-05T00:00", "2024-03-06T00:00")
    assert AnyTimePolicy().calculate(session) == Money(Decimal("10.00"))


def test_stay_over_24_hours_invalidates_special(make_session):
    session = make_session("2024-03-05T00:00", "2024-03-06T00:00:01")
    assert AnyTimePolicy().calculate(session) is None