from datetime import datetime, time, timedelta 
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from .enums import VehicleType, LoyaltyTier

@dataclass(frozen=True)
class Money:
    """
    Value Object representing currency. 
    Uses Decimal to avoid floating-point inaccuracies.
    """
    amount: Decimal

    def __add__(self, other: 'Money') -> 'Money':
        if not isinstance(other, Money):
            raise TypeError("Can only add Money to Money")
        return Money(self.amount + other.amount)

    def __mul__(self, multiplier: Decimal) -> 'Money':
        # Quantize to 2 decimal places using standard rounding
        new_amount = (self.amount * multiplier).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return Money(new_amount)

    def __lt__(self, other: 'Money') -> bool:
        if not isinstance(other, Money):
            raise TypeError("Can only compare Money to Money")
        return self.amount < other.amount

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return False
        return self.amount == other.amount

    def __repr__(self) -> str:
        return f"${self.amount:.2f}"

@dataclass(frozen=True)
class Vehicle:
    type: VehicleType

@dataclass(frozen=True)
class Ticket:
    entry_time: datetime
    vehicle: Vehicle

@dataclass(frozen=True)
class TimeWindow:
    """
    Value Object: a half-open time-of-day window [start, end).

    Half-open intervals avoid boundary double-counting.
    End-of-day is represented with datetime.time.max.
    """
    start: time  # inclusive
    end: time    # exclusive

    def contains(self, moment: datetime) -> bool:
        t = moment.time()
        return self.start <= t < self.end


@dataclass(frozen=True)
class ParkingSession:
    ticket: Ticket
    exit_time: datetime
    loyalty_tier: LoyaltyTier = LoyaltyTier.NONE

    @property
    def duration(self) -> timedelta:
        return self.exit_time - self.ticket.entry_time

    @property
    def is_same_day(self) -> bool:
        return self.ticket.entry_time.date() == self.exit_time.date()

    @property
    def is_consecutive_day(self) -> bool:
        return (self.exit_time.date() - self.ticket.entry_time.date()).days == 1

    def __post_init__(self) -> None:
        if self.exit_time < self.ticket.entry_time:
            raise ValueError("exit_time must not precede ticket entry_time")