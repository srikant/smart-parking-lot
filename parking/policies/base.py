from abc import ABC, abstractmethod
from typing import Optional

from parking.domain.models import Money, ParkingSession


class PricingPolicy(ABC):
    """
    Strategy interface for all rate policies.

    Contract: return the fare if the policy applies to the session,
    or None if the policy is not applicable. The BillingEngine is
    responsible for selecting the lowest valid fare across policies.
    """

    @abstractmethod
    def calculate(self, session: ParkingSession) -> Optional[Money]:
        raise NotImplementedError