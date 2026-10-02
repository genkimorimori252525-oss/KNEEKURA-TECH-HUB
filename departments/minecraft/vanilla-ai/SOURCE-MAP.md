# Vanilla AI Source Map

Status: **initial source ledger — research not complete**

## Source precedence

### Tier A — ANCHOR structural evidence

Use exact Minecraft 1.20.1 / Forge 47.2.x mappings and API documentation first.

Current primary families:

- Forge 1.20.1 JavaDocs:
  - `Mob`
  - `Goal`, `WrappedGoal`, `GoalSelector`
  - `DebugPackets`
  - `PathfindingDebugPayload`
  - `GoalDebugPayload.DebugGoal`
  - `BrainDebugPayload.BrainDump`
  - `PathfindingRenderer`
  - `GoalSelectorDebugRenderer`
  - `BrainDebugRenderer`
- mappings.dev 1.20.1:
  - `Mob`
  - `Brain`
  - `GoalSelector` / `WrappedGoal`
  - `PathNavigation`
  - `PathFinder`
  - `Path`
  - `Node`
  - `NodeEvaluator` families
  - `BlockPathTypes`
  - `MoveControl`
  - Mob-specific nested AI/control classes

Runtime/decompiled inspection in a legally obtained local development environment may be used to answer method-body questions that signatures/mappings cannot establish. Do not commit a third-party full decompiled Minecraft source tree.

## Tier B — implementation precedents

Open-source Mods/libraries are useful for seeing how real projects expose or extend vanilla AI/debug machinery.

Initial precedent:

- `MehVahdJukaar/Moonlight`
  - `DebugPacketsMixin`
  - `DebugRenderersCommand`
  - `DebugRendererMixin`
  - current inspected source injects pathfinding and Goal debug payload production and renders vanilla debug renderers behind explicit toggles.

Treat the exact upstream commit/version as a separate SourceSnapshot. Do not assume its current implementation is identical to Forge 1.20.1.

## Tier C — technical behavior references

- Minecraft Wiki / technical wiki material
- modding documentation/tutorials
- issue discussions with reproducible technical detail

Useful for vocabulary and behavior expectations; verify implementation details against Tier A.

## Tier D — community experiments

Reddit, especially technical Minecraft communities, is useful for:

- edge cases;
- unexpected pathfinding behavior;
- blocks that produce surprising navigation choices;
- reproduction ideas;
- practical questions that expose what a debugger needs to explain.

Community claims are hypotheses until reproduced or tied to source/runtime evidence.

## Initial ANCHOR facts to preserve

### Mob-level state

Minecraft 1.20.1 `Mob` owns:

- `goalSelector`;
- `targetSelector`;
- `navigation`;
- `moveControl`;
- `lookControl`;
- `jumpControl`;
- `bodyRotationControl`;
- `sensing`;
- a `Map<BlockPathTypes, Float>` pathfinding-malus override map;
- `getPathfindingMalus` / `setPathfindingMalus`;
- `sendDebugPackets`.

### Goal scheduler

`GoalSelector` exposes/contains:

- available goals;
- running goals;
- disabled flags;
- per-flag locked goal ownership;
- tick scheduling.

`WrappedGoal` carries:

- goal;
- priority;
- running state;
- replacement/continuation/interruption semantics.

### Brain scheduler

`Brain` contains:

- memories;
- sensors;
- behaviors grouped by integer priority and Activity;
- activity requirements;
- memory-erasure rules;
- core/active/default activities;
- running behavior access.

### Path search

`PathFinder` owns:

- a NodeEvaluator;
- maximum visited-node budget;
- neighbor work array;
- BinaryHeap open set.

`Path` can carry:

- final path nodes;
- open-set debug nodes;
- closed-set debug nodes;
- target debug nodes;
- current/next node index;
- target/reachability.

`Node` carries:

- world x/y/z;
- g/h/f-like cost fields;
- predecessor;
- closed/visited state;
- walked distance;
- `costMalus`;
- `BlockPathTypes`.

`WalkNodeEvaluator` maps world/block/collision state into path types and accepted/rejected nodes.

### Existing vanilla debug vocabulary

1.20.1 exposes payload/render concepts for:

- pathfinding;
- Goal selector;
- Brain;
- Bee/hive/POI and other world diagnostics.

`GoalDebugPayload.DebugGoal` already models:

- priority;
- running state;
- name.

`BrainDebugPayload.BrainDump` already models a useful aggregate including:

- UUID/entity identity;
- position/health;
- current path;
- activities;
- behaviors;
- memories;
- POIs/potential POIs;
- entity-specific fields such as inventory/gossip/anger for supported use cases.

`PathfindingRenderer` contains display switches/vocabulary for open/closed nodes, cost malus and node types.

## Important exception found immediately

Do not assume every moving Mob produces a normal A* `Path`.

Minecraft 1.20.1 Ghast has a custom `GhastMoveControl` with its own collision/reach test. Therefore a universal KNEEKURA "candidate path" overlay must support multiple decision-source families:

- NAVIGATION_PATH;
- DIRECT_MOVE_TARGET;
- CUSTOM_REACH_TEST;
- BRAIN_WALK_TARGET;
- GOAL_LOCAL_CANDIDATE;
- MOD_CUSTOM_STATE;
- UNKNOWN / NOT_EXPOSED.

This exception is a primary reason to complete the per-Mob catalog before finalizing the Decision Debug View.

## Research gaps

Still required before calling this study complete:

- exact GoalSelector tick/replacement flow and cadence in 1.20.1;
- complete Brain Sensor/Memory/Activity/Behavior map;
- exact default `BlockPathTypes` malus values and per-Mob overrides;
- open/closed set capture lifecycle and whether normal 1.20.1 runtime populates debug arrays without instrumentation;
- targetSelector semantics and targeting conditions;
- full navigation family comparison: ground/flying/water/amphibious/wall-climb;
- random-position generators and candidate scoring;
- special Mob controller families;
- full vanilla Mob inventory and inheritance-aware AI catalog;
- vanilla debug packet call sites and disabled/stubbed behavior in production;
- server/client authority boundaries;
- performance cost of exposing search candidates;
- differences from modern FRONTIER versions;
- reproducible runtime probes for selected representative Mobs.

## Promotion rule

A finding may enter `DECISION-VIEW-REQUIREMENTS.md` only after the research can say where that datum comes from and whether it is:

- exact runtime state;
- sampled runtime state;
- reconstructed from exact state;
- derived visualization;
- unavailable for that AI family.
