# Original PathFinder heap operation returns

The additional `frontier` burst channel captures four original heap callsites inside the Forge1.20.1 PathFinder search. It is OFF unless explicitly requested, for example `--decision-channels path,neighbors,frontier`. Existing default channels, search order and200-tick/256-event/512-KiB/node limits are unchanged.

## Exact source boundary

The genuine mapped artifact is SHA256 `1b6e6a166fbc06c6d2422cd5cf515a508977479045095363d5b4c8b89cc7b4eb`. Exact class/disassembly hashes remain in the [ANCHOR ledger](ANCHOR-BYTECODE-LEDGER-2026-10-03.json): PathFinder `5d308818c953fcba2353de06b03fb4a80a0f12370c7f92f1baad7f7d574cae3b` / `d929f5154b88c5c977b99d47a7e0d8003a4d45373e08989b2b04711e8dc4f4aa`; BinaryHeap `05af3f22ca50b795799311c528044598e9e05974b56050929b4c5bcd8d808ff0` / `8648cc10e9147a1e58456630d4fb07e092f37445fce36cbd0f703f8d7218c8c3`. Artifact, actual class bytes and retained normalized disassembly were rechecked before native testing.

The genuine protected inner method descriptor includes Forge's profiler argument:

`findPath(Lnet/minecraft/util/profiling/ProfilerFiller;Lnet/minecraft/world/level/pathfinder/Node;Ljava/util/Map;FIF)Lnet/minecraft/world/level/pathfinder/Path;`

| Original offset | Recorded operation | Boundary |
| --- | --- | --- |
|61|`START_INSERT`|Actual `insert(Node):Node` return|
|120|`POP`|Actual `pop():Node` return, before caller writes closed|
|380|`CHANGE_COST`|Actual `changeCost(Node,float):void` return|
|408|`RELAXATION_INSERT`|Actual accepted-relaxation insertion return|

The caller writes `Node.closed=true` at128. This field write is not instrumented or relabeled as a method return. A pop record's `closedAtReturn` is the actual flag **before** that write. Later neighbor/current-node and search-end cache observations remain separate states; the stream does not establish every closed transition.

Each debug-only Redirect calls the passed heap's original virtual method exactly once, retaining the actual return reference or exception. Recording starts after that call and after selected-search/thread/channel/context/budget checks. The passed heap must match the selected finder's cached `openSet` reference. The observer reads detached base Node fields; it never invokes another search, evaluator, distance/heuristic, heap query or controller setter. Another Mixin redirecting these callsites can conflict; arbitrary MOD coexistence and negligible overhead are unverified.

## Retained facts and limits

`PATH_HEAP_OPERATION_RETURN` retains search ID, actual heap class, operation/phase, g/h/f/costMalus/walkedDistance, coordinates/type and cached open/closed flags. Insertion records explicitly compare the argument reference with the original returned reference, including a custom heap returning another object. Cost-update records keep the passed cost separate from resulting fields. Non-finite values and null nodes are explicitly unavailable.

A per-search `IdentityHashMap` retains at most `maxNodes` (1–64) Node references, allocated only for armed `frontier`. Distinct objects at equal coordinates receive distinct `search:revision:search:node:index` IDs. Further identities remain `NOT_EXPOSED / NODE_IDENTITY_LIMIT`; they are not merged by coordinates or hash codes. Tables clear on search begin/end, session teardown and observed budget/context/writer failure. At most eight selected finder searches are registered simultaneously.

The consumer exposes direct EVALUATION facts and a read-only `path_heap_operations` drilldown with original observation IDs. These are partial operation boundaries, not an invented CANDIDATE/SELECTION, complete live heap, rejected population, final effective path cost, reachable destination or arrival. Missing records do not establish that an operation did not occur. `neighborPopulationStatus`, `rejectionReasonStatus` and `finalPathCostStatus` remain `NOT_EXPOSED`.

## Source verification

- Consumer RED rejected the new opt-in channel, event kind and query. GREEN3 tests cover operation boundaries, strict malformed/unknown facts, custom return identity, bounded IDs, equal coordinates, foreign Arena/revision exclusion and immutable inputs.
- Genuine mapped compilation RED reported the missing original heap wrappers. GREEN counting custom-heap tests verify original call count/reference/exception, detached state, identity limits/new-search reset, OFF/legacy-channel/other-Mob/thread/context/window/event/byte/writer fences. Eight actual Java/Gson payloads pass the Node validator.
- Focused Motion/Decision suite:121 passed /0 skipped. All bridge Java/Mixin sources compile against149 hash-verified genuine compile artifacts plus the pinned TF development artifact/output roots.
- Existing combined genuine API regression passes, including the eight heap/Gson interop payloads. Local full `test:ci` stops in an unchanged55-test bridge suite:51 passed /3 failed /1 skipped. Two failures are Windows symlink creation `EPERM`; the inherited descendant-pipe test reports an early successful close instead of its expected timeout and also fails in isolation. Its test and production collector match the prior HEAD. No OS permission or unrelated process collector change was made. Hosted CI remains a separate gate.
- Source tests do not prove runtime Mixin dispatch. Private native acceptance is pending at this source checkpoint.

This bounded slice continues the original open/closed lifecycle requirement; complete candidate/rejection/cost attribution, other evaluators, arbitrary MOD compatibility, native pixels/GPU and paired observer-effect acceptance remain open.
