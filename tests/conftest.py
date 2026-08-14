from datetime import datetime

import pytest

from parking.domain.enums import LoyaltyTier, VehicleType
from parking.domain.models import ParkingSession, Ticket, Vehicle


@pytest.fixture
def make_session():
    def _make(entry: str, exit_: str, vehicle_type=VehicleType.CAR, tier=LoyaltyTier.NONE):
        return ParkingSession(
            ticket=Ticket(
                entry_time=datetime.fromisoformat(entry),
                vehicle=Vehicle(type=vehicle_type),
            ),
            exit_time=datetime.fromisoformat(exit_),
            loyalty_tier=tier,
        )
    return _make