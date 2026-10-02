# Entity Decision Observatory — Final Design / Implementation Plan

Status: **APPROVED DESIGN — 2026-10-02**

> This is the long-term KNEEKURA Water Tank Studio design for observing and presenting Minecraft entity decision-making. Vanilla Java AI is the first reference implementation, not the universal ontology.

**Primary goal:** Let an implementation AI or human select one exact entity and inspect the runtime facts that led from perception/state to an action, path, attack or movement result, while preserving the boundary between directly observed state, sampled state, derived presentation and unavailable information.

**Core rule:** KNEEKURA must never invent an entity's "thoughts." It displays decision-relevant runtime state and algorithm state when those states are actually exposed or instrumented.

**Related research:** `departments/minecraft/vanilla-ai/`

**Related result-layer design:** `2026-10-02-on-demand-motion-trace.md`

---

## 1. Product decision

The feature is named **Entity Decision Observatory**.

It is not:

- a Vanilla-only Goal debugger;
- a giant always-on HUD;
- a natural-language explanation engine that guesses why a Mob acted;
- a replacement AI implementation;
- a second Minecraft simulator.

It is a reusable observation and presentation layer.

Vanilla Java supplies the first adapters because it gives KNEEKURA a well-understood reference set:

- Goal / GoalSelector / targetSelector;
- Brain / Sensor / Memory / Activity / Behavior;
- PathNavigation / PathFinder / NodeEvaluator / Path;
- path type / pathfinding malus;
- MoveControl / LookControl / JumpControl / BodyRotationControl;
- special Mob-specific controllers;
- existing Mojang debug payloads and renderers.

MOD entities may then add adapters for their own state machines, utility systems, custom navigation, formation controllers, attack planners or any other decision architecture.

---

## 2. The abstraction boundary

Do **not** force every AI into:

```text
Goal -> Path -> Move
```

That is false for many Vanilla and MOD entities.

Instead, the common model is:

```text
INPUT
  what the system directly sensed / was given
        ↓
STATE
  current decision-relevant internal state
        ↓
CANDIDATE
  actions / positions / targets / paths considered
        ↓
EVALUATION
  directly exposed score, cost, condition or rejection state
        ↓
SELECTION
  what was selected
        ↓
EXECUTION
  controller / behavior / navigation / attack now being executed
        ↓
RESULT
  actual movement, projectile, hit, state transition or other outcome
```

Every stage is optional.

An adapter may expose only STATE + EXECUTION + RESULT. That is valid.

Missing stages are reported as `NOT_EXPOSED`, `NOT_APPLICABLE`, `NOT_CAPTURED` or another exact epistemic status. They are never synthesized to make the diagram look complete.

---

## 3. Decision Observation Model v1

Create a versioned neutral contract: **DecisionObservationModel v1**.

### 3.1 Required identity

Every observation or derived decision artifact must bind to the identities already used by LAB where applicable:

- debug session;
- run;
- RunSnapshot;
- process epoch;
- experiment / generation / request;
- Arena / arena epoch / revision;
- exact entity UUID or stable run-scoped entity identity;
- entity type;
- adapter identity + adapter version;
- game tick / gameTime / observation time;
- source Observation IDs or exact source trace rows.

No decision view may silently combine records from different run/epoch/entity identities.

### 3.2 Epistemic status

Every field/group carries one of:

- `DIRECT_OBSERVED`
- `SAMPLED_OBSERVED`
- `INSTRUMENTED_ALGORITHM_STATE`
- `DERIVED_FROM_OBSERVED`
- `COMMUNITY_HYPOTHESIS` — research only, never runtime truth
- `NOT_EXPOSED`
- `NOT_APPLICABLE`
- `NOT_CAPTURED`
- `UNKNOWN`

A human-friendly label may exist, but the machine-readable epistemic status is authoritative.

### 3.3 Causal language

The system may display:

```text
Goal A started
Path X was selected
Node N had costMalus 8
Mob moved to P
```

It must not automatically rewrite that as:

```text
The Mob chose Path X because Node N had malus 8.
```

unless the algorithm instrumentation actually establishes that relation.

Relationships have their own semantics:

- `DIRECT_RUNTIME_RELATION`
- `ALGORITHM_TRACE_RELATION`
- `TEMPORAL_ASSOCIATION`
- `DERIVED_SPATIAL_ASSOCIATION`
- `UNKNOWN_CAUSALITY`

This prevents a polished diagram from overstating certainty.

---

## 4. Adapter architecture

### 4.1 Principle

**Vanilla is an adapter family, not the schema.**

Conceptual layout:

```text
Vanilla GoalSelector --------┐
Vanilla Brain ---------------┤
Vanilla Pathfinding ---------┤
Vanilla custom controls -----┤
MOD state machine -----------┤
MOD utility AI --------------┼--> Decision Observation Model v1
MOD custom flight -----------┤
MOD boss phase --------------┤
MOD formation controller ----┤
future unknown AI -----------┘
                                      ↓
                          Decision Observatory
```

### 4.2 Adapter capability declaration

Every adapter declares exactly what it can expose.

Example:

```json
{
  "adapter": "kneekura:vanilla_goal_selector",
  "version": 1,
  "capabilities": {
    "target": "DIRECT",
    "scheduler": "DIRECT",
    "running_actions": "DIRECT",
    "candidate_actions": "PARTIAL",
    "candidate_scores": "NOT_EXPOSED",
    "rejection_reason": "PARTIAL",
    "navigation": "DIRECT",
    "search_frontier": "ON_DEMAND_INSTRUMENTED",
    "terrain_cost": "DIRECT_OR_DERIVED",
    "movement_controller": "DIRECT",
    "result_motion_trace": "AVAILABLE"
  }
}
```

The Viewer and AI packet use this declaration before asking for deeper data.

### 4.3 Generic fallback adapter

Unknown MOD entities still receive a conservative generic adapter when their superclass/API permits:

- exact identity;
- position/velocity;
- target if exposed by `Mob`;
- active navigation path if exposed;
- current move/look controller identity where safely available;
- Motion Trace result layer.

Everything else remains `NOT_EXPOSED`.

This provides useful baseline debugging without pretending that KNEEKURA understands the MOD's custom AI.

### 4.4 Source-specific adapters

A source-specific adapter may expose additional namespaced concepts such as:

- `twilightforest:hydra_head_state`
- `twilightforest:knight_formation`
- `modid:utility_score`
- `modid:flight_candidate`

Namespaced data remains available in raw/structured form even when no specialized visual renderer exists yet.

---

## 5. Shared visualization primitives

Adapters do not each invent a whole UI.

They emit a bounded set of generic visual primitives when appropriate:

- **POINT** — candidate/target/node;
- **VECTOR** — look, velocity, steering, desired direction;
- **PATH** — selected/planned/actual path;
- **REGION** — sensed/search/avoid/attack area;
- **VOXEL_FIELD** — terrain/path cost or hazard field;
- **CANDIDATE_SET** — alternatives with identifiers;
- **SCALAR_SCORE** — cost/weight/priority;
- **STATE_MACHINE** — current state and directly known transitions;
- **SCHEDULER_LANE** — active/blocked/eligible actions;
- **RELATION_EDGE** — target/owner/memory/source link;
- **EVENT_MARKER** — start/stop/reject/select/hit/teleport;
- **TEXT_FACT** — bounded exact fact that has no spatial form.

Specialized adapters may add a renderer, but must preserve the structured primitive/source identity underneath.

---

## 6. Vanilla reference adapters

Vanilla research must complete before exact implementation details are frozen, but the architecture reserves these adapters.

### 6.1 Vanilla Goal Scheduler Adapter

Observe, where exact access is established:

- goalSelector / targetSelector;
- registered goals;
- priority;
- flags;
- running state;
- control-flag ownership/locking;
- canUse / canContinue state only when safely instrumented;
- start / stop;
- replacement/interruption;
- disabled flags;
- target changes.

Primary view: **Scheduler Stack**.

Example:

```text
P1  MeleeAttackGoal       RUNNING      MOVE LOOK
P2  AvoidEntityGoal       BLOCKED      MOVE
P3  RandomStrollGoal      INACTIVE     MOVE
P8  LookAtPlayerGoal      RUNNING      LOOK
```

Do not label an inactive Goal as "rejected because X" unless X is instrumented.

### 6.2 Vanilla Brain Adapter

Observe:

- Sensor outputs where exposed;
- MemoryModule values/status/expiry where exposed;
- active/core/default Activity;
- running Behaviors;
- behavior transitions;
- memory preconditions where source/runtime instrumentation establishes them;
- WalkTarget / LookTarget / AttackTarget / PATH and other relevant memories.

Primary views:

- **Memory Board**
- **Activity / Behavior lanes**
- **target/memory spatial links**

### 6.3 Vanilla Navigation / Pathfinding Adapter

Observe or instrument:

- current PathNavigation;
- selected path;
- path node index / reachability;
- NodeEvaluator family;
- PathFinder search metadata;
- open nodes;
- closed nodes;
- targets;
- node predecessor;
- g / h / f;
- costMalus;
- PathType / BlockPathTypes;
- visited-node/search budget where established;
- collision/path acceptance state.

Primary views:

- **Chosen Path**
- **Search Frontier**
- **Node Cost Map**
- **Path Type / Malus Field**

This is the main implementation of the user's desired "candidate movement route" and "block penalty color" idea.

### 6.4 Vanilla terrain valuation view

For a selected Mob and bounded region, derive a world-space field from exact path-type/malus semantics.

The display may map values to color, but color is never the only encoding.

Use:

- color;
- numeric value on inspection;
- path type label;
- hatch/pattern or category marker;
- impassable/negative-malused distinction.

The visual must distinguish:

1. block/path type classification;
2. default type malus;
3. Mob-specific malus override;
4. final effective value used by the relevant evaluator where established.

Do not paint every block as "what the Mob thought" if the pathfinder never evaluated that block. A full regional malus map is a **query/derived field**; actually visited/evaluated nodes are a separate overlay.

### 6.5 Vanilla movement-control adapter

Observe selected controller state where meaningful:

- MoveControl;
- FlyingMoveControl;
- SmoothSwimmingMoveControl;
- LookControl;
- JumpControl;
- BodyRotationControl;
- custom nested controls such as Ghast movement.

Primary view:

- desired/operation target;
- steering vector;
- speed modifier;
- orientation target;
- directly exposed reach/collision test result.

This is critical for entities that do not use ordinary Navigation paths.

---

## 7. MOD and custom-AI extension model

### 7.1 State-machine adapter

For bosses/entities whose real AI is an explicit state machine:

```text
STATE
  current phase/state
CANDIDATE
  directly exposed allowed transitions/actions
EVALUATION
  cooldown, distance gate, health phase, attack budget...
SELECTION
  selected next action/state
EXECUTION
  active state
RESULT
  motion/projectile/hit
```

### 7.2 Utility/scoring adapter

For weighted decision systems:

- candidate ID;
- score;
- component scores if directly exposed;
- eligibility;
- selected candidate;
- tie-break/random seed/result if directly observable.

A score visualization can be shown as a bounded table/bar view and spatial candidates where applicable.

### 7.3 Custom movement / flight adapter

For Ghast-like or MOD custom flight:

- current move target;
- candidate positions if the algorithm actually generates them;
- reach/collision tests;
- steering target;
- rejected candidates if instrumented;
- actual Motion Trace.

Do not fabricate an A* path for direct-flight AI.

### 7.4 Group / formation adapter

For coordinated AI:

- leader/group identity;
- formation state;
- slot assignment;
- shared target;
- group progress/clock;
- local action;
- synchronization transitions.

The Viewer may show relations across multiple entities, but one exact selected group/subject remains the scope root.

### 7.5 Adapter authoring contract

A future adapter API should conceptually provide:

- `describeCapabilities()`
- `captureSnapshot(entity, context)`
- `captureBurst(entity, context, request)`
- `emitStructuredFacts()`
- `emitVisualPrimitives()`

Exact Java interfaces are deferred until the Vanilla research identifies safe hook points for 1.20.1 Forge.

Adapters must be versioned and declare:

- target mod ID/version;
- Minecraft/loader compatibility;
- source class/method provenance;
- instrumentation method (public API, event, mixin, AT, reflection, etc.);
- observer-effect risk;
- supported epistemic levels.

---

## 8. Recording versus viewing

The user's desired UX remains:

> **record/retain what is reasonably safe, draw nothing by default, inspect only when requested.**

But decision internals have different cost classes.

### 8.1 Baseline retained state

Within the already selected/registered entity scope, retain low-cost decision state where available:

- target;
- key memories;
- running Goal/Behavior;
- state/phase;
- selected path;
- path progress;
- controller target;
- relevant transitions.

No visual overlay is active by default.

### 8.2 Deep decision burst

High-volume or invasive internals are **not** assumed safe for continuous capture.

Examples:

- every A* open/closed node on every search;
- every rejected random-position candidate;
- every Goal eligibility call;
- per-tick utility score matrices;
- full sensor candidate populations.

These use an explicit bounded **Decision Burst Capture**:

```text
select exact subject
      ↓
arm declared decision channels
      ↓
capture N ticks / one decision / one path search
      ↓
stop instrumentation
      ↓
retain exact bounded artifact
```

This is still "look when needed", but it avoids permanently perturbing AI performance just to preserve hypothetical debug data.

### 8.3 Optional ring buffer

If profiling proves cheap enough for a channel, a small bounded rolling buffer may retain recent decision events before the user/AI asks to inspect them.

The buffer must declare:

- retention window;
- drop/eviction count;
- source cadence;
- observer overhead.

No channel becomes always-on merely because the UI would benefit.

---

## 9. Human presentation

### 9.1 Default

**Decision View OFF.**

Selecting an entity shows a compact capability/status card, not every overlay.

Example:

```text
Entity Decision Data

Goal scheduler       AVAILABLE
Brain                NOT_APPLICABLE
Navigation           AVAILABLE
Search frontier      CAPTURE REQUIRED
Terrain malus        AVAILABLE
Custom AI adapter    NONE
Motion history       AVAILABLE
```

### 9.2 Inspect layers

The human can enable only the needed layer:

- Summary;
- Target / perception;
- Goal/Behavior;
- Memory;
- Candidates;
- Pathfinding;
- Terrain cost;
- Controller;
- State machine;
- Timeline;
- Result motion/projectile.

### 9.3 Spatial overlay

Use the same presentation philosophy as Motion Trace:

- derived client-side overlay;
- no gameplay particles/entities just to draw debug data;
- raw evidence remains separate;
- fixed labels/legend;
- hidden by default.

Examples:

**Path search**
- selected path: strong line;
- open nodes: one marker grammar;
- closed nodes: another;
- target nodes: distinct symbol;
- parent direction optionally shown;
- node cost available on inspect.

**Malus**
- bounded voxel/floor field;
- effective value + PathType on inspect;
- actually evaluated nodes visually distinct from merely queryable regional values.

**Candidates**
- candidate points/volumes with IDs;
- selected candidate emphasized;
- directly rejected candidates annotated only with known reason/status.

### 9.4 3D and orthographic views

Use progressive disclosure:

```text
Level 0: compact structured decision summary
Level 1: 2D table/timeline + plan/elevation
Level 2: fixed-isometric 3D decision scene
Level 3: live Minecraft client decision overlay
```

3D is useful for spatial decision systems but is not mandatory for every decision type.

---

## 10. AI-facing Decision Packet

The implementation AI should not receive a screenshot of a giant debug HUD as its primary input.

Return a **Decision Observation Packet**.

### 10.1 Level 0

Compact machine-readable summary:

- adapter/capabilities;
- current target/state;
- running scheduler entries;
- selected action/path;
- known constraints;
- available drill-down channels;
- exact evidence identity.

### 10.2 Drill-down requests

Examples:

```text
show path search for subject A around tick 420
show effective path malus in radius 8
show Goal scheduler transitions from 400..440
show Brain memories that changed before attack
show custom state-machine transition around projectile spawn
```

Requests are typed/bounded. Free text is translated into typed read-only debug requests; it is not itself authority.

### 10.3 Decision packet ordering

Recommended order:

1. exact identity + capability map;
2. structured state;
3. selected action/path;
4. candidate/evaluation summary if available;
5. event timeline;
6. spatial plan/elevation;
7. fixed 3D artifact if needed;
8. raw/source drill-down references.

This keeps token/image cost proportional to the debugging question.

### 10.4 Result correlation

Decision Packet may link to:

- On-Demand Sampled Motion Trace;
- projectile trace;
- hit/damage events;
- network events;
- render/animation evidence.

The link is temporal/evidence correlation unless direct causal instrumentation proves more.

---

## 11. Decision timeline

One of the highest-value views is a synchronized timeline:

```text
t=400  Target -> Player
t=402  Goal A START
t=405  Path search #17
t=405  candidate/path selected
t=410  Navigation nextNode changed
t=418  Goal B START / Goal A STOP
t=420  Projectile spawned
t=421..435 actual Motion Trace
t=436  Hit event
```

Each event links back to its exact source.

This creates the debugging chain:

```text
what state existed
      ↓
what was considered
      ↓
what was selected
      ↓
what started/stopped
      ↓
what path/control was issued
      ↓
what actually happened
```

without pretending that mere temporal adjacency proves cause.

---

## 12. Research-before-instrumentation gate

Do not implement the deep Vanilla adapters from assumptions.

The `departments/minecraft/vanilla-ai/` research must establish at least:

- complete GoalSelector lifecycle;
- Brain Sensor/Memory/Activity/Behavior semantics;
- PathFinder/NodeEvaluator/open/closed/cost lifecycle;
- BlockPathTypes and effective malus rules;
- movement-control families;
- special Mob families that bypass normal navigation;
- Vanilla debug payload/renderer plumbing;
- server/client authority;
- likely observer cost of candidate-level instrumentation;
- representative Mob matrix.

Only then freeze the exact Java hook/interface surface.

This plan fixes the **architecture**, not unverified method-body claims.

---

## 13. Representative validation matrix

At minimum validate the design against structurally different entities.

### Vanilla

1. Zombie — conventional Goal + ground navigation.
2. Skeleton — target + navigation + ranged attack.
3. Villager or Brain-heavy Mob — Brain/Memory/Activity.
4. Ghast — custom/direct flight control.
5. Phantom — specialized aerial behavior.
6. Slime — nonstandard movement control.
7. aquatic Mob — swimming navigation/control.
8. Enderman — targeting + teleport/non-path behavior where applicable.

### MOD

Use already researched structurally different examples:

1. Twilight Forest Hydra — coordinator + per-head state machines.
2. Snow Queen — explicit phase + phase-specific Goals.
3. Knight Phantom — group/formation state.
4. Ur-Ghast — custom flight/attack state.

The architecture passes only if these can be represented without lying or forcing every case into Goal/Path semantics.

---

## 14. Performance rules

- UI render OFF by default.
- Exact subject selection; no unbounded world scan.
- Baseline channels sampled/bounded.
- Deep candidate capture explicitly armed and time/size bounded.
- Instrumentation overhead measured separately per adapter/channel.
- Search-frontier capture must not silently change search budget/order.
- Visualization generation occurs outside authoritative decision logic where practical.
- Any unavoidable perturbation is recorded and may invalidate behavior assertions.
- Do not retain duplicate copies of state already preserved by the Evidence Store/trace layer unless a versioned artifact requires an immutable cut.

---

## 15. Failure and uncertainty rules

The Observatory must fail honestly.

Examples:

- custom MOD AI unknown -> `CUSTOM_DECISION_NOT_EXPOSED`;
- path absent -> do not show empty "candidate path" as proof that no route was considered;
- goal inactive -> do not invent rejection cause;
- candidate capture armed too late -> `NOT_CAPTURED`;
- missing samples -> visible timeline/trace gap;
- adapter/runtime version mismatch -> reject adapter data;
- instrumentation changed relevant behavior -> mark experiment `INCONCLUSIVE` where required;
- private/internal state inaccessible -> report capability gap.

---

## 16. TechHub knowledge-asset integration

This feature is also a research sink.

Every analyzed MOD may contribute a durable AI record:

```text
AI Family
Decision Adapter availability
Observed stages
Unavailable stages
Scheduler model
Navigation model
State-machine model
Candidate/scoring model
Movement controller
Observer hooks
Water Tank compatibility
Version portability
Evidence locators
```

Therefore the same research that improves MOD implementation also expands Decision Observatory coverage.

The existing per-MOD `AI-BEHAVIOR.md` remains the descriptive engineering asset. Adapter-specific compatibility may later be indexed in a common catalog rather than duplicating whole reports.

---

## 17. Implementation phases

### Phase 0 — Complete Vanilla research

- [ ] Complete Goal system map.
- [ ] Complete Brain system map.
- [ ] Complete navigation/pathfinding/malus map.
- [ ] Complete movement-control and special-Mob map.
- [ ] Complete Vanilla debug infrastructure map.
- [ ] Build representative Vanilla Mob AI catalog.
- [ ] Identify safe 1.20.1 Forge observation hooks and observer risks.

### Phase 1 — Decision Observation Model

- [ ] Define versioned schema and identity rules.
- [ ] Define epistemic statuses and causal-relation semantics.
- [ ] Define capability declaration.
- [ ] Define generic visual primitives.
- [ ] Add fixtures for partial/unavailable capabilities.

### Phase 2 — Generic Mob baseline adapter

- [ ] Expose conservative common Mob state.
- [ ] Integrate current LAB AI_TARGET / NAVIGATION / movement observations.
- [ ] Preserve unknown custom AI as unknown.
- [ ] Add compact capability/status view.

### Phase 3 — Vanilla Goal + Brain adapters

- [ ] Goal scheduler snapshot/transition contract.
- [ ] Brain Memory/Activity/Behavior contract.
- [ ] Human scheduler/memory views.
- [ ] AI Decision Packet structured output.
- [ ] Verify no guessed rejection/causal reasons.

### Phase 4 — Vanilla pathfinding + malus adapter

- [ ] Current path and path progress.
- [ ] Effective path-type/malus query.
- [ ] Bounded path-search burst capture.
- [ ] open/closed/target/cost visualizations where exact.
- [ ] distinguish evaluated nodes from regional queried cost field.

### Phase 5 — movement/custom Vanilla adapters

- [ ] Direct/custom movement control contract.
- [ ] Ghast-like flight case.
- [ ] Phantom/Slime/aquatic representative cases.
- [ ] Link controller intent to Motion Trace result without overstating causality.

### Phase 6 — synchronized decision timeline

- [ ] Unify scheduler/memory/path/controller events by exact tick/source identity.
- [ ] Link to Motion Trace/projectile/hit evidence.
- [ ] Provide bounded before/after windows.
- [ ] Preserve gaps and sampling semantics.

### Phase 7 — MOD adapter SDK/registry

- [ ] Freeze adapter registration API after Vanilla hooks are proven.
- [ ] Namespaced capability extensions.
- [ ] Adapter provenance/version compatibility.
- [ ] Generic fallback behavior.
- [ ] Source-specific visual primitive extensions.

### Phase 8 — MOD proof adapters

- [ ] Hydra state-machine proof.
- [ ] Snow Queen phase proof.
- [ ] Knight Phantom formation/group proof.
- [ ] Ur-Ghast custom flight proof.
- [ ] Demonstrate that all integrate with the same Decision Packet without semantic falsification.

### Phase 9 — performance and final acceptance

- [ ] Measure baseline observer overhead.
- [ ] Measure deep burst overhead.
- [ ] Verify hidden/default-off UI cost.
- [ ] Verify bounded storage/retention.
- [ ] Run existing LAB evidence/Viewer regressions.
- [ ] Run real-machine representative scenarios.
- [ ] Independent adversarial review of epistemic/causal claims.

---

## 18. Acceptance criteria

The design is implemented successfully only when:

1. One exact entity can be selected without world-wide observation.
2. The system first reports what decision data is actually available.
3. Vanilla Goal entities expose scheduler state without guessed motives.
4. Brain entities expose relevant memory/activity/behavior state.
5. Ground pathfinding can show selected path and, when explicitly captured, search/cost details.
6. Block/path malus can be inspected spatially while distinguishing queried terrain values from nodes actually evaluated.
7. A custom-flight Vanilla entity can be debugged without fabricating an A* path.
8. Decision events can be correlated with actual Motion Trace/projectile results.
9. Deep candidate/search instrumentation is bounded and never silently always-on.
10. Missing/private/custom state remains visibly unavailable.
11. An unknown MOD Mob still gets a conservative generic baseline where possible.
12. A source-specific MOD adapter can add namespaced state/candidates/scores without changing the common schema.
13. State-machine, formation and custom-flight MOD examples fit without being falsely converted into Vanilla Goal semantics.
14. Human views and AI Decision Packets use the same underlying identity-bound decision facts.
15. Raw Minecraft evidence remains separate from derived decision overlays.
16. No second evidence database is introduced.
17. No rendering overlay mutates gameplay state.
18. Observer effect and instrumentation uncertainty are represented explicitly.
19. Existing Water Tank functionality remains usable with Decision View disabled.
20. Research artifacts remain reusable independently of the Water Tank implementation.

---

## 19. Non-goals

Not required for v1:

- natural-language mind reading;
- universal automatic explanation of "why";
- always-on capture of every candidate in every entity;
- perfect support for arbitrary closed-source MOD AI without an adapter;
- counterfactual simulation;
- reinforcement-learning introspection;
- automatic AI-quality scoring;
- a universal behavior-tree editor;
- replacing the MOD's own AI architecture.

A future counterfactual/replay tool must be a separate experiment system with its own authority and must never be confused with observed runtime thought.

---

## 20. Final architecture

```text
                Vanilla / MOD runtime
                         │
                 source-specific adapter
                         │
                 capability declaration
                         │
              Decision Observation Model
                         │
          ┌──────────────┼──────────────┐
          │              │              │
   structured facts   timeline    visual primitives
          │              │              │
          └──────────────┼──────────────┘
                         │
                 Decision Observatory
                         │
          ┌──────────────┴──────────────┐
          │                             │
       Human                         AI Packet
          │                             │
          └──────────────┬──────────────┘
                         │
        Motion Trace / Projectile / Hit / Render evidence
```

The persistent design principle is:

> **Observe what exists. Declare what is unavailable. Visualize only what the evidence supports. Extend by adapter, not by pretending every Mob thinks the same way.**
