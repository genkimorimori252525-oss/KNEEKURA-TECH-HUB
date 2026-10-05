# Original accepted-neighbor g-field write checkpoint

This optional continuation of original sections5B4/8E4 observes an actual accepted-neighbor `Node.g` assignment inside the selected original PathFinder search. Explicit `path_g` enables it; defaults and numeric limits remain unchanged. It does not establish a complete neighbor population, original comparison operands, rejection reasons, minimum effective path cost or adopted Navigation.

## Exact source and observation boundary

The genuine mapped Forge1.20.1 artifact SHA256 is `1b6e6a166fbc06c6d2422cd5cf515a508977479045095363d5b4c8b89cc7b4eb`. PathFinder/Node/Target/BinaryHeap/Path actual class bytes and retained disassemblies match the [ANCHOR ledger](ANCHOR-BYTECODE-LEDGER-2026-10-03.json). The exact inner `findPath(ProfilerFiller,Node,Map,float,int,float):Path` has two `Node.g:F` PUTFIELD sites:27 initializes the start;336 assigns the accepted neighbor from the original receiver at332 and local17 value at334. Original cameFrom assignment329 precedes it; heuristic update calls getBestH346 afterward.

The FIELD Redirect targets opcode181, ordinal1, require1 on that exact descriptor. The handler accepts the original Node receiver and float operand and delegates to a helper whose first statement is the original `node.g=writtenG`, exactly once. No setter, distance calculation, search replay or cancellation replaces it. Original null receiver failure precedes observer gates. Genuine Mixin0.8.5 artifact/class hashes and `RedirectInjector.injectAtPutField` bytecode establish the void handler's owner/value argument shape; static mechanism proof alone is not transformed-runtime acceptance or arbitrary Mixin compatibility.

`writtenGScope=ORIGINAL_PUTFIELD_ARGUMENT` retains the passed operand independently from `fieldScope=BASE_NODE_FIELDS_AFTER_WRITE_AND_CAPTURE_GATES`. The later cached g/h/f, flags and cameFrom reference are separate field observations; context/time/budget gates occur before capture and another hook can change them. Equality of cached g and writtenG is neither enforced nor inferred. Unknown/nonfinite values remain explicit. No old g, branch operands or recomputed f=g+h is supplied.

## Retention and consumption

`PATH_NODE_G_WRITE_CHECKPOINT` uses field-write semantics and the typed `path_g_writes` query. Decision EVALUATION labels it `INSTRUMENTED_ALGORITHM_STATE` / `ALGORITHM_TRACE_RELATION`; it does not add SELECTION or RESULT. Exact session/run/snapshot/process/Arena/selection/dimension, thread, bounded window/event/byte and source IDs remain mandatory. Node/predecessor identity uses the existing finite per-search reference table shared with heap and returned-Path observation, capped by maxNodes1..64 and eight selected finders. Coordinates never replace identity. `path_g` alone allocates no pending pop markers; stop/end/reuse, budget/context and writer fences release retained references.

## Source verification

Genuine missing-producer compile RED and consumer RED preceded implementation.136 focused tests pass with no skips. All bridge/Mixin sources compile against149 hash-verified genuine compile artifacts, two existing output roots and the pinned TF mapped artifact. The combined genuine Forge API test passes without launching Minecraft. Five actual Gson checkpoint payloads validate through JavaScript, including a fixture where a context gate changes cached g to77 after original writtenG9. That fixture documents separate capture times; it is not a native gameplay claim.

Tests cover assignment-before-observer bytecode with a sole original PUTFIELD, null exception, unknown/nonfinite values, no virtual Node query, exact source/context, independent shared IDs, default OFF and explicit thirteen-channel parsing, thread/window/event/byte/writer fences and reference release. Earlier [R44 returned-Path acceptance](PATH-RETURNED-NODES-2026-10-04.md) remains separate.

## Frozen R45 native acceptance

Frozen producer `7d355edf80ed1048e9f9941b0eb5ba021180ff48` ran genuine Java17/Forge1.20.1 with unchanged pinned MOD `53a84d06578632b5d123e3c2bb631b611bf830d7` and exact mapped TF input. The labeled private Survival/player/Zombie/52-fence fixture is copied from the formal Tank; original Zombie AI executes afterward. No observer seeds g, replays a search or forces a result.

Run `run-20261004054759-c356df67be73`, session `sess-20261004054759-f62499aa35a9`, snapshot `snapshot-20261004054759-33485dbcfd6d`, process1/Arena0; selected Zombie `55555555-6666-7777-8888-000000000001`.

| Selection / actual armed channels | Original checkpoint evidence | Independent Motion / budget |
| --- | --- | --- |
|rev1, `path_g`, maxNodes4;40428–40829|194 actual g writes across two selected searches;188 receiver IDs remain unknown at the reference cap. The first passed g1 has later cached g1/h0/f0, before heuristic update. No heap or returned-Path acquisition is armed.|80 actual samples,0 gaps;194 events/261,840 payload bytes;WINDOW_ENDED.|
|rev2, `path_g,frontier`, maxNodes32;40828–41243|47 g writes with available receiver IDs,74 heap returns (7start/47accepted insertion/20pop/0cost update) and20 explicit pop→closed pairs. All47 g records have a subsequent accepted insertion retaining the same exact per-search reference. These ordered observations do not establish an AI causal explanation.|66 actual samples,9 SOURCE_GAP records;141 events/163,784 payload bytes;WINDOW_ENDED.|
|rev3, `path_g,path,path_nodes`, maxNodes32;41234–41643|Zero retained g writes;10 cache/result/returned-Path groups, each nodeCount1/canReach=true. Zero is preserved without inferring original write absence or a rejection reason; g timing is NOT_CAPTURED.|40 actual samples,18 SOURCE_GAP records;30 events/30,263 payload bytes;WINDOW_ENDED.|

First g checkpoint `obs:forge-runtime:59192:82`, search1:1/tick40497; last rev1 record398/tick40621 has passed g25.24264 and unknown receiver/predecessor IDs. Rev2's first is672/search2:1 and last921/search2:7. Passed g and later cached g happen to agree in all241 native records; their scopes remain distinct, and cached h/f must not be reconstructed. CANDIDATE and SELECTION remain NOT_CAPTURED. SOURCE_GAP delimits retained Motion without interpolation or an inferred cause.

Per-revision g payload-build min/upper-median/max are8,400/25,300/3,471,300ns (194samples) and7,600/11,100/59,700ns (47samples). This excludes original assignment, final encoding/writer/Viewer and other instrumentation; no matched OFF or gameplay/CPU/GPU equivalence is established.

All1,385 canonical observations are unique and finalize `EVIDENCE_COMPLETE`; SHA256 `fc0fd14abaf35fb3e84946df3af81f2e26abdfc88133b2a6d56bafc38375ff47`. Finalization SHA256 `45cda4e845d8f08cedc1fda83ab44577e41511a609b4112c7f97d36579554119`. Clean ACK reports dropped0/remainingQueue0; exact owned launcher44616/runtime59192 are OS-absent. Original/control/predecessorR44/post-setup baseline85 files each retain expected hashes. JFR4,855,212bytes, SHA256 `d642967ac3cfe91d6c1393e73d9760770a44c2cb7e18109185f155e66cdcd44b`, has actual owned-runtime start/stop receipts.

The first private finalizer incorrectly required positive g records in every case. Its failed assertion/log are retained. Separate r2 preserves the zero-record third case and requires transformed g evidence in the first two dedicated cases; producer, driver and canonical bytes are unchanged. No source/gameplay change or native rerun satisfied that erroneous premise.

## Hosted checks and remaining acceptance

All three hosted runs associated with exact producer HEAD succeed: [push source37180880455](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/37180880455), [PR source37180883290](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/37180883290), [PR pytest37180883300](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/37180883300). Push source checks the producer directly; PR jobs actually check generated merge `c01ac7598681393c56ee7ade8fe1b5ffdb98bc7c`. Complete LAB source, portable contracts, actual pinned MOD compile and dependency/resource/unit regressions pass; pytest3,149passed/332skipped/8warnings in231.60s. Metadata, actual checkout logs and native receipts are retained separately. Earlier unresolved Windows full-suite failures remain separate; no unchanged Windows whole-suite rerun occurred.

Complete accepted/rejected population, comparison operands, final effective cost, arbitrary MOD/Mixin coexistence, Navigation adoption and paired/GPU/pixel acceptance remain open. The full goal remains active and the PR remains Draft.
