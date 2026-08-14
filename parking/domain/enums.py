from enum import Enum
from decimal import Decimal

class VehicleType(Enum):
    MOTORCYCLE = Decimal('0.8')
    CAR = Decimal('1.0')
    BUS = Decimal('2.0')

    @property
    def multiplier(self) -> Decimal:
        return self.value

class LoyaltyTier(Enum):
    NONE = Decimal('0.00')
    SILVER = Decimal('0.10')
    GOLD = Decimal('0.20')
    PLATINUM = Decimal('0.30')

    @property
    def discount_rate(self) -> Decimal:
        return self.value