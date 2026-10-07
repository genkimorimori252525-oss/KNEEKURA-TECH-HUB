# Bedrock Wither Reconstruction — Acceptance

The acceptance target is **behavioral equivalence within declared scenarios**, not hidden-code equivalence.

## Acceptance tiers

### R0 — build and identity

- Forge 1.20.1 / Java 17 build succeeds.
- `kneekura:bedrock_wither` registers independently from `minecraft:wither`.
- vanilla Java Wither remains unchanged.
- save/load does not corrupt phase/state.
- dedicated-server classloading contains no client-only references.

### R1 — official exposed behavior

Must pass before community-derived combat details are accepted:
- airborne navigation is functional
- target distance contract uses the accepted Bedrock range
- threat ledger can prioritize the entity that dealt the most damage
- three head targets/rotations are independently synchronized
- dangerous and normal skull paths are distinguishable

### R2 — phase 1 behavior

For each difficulty:
- accepted max health matches measured Bedrock reference
- no unapproved Java Wither regeneration leaks in
- reference target-reposition scenario matches within declared spatial/timing tolerance
- burst sequence matches measured skull count/order
- health-dependent cadence matches measured reference points
- damage reaction reproduces accepted block-destruction and dangerous-skull behavior

### R3 — transition and phase 2

- transition fires exactly once at the accepted health boundary
- accepted explosion timing/strength behavior is reproduced
- skeleton summon count and Easy exception match measurement
- projectile immunity boundary matches measurement
- dash direction, duration and speed meet scenario tolerance
- dash destruction volume/origin/timing match measurement
- dash cannot create an unbounded block-destruction loop after target invalidation

### R4 — death and persistence

- death sequence and explosion match the accepted Bedrock scenario
- boss bar and state clean up on removal
- save/reload in safe persistent states resumes consistently
- reload during transient attack states follows documented recovery semantics

### R5 — Tank comparative acceptance

Run paired scenarios:
1. Java vanilla Wither control
2. KNEEKURA Bedrock Wither
3. Bedrock reference observation

Compare:
- health/time series
- state-transition ticks
- position/velocity series
- skull spawn ticks/types/origins
- target IDs
- destruction bounding boxes and counts
- summoned entity count/type
- damage acceptance/rejection
- boss death timing

Screenshots/video are supporting evidence, not the sole pass criterion.

## Required test types

### Pure/unit/state tests
- state transition table
- one-shot 50% transition latch
- difficulty health selection
- threat ledger ordering/expiry
- burst sequencer
- dash timeout
- persistence recovery

### Forge GameTests
- phase transition
- summon count by difficulty
- projectile immunity
- phase-1 destruction fixture
- dash destruction fixture
- unbreakable block fixture
- target invalidation during dash
- death cleanup

### Real client/Tank
- three-head aim
- hover/reposition shape
- dash appearance and trajectory
- shield/armor visibility
- skull visual distinction
- boss bar behavior
- before/after regression captures

## Comparison tolerances

Tolerance must be scenario-specific and fixed before the run.

Examples:
- tick timing: exact where deterministic; otherwise declared ±N ticks from measured Bedrock variance
- position: declared block/vector tolerance
- destruction: exact set when deterministic, otherwise exact bounding volume plus explained block exceptions
- entity count: exact
- projectile type/order: exact once reference measurement is stable

Do not widen tolerances after seeing a failed result without creating a new scenario revision.

## Failure policy

A failed or ambiguous runtime result is retained as FAIL/UNKNOWN. It does not trigger automatic behavior changes.

Every repair records:
- observed mismatch
- source/reference scenario
- cause
- code change
- before/after evidence
- regression scope

Use the existing KNEEKURA Failure/Repair History format for implementation incidents.

## First milestone definition of done

Milestone BWR-M1 is complete when a standalone boss can be spawned and, in bounded tests, demonstrates:

- difficulty-aware health
- explicit highest-damage threat targeting
- phase-1 controlled skull burst with normal/dangerous distinction
- one-time 50% phase transition
- configured transition explosion/skeleton summon candidate
- phase-2 projectile immunity
- bounded target-directed dash
- separate dash destruction controller
- debug state export suitable for Tank observation

Exact cadence and destruction dimensions may remain `TBD_MEASURE` in M1 if they are parameterized and clearly not claimed as Bedrock-accurate.

BWR-M2 begins only after direct Bedrock measurements replace the critical TBD values.
