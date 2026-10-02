# Motion Trace / Decision Observatory Foundation Status — 2026-10-03

Status: **IMPLEMENTED FOUNDATION / RUNTIME-SPECIFIC WORK REMAINS**

This record supplements, and does not replace:

- `departments/minecraft/LOCAL-EXECUTION-HANDOFF-2026-10-02.md`
- `departments/minecraft/lab/docs/superpowers/plans/2026-10-02-on-demand-motion-trace.md`
- `departments/minecraft/lab/docs/superpowers/plans/2026-10-02-entity-decision-observatory.md`

## Implemented in PR #79

### SampledMotionTrace v1 foundation

Implemented:

- versioned `kneekura.sampled-motion-trace/v1` contract;
- `MOB_ACTUAL`, `PROJECTILE_ACTUAL`, and `NAVIGATION_DECLARED` trace classes;
- exact retained source-observation references;
- sampled-endpoint segment semantics;
- explicit identity-boundary and typed-discontinuity gaps;
- optional source-gap rule;
- bounded sample count;
- net displacement, sampled polyline length, altitude and observed-speed metrics;
- compact AI motion packet;
- deterministic PLAN_XZ, ELEVATION and fixed-isometric derived SVG views;
- explicit declaration that lines are derived presentation and not exact continuous paths.

The extractor refuses to reinterpret SimStore `trackOf().at(t)` forward-filled state as a sampled observation.

SimStore now exposes `trackOf().samples(...)`, which returns only retained position-lane points with source locators.

### Viewer migration slice

Implemented:

- motion trace visualization OFF by default;
- existing projectile trail remains opt-in through the existing trail control;
- explicit Mob subject selector;
- only the selected Mob receives an additional trace;
- selected Mob trace is built from retained sample points;
- F3/perspective, plan and elevation views can display the selected Mob trace;
- Mob trace uses long dash + heavier width + circle markers, distinct from projectile presentation by more than color;
- no automatic all-Mob scan or always-on trace drawing was added.

### DecisionObservationModel v1 foundation

Implemented:

- neutral optional stages: INPUT, STATE, CANDIDATE, EVALUATION, SELECTION, EXECUTION, RESULT;
- machine-readable epistemic statuses;
- explicit causal-relation classes;
- capability declarations;
- source-reference requirements for direct/instrumented claims;
- bounded compact Decision Packet;
- temporal adjacency remains temporal association unless stronger evidence is supplied;
- missing/custom state remains explicit rather than inferred.

### Generic Mob fallback adapter

Implemented a conservative exact-subject SimStore adapter that:

- observes only the requested entity;
- exposes retained position/motion availability;
- labels exact retained points as `SAMPLED_OBSERVED`;
- labels forward-filled current state as `DERIVED_FROM_OBSERVED`;
- reports Vanilla Goal/Brain/pathfinding/movement-control state as `NOT_EXPOSED` until a proven source-specific adapter exists;
- supports unknown MOD entities without forcing Vanilla Goal/Path semantics.

## Deliberately not claimed complete

The following parts of the authoritative handoff still require local source/runtime evidence and are not completed by this foundation slice:

- real local Minecraft 1.20.1 Forge Foundation Map generation;
- complete Vanilla AI Goal/Brain/pathfinding/malus/movement-control research;
- exact safe Forge Java hook selection;
- Vanilla Goal adapter;
- Vanilla Brain adapter;
- path-search/open/closed/cost burst capture;
- terrain/malus runtime adapter;
- movement-control/custom-flight runtime adapter;
- live Minecraft client trace overlay;
- synchronized runtime Decision Timeline across Goal/Brain/path/projectile/hit channels;
- Twilight Forest Hydra/Snow Queen/Knight Phantom/Ur-Ghast runtime proof adapters;
- representative real-machine Zombie/Skeleton/Villager/Ghast/Phantom/Slime/aquatic/Enderman acceptance;
- runtime observer-effect/performance measurements.

No claim in this file upgrades those items from NOT_RUN/NOT_EXPOSED/UNKNOWN.

## Verification boundary

The new contract tests are wired into `npm run test:ci` and therefore into the MOD AI LAB source-verification workflow.

A successful hosted source/compilation run proves the repository/source contracts and existing pinned MOD compilation path. It does **not** prove loaded Minecraft runtime behavior or client visual acceptance.

The runtime-specific checklist in the authoritative local execution handoff remains the source of truth for those later steps.
