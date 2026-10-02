# Bedrock Wither Reconstruction — Design

Date: 2026-10-02  
ANCHOR: Minecraft Java Edition 1.20.1 / Forge 47.2.x / Java 17  
Target: a separate custom entity, tentatively `kneekura:bedrock_wither`

## Goal

Reproduce the **observable gameplay behavior** of the current Bedrock Edition Wither in Java Edition as closely as practical, without claiming access to Bedrock's closed native implementation.

The first implementation MUST NOT replace `minecraft:wither` globally. Vanilla Java Wither remains available as a control/reference and to reduce compatibility risk. A later optional replacement/spawn-routing layer may be considered only after the standalone entity is accepted.

## Evidence rule

The implementation is driven by an evidence ladder:

1. **A — official exposed behavior**: Microsoft Creator/Vanilla Behavior Pack documentation.
2. **B — maintained gameplay observation**: current Minecraft Wiki / Bedrock Wiki or equivalent, version-bound when possible.
3. **C — community report**: Reddit/forum/video. Discovery evidence only.
4. **D — direct Bedrock runtime observation**: our measured scenario with retained conditions and evidence.

A/B/C material may define a candidate behavior, but uncertain numeric constants remain `TBD_MEASURE` until runtime measurement or stronger evidence. Disagreement is retained; it is not resolved by majority vote.

## Why this is a custom entity

Java 1.20.1 `WitherBoss` already contains Java-specific server AI, private head timers, private block-breaking state and private ranged-attack helpers. Reusing it as the behavioral base would make it difficult to prove that Bedrock behavior is not contaminated by Java behavior.

Therefore the target architecture is:

```
BedrockWitherEntity extends Monster
    |
    +-- BedrockWitherStateMachine
    +-- BedrockWitherTargeting
    +-- BedrockWitherFlightController
    +-- BedrockWitherAttackController
    +-- BedrockWitherDashController
    +-- BedrockWitherDestructionController
    +-- BedrockWitherPhaseController
    +-- BedrockWitherBossEvent
    +-- BedrockWitherPersistence
```

Client side:

```
BedrockWitherRenderer
BedrockWitherModel
BedrockWitherArmorLayer
```

Projectile implementation should prefer the vanilla Wither Skull entity/mechanics where they match the observed Bedrock contract, but dangerous/blue-skull selection, cadence and ownership remain controlled by the new boss. Any mismatch becomes an explicit adaptation rather than silently inheriting Java boss AI.

## Top-level state machine

Exact durations are deliberately not all fixed yet.

```
SPAWN_SEQUENCE
    -> PHASE1_REPOSITION
    -> PHASE1_BURST
    -> PHASE1_COOLDOWN
         ^        |
         |        +----> PHASE1_REPOSITION
         |
damage event
    -> PHASE1_HURT_REACTION
    -> previous phase1 flow

health <= 50%
    -> PHASE_TRANSITION
    -> PHASE2_DASH_PREP
    -> PHASE2_DASH
    -> PHASE2_RECOVER
    -> PHASE2_DASH_PREP ...

health <= 0
    -> DEATH_SEQUENCE
    -> removed
```

Target selection is orthogonal to the phase state. The boss retains a primary threat target and three visible head targets. Target identity, head aim and attack ownership must be synchronized independently from movement state.

## Candidate Bedrock behavior contract

| Behavior | Candidate contract | Evidence state | Implementation status |
|---|---|---|---|
| Difficulty health | Easy 300 / Normal 450 / Hard 600 | B; official JSON exposes base 600 only | TBD_MEASURE |
| Flight | airborne boss with Bedrock-specific repositioning | A/B | DESIGN |
| Target priority | prefer the living target that dealt the most damage | A | DESIGN |
| Search distance | exposed target max distance 70 | A | DESIGN |
| Phase 1 burst | repeated skull burst, reported as 3 normal + 1 dangerous | B | TBD_MEASURE |
| Passive dangerous skull | dangerous/blue skull can occur independently in phase 1 | B | TBD_MEASURE |
| Shot cadence | accelerates with health loss; exact thresholds/timers uncertain | B | TBD_MEASURE |
| Phase 1 hurt reaction | local block destruction plus dangerous skull | B | TBD_MEASURE |
| 50% transition | distinct second phase transition | B; unique behavior is official | DESIGN |
| Transition explosion | explosion during phase transition | B | TBD_MEASURE |
| Wither Skeleton summon | summon reported as 3 on Normal/Hard, none on Easy | B; summoning existence A | TBD_MEASURE |
| Projectile immunity | phase 2 rejects projectile damage | B | DESIGN |
| Dash/charge | phase 2 uses target-directed dash/charge | B | DESIGN |
| Dash duration | roughly 20 ticks reported | B | TBD_MEASURE |
| Dash destruction | reported 6x8x6 cuboid each tick while charging | B | TBD_MEASURE |
| Passive regeneration | reported absent in current Bedrock behavior | B | TBD_MEASURE |
| Death explosion/sequence | distinct Bedrock death sequence/explosion | B | TBD_MEASURE |

No `TBD_MEASURE` value may become an acceptance-critical constant without either direct measurement or an explicit temporary-candidate annotation in code/config.

## Server architecture

### BedrockWitherEntity

Owns only durable entity state and delegates phase behavior.

Synced data candidates:
- state enum/id
- phase 2 flag
- spawn/transition sequence counter
- primary target entity ID
- left/right head target entity IDs
- left/right head yaw/pitch
- dash vector / dash-active flag
- dangerous-skull visual state if needed

NBT persistence:
- stable phase/state only where resume semantics are meaningful;
- transient attack counters may be restored conservatively or reset through a documented recovery state;
- never resume a dash from stale coordinates without validation.

### Targeting

Maintain a bounded threat ledger:
- damage source entity
- accumulated or last-window damage
- last seen tick
- validity predicate

The official `wither_target_highest_damage` contract is reproduced explicitly rather than approximated with Java's nearest-target goal.

### Movement

Do not use Java Wither's movement code as authority.

Phase 1 controller:
- choose/revise candidate attack position around the current target;
- fly toward it;
- enter hover/burst state only under explicit reach/visibility rules.

Phase 2 controller:
- prepare target/vector;
- enter a bounded dash state;
- apply velocity deterministically for the accepted duration;
- terminate on timeout, invalid target or collision rule.

### Attack controller

Own all per-head cooldowns and burst sequence state.

The center/head attack schedule is modeled independently from movement so runtime measurements can adjust timing without rewriting navigation.

Dangerous/blue skull selection is explicit and testable.

### Destruction controller

Use Forge-aware entity-destruction checks rather than assuming every Java-breakable block is Bedrock-breakable.

Two separate operations:
- phase 1 damage-reaction destruction volume;
- phase 2 dash destruction volume.

Every destruction attempt records a reason/category in debug builds so the Tank can explain mismatches.

### Phase controller

The 50% transition must fire exactly once.

Candidate transition actions:
- freeze/cancel phase 1 burst
- switch second-phase state
- perform explosion
- summon skeletons according to difficulty
- enable projectile immunity
- initiate phase 2 movement sequence

The exact ordering/timing is a runtime-observation target.

## Client architecture

A custom renderer/model is preferred over inheriting `WitherBossRenderer`, whose type is bound to `WitherBoss`.

Use the vanilla Wither visual language as a baseline:
- three heads
- body/tail pose
- invulnerable/spawn texture behavior where applicable
- phase-2 armor/shield layer

Animation is driven from our synced state, not from vanilla Wither timers.

## Debug/observation hooks

For KNEEKURA Tank runs expose read-only diagnostics:
- current state
- state-enter tick
- max/current health
- primary and side-head target IDs
- next attack/head cooldowns
- burst index
- dangerous-skull flag
- dash remaining ticks/vector
- last destruction volume and broken/skipped counts
- last transition reason

These are observability surfaces, not gameplay control APIs.

## Non-goals for the first accepted version

- byte-for-byte imitation of Bedrock native code
- replacing every vanilla Wither globally
- reproducing Bedrock engine bugs by accident
- claiming exact timing from Wiki/Reddit text without measurement
- performance claims outside the bounded Tank scenarios

A Bedrock quirk/bug may later be emulated behind a compatibility option only after it is reproduced and version-bound.
