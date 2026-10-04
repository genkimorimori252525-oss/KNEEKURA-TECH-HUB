# Vanilla AI architecture — exact ANCHOR core

Status: **CORE DEVELOPMENT BYTECODE INSPECTED; NATIVE ACCEPTANCE PENDING**

All ANCHOR statements here refer to the exact Minecraft 1.20.1 / Forge 47.2.0 development artifact in [the bytecode ledger](ANCHOR-BYTECODE-LEDGER-2026-10-03.json), discovered through [the local Foundation Map](../vanilla-foundation/LOCAL-GENERATION-2026-10-03.md). They are not assertions about loaded post-Mixin bytes.

`Mob.serverAiStep()` samples sensing, advances target/goal schedulers, navigation, custom server AI, and movement/look/jump controls. The scheduler cadence is implemented at the Mob call site: after the initial tick, odd `(server tick count + entity ID) % 2` calls `tickRunningGoals(false)`; the other branch calls full `GoalSelector.tick()` for both selectors. Goals requiring every-tick updates can run on the reduced branch. A five-tick observer cannot identify every eligibility call or exact start/stop tick.

`Brain.tick(ServerLevel, LivingEntity)` performs, in order, outdated-memory handling, sensor ticks, starts of eligible non-running behaviors, and ticks/stops of running behaviors. Concrete Mob code must call Brain; the existence of an inherited Brain object is not proof that Brain is the entity's active decision mechanism.

Navigation owns a selected `Path` and execution progress. `PathFinder` and its `NodeEvaluator` produce a path search within an explicit budget. The selected path, search frontier and actual movement are three different observations. A valid path does not prove that a controller or collision executed it successfully.

Ghast and Phantom use custom flight/control. Slime uses custom jump/direction control. Enderman can teleport. The representative [catalog](MOB-AI-CATALOG.json) preserves these distinctions; it is a static eight-family catalog, not a complete inventory of every Vanilla Mob or a runtime PASS matrix.

## Authority and observation

- Server state/AI/path search is authoritative for the observed logical server.
- A client renderer or interpolated pose is presentation evidence with its own timing.
- Read only exact selected UUIDs; preserve run, process, Arena and subject-selection generation.
- Public getters expose sampled state. Calling `canUse`, `canContinueToUse`, a Sensor, `Brain.tick`, a control tick, or a new path search merely to inspect it would execute AI again.
- Source-verified hook bodies establish where data could be observed. Actual installed-hook and representative-run evidence is still required.

The common Decision stages are optional. No adapter fills CANDIDATE/EVALUATION from an observed selection unless the source actually exposes those stages.

## Research boundary

The ledger retains 60 selected core/representative class identities and private disassembly locators. Goal/Brain/pathfinding/control/debug core semantics below are grounded in those bytes. Full inheritance-aware all-Mob inventory, broader random-position/sensor candidate semantics, COMMUNITY reproduction, a pinned modern Vanilla FRONTIER, and observer-effect/native coverage remain unfinished.
