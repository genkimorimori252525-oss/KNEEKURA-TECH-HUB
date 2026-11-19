# Original PathFinder closed-field checkpoint

This bounded continuation of original sections5B4/8E4 adds an optional checkpoint immediately after the original inner PathFinder writes `Node.closed=true`. It uses the existing explicit `frontier` channel; defaults and200-tick/256-event/512-KiB/node limits are unchanged. The [earlier heap-return generation](PATH-HEAP-OPERATION-RETURN-2026-10-04.md) and its R42 acceptance remain separate evidence.

## Exact source and original control flow

The genuine mapped Forge1.20.1 artifact SHA256 is `1b6e6a166fbc06c6d2422cd5cf515a508977479045095363d5b4c8b89cc7b4eb`. Actual PathFinder, Node, Target and BinaryHeap bytes and retained disassemblies were rechecked against the [ANCHOR ledger](ANCHOR-BYTECODE-LEDGER-2026-10-03.json). PathFinder class/disassembly: `5d308818c953fcba2353de06b03fb4a80a0f12370c7f92f1baad7f7d574cae3b` / `d929f5154b88c5c977b99d47a7e0d8003a4d45373e08989b2b04711e8dc4f4aa`. Node class/disassembly: `ea0bcbf7e19a3b628b607ffd94336e925bd65d07fc9503036480ede3599a71c4` / `31fff4c7f961990353ecce16a51508b3f14e4cf2c248506e356492aef332aa9f`.

The inner descriptor is `(ProfilerFiller,Node,Map,float,int,float):Path`. Bytecode120 calls the original heap `pop`;123 stores that actual returned reference in local12;125 loads it;127 supplies true;128 performs the sole inner `Node.closed:Z` PUTFIELD. No original method call lies between the return and the field write. The non-cancelling FIELD injection selects opcode181/ordinal0/shiftAFTER/require1 on this exact method. It does not replace the write or capture local frames.

Additional static method-body research establishes these original branches, without converting them to dynamic rejection facts:

| Original boundary | Inspected behavior and remaining limit |
| --- | --- |
|106–120|Increment visited count and break when count >= integer-converted `maxVisitedNodes * depthMultiplier`, before the next pop. Neither local count nor the limit is captured by this checkpoint.|
|166–204|Compare the current Node's original `distanceManhattan(Target)` return against accuracy; mark reached targets and stop when the reached set is nonempty. No reached-target population is newly captured.|
|210–232|Call current `distanceTo(start)`; continue without neighbors if its returned distance is >= maxRange. Otherwise call the original evaluator `getNeighbors`.|
|261–303|Original `PathFinder.distance(current,neighbor)` returns the step distance; write `walkedDistance=current.walkedDistance+distance`; compute tentative g in float order `(current.g+distance)+neighbor.costMalus`; continue only for walkedDistance < maxRange. NaN also follows the skip branch at this comparison.|
|308–352|Accept a neighbor when original `inOpenSet()` is false, or when tentative g < its existing g; then write cameFrom/g and `h=getBestH(neighbor,targets)*1.5f`. This inner loop has no separate closed-flag predicate; evaluator filtering is a distinct matter.|
|357–408|Call `inOpenSet()` again independently. True dispatches original changeCost with g+h; false writes f=g+h and dispatches original accepted insertion. The observer does not assume custom overrides make the two calls equivalent.|
|428–538|For reached targets choose minimum reconstructed Path node count. Otherwise compare returned Path distance-to-target, then node count. An empty Optional returns null. This is not proof that the selected result minimizes g or effective traversal cost.|

The inspected base `PathFinder.distance` delegates to the original virtual `Node.distanceTo(Node)`. The base Node implementation subtracts integer coordinates, converts to floats, sums squared components and calls `Mth.sqrt`; base `distanceManhattan` sums float-converted absolute integer differences, and base `inOpenSet` reads heapIdx >=0. `getBestH` calls original virtual distances for each target, updates its best Node and returns the minimum. Reconstruction follows cameFrom into a Node list and constructs Path with target/reached arguments. These base bodies do not establish arbitrary overrides, exact captured branch operands, evaluator rejection reasons or runtime final path cost; no observer calls these methods.

## Retention and consumer contract

After successful selected finder/thread/heap-reference/context/budget validation of an original non-null pop return, retain one pending reference and its actual producer event index. At most8 registered finders each retain one pending reference, in addition to the existing per-search identity table of at most maxNodes (1–64). A Node beyond that table may supply this one transient reference while its identity remains `NODE_IDENTITY_LIMIT`; coordinates never create identity. The pending map is not allocated for legacy channels.

Consume the reference once at the checkpoint. Release it on next original pop, including an exception, search begin/end, excluded Mob, session clear/rearm, observed context/window/event/byte/capture/writer failure. Field reads and serialization occur only inside the existing guarded record operation. There is no heap query, setter, evaluator/search replay or extra original AI invocation.

`PATH_NODE_CLOSED_CHECKPOINT` has distinct `ORIGINAL_FIELD_WRITE_CHECKPOINT_ONLY` semantics. Its detached base fields use `openAtCheckpoint`/`closedAtCheckpoint`; old heap returns keep `openAtReturn`/`closedAtReturn` and their original-return semantics. Data records preceding pop event index, search/reference scopes, capped Node identity and explicit unknown neighbor population/rejection reason/final path cost. The observer copies actual flags rather than claiming that other Mixins cannot subsequently change them.

Strict consumer validation exposes EVALUATION / `path_closed_nodes` as `INSTRUMENTED_ALGORITHM_STATE` / `ALGORITHM_TRACE_RELATION`, plus an optional read-only retained drilldown. Its actual checkpoint observation ID remains the source. Missing preceding pop records do not produce fabricated pop observation IDs, equal-coordinate links, CANDIDATE/SELECTION or causal reasons.

## Verification and acceptance scope

Consumer RED3 rejected the unsupported kind/semantics/query; genuine mapped compilation RED reported9 missing-hook errors. GREEN consumer cases cover phase/flag semantics, strict malformed fields, capped/unknown identities, retained context/revision separation, query limits and immutable inputs. Genuine producer tests use one original virtual pop and an explicitly manual caller field write: reference/exception/no-query, detached values, one-shot markers, eight-finder/identity limits, null returns, OFF/legacy/thread/search/context/window/event/byte/sink boundaries and actual Gson output. Manual test writes are not native Mixin acceptance.

Focused Motion/Decision suite passes124 tests /0 skipped. Every bridge/Mixin source compiles against149 hash-verified genuine compile artifacts plus the pinned TF development artifact/output roots. Two actual Java/Gson checkpoint payloads (known reference and identity limit) validate in Node. Existing combined genuine API regression also passes, including original heap returns and the new checkpoint test. Static source checks verify the exact five-instruction boundary and injection signature; these remain development-source proof.

R42 proves earlier pop-before-close returns only. Frozen producer `5c9275d489556a2b31f26b7527913c9bb043dd84` subsequently establishes the additional bounded native acceptance below. Arbitrary Mixin coexistence, complete frontier/candidate/rejection/final-cost coverage and paired observer/GPU acceptance remain unverified. Existing Windows whole-suite failures remain disclosed in the earlier record; they have not been relabeled as a passing gate.

## Native-r43 bounded acceptance

Normal private Java Forge1.20.1 R43 uses the same labeled prelaunch one-Zombie/Survival-player/52-fence scenario, with no seeded AI target/search/closed flags. Original/control85 files, predecessor R42 world85 files and post-setup baseline85 files remain hash-matched. The actual selected Zombie UUID is `55555555-6666-7777-8888-000000000001`; run `run-20261004040513-47a529901c59`, session `sess-20261004040513-6d4b8661759c`, snapshot `snapshot-20261004040513-6a0c09017a03`, process1/Arena0. Source stays clean and frozen throughout launch/capture/stop.

| Explicit channels / selection revision | Actual heap returns: start / accepted insert / pop / cost | Closed checkpoints | Other retained facts | Stop |
| --- | --- | --- | --- | --- |
|`path,frontier` /1|176:1 /83 /81 /11|80|No retained cache/result before cap|256 events /280,775 bytes; EVENT_BUDGET|
|`path,neighbors,frontier` /2|85:8 /54 /23 /0|23|15 neighbors;8 cache/result pairs, all returned canReach=true|139 events /171,043 bytes; WINDOW_ENDED|
|`frontier` /3|22:11 /0 /11 /0|11|No neighbor/cache/result records|33 events /35,280 bytes; WINDOW_ENDED|

All283 heap returns and114 checkpoints validate in the real retained consumer/drilldown. Each checkpoint refers to exactly one actual prior pop event index under the same burst/search/run/snapshot/process/Arena/revision/selected UUID. Known Node IDs match; capped identities stay unavailable. All115 pops retain open=false/closed=false before the original write; all114 checkpoints retain open=false/closed=true after it. Each actual pop is referenced at most once.

The first pair is `obs:forge-runtime:61336:65` → `obs:forge-runtime:61336:66`, search:1:1, tick40497, producer event2→3, known node1. The last retained pair of this capped search is315→316, event252→253, with NODE_IDENTITY_LIMIT. Pop `obs:forge-runtime:61336:319` is the final captured event256 and has no retained checkpoint. This absent callback does not establish that the original field write was skipped. Revision1's32-reference table yields112 heap and48 checkpoint identity-limit **records**, not160 known distinct objects. For example cost return `obs:forge-runtime:61336:165` retains passed22.093388 and actual g10/h12.093387/f22.093388/costMalus0/walkedDistance15.656854, with unknown Node identity; no final effective path cost is invented.

Revision2 retains eight separate search IDs and eight Path results of2–3 nodes. Their returned canReach flags do not prove actual arrival. Revision3 retains11 independent start/pop/checkpoint sequences, one known Node reference per search. All three packet windows leave CANDIDATE/SELECTION NOT_CAPTURED. Real retained Motion samples are80/60/59 with0/8/10 SOURCE_GAP records. Gaps do not prove teleport, and zero retained gaps do not prove continuous acquisition.

Canonical1,479 unique observations finalize EVIDENCE_COMPLETE, SHA256 `3b63a196c34c85f4a43892a45878e8e14b8f336b032caa7125b389206b05292d`; finalization SHA256 `572f0df8512c99fc441c17dc5237fa9ea9ea5cd00ed215beef6eccf6785ee3d0`. Clean ACK reports drop0/remainingQueue0. OS inspection separately confirms owned runtime61336 and launcher1872 absent. Actual JFR start/stop receipts and4,386,151 bytes remain retained, SHA256 `f118f96d33c959d72f34b87d104c8d689144164947bc980b19bb237d4f8a9dcf`.

Closed-checkpoint build/first-byte-check medians are16,400ns /8,700ns /11,200ns by revision, maxima82,700ns /33,200ns /48,400ns. The first heap search's maximum is26,787,600ns. These exclude original heap work and final encoding/writer; concurrent activity, initial/JIT work and unmatched OFF conditions prevent a paired or negligible-overhead claim.

The R43 driver records each actual requested channel set, fixing R42's case-metadata reporting error. The first private finalizer compared channel array order against producer Set order and failed although contents matched. Its original helper/log are preserved; a separate r2 helper compares sets and validates all facts without rewriting the native report or canonical bytes. This is a post-stop verifier diagnostic, not a failed native field callback.

## Hosted source generation

All three runs associated with `5c9275d489556a2b31f26b7527913c9bb043dd84` are SUCCESS: source push37175864160, source PR37175868106 and repository pytest37175868141. Complete LAB source suite, portable contracts, genuine pinned MOD/bridge compilation, dependency contracts and pinned resource/unit checks succeed. Hosted pytest reports3,149 passed /332 skipped /8 warnings. The source push checks this producer directly; PR jobs use generated merge checkout `c2a74dd489b729461f0fd898ced0a34608765bd7`. Pinned MOD checkout remains `53a84d06578632b5d123e3c2bb631b611bf830d7`. Later research/publication commits require their own exact-head checks.
