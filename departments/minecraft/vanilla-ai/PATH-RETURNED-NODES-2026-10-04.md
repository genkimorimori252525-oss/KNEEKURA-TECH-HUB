# Original returned Path nodes and cached terminal values

This bounded continuation of original sections5B4/8E4 adds explicit `path_nodes` observation at the existing selected outer `PathFinder.findPath` RETURN. The default channels remain unchanged. A returned Path is neither an adopted Navigation route nor sampled actual Motion; its terminal cached `g` does not prove minimum effective traversal cost.

## Exact source

The genuine mapped Forge1.20.1 artifact SHA256 is `1b6e6a166fbc06c6d2422cd5cf515a508977479045095363d5b4c8b89cc7b4eb`. Actual PathFinder, Node, Target, BinaryHeap and Path class bytes and retained disassemblies were rechecked against the [ANCHOR ledger](ANCHOR-BYTECODE-LEDGER-2026-10-03.json). Path class/disassembly SHA256: `94bfcd6f1aa220bce972201fc2f109f2bff3abc45c39b502fa2807da4cd65c93` / `dd1540b07207eab558c5462623ee7b323a05957beacf8348068e6a8067996e63`.

Path constructor bytecode22 stores the passed List reference directly;27 stores target. For a nonempty list,72 calls the original terminal Node's virtual `distanceManhattan(BlockPos)` and75 stores that return in `distToTarget`; an empty list instead stores Float.MAX_VALUE.80 stores reached. `getEndNode` and `getNodeCount` dispatch arbitrary List methods; exact Path class alone does not establish exact List ownership. The original reached-result selection compares reconstructed node counts; unreached selection compares cached distance-to-target, then count. It is not a minimum-g selection.

The observer adds no new Mixin injection. The existing non-cancelling exact outer RETURN passes `getReturnValue()` to the hook before `pathEnd`. It reads supported cached fields without invoking Path/List subclass getters or Node query methods, replaying distance/search, traversing predecessor chains, mutating original state or replacing the original return.

## Retention and derived view

- `PATH_RETURNED_NODES` retains an indexed prefix bounded by maxNodes1..64 and an independently captured terminal slot. When the terminal is already in the prefix, its captured slot is copied without a second read. Actual count, retained count and truncation remain explicit.
- Only exact `Path.class` with exact `ArrayList.class` is supported. Null Path, custom Path and custom/null List remain `NOT_EXPOSED`. Interior null Node slots retain their indices; NaN/infinite cached numbers remain unknown.
- Node x/y/z, path type, g/h/f, costMalus, walkedDistance and open/closed-at-return flags are cached observations. Actual `cameFrom` is represented by presence and a bounded per-search reference ID, without following it. Node and predecessor IDs share the existing table, capped by maxNodes; coordinates never substitute for unknown reference identity.
- Per-finder state is limited to eight selected searches. Thread, exact session/run/snapshot/process/Arena/selection/dimension,200-tick/256-event/512-KiB and32-KiB-event gates remain in force. End/reuse, stop, context/cap and writer failure release retained references. `path_nodes` alone allocates no pending pop markers; legacy `path` alone allocates no Node-ID table.
- `path_returned_nodes` is a separate typed retained query. Query prefix clipping leaves the producer's count/limit/truncation unchanged and preserves a separate query-clipped flag and terminal slot. Missing/custom later returns displace old geometry; no forward fill occurs.
- The independent Viewer layer is default OFF. PLAN_XZ/fixed isometric connect only adjacent captured list indices, never a missing/suppressed interval or an independently retained distant terminal/target. Squares/index labels, terminal/target points and bounded cache/source-ID inspection distinguish it from actual Motion, evaluator cache and declared Navigation. ELEVATION uses tick/y and omits this one-return spatial Path.

## Verification and pending acceptance

Consumer/channel RED, genuine unsupported-request RED and Viewer missing-control RED preceded implementation.132 focused tests pass with no skips. All bridge/Mixin sources compile against149 hash-verified genuine compile artifacts, two existing output roots and the separately pinned TF mapped artifact. The production combined genuine-API check passes; seven actual Gson payloads validate through the JavaScript consumer, covering partial/full/null/empty/custom Path/custom List/max64 cases, including custom Node no-query, interior null and unknown g. Strict terminal/prefix consistency, dimension/context, writer/cap/ref-release and read-only rendering checks pass.

Fresh frozen native acceptance for this new producer is pending. Earlier [R43 closed-field acceptance](PATH-CLOSED-CHECKPOINT-2026-10-04.md) remains separate. Complete candidate/rejected lifecycle, branch operands, final effective cost, arbitrary MOD coexistence, adopted-navigation correspondence and matched observer/GPU/pixel acceptance remain open.
