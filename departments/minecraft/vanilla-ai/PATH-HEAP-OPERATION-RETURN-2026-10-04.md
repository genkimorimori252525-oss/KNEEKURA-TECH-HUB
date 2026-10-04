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
- Source tests do not prove runtime Mixin dispatch. Frozen producer `e513a7f0838bfe1cc040fb53867baf20aa7a1dd9` subsequently established the bounded native acceptance below.

## Native-r41 abort and native-r42 acceptance

R41 reached the Java1.20.1 integrated-server startup but exceeded its200-second READY allowance before capture was armed. Its original failure, missing runtime PID/clean ACK and incomplete identity remain recorded. An additional OS inspection found the exact launcher absent and no matching private Java process; the private world lock was available. This is an idle audit, not a reconstructed clean shutdown or a successful observation.

R42 used the same frozen source and labeled private prelaunch Zombie/Survival-player/52-fence scenario, with a finite600-second startup allowance. No target, heap operation or search result was seeded. Original/control85 files, both predecessor worlds and the new85-file fixture baseline are preserved. Actual producer summaries establish the following separate selection revisions:

| Explicit channels | Heap returns: start / accepted insert / pop / cost update | Other original records | Actual stop |
| --- | --- | --- | --- |
|`path,frontier`|254:2 /123 /118 /11|1 cache +1 Path result|256 events /285,101 bytes; `EVENT_BUDGET`|
|`path,neighbors,frontier`|177:9 /98 /70 /0|63 neighbor returns +8 cache/result pairs|256 events /331,275 bytes; `EVENT_BUDGET`|
|`frontier`|24:12 /0 /12 /0|No neighbor/cache/result records|24 events /25,457 bytes; `WINDOW_ENDED`|

All455 actual heap returns pass the strict retained consumer/drilldown. All200 pops retain `openAtReturn=false` and `closedAtReturn=false`, at the proven boundary before the caller's closed write. There are11 actual cost updates; for example `obs:forge-runtime:54456:136`, tick40497, records passed cost22.093388 separately from copied Node fields. Its reference identity is explicitly unavailable because that search's32-reference retention limit had already been reached.

Revision1's first search retains183 heap operations from `obs:forge-runtime:54456:66`–`:248` at tick40497, then cache`:249` / result`:250`:127 cached nodes, retained32, Path15 nodes, `canReach=false`. Its next search retains71 operations at40621 before the event budget closes; absence of the later cache/result is not an unreachable/no-search conclusion. Revision2 retains nine heap search IDs and eight cache/result pairs (seven `canReach=true`, one false); its ninth search's ending is unobserved. Revision3 retains twelve independent start/pop pairs with no requested path/neighbor layer.

Per-search identity tables never exceed32 references. The two larger searches in revision1 and one in revision2 produce119/9/38 records with `NODE_IDENTITY_LIMIT`; these166 **records** are not166 known distinct Node objects. The consumer does not join them by coordinates. Retained Motion contains84/58/50 real SERVER samples and0/9/15 `SOURCE_GAP` intervals respectively. These are intervals without sufficient retained points, not inferred teleport/collision causes or guaranteed continuous acquisition. Callback timing, snapshot changes and sampled movement do not establish causal selection or arrival.

The private driver's original case metadata mistakenly reused the first channel list for revisions2/3, although each actual request used its intended list. The first audit therefore rejected63 genuine neighbor records. Both original report and failed audit are preserved; an additive audit reads the actual `channels` from the three canonical producer summaries (source IDs`:445`,`:1063`,`:1422`). It does not rewrite runtime evidence or infer requested channels from missing events.

The run finalizes1,576 unique observations as `EVIDENCE_COMPLETE`, canonical SHA256 `5d43917a08624dac0dd152ac44fa64c6aea3da2d32c841d73c8fb911096b99d9`; finalization SHA256 `5a6a3a4a11ca44e7051042bbd3d1b899e604c0842267011617948e58bcfbe427`. Clean ACK/drop0/queue0, `VERIFIED_EXIT`, absence of both owned PIDs and original/control85 hashes were verified. No pixels/raw Cardinal request was taken.

Actual JFR start/stop receipts and4,371,812 bytes are retained (SHA256 `887e9f9935e8878fcff15d5da659697280da5b50173d0a6b23a0d57c631a4e00`). Callback build/first-byte-check medians for revision1's two searches are24,400ns and12,100ns, with the first search's maximum1,456,000ns. These exclude final encoding/writer and original heap work; concurrent machine activity and lack of matched OFF trials prevent a paired observer-effect claim.

## Hosted and local gate scope

Three hosted runs associated with producer `e513a7f` succeed: source push37172724935, source PR37172727131 and repository pytest37172727133. Source jobs include the complete LAB suite, genuine pinned MOD/bridge compilation, actual dependency contracts and pinned resource/unit regressions. Hosted pytest reports3,149 passed /332 skipped /8 warnings. PR workflows use GitHub's generated merge checkout; their success is associated with this PR head, while the push source workflow checks the producer commit directly.

Local Windows full pytest reports2,781 passed /563 skipped /92 failed /48 errors /10 warnings. These broader failures are not resolved by this slice and are not presented as a passing local whole-repository suite. New focused tests, genuine API tests and the specific frozen native trial are independently verified. The3 earlier local LAB failures and the failed R41 startup remain disclosed above.

This bounded slice continues the original open/closed lifecycle requirement; complete candidate/rejection/cost attribution, other evaluators, arbitrary MOD compatibility, native pixels/GPU and paired observer-effect acceptance remain open.
