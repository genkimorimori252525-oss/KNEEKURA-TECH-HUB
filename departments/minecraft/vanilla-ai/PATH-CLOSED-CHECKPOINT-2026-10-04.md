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

R42 proves earlier pop-before-close returns only. Native dispatch for this additional field checkpoint, arbitrary Mixin coexistence, complete frontier/candidate/rejection/final-cost coverage and paired observer/GPU acceptance remain unverified until separately recorded. Existing Windows whole-suite failures remain disclosed in the earlier record; they have not been relabeled as a passing gate.
