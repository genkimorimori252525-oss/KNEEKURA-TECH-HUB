# Representative Decision catalog — retained native-r13 reconciliation

This reconciles section14 of [the approved handoff](../LOCAL-EXECUTION-HANDOFF-2026-10-02.md) against eight actually captured Vanilla entity families. It is a bounded component catalog, not completion of every integrated scenario or a pure-Vanilla runtime claim. The Minecraft1.20.1 / Forge47.2.0 instance also loaded MODs: sampled registered Goal lists contain `mods.flammpfeil.slashblade.entity.ai.StunGoal` for Zombie, Skeleton, Villager, Dolphin and Enderman. An empty non-Vanilla list for the other three subjects describes only their bounded captured lists.

## Exact acquisition and read-only interpretation

- Producer: `85794a3ebb46e8730044e065e9d818816f5a0111`; current consumer: `3f8e7946262692ac2a4e2a4c042ca550f2ebc0b5`.
- Run: `run-20261003120721-a046e4f3a796`; session: `sess-20261003120721-6f4d00107e1b`; snapshot: `snapshot-20261003120721-4718d823bfcf`; process epoch1; Arena epoch0.
- Canonical7,603 unique observations, SHA256 `eac7b48884035142148cfa98a3bf23ed0f883322bf91be7fc2676d19ad31cb0d`; finalization SHA256 `97e574d2757d73b15a0215f33ef2d86d2c6a104fb64b9f44335fb72ecb554521`.
- Each family has56 state snapshots and256 original callback records. Every burst reaches `EVENT_BUDGET`; a late callback or unarmed stage remains unknown. Acquisition conditions, clean finalization and unchanged original85-file manifest are documented in [the original r13 receipt](NATIVE-REPRESENTATIVE-OBSERVER-ACCEPTANCE-2026-10-03.md).
- The current production `observeDebugWorkspaceDecision` and `buildRetainedDecisionPresentation` were replayed read-only, filtering SERVER side, exact UUID and selection revision within the same full identity. Canonical bytes remain unchanged. No current callback is inserted into this older run.

In the tables, `S:n` means `n` **SAMPLED_OBSERVED** facts; `D:n` means `n` **DIRECT_OBSERVED** original invocation/return facts; `A:n` means `n` **INSTRUMENTED_ALGORITHM_STATE** facts captured at an original callback. Directness and acquisition mode are separate: all `D`/`A` facts here were acquired by the explicitly armed finite burst. `NC` is the production overview's **NOT_CAPTURED**, not `false`, a negative decision or proof that a stage does not apply.

Counts describe the adapter's retained facts before compact overview truncation. Sampled facts represent the adapter's latest corresponding state, not all56 snapshots. A stage marked `AVAILABLE` can still contain individual values marked `NOT_EXPOSED`. Registered Goal lists do not establish evaluated candidates or a selection reason. Successful start/stop returns are EXECUTION receipts and do not retrospectively populate SELECTION.

## All seven Decision stages

| Family / revision | INPUT | STATE | CANDIDATE | EVALUATION | SELECTION | EXECUTION | RESULT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Zombie /9 | NC | S:6 | NC | D:160 + A:1 | NC | S:3 + D:94 | D:1 |
| Skeleton /10 | NC | S:6 | NC | D:253 | NC | S:3 + D:3 | NC |
| Villager /11 | D:8 | S:6 | NC | D:133 | NC | S:3 + D:115 | NC |
| Ghast /12 | NC | S:6 | NC | D:103 | NC | S:3 + D:153 | NC |
| Phantom /13 | NC | S:6 | NC | D:87 | NC | S:3 + D:169 | NC |
| Slime /14 | NC | S:6 | NC | D:103 | NC | S:3 + D:153 | NC |
| Dolphin /15 | NC | S:6 | NC | D:160 | NC | S:3 + D:96 | NC |
| Enderman /16 | NC | S:6 | NC | D:161 | NC | S:3 + D:95 | NC |

Zombie's RESULT is an original `PATH_SEARCH_RESULT`; its algorithm-state fact is `PATH_SEARCH_STATE`. Neither establishes that the final route was executed successfully. Skeleton's247 base-malus returns are not247 completed searches. Villager's eight INPUT facts are original sensor-scan returns; they do not reveal every sensed value or the reason for a later behavior.

## Original burst records and lookup anchors

Observation suffixes below use the exact prefix **`obs:forge-runtime:43416:`**. Each subject UUID uses **`22222222-3333-4444-5555-00000000000`** followed by its family number1..8. `first` means the first record of that callback kind in this family/revision, not first-ever execution.

| Family | Callback kind: count (first suffix) |
| --- | --- |
| Zombie | GOAL_CONTINUATION_RETURN:24(2100); GOAL_ELIGIBILITY_RETURN:76(2101); CONTROL_TICK_RETURN:89(2104); GOAL_STOP_RETURN:3(2182); GOAL_START_RETURN:2(2205); BASE_MALUS_RETURN:60(2206); PATH_SEARCH_STATE:1(2266); PATH_SEARCH_RESULT:1(2267) |
| Skeleton | CONTROL_TICK_RETURN:3(2593); GOAL_CONTINUATION_RETURN:1(2596); GOAL_ELIGIBILITY_RETURN:5(2597); BASE_MALUS_RETURN:247(2601) |
| Villager | GOAL_ELIGIBILITY_RETURN:10(3083); BEHAVIOR_TRY_START_RETURN:123(3084); BEHAVIOR_STOP_RETURN:19(3090); BEHAVIOR_TICK_OR_STOP_RETURN:24(3091); BRAIN_TICK_RETURN:18(3093); CONTROL_TICK_RETURN:54(3094); SENSOR_SCAN_RETURN:8(3097) |
| Ghast | CONTROL_TICK_RETURN:153(3481); GOAL_CONTINUATION_RETURN:78(3484); GOAL_ELIGIBILITY_RETURN:25(3487) |
| Phantom | GOAL_CONTINUATION_RETURN:87(3972); CONTROL_TICK_RETURN:169(3975) |
| Slime | CONTROL_TICK_RETURN:153(4444); GOAL_CONTINUATION_RETURN:78(4447); GOAL_ELIGIBILITY_RETURN:25(4450) |
| Dolphin | GOAL_ELIGIBILITY_RETURN:144(4870); GOAL_CONTINUATION_RETURN:16(4871); CONTROL_TICK_RETURN:96(4880) |
| Enderman | CONTROL_TICK_RETURN:93(5307); GOAL_CONTINUATION_RETURN:23(5310); GOAL_ELIGIBILITY_RETURN:138(5311); GOAL_STOP_RETURN:1(5361); GOAL_START_RETURN:1(5536) |

## Sampled state and derived Motion

Motion samples are actual SERVER position records. Distances, speed, segments and gaps are **DERIVED** from these records; they are a separate presentation layer and do not fabricate a Decision RESULT. Every displayed point retains its source observation ID. PLAN_XZ, ELEVATION and fixed isometric are projections of these same samples.

| Family | SERVER position samples / derived gaps | First SERVER state / snapshot suffix | Game-tick window | Declared Navigation / Path cache in final presentation |
| --- | --- | --- | --- | --- |
| Zombie | 50 /0 | 2096 /2099 | 44068..44343 | NOT_CAPTURED /AVAILABLE |
| Skeleton | 52 /1 | 2589 /2592 | 44348..44623 | NOT_CAPTURED /NOT_CAPTURED |
| Villager | 28 /3 | 3079 /3082 | 44628..44903 | AVAILABLE /NOT_CAPTURED |
| Ghast | 56 /0 | 3477 /3480 | 44908..45183 | NOT_CAPTURED /NOT_CAPTURED |
| Phantom | 56 /0 | 3968 /3971 | 45188..45463 | NOT_CAPTURED /NOT_CAPTURED |
| Slime | 25 /5 | 4440 /4443 | 45468..45743 | NOT_CAPTURED /NOT_CAPTURED |
| Dolphin | 56 /0 | 4866 /4869 | 45748..46023 | AVAILABLE /NOT_CAPTURED |
| Enderman | 48 /3 | 5303 /5306 | 46028..46303 | NOT_CAPTURED /NOT_CAPTURED |

Navigation status above is the bounded consumer's final presentation, not absence of a path throughout the entire window. For example, initial Zombie2099 and Enderman5306 snapshots contain a declared route; neither is an original open/closed frontier or executed Motion. All eight related-projectile layers are `NOT_CAPTURED` in this producer generation.

## Availability and narrowly scoped applicability

- All eight snapshot families expose Goal scheduler, base Brain memory/activity, navigation and movement-control sections. Each Brain snapshot reports `activeTickMechanismStatus=NOT_EXPOSED`; an empty memory map/base Brain object does not prove active Brain scheduling, and does not justify marking the whole Brain stage `NOT_APPLICABLE`. Villager additionally has actual original Brain/sensor/behavior callbacks. Its MOD `StunGoal` also has actual eligibility returns; its Goal layer is not globally inapplicable.
- Eligibility booleans are direct returns. Rejection/selection reasons and exact internal call-site explanations remain `NOT_EXPOSED` unless separately captured. Temporal adjacency remains `UNKNOWN_CAUSALITY`/`TEMPORAL_ASSOCIATION` rather than an invented causal edge.
- Ghast3480 exposes base wanted coordinates and `Ghast$GhastMoveControl`; Phantom3971 and Slime4443 expose their custom controller class names. `fieldScope=BASE_CONTROL_FIELDS_ONLY` means custom private targets/phase/jump delay/reach tests are **NOT_EXPOSED by that sampled field set**. A Phantom base `WAIT` value does not prove that its private controller is idle.
- The conventional ground-A* interpretation is **not applicable to the observed custom Ghast/Phantom steering mechanism**, as distinguished in [movement source research](MOVEMENT-CONTROLS.md). This scoped statement does not classify an entire Decision stage, entity navigation object or every future action as inapplicable. This capture establishes no stage-wide `NOT_APPLICABLE` entries.
- Dolphin4869 exposes `WaterBoundPathNavigation`, `SmoothSwimmingLookControl` and `SmoothSwimmingMoveControl`; the pool trial does not cover every aquatic algorithm. Enderman's y=-60 position does not establish a teleport cause or successful teleport return in r13.

## Later evidence remains separately identified

Later producers supply additional bounded scenarios: [R16–R24 typed teleport, ranged results, Brain and pursuit](NATIVE-RESULT-ACCEPTANCE-2026-10-04.md), [R29 Knight coordination](KNIGHT-COORDINATION-RETURN-2026-10-04.md), [R30 neighbor returns](PATH-NEIGHBOR-RETURN-2026-10-04.md), [R31/R32 effective malus](EFFECTIVE-MALUS-RETURN-2026-10-04.md), and [R33–R39 related native display/raw separation/labels](NATIVE-PROJECTILE-ID-LABELS-2026-10-04.md). Their run/process/Arena/UUID/revision/source boundaries remain separate. They do not retroactively convert this catalog's NC cells to captured facts.

Section14's eight-family component classification is now recorded. Full section15 diagnostic acceptance, all-algorithm semantics, custom flight reach/candidates, complete search/cost/rejection explanations, full Boss battle and broad observer/GPU/resize acceptance remain work in progress in [the execution matrix](REMAINING-EXECUTION-MATRIX-2026-10-04.md).
