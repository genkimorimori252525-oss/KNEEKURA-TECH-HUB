# Vanilla Java Mob AI Research

Status: **RESEARCH IN PROGRESS — not yet a complete vanilla-AI inventory**

Current implementation/native evidence: [2026-10-03 handoff](../CURRENT-HANDOFF-2026-10-03.md) and [representative/observer acceptance](NATIVE-REPRESENTATIVE-OBSERVER-ACCEPTANCE-2026-10-03.md). Selected core ANCHOR hooks, retained/native views and four cached Boss proofs now exist; full inventory/FRONTIER and complete behavior acceptance remain separate.

This directory is a KNEEKURA TECH HUB technical-asset area for understanding Minecraft Java Edition mob decision-making, navigation, movement control and built-in AI debugging.

## Static discovery baseline

The [2026-10-03 local generation report](../vanilla-foundation/LOCAL-GENERATION-2026-10-03.md) now records an actual 1.20.1 Forge class-root map: 7,108 Minecraft owners, 61,051 structural edges and 13/13 anchors. The [ANCHOR bytecode ledger](ANCHOR-BYTECODE-LEDGER-2026-10-03.json) pins 60 selected core/representative classes, with member/body locators in private retained disassemblies. The required core research files and eight-family static catalog are available. Full semantic inventory, FRONTIER/community comparison and native/runtime acceptance are still in progress.

Before widening an external search, use the implemented [Minecraft 1.20.1 Vanilla Foundation Map](../vanilla-foundation/README.md) when an exact local ANCHOR map is available. It is the static discovery/provenance layer; this directory remains the place for verified AI semantics and engineering conclusions.

## Approved downstream architecture

The long-term Water Tank Studio consumer of this research is the approved **Entity Decision Observatory** design:

- `departments/minecraft/lab/docs/superpowers/plans/2026-10-02-entity-decision-observatory.md`

That design intentionally treats Vanilla as the first adapter family rather than the universal AI schema. Research in this directory must therefore preserve differences between Goal, Brain, navigation, custom movement, state-machine, formation and other AI families instead of flattening them into one model.


It is deliberately separate from Water Tank Studio implementation plans. Research facts belong here first; LAB visualization requirements are derived later.

## Tracks

### ANCHOR

- Minecraft Java Edition **1.20.1**
- Forge **47.2.0 / 47.2.x**
- Mojmap/mappings and exact-version API surfaces
- primary target for KNEEKURA implementation/backport decisions

### FRONTIER

- latest useful vanilla / loader / community implementations
- kept separate from ANCHOR
- used to recover newer debugging techniques and design evolution

### COMMUNITY EVIDENCE

- technical Minecraft discussions, issue reports and Reddit experiments
- hypothesis/edge-case discovery only
- never promoted to implementation fact without source/runtime confirmation

## Research objective

Build an AI-facing engineering model of a Mob decision pipeline:

```text
Perception / sensing
        ↓
Target / memory / world facts
        ↓
Decision scheduler
  GoalSelector or Brain
        ↓
Candidate actions / eligibility / priority / conflicts
        ↓
Navigation / path search
        ↓
Terrain / node valuation
        ↓
Move / Look / Jump / Body controls
        ↓
Actual entity motion / attack
```

Not every Mob uses every layer. Special/custom controllers, imperative tick logic and boss state machines must be catalogued explicitly rather than forced into one generic model.

## Core research areas

1. **Goal system**
   - Goal
   - WrappedGoal
   - GoalSelector
   - targetSelector
   - priority
   - flags/control locking
   - canUse / canContinueToUse
   - start / tick / stop
   - replacement/interruption

2. **Brain system**
   - Sensor / SensorType
   - MemoryModuleType / MemoryStatus
   - Activity / Schedule
   - BehaviorControl / Behavior
   - priority buckets
   - memory preconditions
   - memory expiry/erasure
   - running behavior transitions

3. **Targeting and perception**
   - Mob target state
   - Sensing
   - nearest/visible target logic
   - line of sight
   - follow/attack range
   - anger/universal anger where applicable

4. **Pathfinding**
   - PathNavigation families
   - PathFinder
   - NodeEvaluator families
   - Path
   - Node / Target / BinaryHeap
   - open set / closed set
   - g / h / f
   - costMalus
   - BlockPathTypes
   - reachability and target-distance semantics
   - recomputation and visited-node budgets

5. **Terrain valuation**
   - Mob pathfindingMalus overrides
   - BlockPathTypes default malus
   - per-Mob overrides
   - collision and bounding-box constraints
   - doors, rails, water, lava, fire, hazards, fences and special terrain

6. **Movement execution**
   - MoveControl
   - FlyingMoveControl
   - SmoothSwimmingMoveControl
   - LookControl
   - JumpControl
   - BodyRotationControl
   - custom Mob-specific controls

7. **Non-standard AI**
   - Ghast-style custom flight
   - Phantom movement
   - Slime movement
   - aquatic/swimming specializations
   - Enderman/teleport behavior
   - bosses and explicit state machines
   - imperative aiStep/tick logic

8. **Vanilla debug infrastructure**
   - DebugPackets
   - exact 1.20.1 Path/debug-renderer data and channel/buffer packet
   - PathfindingRenderer
   - GoalSelectorDebugRenderer
   - BrainDebugRenderer
   - dormant/stubbed paths and mod re-enablement precedents

9. **Performance / cadence**
   - scheduler cadence
   - path recomputation cadence
   - search limits
   - cache behavior
   - cost of recording candidate-search state
   - observer-effect risks for debug instrumentation

## Required outputs

Research should eventually produce:

- `SOURCE-MAP.md`
- `AI-ARCHITECTURE.md`
- `GOAL-SYSTEM.md`
- `BRAIN-SYSTEM.md`
- `PATHFINDING.md`
- `MOVEMENT-CONTROLS.md`
- `DEBUG-INFRASTRUCTURE.md`
- `MOB-AI-CATALOG.json`
- `VERSION-PORTABILITY.md`
- `DECISION-VIEW-REQUIREMENTS.md`

The final decision-view design must be derived from these findings rather than reverse-fitting research to an already desired UI.

## Evidence rule

Distinguish:

- **OBSERVED API/STRUCTURE** — exact version source/mapping/runtime evidence;
- **DERIVED ENGINEERING INTERPRETATION** — explanation based on those facts;
- **COMMUNITY REPORT** — useful experiment/anomaly report;
- **UNKNOWN / VERSION-UNVERIFIED** — not yet established for the ANCHOR.

Do not call a visualization "Mob thought" unless the runtime exposes that state directly. Prefer decision state, candidate state, path-search state, memory, scheduler state, or derived explanation.

## Early finding

Minecraft 1.20.1 already contains substantial dormant/diagnostic primitives for exactly the problem KNEEKURA is studying:

- Goal debug payload/renderer;
- Brain debug payload/renderer;
- Pathfinding debug payload/renderer;
- Path objects with optional open/closed/target debug node sets;
- Nodes carrying A*-related score fields, path type and cost malus.

This means KNEEKURA should study and reuse the semantics of vanilla debugging before inventing a parallel vocabulary. It does **not** mean the existing vanilla debug transport is sufficient for KNEEKURA evidence requirements.
