# Original PathFinder neighbor return

The additional `neighbors` burst channel records the result of the **one original virtual** `NodeEvaluator.getNeighbors(Node[], Node)` call inside the genuine Forge1.20.1 PathFinder loop. It does not run a second search, terrain scan or neighbor query. Default channels and the existing path-only cache/result capture remain unchanged. Request `--decision-channels path,neighbors` to opt into both layers; launch hook enablement is still a separate prerequisite.

The inspected Forge mapped artifact SHA256 is `1b6e6a166fbc06c6d2422cd5cf515a508977479045095363d5b4c8b89cc7b4eb`. Its inner method is protected and includes Forge's profiler argument:

`findPath(Lnet/minecraft/util/profiling/ProfilerFiller;Lnet/minecraft/world/level/pathfinder/Node;Ljava/util/Map;FIF)Lnet/minecraft/world/level/pathfinder/Path;`

The original bytecode invokes `getNeighbors([Lnet/minecraft/world/level/pathfinder/Node;Lnet/minecraft/world/level/pathfinder/Node;)I` at offset232, then stores the returned count and enters the neighbor relaxation loop. The debug-only Redirect calls that virtual method once, preserves its count/exception, and copies returned slots immediately afterward. It introduces an invocation wrapper when debug Mixins are enabled; compilation alone cannot establish native compatibility or negligible timing impact. Another Mixin redirecting the same callsite can conflict; arbitrary MOD coexistence remains unverified.

`PATH_NEIGHBORS_RETURN` carries the selected outer search ID, evaluator class, current Node, actual returned count/array length and bounded ordered slots. At most `maxNodes` (1–64) are copied, within existing200-tick/256-event/byte/context limits. Only base Node fields are read before relaxation, including g/h/f, costMalus, walkedDistance, type and cached open/closed flags. These are values at that invocation boundary; they do not prove the later relaxed scores, selected route or why a candidate was rejected. A custom evaluator's class is labeled without interpreting its AI; a null returned slot remains `NOT_EXPOSED`. Non-finite numeric fields are explicitly unavailable to the JSON contract. Mutable Node references are not retained.

The returned list is **not** the complete geometric neighbor population: the evaluator can already have filtered candidates. `neighborPopulationStatus` and `rejectionReasonStatus` remain `NOT_EXPOSED`. Existing frontier cache records continue to make that limitation explicit, even if separate neighbor callbacks were captured. No missing record is converted into a rejected node, unreachable result or no-search claim.

The retained consumer adds an EVALUATION fact and a bounded read-only `path_neighbors` drilldown. Query truncation is distinct from source truncation, source counts/slots/observation IDs are preserved, and the canonical store is unchanged.

## Source checkpoint

- Consumer meaningful RED: opt-in channel rejected and valid neighbor record unsupported; GREEN2 tests preserve order, bounds, query/source truncation and unknown/null/rejected-population distinctions.
- Genuine mapped Java compilation RED: missing original-call wrapper API; GREEN counting custom evaluator tests verify exactly one original call, preserved return/exception, detached state, finite budget, OFF/path-only suppression, other-thread and ended-search exclusion. Java Gson output passes the Node validator.
- Motion/Decision111 tests passed /0 skipped. Existing genuine owner/Arena/camera/writer API regression includes the new producer test and interop assertion.
- Frozen `b39fa3d14010fb89a99dba3b24714185291ef9c2` established the following private native trial. Full candidate generation/rejection/effective custom malus and broader observer-effect/MOD coexistence remain open.

## Native-r30

The labeled private Zombie fixture restores an exact original85-file copy, then prepares a controlled survival player, one actual-AI Zombie and52 fence cells. No target, search or neighbor result is seeded. Original/control85 hashes remain unchanged; all85 predecessor R29 files and the new85-file post-setup prelaunch baseline are preserved.

Explicit `path,neighbors` captured175 original neighbor RETURNs plus two cache/result pairs within one200-tick burst:179 callbacks /311,695 payload bytes, ending `WINDOW_ENDED`. Source arrays were not truncated in this trial; the returned slots total416 **with repetitions across invocations**, not416 distinct geometric neighbors.

| Search | Original returns / slots | Callback source range | Same-search cache / result | Result |
|---|---|---|---|---|
| `search:1:1` | 86 /203 (4 zero returns) | `obs:forge-runtime:46284:35`–`:120`, tick40459 | `:121` /`:122`; cache127 nodes, retained32 | Path15 nodes, `canReach=false` |
| `search:1:2` | 89 /213 (4 zero returns) | `obs:forge-runtime:46284:242`–`:330`, tick40583 | `:331` /`:332`; cache146 nodes, retained32 | Path18 nodes, `canReach=false` |

Both evaluator classes are `WalkNodeEvaluator`. All175 genuine records passed the consumer; the retained presentation builds with normal bounds. A `path_neighbors` query with `maxNodes=1` returned175 items and marked111 item truncations, preserving actual source counts/IDs and canonical bytes. No neighbor was reconstructed from the final cache and no missing result or rejection reason was inferred. Both paths being present is separate from successful arrival.

605 unique observations finalized as `EVIDENCE_COMPLETE`, canonical SHA256 `d292e050269a65a0faebf2d7070e3504035526433908c250727c0d87bba3f04a`. Clean ACK/drop0/queue0, `VERIFIED_EXIT` and absence of owned native PID46284 were checked. The same run retains80 real motion samples and80 sampled decision snapshots; these do not prove continuous movement or full pursuit.

Actual JFR start/stop receipts and2,551,764 bytes were retained (SHA256 `e0d3f61912d52aebd676ec00093d5566c9432eeeadd8ba484db598da2bf63313`). Callback build/first-byte-check costs: min11,400ns, median53,800ns, max3,119,200ns. These exclude final encoding/writer and original evaluator runtime, and are not a paired observer-effect measurement. No pixels or raw Cardinal requests were taken in this trial.
