# Smart Parking Lot — Rate Calculator

A billing engine for a multi-level parking complex that evaluates multiple concurrent rate
policies and always charges the customer the **lowest valid fare** (Best Value Logic).

Built as a coding assignment for Sahaj. The solution prioritizes domain modelling,
explicit trade-offs, and verified correctness over feature surface area.

---

## Quick Start

**Requirements:** Python 3.10+

```bash
pip install -r requirements.txt   # installs pytest only
python -m pytest -v               # 64 tests
```

There is intentionally **no CLI or GUI**. Per the assignment instructions, the executable
specification is the unit test suite — sessions are constructed directly in tests:

```python
session = ParkingSession(
    ticket=Ticket(entry_time=datetime(2024, 3, 5, 6, 30), vehicle=Vehicle(VehicleType.CAR)),
    exit_time=datetime(2024, 3, 5, 16, 0),
    loyalty_tier=LoyaltyTier.NONE,
)
result = BillingEngine.with_active_policies().calculate(session)
# FareResult(amount=$15.00, applied_policy='EarlyBirdPolicy', quotes=...)
```

---

## Project Structure

```
smart-parking-lot/
├── conftest.py                        # makes `parking` importable without installation
├── requirements.txt                   # pytest only — no frameworks
├── parking/
│   ├── domain/                        # pure domain: no dependencies on policies/services
│   │   ├── enums.py                   # VehicleType (multipliers), LoyaltyTier (discounts)
│   │   ├── models.py                  # Money, TimeWindow, Vehicle, Ticket, ParkingSession
│   │   ├── calendar.py                # Calendar protocol + StandardCalendar (holiday seam)
│   │   └── peak.py                    # PeakHourDetector (time-overlap reasoning)
│   ├── policies/
│   │   ├── base.py                    # PricingPolicy strategy interface
│   │   ├── flat_rate.py               # shared template for Early Bird / Night Owl
│   │   ├── early_bird.py
│   │   ├── night_owl.py
│   │   └── standard_hourly.py         # progressive rates + floating peak blocks
│   └── services/
│       └── billing_engine.py          # exhaustive evaluation + Best Value selection
└── tests/                             # 64 tests; the executable specification
```

**Dependency direction is strictly one-way:** `services → policies → domain`.

---

## Architecture

```
BillingEngine (orchestration)
 │  evaluates every registered policy, selects the minimum fare
 │
 ├── StandardHourlyPolicy      progressive $5/$3/$2 rates, floating hourly blocks
 │      └── PeakHourDetector   partial-overlap + midnight-crossing peak detection
 │             └── Calendar    weekday classification (injectable holiday seam)
 │
 ├── EarlyBirdPolicy ─┐
 │                    ├── FlatRateSpecialPolicy   shared: time windows, 24h guard,
 └── NightOwlPolicy  ─┘                           vehicle multiplier, loyalty discount
```

### Key design decisions

**1. Strategy Pattern for rate policies.** Each policy implements
`PricingPolicy.calculate(session) -> Optional[Money]`, returning `None` when it does not
apply. The engine is policy-agnostic, so adding a future policy (e.g., a weekend flat
rate) requires zero changes to orchestration code (Open/Closed).

**2. Shared template for the flat-rate specials.** The spec explicitly notes that Early
Bird and Night Owl share time-window validation and loyalty logic. `FlatRateSpecialPolicy`
captures everything common (24h cap, window checks, multiplier, discount) and leaves only
the day-relationship constraint to vary (Template Method). This was the single most
effective reuse decision in the design.

**3. Behaviour separated from state.** Value objects (`Money`, `TimeWindow`) are immutable
and carry their own arithmetic. Entities (`Ticket`, `ParkingSession`) are frozen
dataclasses that expose derived facts (`duration`, `is_same_day`, `is_consecutive_day`)
rather than leaking raw dates into policy code.

**4. `Money` uses `Decimal`, never `float`.** Currency arithmetic with binary floats
produces rounding errors. `Money` centralizes rounding (`ROUND_HALF_UP`, 2dp) so every
policy benefits without repeating the logic.

**5. Half-open time windows `[start, end)`.** Peak boundaries are defined as start-inclusive,
end-exclusive. Modelling all windows as half-open intervals eliminates boundary
double-counting by construction instead of by convention.

**6. The >24h rule lives in the policies, not the engine.** The spec requires specials to
be invalidated for stays over 24 hours. Since this is a statement about *special-policy
applicability*, it is enforced inside `FlatRateSpecialPolicy.is_applicable`. Consequence:
the BillingEngine contains zero special-case code — for a 25-hour stay the specials
return `None` and Standard wins naturally. Responsibility sits with the knowledge.

**7. `FareResult` includes an audit trail.** The engine returns not just the winning fare
but every policy's quote (`None` = "evaluated, not applicable"). This is a deliberate,
slightly-beyond-minimal choice: a billing system must *explain* a charge (receipts,
disputes — the spec's "transactional integrity"). The cost is one extra dataclass; the
alternative (returning bare `Money`) was considered and rejected.

---

## Trade-offs & alternatives considered

| Decision | Chosen | Alternative considered | Why |
|---|---|---|---|
| Currency type | `Decimal` inside `Money` VO | `float` / integer cents | `Decimal` reads naturally ($15.00) and avoids float error; integer cents was a close second |
| Policy interface | `ABC` | `typing.Protocol` | ABC makes the strategy contract explicit and discoverable; structural typing buys nothing here |
| Vehicle multiplier | Applied inside each policy | Centralized in the engine | Keeps each policy a self-contained `session → fare` function; noted as a refactor candidate if a fourth policy appears (rule of three) |
| Holiday handling | Injectable `Calendar` protocol, default = Mon–Fri | Hardcoded `weekday() < 5` | Spec mentions holidays but supplies no calendar; a seam documents the gap instead of hiding it |
| Result shape | `FareResult` with quotes | Bare `Money` | Auditability outweighs one extra type (see decision 7) |
| Frameworks | None — stdlib + `dataclasses` | Pydantic for validation | Assignment forbids heavy frameworks; `dataclasses` + `frozen=True` covers the need |
| Peak detection | Dedicated `PeakHourDetector` | Inline in StandardHourlyPolicy | Partial overlap + midnight crossing is the hardest logic in the problem; isolating it makes it unit-testable in seconds |

---

## Assumptions

Where the spec was ambiguous, I made the ambiguity explicit and chose deterministic
behaviour. Each item maps to at least one test.

1. **Specials apply on all days of the week.** Only the Peak Hour Surcharge is explicitly
   weekday-restricted; Early Bird / Night Owl specify only time windows and day
   relationships. (`test_night_owl_applies_on_weekends`)
2. **Floating blocks are full rounded-up hours.** The final hourly block extends to
   `entry + N hours`, even past actual exit. Consequence: a short stay overlapping a peak
   boundary is charged peak (entry 06:30, exit 07:00 → one block 06:30–07:30 → $7.50).
   This is the literal reading of "first hour starts exactly at the vehicle's entry time
   (floating block)" combined with "rounded upward". (`test_rounded_up_block_catches_peak`)
3. **Public holidays are out of scope** — no calendar is provided. `StandardCalendar`
   treats all Mon–Fri as weekdays; a holiday-aware `Calendar` can be injected without
   touching policy code.
4. **Standard Hourly ignores loyalty tiers.** Discounts are only defined for the specials.
5. **Loyalty discount applies to the vehicle-adjusted base rate** (multiplication is
   commutative, so ordering cannot change the result — documented for determinism).
6. **Vehicle multiplier applies to the total car fare** for Standard Hourly (equivalent to
   per-hour application, simpler).
7. **End-of-day is `23:59:59.999999`** (`time.max`). Sub-microsecond precision is out of
   scope; Night Owl entry at `23:59:59` is accepted as required.
8. **Single timezone, naive datetimes.** The facility operates in one locale; DST
   transitions are out of scope.
9. **0-duration sessions bill $0.00.** No minimum charge is defined; any positive duration
   rounds up to at least one hour.
10. **Exact fare ties break deterministically** to the first registered policy
    (registration order = spec order). The customer pays the same either way.
11. **Malformed sessions fail fast.** Exit before entry raises `ValueError` at
    construction rather than silently billing $0.
12. **The >24h guard is defensive.** Under the current window/day constraints a >24h stay
    cannot actually satisfy a special's windows — the guard is implemented anyway because
    the spec mandates it, and it protects against future window changes. Verified in
    isolation via a test double.

---

## Verification

**64 unit tests**, all passing. Confidence strategy:

- **The spec's worked example is a test.** Weekday car, 06:30 → 08:30 = $7.50 + $4.50 =
  **$12.00**.
- **The spec's conflict scenario is a test.** Weekday car, 06:30 → 16:00: Standard is
  evaluated at **$31.00** (10 floating blocks: 4 morning-peak, 1 evening-peak), Early Bird
  at **$15.00**, Night Owl not applicable → engine selects **Early Bird, $15.00**.
- **Boundary saturation.** Every inclusive/exclusive edge in the spec has a paired test
  (e.g., entry at 06:00 accepted / 05:59 rejected; exit at 19:00 rejected / 18:59 accepted;
  peak block ending exactly at 10:00 not surcharged).
- **Hard logic tested in isolation.** `PeakHourDetector` has dedicated tests for partial
  overlap, midnight-crossing blocks, weekend suppression, and injected holiday calendars.
- **End-to-end engine tests** cover best-value selection, loyalty-discounted conflicts,
  the >24h fallback to Standard-only ($65.00 over 25 hours, hand-verified), deterministic
  tie-breaking, and failure modes.
- All expected fare values were **derived by hand first**, then encoded as assertions.

---

## AI Usage & Transparency

In line with the assignment's AI policy, an LLM was used as a **pairing partner** — for
exploring design alternatives, sanity-checking boundary logic, and generating first-draft
tests. The full, unedited interaction history is in
[`ai-chat-history.txt`](ai-chat-history.txt).

Judgment remained human throughout:

- Ambiguities (weekend applicability of specials, holiday handling, floating-block billing
  for short stays) were **identified and resolved by me**, then documented above.
- Every fare assertion was **hand-calculated before being encoded** — AI-generated
  expectations were never trusted blindly.
- AI-suggested abstractions were rejected where they violated YAGNI (e.g., a generic
  "rule engine" was considered and discarded in favour of three explicit policy classes).

No agents or multi-step AI workflows were used, so no additional reproducibility setup is
required beyond this repository.

---

## What I would do with more time

Deliberately out of scope for a 1–3 hour assignment, but the seams are in place:

- **Holiday calendar integration** behind the existing `Calendar` protocol.
- **Timezone-aware datetimes** with DST-safe arithmetic (the window logic is already
  isolated in one place).
- **Property-based tests** (e.g., "fare is monotonic in duration for a fixed entry time")
  to complement the example-based suite.
- A thin **adapter layer** (API/CLI) over `BillingEngine` — the domain is already
  framework-free and trivially embeddable.