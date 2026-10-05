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

## Source verification

Consumer/channel RED, genuine unsupported-request RED and Viewer missing-control RED preceded implementation.132 focused tests pass with no skips. All bridge/Mixin sources compile against149 hash-verified genuine compile artifacts, two existing output roots and the separately pinned TF mapped artifact. The production combined genuine-API check passes; seven actual Gson payloads validate through the JavaScript consumer, covering partial/full/null/empty/custom Path/custom List/max64 cases, including custom Node no-query, interior null and unknown g. Strict terminal/prefix consistency, dimension/context, writer/cap/ref-release and read-only rendering checks pass.

## Frozen R44 native acceptance

Frozen producer `e195f91baf546377d5dfac34842efbae82c39a82` ran genuine Java17/Forge1.20.1 with the unchanged pinned MOD `53a84d06578632b5d123e3c2bb631b611bf830d7` and exact mapped TF input. This is a labeled private prelaunch Survival/player/Zombie/52-fence fixture copied from the formal Tank, with actual original Zombie AI afterward. No observer replayed search or seeded a decision result.

Run `run-20261004050558-7e1a5055d6e0`, session `sess-20261004050558-a13dee905042`, snapshot `snapshot-20261004050558-bd821aa355bb`, process1/Arena0; selected Zombie `55555555-6666-7777-8888-000000000001`.

| Selection / actual armed channels | Retained original results | Independent Motion / budget |
| --- | --- | --- |
|rev1, `path_nodes`, maxNodes4;40441–40856|Two partial Path returns, counts15/18, retained prefixes4 each and separate terminal indices14/17. Both canReach=false. Cached terminal g14.414213/17.414213 differs from constructor distance6/3; terminal and parent reference IDs remain unknown at the4-ID cap.|80 actual samples,0 trace gaps;2 events/6,354 payload bytes;WINDOW_ENDED. No path-cache/heap acquisition.|
|rev2, `path,path_nodes`, maxNodes32;40848–41256|Nine return/cache/summary groups paired by exact context/burst/search and source event order. Counts3/2/3/3/3/5/2/3/3;8 canReach=true,1false. The false result has5 Nodes, cached terminal g4 and cached distance17. These are distinct observed fields.|59 actual samples,7 SOURCE_GAP records;27 events/53,150 payload bytes;WINDOW_ENDED.|
|rev3, `frontier,path_nodes`, maxNodes32;41248–41661|Ten returned Paths, counts2/2/2/2/1/1/1/1/1/1, all canReach=true;44 heap returns (10start/20accepted insertion/14pop/0cost update) and14 exact pop→closed pairs. Existing per-search reference IDs are shared with returned slots. No path-cache/summary or neighbor acquisition.|41 actual samples,19 SOURCE_GAP records;68 events/82,733 payload bytes;WINDOW_ENDED.|

The first partial return is `obs:forge-runtime:48952:66` /search1:1/tick40497; the second is `obs:forge-runtime:48952:189` /search1:2/tick40621. Rev2's false result is `obs:forge-runtime:48952:570`; the final rev3 return is `obs:forge-runtime:48952:949`. CANDIDATE and SELECTION remain NOT_CAPTURED in all three retained presentations; canReach is the returned Path flag, not target arrival or accepted Navigation. SOURCE_GAP is a retained interval boundary, not interpolated Motion or an inferred AI reason.

The21 returned-Path payload build timings have per-revision min/upper-median/max138,600/2,420,800/2,420,800ns (2samples),40,000/55,200/365,800ns (9),28,600/31,900/37,700ns (10). This scope excludes original algorithm calls, final encoding/writer/Viewer; no matched OFF or CPU/GPU equivalence is established.

All1,099 canonical observations are unique and finalize `EVIDENCE_COMPLETE`; SHA256 `7d428bb0aae45042848dda89d7e2cb6d4e47149f55e08dab5ab59d31aae712a0`. Finalization SHA256 `29d5dd907ed2a0e9a80c2700a77c213fdc4a12bbd1c4a157f108ceef09add987`. Clean shutdown ACK reports dropped0/remainingQueue0; exact owned launcher60848/runtime48952 are OS-absent. Original/control/predecessorR43/post-setup baseline85 files each retain their expected hashes. JFR4,681,373bytes, SHA256 `bd0fb0f81f08933f8160b66fbede7777a9c292c46c318426fe54d8d03f766917`, has actual owned-runtime start/stop receipts.

## Read-only browser and hosted checks

Two derived HTML artifacts outside the canonical run inspect the same retained first partial return. Native producer prefix4 and a further retained-query prefix1 are separately labeled; terminal14, target, actual cached values and source ID remain independent. Browser checks establish all six layers initially OFF, contiguous indices0–3 connected without an edge to14/target, prefix1 with no invented connecting edge, fixed isometric, ELEVATION omission, and cursor40496 hiding the future40497 return. Console errors0; five screenshots and the observed receipt remain private. The canonical SHA is unchanged, and the loopback server/test tab are closed. This is browser replay QA of actual retained data, not a native Minecraft framebuffer/GPU proof or a new missing-position acquisition.

Three hosted runs associated with exact producer HEAD all succeed: [push source37178825179](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/37178825179), [PR source37178828031](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/37178828031), [PR pytest37178828037](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/37178828037). The push source checkout is the producer itself; PR jobs actually check generated merge `29d17035f89d036b1617d8106a4a81728de6683e`. Complete LAB source and pinned MOD compile gates pass; pytest3,149passed/332skipped/8warnings in280.86s. Metadata, actual checkout logs and receipts are retained separately.

Earlier [R43 closed-field acceptance](PATH-CLOSED-CHECKPOINT-2026-10-04.md) remains separate. Complete candidate/rejected lifecycle, branch operands, final effective cost, arbitrary MOD coexistence, adopted-navigation correspondence and matched observer/GPU/pixel acceptance remain open. The full `/goal` stays active and both PRs remain Draft.
