from datetime import datetime
from parking.domain.enums import LoyaltyTier, VehicleType
from parking.domain.models import ParkingSession, Ticket, Vehicle
from parking.services.billing_engine import BillingEngine


def quote(entry, exit_, vehicle_type=VehicleType.CAR, tier=LoyaltyTier.NONE):
    session = ParkingSession(
        ticket=Ticket(
            entry_time=datetime.fromisoformat(entry),
            vehicle=Vehicle(type=vehicle_type),
        ),
        exit_time=datetime.fromisoformat(exit_),
        loyalty_tier=tier,
    )
    result = BillingEngine.with_active_policies().calculate(session)

    print(f"{entry} -> {exit_} | {vehicle_type.name}, {tier.name}")
    print(f"  CHARGED: {result.amount} via {result.applied_policy}")
    for q in result.quotes:
        status = str(q.amount) if q.amount is not None else "not applicable"
        print(f"    - {q.policy_name}: {status}")
    print()


# Spec's exact conflict scenario: Early Bird $15 beats Standard $31
quote("2024-03-05T06:30", "2024-03-05T16:00")

# Spec's worked example: Standard peak hours -> $12.00
quote("2024-03-05T06:30", "2024-03-05T08:30")

# Night Owl overnight -> $8.00
quote("2024-03-05T18:30", "2024-03-06T06:30")

# Bus + GOLD loyalty, Early Bird -> $24.00
quote("2024-03-05T06:30", "2024-03-05T16:00", VehicleType.BUS, LoyaltyTier.GOLD)