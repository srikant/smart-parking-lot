import math
from datetime import timedelta
from decimal import Decimal
from typing import Optional

from parking.domain.calendar import StandardCalendar
from parking.domain.models import Money, ParkingSession
from parking.domain.peak import PeakHourDetector
from parking.policies.base import PricingPolicy

PEAK_MULTIPLIER = Decimal("1.5")
FIRST_HOUR_RATE = Money(Decimal("5.00"))
SECOND_HOUR_RATE = Money(Decimal("3.00"))
SUBSEQUENT_HOUR_RATE = Money(Decimal("2.00"))


class StandardHourlyPolicy(PricingPolicy):
    """
    Progressive hourly rate with peak-hour surcharge.

    Always applicable (it is the fallback policy). Duration is rounded up to
    whole hours; each floating hourly block is individually assessed for peak
    overlap. Loyalty discounts do not apply to this policy.
    """

    def __init__(self, peak_detector: Optional[PeakHourDetector] = None) -> None:
        self._peak_detector = peak_detector or PeakHourDetector(StandardCalendar())

    def calculate(self, session: ParkingSession) -> Money:
        num_hours = self._round_up_to_hours(session.duration)
        entry = session.ticket.entry_time

        total = Money(Decimal("0.00"))
        for index in range(num_hours):
            block_start = entry + timedelta(hours=index)
            block_end = entry + timedelta(hours=index + 1)

            rate = self._rate_for_hour(index)
            if self._peak_detector.is_peak(block_start, block_end):
                rate = rate * PEAK_MULTIPLIER
            total = total + rate

        return total * session.ticket.vehicle.type.multiplier

    @staticmethod
    def _round_up_to_hours(duration: timedelta) -> int:
        return math.ceil(duration.total_seconds() / 3600)

    @staticmethod
    def _rate_for_hour(index: int) -> Money:
        if index == 0:
            return FIRST_HOUR_RATE
        if index == 1:
            return SECOND_HOUR_RATE
        return SUBSEQUENT_HOUR_RATE