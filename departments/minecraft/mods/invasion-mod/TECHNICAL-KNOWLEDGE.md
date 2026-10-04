# Technical Knowledge — reusable Invasion techniques

This document records techniques, not copy/paste recipes. Legacy code is read to recover invariants; the 1.20.1 track shows a safer modern expression of several invariants.

## T01 — Action-bearing route search

**Problem:** a siege mob cannot reach the objective through a purely traversable-block graph.

**Mechanism:** make an operation part of node state. A path edge may mean “walk here”, “dig this collision cell”, “place a bridge”, “construct a ladder/tower” or “build scaffold upward”. Cost includes the work required.

**Why it matters:** the planner can compare a longer open route against a shorter destructive route instead of using “walk until stuck, then randomly break.”

**Legacy evidence:** \`PathNode.action\`, \`PathAction\`, entity successor/cost callbacks, \`NavigatorEngy.handlePathAction\`.

**1.20.1 expression:** vanilla \`Node\` receives \`PathAction\` through \`PathNodeMixin\`; \`IMLandPathNodeMaker\` and \`BuilderIMMobNavigation\` create actionable nodes.

**KNEEKURA guidance:** reuse the invariant. Prefer the 1.20.1 vanilla-pathfinder extension over porting \`PathfinderIM\`.

## T02 — Counterfactual infrastructure selection

**Problem:** vertical access could be built in many places; choosing the first possible tower wastes work or still fails.

**Mechanism:** first generate a route allowing hypothetical scaffolding. Extract candidate scaffold segments. Re-run pathfinding with one candidate marked as present. Prefer the candidate that produces a terminating path with the best route cost.

**Why it matters:** construction becomes a planning decision rather than a hardcoded reaction.

**Modern preservation:** \`ScaffoldGenerator.findCheapestReachable\` still performs the same counterfactual re-search on a headless pathfinder.

**Generalization:** bridges, breaches, doors, ladders, temporary cover or demolition points can all be treated as hypothetical world edits evaluated by re-search.

## T03 — Density as a non-block terrain layer

**Problem:** many attackers select the same cheapest corridor and jam each other.

**Mechanism:** overlay mob density on pathing terrain. Do not mutate blocks. Add a density multiplier to route cost.

**Legacy:** exact-node count capped at seven, recomputed every 20 ticks. Ordinary attackers are more density-averse than the engineer.

**1.20.1:** density accumulation is spread across a 20-tick period, reducing the periodic full-scan spike.

**KNEEKURA guidance:** keep tactical overlays separate from physical block state. The same layer can later hold danger, friendly reservations or temporary no-go scores.

## T04 — Costed terrain transactions

**Problem:** instant block edits make siege units unfair and create race conditions between movement and world changes.

**Mechanism:** submit ordered \`ModifyBlockEntry\` jobs. Each entry has a cost; the modifier checks reach, waits cost ticks, performs one change, reports status, then advances.

**Useful properties:** explicit ownership, cancellation, reach boundary, block-change callback and completion callback.

**Modern improvement:** typed \`SUCCESS / OUT_OF_RANGE / UNMODIFIABLE\` results; a failed entry cancels the job rather than allowing later edits to proceed on a broken assumption.

## T05 — Specialist cooperation

**Problem:** a route-builder is strategically important but can be separated from the wave.

**Mechanism:** ordinary attackers may follow/wait for Pig Engineer; selected followers call \`supportForTick\`, increasing engineer build rate. Zombies following an Engineer/Creeper suppress their own destructiveness, reducing competing edits. When a Nexus route ends too far away, special targeting can prefer an Engineer.

**KNEEKURA guidance:** make cooperation emerge from small role contracts (follow, assist, reserve corridor) rather than one global squad brain.

## T06 — Time-window + angular-sector wave composition

**Problem:** a wave that only says “spawn N mobs” has little tactical rhythm.

**Mechanism:** \`Wave\` holds overlapping \`WaveEntry\` windows. Each entry defines amount, time interval, granularity, weighted mob pool and optional angle sector. Entries can form a steady stream, specialist insertion, concentrated burst, finale and cleanup.

**Failure handling:** if a sector has too few valid spawn points, rotate among valid sectors, then lower minimum points, then relax to 360 degrees.

**Use:** preserves composition intent while adapting to player-built terrain.

## T07 — Separate movement cost from demolition strength

**Problem:** vanilla hardness is not enough to express tactical preference or siege time.

**Mechanism:** maintain a path cost and a destruction strength separately. A wall can be legal but unattractive; destruction time can be tuned independently.

**Structural bonus:** connected construction blocks receive a neighbour multiplier. The modern anchor keeps this in \`BlockMetadata\` and generalizes categories through tags/config.

**Use:** defense materials can matter to AI without rewriting Minecraft block hardness.

## T08 — Layered failure recovery

**Legacy route-to-Nexus behavior:** repath when path is absent/stuck; increase retry delay after repeated failure; fall back to direct movement toward the objective.

**Modern behavior:** bridge jobs, ladder climbs, mining failures and missing paths have separate recovery states. Repeated block failures can request a repath; engineer idleness can trigger escape/bridge/tower recovery.

**Lesson:** distinguish “planner found no route”, “terrain task failed”, “movement did not reach completed work” and “spawn point impossible”. One generic stuck timer is insufficient.

## T09 — Scheduler persistence with explicit boundary

**Legacy mechanism:** save wave number + elapsed time, then replay \`Wave.doNextSpawns\` in 100 ms increments with spawning disabled to reconstruct scheduler state.

**Advantage:** avoids serializing every queued construct.

**Limit:** restoration work grows with elapsed time and requires deterministic scheduler semantics. Do not copy this blindly.

**Modern preference:** persist explicit phase/wave state and retain bounded retry queues; use replay only when its deterministic and cost properties are proven.

## T10 — Incremental expensive-world probing

The modern spawn generator caps work to **256 spawn-point probes per tick** instead of doing the entire spatial scan in one burst. The modern density map is likewise amortized across 20 ticks.

**Lesson:** when siege logic needs large spatial sampling, split discovery across ticks while keeping an immutable/committed result for consumers.


## T11 — Drive long bodies from actual movement breadcrumbs

**Problem:** a multi-segment creature becomes unstable when every segment follows predicted path nodes, especially after collision or replanning.

**Mechanism:** record the head's realized world-space trace and resample it at fixed distance intervals. Place each visual/body segment at an older point on that centerline.

**Why it matters:** spacing remains approximately constant across speed changes, stalls and collision.

**Modern evidence:** Burrower movement/render history; the later implementation replaces broad segment synchronization with bounded client-side history.

**KNEEKURA guidance:** use actual traveled distance as the source of truth for worms, snakes, trains, tails and other long bodies.

## T12 — Give special movement an owned phase

**Problem:** generic repath/stuck recovery can interrupt a climb, bridge crossing or attack run halfway through.

**Mechanism:** represent the maneuver explicitly, for example `APPROACH -> CLIMB -> CROSS`, and suppress competing movement until completion or explicit abort.

**Evidence:** modern Burrower stair/ledge repairs, Engineer tower ownership, and legacy flying strike commitment.

**KNEEKURA guidance:** special movement should own locomotion just as a terrain transaction owns block edits.

## T13 — Adapt strategic intent to a mob's native controller

**Problem:** forcing every creature through one navigation abstraction discards useful native physics and MOD-specific movement.

**Mechanism:** keep Phantom/Ghast/flying/jumping controls and provide a small adapter that supplies Nexus-directed targets. Add narrow obstacle helpers such as a cached wall-crossing waypoint only when required.

**Why it matters:** compatibility improves while the invasion layer remains responsible for intent rather than locomotion internals.

## T14 — Persist exact tactical purchases for procedural waves

**Problem:** rerolling a procedural wave after save/load changes difficulty and unit relationships.

**Mechanism:** generate themed phases once from a budget, persist every purchase plus phase index, and turn those purchases into spawn entries later.

**Modern evidence:** `BudgetWavePlan`.

**Useful extension:** player behavior can softly bias future theme probabilities without deterministically hard-countering every successful defense.

## T15 — Separate strategic, hostile and cooperation targets

**Legacy observation:** some mobs reuse `attackTarget` to point at an Engineer when they need route help; task priority makes `WaitForEngy` interpret that target as an ally before generic combat consumes it.

**Lesson:** the behavior is clever but brittle.

**KNEEKURA guidance:** model at least three distinct concepts: strategic objective (Nexus), hostile combat target, and ally/cooperation target.

## Techniques not promoted

- Legacy \`PathfinderIM\` implementation itself: globally synchronized, singleton state.
- \`quickFailDepth\`: exposed but not used by the pinned pathfinder.
- legacy async \`PathCreator\` overloads: empty.
- legacy flying “retina” obstacle field: relevant ray-trace assignment is commented in the pinned source and the feature is WIP/debug-facing.
- generic legacy PacketPipeline: entirely commented out.

These are useful historical evidence, not preferred reusable components.
