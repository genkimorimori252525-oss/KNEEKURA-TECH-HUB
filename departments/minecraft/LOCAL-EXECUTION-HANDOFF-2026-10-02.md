# KNEEKURA Minecraft — Local Execution Handoff

Date: **2026-10-02**  
Status: **EXECUTE ALL REMAINING WORK FROM THE 2026-10-02 WATER TANK / VANILLA AI SESSION**  
Canonical repository: `genkimorimori252525-oss/KNEEKURA-TECH-HUB`  
Canonical branch: **`main`**  
Start from: **latest `origin/main`**  
Foundation Map implementation merge already present: **`4c5518f432bf0ffdc5ba215891f3248f0e681dbc`**

This document is the single execution handoff for the local implementation AI.

The user has already approved the product direction and core designs created in the 2026-10-02 session. Do not repeatedly ask whether to implement already-approved work. Execute it, verify it, preserve evidence, and leave the repository in a coherent finished state.

The remaining work includes **both the still-unimplemented motion/trajectory plan and the Mob decision-observation plan**.

---

# 0. Read this first

Read these in order before changing code:

1. `departments/minecraft/CURRENT-HANDOFF-2026-10-02.md`
2. `departments/minecraft/README.md`
3. `departments/minecraft/design/2026-09-28-mod-ai-environment/DESIGN.md`
4. `departments/minecraft/vanilla-foundation/README.md`
5. `departments/minecraft/vanilla-ai/README.md`
6. `departments/minecraft/vanilla-ai/SOURCE-MAP.md`
7. `departments/minecraft/lab/docs/superpowers/plans/2026-10-02-on-demand-motion-trace.md`
8. `departments/minecraft/lab/docs/superpowers/plans/2026-10-02-entity-decision-observatory.md`

Also inspect current implementation before editing:

- `src/kneekura_tech_hub/minecraft/`
- `departments/minecraft/mod-ai/`
- `departments/minecraft/lab/`
- `departments/minecraft/mods/twilight-forest/`

Historical documents remain evidence. If older files contradict newer 2026-10-02 plans or current `main`, the newer/current source wins.

---

# 1. Final objective

Complete the remaining Water Tank Studio / Minecraft AI work from this session:

```text
real Minecraft 1.20.1 + Forge ANCHOR
        ↓
exact local Vanilla Foundation Map artifact
        ↓
complete Vanilla Java AI technical research
        ↓
On-Demand Sampled Motion Trace
        ↓
Entity Decision Observatory
        ↓
Vanilla representative validation
        ↓
MOD-specific adapter proofs
        ↓
integrated regression + real-machine validation
        ↓
durable TechHub documentation / final handoff
```

At completion, an implementation AI must be able to:

1. discover Minecraft 1.20.1 classes from TechHub before using public-web search;
2. inspect exact Vanilla AI structure and provenance;
3. request a Mob or projectile motion history only when movement is relevant;
4. inspect decision-relevant state for one exact selected entity;
5. drill into Goal / Brain / navigation / pathfinding / malus / movement controls where supported;
6. see unsupported or unavailable state explicitly rather than receiving guessed explanations;
7. correlate decision state with actual motion/projectile/hit evidence;
8. extend the same framework to MOD-specific AI without pretending every Mob uses Vanilla Goal/Path semantics.

---

# 2. Non-negotiable design rules

## 2.1 Evidence boundary

Raw observations remain evidence.

The following are derived presentation unless explicitly proven otherwise:

- trajectory lines;
- interpolated line segments;
- cost heatmaps;
- candidate diagrams;
- fixed-isometric 3D views;
- live debug overlays;
- summaries;
- causal explanations.

Never convert a derived visualization into authoritative runtime fact.

## 2.2 No mind-reading

Do not display:

> the Mob thought X

unless X is an actual exposed/instrumented runtime state.

Prefer:

- decision state;
- candidate;
- scheduler state;
- path-search state;
- memory;
- selected action;
- controller target;
- derived explanation.

Unknown reason = unknown reason.

## 2.3 Default-off visualization

Motion Trace and Decision View are **OFF by default**.

Do not continuously draw debug paths merely because evidence exists.

## 2.4 Exact subject scope

Operate on exact selected/registered subjects.

No automatic unbounded world scan.

## 2.5 No gameplay mutation for visualization

Do not render debug paths by spawning:

- particles;
- entities;
- blocks;
- fake projectiles;
- other gameplay objects.

Prefer presentation-only/client-side overlays.

## 2.6 Reuse existing stores

Do not create:

- a second evidence database;
- a second full position-history database;
- a long-term trajectory warehouse.

Reuse current Evidence Store, Source Intelligence, LAB/SimLab retained state and existing identity contracts.

## 2.7 Preserve identity

Keep run/session/profile/Arena/entity/time identity intact.

Never silently combine:

- different runs;
- different Arena epochs;
- different entity UUIDs;
- different build generations;
- ANCHOR and FRONTIER evidence.

## 2.8 Failure remains visible

`UNKNOWN`, `PARTIAL`, `NOT_RUN`, `BLOCKED`, `INCONCLUSIVE`, `NOT_EXPOSED` are valid outcomes.

Never round them into PASS.

---

# 3. Current status summary

## Already implemented

### A. Vanilla Foundation Map engine

Merged into `main`.

Implemented:

- `foundation-map build`
- `foundation-map search`
- `foundation-map inspect`
- `foundation-map subsystems`
- `net/minecraft/**` class mapping
- package/subsystem classification
- extends / implements
- JVM `CONSTANT_Class` reference candidates
- exact origin/root/stage/hash preservation
- duplicate-class ambiguity preservation
- AI/debug readiness anchors
- CAS/content-addressed map artifact

The implementation was accepted by the complete repository suite before merge.

**Do not reimplement this.**

### B. Motion Trace design

Design is approved.

Implementation is **not yet complete**.

This is a first-class remaining workstream and must not be skipped.

### C. Entity Decision Observatory design

Design is approved.

Implementation is **not yet complete**.

### D. Vanilla AI research

Research directory and initial source ledger exist.

The detailed research program is **not yet complete**.

---

# 4. Workstream A — generate the real local Vanilla Foundation Map

The engine exists. The real exact map artifact must now be produced from the user's local Minecraft 1.20.1 Forge environment.

## A1. Sync

Start from latest `origin/main`.

Confirm these exist:

- `src/kneekura_tech_hub/minecraft/foundation_map.py`
- Foundation Map CLI in `connected_cli.py`
- `class_references` support in `classfile.py`
- `tests/test_minecraft_foundation_map.py`

## A2. Resolve an exact ANCHOR profile

Use the existing Source Intelligence / Forge workspace path.

Required identity:

- Minecraft **1.20.1**
- Forge, exact locally resolved version
- Java 17 game toolchain
- Mojmap namespace
- exact Gradle/source/config/classpath fingerprints

Prefer the existing resolved ForgeGradle export rather than hand-writing a manifest.

If the selected workspace does not expose a complete Minecraft class root, fix/diagnose the classpath export. Do not weaken readiness anchors to force `OK`.

## A3. Prepare the exact IndexSnapshot

Preserve:

- profile ID/hash;
- exact resolved roots;
- classpath order;
- scope;
- namespace;
- mapping identity;
- coverage gaps.

A partial IndexSnapshot remains partial.

## A4. Build the real Foundation Map

Equivalent command:

```bash
python -m kneekura_tech_hub.minecraft \
  --store .kneekura-cache/minecraft \
  foundation-map build \
  --index <INDEX_SNAPSHOT_ID> \
  --max-classes 20000
```

Retain locally:

- `foundation_map_id`;
- source IndexSnapshot ID;
- profile ID;
- unique Minecraft class count;
- edge count;
- subsystem counts;
- missing/ambiguous anchors;
- exact coverage result.

## A5. Validate discovery

At minimum search and inspect:

- `net/minecraft/world/entity/Mob`
- `net/minecraft/world/entity/ai/goal/GoalSelector`
- `net/minecraft/world/entity/ai/Brain`
- `net/minecraft/world/entity/ai/navigation/PathNavigation`
- `net/minecraft/world/entity/ai/control/MoveControl`
- `net/minecraft/world/level/pathfinder/PathFinder`
- `net/minecraft/world/level/pathfinder/NodeEvaluator`
- `net/minecraft/world/level/pathfinder/Path`
- `net/minecraft/world/level/pathfinder/Node`
- `net/minecraft/client/renderer/debug/PathfindingRenderer`
- `net/minecraft/client/renderer/debug/GoalSelectorDebugRenderer`
- `net/minecraft/client/renderer/debug/BrainDebugRenderer`

If `DebugPackets` lives under a different exact 1.20.1 package/owner than the readiness anchor currently expects, fix the anchor using exact local evidence rather than guessing.

## A6. Persist only appropriate artifacts

Do not commit:

- Minecraft JARs;
- decompiled Minecraft full source;
- local caches;
- copyrighted whole-source dumps.

Do commit compact, useful, provenance-safe metadata if it improves reproducibility:

- local generation report;
- artifact IDs/hashes;
- exact environment identity;
- coverage summary;
- any Foundation Map bugfix proven necessary by the real input.

---

# 5. Workstream B — complete Vanilla Java Mob AI research

This is a TechHub knowledge asset in its own right, not merely implementation notes for the LAB.

Primary research directory:

`departments/minecraft/vanilla-ai/`

Use the real Foundation Map first for exact 1.20.1 discovery.

External sources remain valuable for:

- API/mapping clarification;
- upstream implementation precedent;
- issue/PR history;
- technical behavior reports;
- edge-case discovery.

But public-web search must no longer be the hidden primary class index when the local exact map is available.

## B1. Required final research outputs

Produce or complete:

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

## B2. Goal system

Establish exact 1.20.1 behavior for:

- `Goal`
- `WrappedGoal`
- `GoalSelector`
- `targetSelector`
- priority semantics;
- control flags;
- flag ownership/locking;
- `canUse`;
- `canContinueToUse`;
- start/tick/stop;
- replacement/interruption;
- scheduler cadence;
- disabled flags.

Separate API existence from exact method-body behavior.

## B3. Brain system

Map:

- Sensor / SensorType;
- MemoryModuleType;
- MemoryStatus;
- memory expiry/removal;
- Activity;
- Schedule;
- Behavior / BehaviorControl;
- priority buckets;
- activity requirements;
- core/default/active activities;
- running Behavior semantics;
- WalkTarget / LookTarget / AttackTarget / PATH;
- transition timing/cadence.

## B4. Pathfinding

Map:

- PathNavigation families;
- PathFinder;
- NodeEvaluator families;
- WalkNodeEvaluator;
- FlyNodeEvaluator;
- swim/amphibious/special evaluators;
- Path;
- Node;
- Target;
- BinaryHeap;
- open/closed sets;
- predecessor relation;
- g/h/f;
- `costMalus`;
- BlockPathTypes;
- reachability;
- target accuracy;
- max visited nodes;
- search depth multiplier;
- recomputation;
- collision/accepted-node logic.

## B5. Terrain valuation

Recover exact semantics for:

- default BlockPathTypes malus;
- per-Mob pathfinding malus overrides;
- negative malus / impassable behavior;
- water/lava/fire/fence/door/rail/hazard handling;
- collision/BBox effect;
- queried regional path cost vs nodes actually evaluated.

This distinction matters directly to the future malus visualization.

## B6. Movement controls

Map:

- MoveControl;
- FlyingMoveControl;
- SmoothSwimmingMoveControl;
- LookControl;
- JumpControl;
- BodyRotationControl;
- operation state;
- desired position;
- speed modifiers;
- rotation targets;
- custom Mob-specific controls.

## B7. Special AI families

Do not force all entities into A* path semantics.

Study representative non-standard cases, at minimum:

- Ghast;
- Phantom;
- Slime;
- aquatic Mob;
- Enderman;
- Brain-heavy Mob;
- ordinary Goal + ground navigation Mob.

Document which decision layers genuinely exist for each family.

## B8. Vanilla debug infrastructure

Fully map:

- DebugPackets;
- Pathfinding debug payload;
- Goal debug payload;
- Brain debug payload;
- PathfindingRenderer;
- GoalSelectorDebugRenderer;
- BrainDebugRenderer;
- call sites;
- server/client authority;
- disabled/dormant production behavior;
- open/closed/target debug population;
- capture-debug switches;
- existing mod precedent for re-enabling Vanilla debug flows.

## B9. Community evidence

Use Reddit/technical community reports for:

- surprising pathfinding cases;
- practical repro scenarios;
- blocks/terrain with unintuitive results;
- debugger UX requirements.

Do not promote community claims to ANCHOR implementation truth without source/runtime confirmation.

## B10. FRONTIER

Compare useful modern Minecraft versions only after ANCHOR is mapped.

Separate:

- concept;
- version-specific implementation;
- changed API;
- backport strategy;
- unavailable/risky parts.

---

# 6. Workstream C — implement On-Demand Sampled Motion Trace

**This plan is still unimplemented and must be executed.**

Authoritative plan:

`departments/minecraft/lab/docs/superpowers/plans/2026-10-02-on-demand-motion-trace.md`

Do not replace the plan with a new trajectory system.

## C1. Core contract

Implement versioned `SampledMotionTrace v1`.

Each sample must retain appropriate identity:

- run / RunSnapshot;
- Arena/epoch where relevant;
- entity UUID or exact stable run-scoped ID;
- entity type;
- trace class;
- tick/gameTime/time identity;
- XYZ;
- directly observed velocity when available;
- source observation/trace-row identity;
- source kind.

Segments are derived connections between sampled endpoints.

They are not automatically exact continuous motion.

## C2. Trace classes

Implement at least:

- `MOB_ACTUAL`
- `PROJECTILE_ACTUAL`
- `NAVIGATION_DECLARED`

Do not conflate them visually or semantically.

Color is not enough.

Also differentiate by:

- line pattern;
- line width;
- marker shape.

## C3. Gaps/discontinuities

Break the trace when continuity is not evidenced.

Examples:

- entity missing/gone;
- source gap beyond allowed window;
- dimension change;
- run/epoch change;
- reset boundary.

Explicit typed teleport may use a special discontinuity marker.

Unknown jumps are not automatically teleports.

## C4. Reuse existing Viewer

Current Viewer already has:

- playback/scrub;
- projectile trail;
- plan/elevation views;
- position history.

Refactor rather than duplicate.

Required:

- extract projectile-only trail builder into generic trace builder;
- allow explicit selected Mob trace;
- preserve old projectile behavior;
- traces OFF by default;
- no hidden draw loop when off.

## C5. Human views

Phase 1:

- PLAN / XZ;
- ELEVATION;
- existing context.

For flight, plan alone is insufficient.

## C6. Optional fixed 3D view

Implement the approved optional Level-2 3D drill-down after the basic contract/views are stable.

Preferred form:

- deterministic fixed-isometric/oblique camera;
- world axes/grid;
- minimal scene context;
- measured sample nodes;
- selected Mob/projectile/target/obstacle context only;
- no cinematic arbitrary camera for AI comparison.

Do not require GLTF/OBJ.

A generated deterministic image/derived artifact is sufficient for the initial AI-facing 3D view.

## C7. Live Minecraft overlay

Implement as optional final drill-down.

Rules:

- OFF by default;
- client-side/presentation-only where practical;
- no gameplay particle/entity/block spawning;
- same trace contract as structured/2D/3D views;
- closes immediately when disabled or subject/window changes.

Suggested visual grammar:

```text
MOB_ACTUAL         thick long-dash + circle sample points
PROJECTILE_ACTUAL  thin short-dash + diamond sample points
NAVIGATION         fine dotted guide
```

## C8. AI-facing request

AI should not receive all trajectory data by default.

Normal packet only advertises availability.

Explicit request must be bounded by:

- subject;
- trace classes;
- time window;
- requested views;
- optional metrics.

Return structured metrics before images.

At minimum:

- sample count;
- first/last tick;
- duration;
- net displacement;
- sampled polyline length;
- min/max altitude;
- speed statistics if valid;
- gaps;
- event markers;
- source identities;
- epistemic label.

## C9. Visual Evidence Compiler integration

Add on-demand derived motion artifacts without contaminating raw Cardinal frames.

The normal raw images remain untouched.

## C10. Performance validation

Before adding higher-frequency recording, prove existing retained cadence is insufficient using actual fixtures.

Do not assume one-tick recording is needed.

Test:

- Ghast-like float/wander;
- tight aerial turn/orbit;
- projectile;
- Mob + projectile overlay;
- explicit teleport;
- missing/gapped samples.

Only add a bounded high-resolution lane if evidence shows the existing cadence fails.

---

# 7. Workstream D — implement Entity Decision Observatory

Authoritative plan:

`departments/minecraft/lab/docs/superpowers/plans/2026-10-02-entity-decision-observatory.md`

The architecture is fixed. Exact Java hooks must be chosen from Workstream B's verified research.

## D1. Decision Observation Model v1

Implement the neutral stages:

```text
INPUT
STATE
CANDIDATE
EVALUATION
SELECTION
EXECUTION
RESULT
```

Every stage is optional.

Do not force every adapter to populate all stages.

## D2. Epistemic status

Support machine-readable certainty such as:

- `DIRECT_OBSERVED`
- `SAMPLED_OBSERVED`
- `INSTRUMENTED_ALGORITHM_STATE`
- `DERIVED_FROM_OBSERVED`
- `NOT_EXPOSED`
- `NOT_APPLICABLE`
- `NOT_CAPTURED`
- `UNKNOWN`

Do not use polished UI to hide uncertainty.

## D3. Causal relation semantics

Distinguish:

- direct runtime relation;
- algorithm-trace relation;
- temporal association;
- derived spatial association;
- unknown causality.

Do not automatically convert:

```text
Goal started
Path selected
Mob moved
```

into:

```text
The Mob moved because that Goal selected that Path
```

unless direct/instrumented evidence proves the link.

## D4. Adapter capabilities

Every adapter declares what it can expose.

The Viewer/AI asks for deep data only after inspecting capabilities.

Unknown MOD Mob gets a conservative fallback, not invented introspection.

## D5. Shared visual primitives

Support the common vocabulary where useful:

- POINT;
- VECTOR;
- PATH;
- REGION;
- VOXEL_FIELD;
- CANDIDATE_SET;
- SCALAR_SCORE;
- STATE_MACHINE;
- SCHEDULER_LANE;
- RELATION_EDGE;
- EVENT_MARKER;
- TEXT_FACT.

Source-specific adapters may extend it without replacing the common contract.

---

# 8. Workstream E — Vanilla Decision adapters

## E1. Generic Mob baseline

Reuse existing LAB observations:

- AI target;
- Navigation;
- position/velocity;
- current path/progress where available;
- controller identity/state where safely available;
- Motion Trace link.

Unknown custom state remains unknown.

## E2. Goal Scheduler adapter

Expose where exact instrumentation supports it:

- registered Goal;
- priority;
- flags;
- running state;
- start/stop;
- replacement/interruption;
- control ownership/locking;
- disabled flags;
- target-selector state.

Potential UI:

```text
P1  MeleeAttackGoal   RUNNING
P2  AvoidEntityGoal   BLOCKED
P3  RandomStrollGoal  INACTIVE
```

Do not invent why an inactive Goal is inactive.

## E3. Brain adapter

Expose:

- key Sensor result where available;
- Memories;
- memory changes;
- core/active/default Activity;
- running Behavior;
- Behavior transitions;
- WalkTarget;
- LookTarget;
- AttackTarget;
- PATH;
- exact timing/cadence.

Primary UI:

- Memory Board;
- Activity/Behavior lane;
- spatial target/memory links.

## E4. Pathfinding adapter

Implement the user's desired path-search debugging.

Where exact state can be captured:

- selected Path;
- current path node;
- target;
- open set;
- closed set;
- candidate/search nodes;
- predecessor;
- g/h/f;
- costMalus;
- PathType;
- search/visited budget;
- canReach.

Primary UI:

- chosen path;
- search frontier;
- node cost view;
- target nodes;
- open/closed distinction.

## E5. Terrain/Malus visualization

Implement a bounded spatial field for selected Mob.

The display must distinguish:

1. PathType classification;
2. default type malus;
3. Mob-specific override;
4. effective value where exact semantics are known;
5. block/node actually evaluated by the pathfinder;
6. merely queryable regional cost that was not proven evaluated.

Do not paint a regional map and imply the Mob actually examined every shown block.

Color must not be the only encoding.

Also provide numeric/text inspection.

## E6. Movement-control adapter

Critical for non-A* entities.

Expose where available:

- move target;
- operation;
- speed modifier;
- steering/desire vector;
- look target;
- jump state;
- custom reach/collision test.

For Ghast-like flight, do not fabricate a normal path.

---

# 9. Workstream F — Decision Burst Capture

Some decision internals are too expensive or intrusive for continuous capture.

Implement bounded on-demand capture for such channels.

Potential burst-only data:

- every open/closed A* node;
- every random-position candidate;
- Goal eligibility calls;
- utility score matrices;
- full sensor candidate populations.

Flow:

```text
select exact subject
        ↓
arm exact channels
        ↓
capture N ticks / one decision / one path search
        ↓
stop instrumentation
        ↓
retain bounded immutable artifact
```

Measure observer overhead.

If instrumentation can affect behavior, record that risk explicitly.

Do not claim the observed behavior is unaffected without evidence.

---

# 10. Workstream G — synchronized Decision Timeline

Create a synchronized timeline across available sources.

Example:

```text
t=400 Target -> Player
t=402 Goal A START
t=405 Path search #17
t=405 path selected
t=410 next node changed
t=418 Goal B START / Goal A STOP
t=420 projectile spawned
t=421..435 actual motion trace
t=436 hit
```

Every event must link to its exact source identity.

This is correlation unless direct causal instrumentation proves more.

Integrate links to:

- Motion Trace;
- Projectile Trace;
- hit/damage;
- Brain changes;
- Goal/Behavior transition;
- navigation;
- controller state.

---

# 11. Workstream H — AI-facing Decision Packet

Do not make a giant screenshot HUD the primary AI interface.

## H1. Level 0

Return compact:

- exact subject identity;
- adapter list;
- capability map;
- current target/state;
- running scheduler entries;
- selected path/action;
- available drill-down channels;
- evidence identity.

## H2. Typed drill-down

Support bounded requests equivalent to:

- show path search around tick X;
- show effective malus radius N;
- show Goal transitions in window;
- show Brain memories changed before attack;
- show custom state-machine transition around projectile spawn.

Free-text requests may be translated to typed read-only queries.

Do not use free text itself as execution authority.

## H3. Progressive visual depth

Use:

```text
Level 0  structured summary
Level 1  table/timeline + plan/elevation
Level 2  fixed-isometric 3D
Level 3  live Minecraft overlay
```

3D is useful but not mandatory for every decision problem.

---

# 12. Workstream I — MOD adapter extensibility

Vanilla is the first adapter family, not the universal schema.

Implement a versioned adapter registry/SDK only after Vanilla hook points are proven.

Conceptual interface:

- `describeCapabilities()`
- `captureSnapshot(entity, context)`
- `captureBurst(entity, context, request)`
- `emitStructuredFacts()`
- `emitVisualPrimitives()`

Adapter metadata should declare:

- MOD ID/version;
- Minecraft/loader compatibility;
- source class/method provenance;
- instrumentation method;
- observer-effect risk;
- supported epistemic levels.

Namespaced custom facts are allowed.

Examples:

- `twilightforest:hydra_head_state`
- `twilightforest:knight_formation`
- `modid:utility_score`
- `modid:flight_candidate`

---

# 13. Workstream J — prove extensibility with existing Twilight Forest research

Use the already-researched MOD as a real architecture proof.

At minimum:

## Hydra

Represent:

- authoritative coordinator;
- per-head state machines;
- head transitions;
- active attack state;
- selected/assigned target where evidenced.

Do not flatten it into one Vanilla Goal list.

## Snow Queen

Represent:

- SUMMON / DROP / BEAM phase;
- phase-specific Goals/actions;
- direct phase transition evidence.

## Knight Phantom

Represent:

- formation state;
- group leader;
- group progress/clock;
- slot/local action;
- shared target.

## Ur-Ghast

Represent:

- custom flight;
- attack/tantrum/phase-related state;
- no fake A* path when not present.

Success means these can all flow into the common Decision Packet without semantic lying.

---

# 14. Representative Vanilla validation matrix

At minimum validate:

1. Zombie — conventional Goal + ground navigation.
2. Skeleton — target + navigation + ranged attack/projectile.
3. Villager or another Brain-heavy Mob.
4. Ghast — custom/direct flight.
5. Phantom — specialized aerial behavior.
6. Slime — custom movement control.
7. aquatic Mob — swimming navigation/control.
8. Enderman — target + teleport/non-path behavior.

For each representative, record which DecisionObservationModel stages are:

- direct;
- sampled;
- burst-instrumented;
- derived;
- unavailable;
- not applicable.

---

# 15. Integrated Motion + Decision acceptance scenarios

The most important final validation is not isolated unit behavior but combined diagnosis.

## Scenario 1 — conventional pursuit

Selected ground Mob:

- target;
- Goal;
- path search;
- path malus;
- chosen path;
- actual Motion Trace.

Demonstrate whether the system can distinguish:

- bad target/Goal;
- bad terrain valuation;
- bad path search;
- correct path but bad execution.

## Scenario 2 — Ghast-like flight

Show:

- custom move target/controller;
- candidate/reach tests only if truly exposed;
- no fabricated A*;
- actual 3D-capable motion trace;
- projectile trajectory if attack occurs.

## Scenario 3 — ranged Mob

Show:

- decision/attack state;
- projectile spawn;
- projectile path;
- Mob movement path;
- hit/miss event.

Mob and projectile traces must remain clearly distinct.

## Scenario 4 — Brain Mob

Show:

- memory changes;
- Activity/Behavior;
- navigation;
- result movement.

## Scenario 5 — missing capture

Arm deep capture too late or omit a sample interval.

UI/packet must report `NOT_CAPTURED` / gap.

It must not reconstruct missing "thought."

## Scenario 6 — MOD state machine

Use one Twilight Forest proof adapter and correlate:

- state/phase;
- selected action;
- actual motion/projectile result.

---

# 16. Performance and observer-effect acceptance

Measure separately:

- default Water Tank with Decision/Motion views OFF;
- baseline selected-subject observation;
- Motion Trace generation;
- plan/elevation render;
- fixed-isometric 3D render;
- live client overlay;
- Goal/Brain observation;
- deep path-search burst;
- malus field query.

Requirements:

- OFF state adds no hidden visualization loop;
- no unbounded world scan;
- no unbounded path node retention;
- no silent increase of path search budget/order;
- no silent gameplay mutation;
- bounded cache/storage;
- explicit dropped/evicted samples where applicable.

If capture perturbs AI significantly, keep that capture mode diagnostic-only and label affected experiments accordingly.

---

# 17. Testing and verification order

Use the cheapest trustworthy test first.

1. schema/static/unit tests;
2. complete repository Python/Node/Java source tests as relevant;
3. Forge compilation;
4. GameTest where server behavior is enough;
5. client/runtime observation where rendering/synchronization is required;
6. real-machine representative scenarios.

Do not repeatedly start the full Minecraft client when static/unit/GameTest evidence is enough.

But do not claim visual/runtime success without an actual client/runtime check where required.

Keep existing tests intact.

Do not weaken assertions simply to make the new implementation pass.

---

# 18. Required regression protections

Preserve:

- old projectile trail behavior;
- Viewer playback/scrub;
- existing SimLab history;
- Visual Evidence Compiler raw-frame semantics;
- current LAB owner/session/Arena authority;
- existing TaskContext behavior;
- current MOD-AI Source Intelligence;
- existing Forge bridge compilation;
- existing full TechHub suite.

A new feature must not silently turn old exact evidence into derived data or vice versa.

---

# 19. Git / execution discipline

Use feature branches/PRs for non-trivial code changes unless the current local project instructions explicitly require another workflow.

Before merging:

- inspect current main;
- avoid touching unrelated code;
- keep commits logically scoped;
- run the relevant focused tests;
- then run the complete repository suite;
- inspect CI failures rather than rerunning blindly.

If CI reveals a real regression, fix the implementation or update a test only when the public contract intentionally changed.

Do not dismiss a failing old test as stale without evidence.

---

# 20. Documentation that must be updated at completion

Update the durable source of truth, not only temporary notes.

At minimum:

- `departments/minecraft/CURRENT-HANDOFF-2026-10-02.md` or a newer current handoff;
- `departments/minecraft/vanilla-foundation/` with the real local generation status;
- `departments/minecraft/vanilla-ai/` final research outputs;
- Motion Trace plan/status;
- Entity Decision Observatory plan/status;
- LAB history/current acceptance as appropriate;
- MOD adapter compatibility/catalog records;
- failure/repair history for meaningful implementation failures.

Do not overwrite historical documents to pretend old RED/UNKNOWN statements never existed.

Add newer acceptance/status records.

---

# 21. Completion criteria

Do not call this session's remaining work complete until all of the following are true.

## Foundation Map

- [ ] Real local exact 1.20.1 Forge Foundation Map generated.
- [ ] Required AI/debug anchors verified or exact exceptions documented.
- [ ] Search/inspect proven useful on real captured Minecraft classes.
- [ ] Provenance/coverage retained.

## Vanilla AI research

- [ ] Goal system complete.
- [ ] Brain system complete.
- [ ] pathfinding/malus complete.
- [ ] movement controls complete.
- [ ] Vanilla debug infrastructure complete.
- [ ] representative Mob catalog complete.
- [ ] ANCHOR vs useful FRONTIER differences recorded.

## Motion Trace

- [ ] `SampledMotionTrace v1` implemented.
- [ ] selected Mob trace works.
- [ ] projectile trace preserved/generalized.
- [ ] navigation trace separate.
- [ ] gaps/discontinuities correct.
- [ ] plan/elevation implemented.
- [ ] AI structured request implemented.
- [ ] optional fixed 3D drill-down implemented.
- [ ] optional live Minecraft overlay implemented.
- [ ] default OFF.
- [ ] no gameplay-object visualization hack.
- [ ] no second motion database.

## Decision Observatory

- [ ] DecisionObservationModel v1 implemented.
- [ ] capabilities implemented.
- [ ] generic Mob adapter implemented.
- [ ] Vanilla Goal adapter implemented.
- [ ] Vanilla Brain adapter implemented.
- [ ] Vanilla pathfinding adapter implemented.
- [ ] malus/cost field implemented.
- [ ] movement/custom control adapter implemented.
- [ ] bounded Decision Burst implemented.
- [ ] synchronized Decision Timeline implemented.
- [ ] AI Decision Packet implemented.
- [ ] default OFF.
- [ ] uncertainty/causal semantics preserved.

## MOD extensibility

- [ ] adapter registry/contract implemented.
- [ ] unknown MOD fallback safe.
- [ ] Hydra proof.
- [ ] Snow Queen proof.
- [ ] Knight Phantom proof.
- [ ] Ur-Ghast proof.
- [ ] no false conversion into Vanilla semantics.

## Final verification

- [ ] focused tests pass.
- [ ] complete repository suite passes.
- [ ] relevant Forge compilation passes.
- [ ] runtime/client tests performed where necessary.
- [ ] representative real-machine scenarios retained.
- [ ] performance/observer effect measured.
- [ ] final current handoff updated.
- [ ] no user/private runtime data committed.

---

# 22. Stop conditions / ask the user only when necessary

Continue autonomously through normal implementation choices.

Ask the user only if one of these is reached:

- destructive action outside disposable/test scope;
- credentials/account/permission change;
- ambiguity that materially changes the approved product behavior;
- need to use a production Minecraft save;
- unavoidable requirement for a substantially different architecture than the approved plans;
- local environment is missing an essential artifact that cannot be safely recreated/resolved.

Do not ask merely because a routine implementation choice exists.

---

# 23. Final principle

The finished system should let an implementation AI move through:

```text
Where is the relevant Minecraft code?
        ↓
Foundation Map

What does that AI mechanism really do?
        ↓
Vanilla / MOD TechHub research

What did this exact entity actually do?
        ↓
Motion Trace / projectile / hit evidence

What decision-relevant runtime state preceded it?
        ↓
Entity Decision Observatory

What is directly known, derived, or unavailable?
        ↓
Epistemic labels + exact provenance
```

The enduring rule is:

> **Observe what exists. Preserve exact identity. Draw only on request. Separate evidence from explanation. Extend by adapter instead of pretending every Mob thinks the same way.**
