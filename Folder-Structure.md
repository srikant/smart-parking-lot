smart-parking-lot/
├── src/
│   ├── domain/
│   │   ├── enums.py           # VehicleType, LoyaltyTier, DayOfWeek
│   │   ├── value_objects.py   # Money, TimeWindow, Duration
│   │   └── models.py          # Vehicle, Ticket, ParkingSession
│   ├── policies/
│   │   ├── base.py            # PricingPolicy (Protocol/Interface)
│   │   ├── standard.py        # StandardHourlyPolicy (Peak logic)
│   │   ├── early_bird.py      # EarlyBirdPolicy
│   │   └── night_owl.py       # NightOwlPolicy
│   └── services/
│       └── billing_engine.py  # Orchestrator: evaluates policies, resolves conflicts
├── tests/
│   ├── test_standard_policy.py
│   ├── test_early_bird_policy.py
│   ├── test_night_owl_policy.py
│   ├── test_billing_engine.py # Conflict resolution & >24hr edge cases
│   └── conftest.py            # Shared fixtures
├── README.md                  # Setup, execution, design decisions, and assumptions
├── ai-chat-history.txt        # Transparent log of our interaction
└── requirements.txt           # Only pytest


----------------

smart-parking-lot/
├── conftest.py
├── requirements.txt
├── parking/
│   ├── __init__.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── enums.py
│   │   └── models.py
│   └── policies/
│       ├── __init__.py
│       ├── base.py
│       ├── flat_rate.py
│       ├── early_bird.py
│       └── night_owl.py
└── tests/
    ├── conftest.py
    ├── test_early_bird_policy.py
    ├── test_night_owl_policy.py
    └── test_flat_rate_special_policy.py