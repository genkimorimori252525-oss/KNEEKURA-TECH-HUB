# Original evaluator malus return — source checkpoint

Date: 2026-10-04 (Asia/Tokyo). This slice is part of the active remaining goal; native injection and operational acceptance are separate gates.

## Captured boundary

The additional `effective_malus` burst channel is explicitly opt-in. The existing six default channels are unchanged. An optional Mixin redirects original virtual `Mob.getPathfindingMalus(BlockPathTypes)F` invocations in the known Walk/Fly/Swim/Amphibious evaluator class set. Exact mapped Forge1.20.1 bytecode contains20 such callsites (10/6/1/3 respectively). The original getter executes once before observation, including custom override dispatch. Its return value and exception are preserved; observation never queries the getter again, changes the malus table, prepares an evaluator or replays pathfinding.

`EFFECTIVE_MALUS_RETURN` retains the selected receiver's cached UUID, receiver/evaluator classes, path type and actual getter return. A non-finite return remains unchanged for gameplay and becomes explicit `NOT_EXPOSED` in JSON. Negative finite values remain available. This is the getter return at an original callsite, **not the final node/path cost, a formula, rejection reason, full candidate population or exact calling-method identity**. Those unavailable quantities remain unknown. The channel may reach its finite budget during a search; absence is not evidence that no getter ran.

The original invocation executes with observation OFF, excluded receiver/channel/thread, changed context, closed budget or capture failure. Only the owning selected receiver/server thread and unchanged burst context can produce a row. Cached receiver UUID mismatch closes capture. Consumer validation requires the row's entity UUID to match the retained receiver and rejects fabricated final-cost/source claims. The read-only `effective_malus` drilldown retains source observation IDs without altering canonical data.

## Source validation

- RED→GREEN dedicated Node tests reject the previously unsupported channel/kind, then accept bounded custom values and unknown non-finite values while rejecting forged receiver/formula/final-cost claims.
- Motion/Decision regression:113 passed /0 skipped.
- Hash-checked genuine mapped Forge API compilation covers all bridge Java sources, including the new Mixin.
- A genuine-API constructor-free synthetic Mob override verifies exactly one virtual dispatch, original finite/negative/NaN results and exceptions, other receiver/thread, OFF/base-channel-only, event/window/context/UUID boundaries. Production Gson output passes the actual Node validator. This fixture is a source contract test, **not a native custom MOD acceptance claim**.

Native runtime injection, custom override in a running game, other evaluator classes, final path cost attribution and paired observer-effect acceptance remain unverified at this source checkpoint. The optional wildcard injection's compilation alone does not establish that it matched any runtime callsite.
