# Original evaluator malus return — bounded native acceptance

Date: 2026-10-04 (Asia/Tokyo). This slice is part of the active remaining goal; the source checkpoint and limited native acceptance below do not establish full operational acceptance.

## Captured boundary

The additional `effective_malus` burst channel is explicitly opt-in. The existing six default channels are unchanged. An optional Mixin redirects original virtual `Mob.getPathfindingMalus(BlockPathTypes)F` invocations in the known Walk/Fly/Swim/Amphibious evaluator class set. Exact mapped Forge1.20.1 bytecode contains20 such callsites (10/6/1/3 respectively). The original getter executes once before observation, including custom override dispatch. Its return value and exception are preserved; observation never queries the getter again, changes the malus table, prepares an evaluator or replays pathfinding.

`EFFECTIVE_MALUS_RETURN` retains the selected receiver's cached UUID, receiver/evaluator classes, path type and actual getter return. A non-finite return remains unchanged for gameplay and becomes explicit `NOT_EXPOSED` in JSON. Negative finite values remain available. This is the getter return at an original callsite, **not the final node/path cost, a formula, rejection reason, full candidate population or exact calling-method identity**. Those unavailable quantities remain unknown. The channel may reach its finite budget during a search; absence is not evidence that no getter ran.

The original invocation executes with observation OFF, excluded receiver/channel/thread, changed context, closed budget or capture failure. Only the owning selected receiver/server thread and unchanged burst context can produce a row. Cached receiver UUID mismatch closes capture. Consumer validation requires the row's entity UUID to match the retained receiver and rejects fabricated final-cost/source claims. The read-only `effective_malus` drilldown retains source observation IDs without altering canonical data.

## Source validation

- RED→GREEN dedicated Node tests reject the previously unsupported channel/kind, then accept bounded custom values and unknown non-finite values while rejecting forged receiver/formula/final-cost claims.
- Motion/Decision regression:113 passed /0 skipped.
- Hash-checked genuine mapped Forge API compilation covers all bridge Java sources, including the new Mixin.
- A genuine-API constructor-free synthetic Mob override verifies exactly one virtual dispatch, original finite/negative/NaN results and exceptions, other receiver/thread, OFF/base-channel-only, event/window/context/UUID boundaries. Production Gson output passes the actual Node validator. This fixture is a source contract test, **not a native custom MOD acceptance claim**.

## Native-r31 / r32 at frozen source

Both runs use clean producer `3d702e41c16c5f935ed4d73d9d0d1a53569bcf00`, Java Edition1.20.1 /Forge47.2.0 with the existing mapped dependencies. `IntegratedServer` denotes the Java single-player server. The original official Tank and control copy each retain85/85 matching SHA256 files. Fresh labeled private copies preserve their predecessor85 files and a separate85-file post-setup/prelaunch baseline; no RegionFile is opened on those preserved baselines. The bounded private room, survival player, high health and52 fence cells are setup, not original-world resize or normal combat acceptance.

R31 uses the ordinary Vanilla Zombie. R32 additionally loads one explicitly synthetic private fixture JAR: a Zombie subclass inherits ordinary AI and overrides the `WALKABLE` getter result to17.25, using the original superclass result for other path types. The fixture does not seed a target or invoke AI/getters from a diagnostic. Its source SHA256 is `7ae9b8bbf111cb07657317e60287d2a857004bf31dad5b6581e410d4cff2df0e`; JAR SHA256 `ce370a90c5373d6561f5a05a8c5acfa00895bf7619c23ab30b11ac4cdc2c83f0`.149 existing compile artifacts are hash-checked; no tracked dependency/MOD source changes or arbitrary third-party compatibility claim follow from this fixture.

| Trial | Original getter returns | Canonical evidence |
| --- | --- | --- |
| R31 ordinary Zombie |256: OPEN0×100, BLOCKED−1×30, WALKABLE0×93, FENCE−1×33 |677 unique observations, SHA256 `9508df4ad94819d394d4ecd2ebfca9334cdce1b11e4f417432b478d9822b1fcc` |
| R32 synthetic CustomZombie |256: OPEN0×99, BLOCKED−1×29, WALKABLE17.25×94, FENCE−1×34 |686 unique observations, SHA256 `03e512aaf1fc30143fa7c2737300774cb0ebff7820eb62be6488e1956fa6c0ed` |

All callbacks come from `WalkNodeEvaluator`. R31 source IDs are `obs:forge-runtime:30832:64`..`:319`; R32 `obs:forge-runtime:50472:82`..`:337`. Each trial's callbacks all have gameTime40497. The explicitly armed `effective_malus`-only burst reaches **EVENT_BUDGET256** within that tick, retaining188,357/193,487 payload bytes respectively. It does not cover later getter calls, complete searches, all calling methods or final costs. Both production validators, the256-item read-only drilldown and default retained presentation pass without changing canonical bytes; the presentations retain80/84 actual selected-Mob positions, not extra getter-derived motion points.

Both trials finalize `EVIDENCE_COMPLETE`, clean ACK/drop0/queue0 and `VERIFIED_EXIT`. These evidence receipts do not imply an ordinary Minecraft save or full battle outcome. Actual JFR start/stop receipts and FLR headers are checked: R31 2,458,078 bytes /SHA256 `5f73209a907cd1b7af9921063d4202b5ad303672aeb95b6270838c86525328c3`; R32 2,378,685 bytes /`9d5c70d43d82b300d6af4dccc829338fcd6be28f006bc50d97fb352fe232846f`. Callback build/first-byte-check cost min/median/max is10.6µs/13.4µs/2.6902ms (R31),7.1µs/9µs/2.1687ms (R32); it excludes original getter execution, final encoding and writer. Different entity definitions, readiness and RNG mean these are **not paired causal overhead measurements**.

The frozen source's three GitHub checks are SUCCESS: source push `37161392341`, source PR `37161394653`, pytest `37161394660`. Later documentation HEADs require their own checks.

The optional wildcard injection is now proven to capture real Walk evaluator virtual calls, including this synthetic native override. Fly/Swim/Amphibious runtime callsite coverage, arbitrary custom evaluators/MODs, exact method/search/cell attribution, final path cost/rejection formula and paired observer-effect acceptance remain open. Source compilation and a successful Walk trial do not prove these remaining outcomes.
