# Bedrock Wither Reconstruction — Acceptance

Updated completion boundary: 2026-10-03. The user chose **source-backed software completion without empirical Bedrock measurements**. The required target is a functioning standalone boss whose ordinary code paths satisfy the declared, version-labelled reconstruction policies and automated regression tests. This is not a claim of experimentally demonstrated Bedrock equivalence.

`SOURCE-COMPLETION-PLAN-2026-10-03.md` controls current execution. Earlier empirical comparisons remain optional research, outside this completion pass.

## Acceptance tiers

### R0 — build and identity

- Forge 1.20.1 / Java 17 build succeeds.
- `kneekura_bedrock_wither:bedrock_wither` registers independently from `minecraft:wither`.
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
- max health matches the accepted source-backed 300/450/600 difficulty policy
- no unapproved Java Wither regeneration leaks in
- ordinary entity ticking reaches bounded target-relative repositioning, hover and firing using declared source-derived/adaptation parameters
- ordinary projectiles follow the accepted 3-normal/1-dangerous sequence
- health-dependent cadence follows its explicitly version-labelled rule; per-shot and inter-volley delays are independent
- damage reaction reproduces accepted block-destruction and dangerous-skull behavior

### R3 — transition and phase 2

- transition fires exactly once at the accepted health boundary
- accepted explosion timing/strength behavior is reproduced
- skeleton summon count is three on Normal/Hard and zero on Easy
- projectile immunity follows the declared second-phase boundary
- ordinary phase-2 volleys reach preparation, bounded target-directed dash and recovery using the documented policy
- dash destruction follows the accepted 6×8×6 candidate geometry and attack-specific block rules
- dash cannot create an unbounded block-destruction loop after target invalidation

### R4 — death and persistence

- accepted semantic death enters the documented provisional visual countdown/explosion exactly once and preserves Forge events/rewards
- boss bar and state clean up on removal
- save/reload in safe persistent states resumes consistently
- reload during transient attack states follows documented recovery semantics

### R5 — optional empirical comparison, not executed or required

The original paired-scenario proposal is retained below for historical context. The user has chosen not to run measurements; do not schedule these as completion prerequisites. If separately requested in the future, the proposal would compare:
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

### Optional real client/Tank evidence, not performed
- three-head aim
- hover/reposition shape
- dash appearance and trajectory
- shield/armor visibility
- skull visual distinction
- boss bar behavior
- before/after regression captures

## Optional future comparison tolerances

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

All required ordinary M1 paths must execute; neutral controller boundaries waiting for measurements do not count as implemented behavior. Uncertain values must instead have an explicit, bounded source-derived/adaptation policy, provenance and tests.

Complete source-backed acceptance additionally requires real projectile collision/effect paths, consistent liquid inertia, safe owner/reflection handling, synchronized presentation inputs and reload recovery. Headless tests establish these software contracts, not pixel appearance or exact Bedrock native internals.

The original measurement-gated BWR-M2 endpoint is superseded for this request. No new empirical phase or optional compatibility/replacement layer is implied by software completion.
