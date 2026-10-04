# Original accepted-neighbor g-field write checkpoint

This optional continuation of original sections5B4/8E4 observes an actual accepted-neighbor `Node.g` assignment inside the selected original PathFinder search. Explicit `path_g` enables it; defaults and numeric limits remain unchanged. It does not establish a complete neighbor population, original comparison operands, rejection reasons, minimum effective path cost or adopted Navigation.

## Exact source and observation boundary

The genuine mapped Forge1.20.1 artifact SHA256 is `1b6e6a166fbc06c6d2422cd5cf515a508977479045095363d5b4c8b89cc7b4eb`. PathFinder/Node/Target/BinaryHeap/Path actual class bytes and retained disassemblies match the [ANCHOR ledger](ANCHOR-BYTECODE-LEDGER-2026-10-03.json). The exact inner `findPath(ProfilerFiller,Node,Map,float,int,float):Path` has two `Node.g:F` PUTFIELD sites:27 initializes the start;336 assigns the accepted neighbor from the original receiver at332 and local17 value at334. Original cameFrom assignment329 precedes it; heuristic update calls getBestH346 afterward.

The FIELD Redirect targets opcode181, ordinal1, require1 on that exact descriptor. The handler accepts the original Node receiver and float operand and delegates to a helper whose first statement is the original `node.g=writtenG`, exactly once. No setter, distance calculation, search replay or cancellation replaces it. Original null receiver failure precedes observer gates. Genuine Mixin0.8.5 artifact/class hashes and `RedirectInjector.injectAtPutField` bytecode establish the void handler's owner/value argument shape; static mechanism proof alone is not transformed-runtime acceptance or arbitrary Mixin compatibility.

`writtenGScope=ORIGINAL_PUTFIELD_ARGUMENT` retains the passed operand independently from `fieldScope=BASE_NODE_FIELDS_AFTER_WRITE_AND_CAPTURE_GATES`. The later cached g/h/f, flags and cameFrom reference are separate field observations; context/time/budget gates occur before capture and another hook can change them. Equality of cached g and writtenG is neither enforced nor inferred. Unknown/nonfinite values remain explicit. No old g, branch operands or recomputed f=g+h is supplied.

## Retention and consumption

`PATH_NODE_G_WRITE_CHECKPOINT` uses field-write semantics and the typed `path_g_writes` query. Decision EVALUATION labels it `INSTRUMENTED_ALGORITHM_STATE` / `ALGORITHM_TRACE_RELATION`; it does not add SELECTION or RESULT. Exact session/run/snapshot/process/Arena/selection/dimension, thread, bounded window/event/byte and source IDs remain mandatory. Node/predecessor identity uses the existing finite per-search reference table shared with heap and returned-Path observation, capped by maxNodes1..64 and eight selected finders. Coordinates never replace identity. `path_g` alone allocates no pending pop markers; stop/end/reuse, budget/context and writer fences release retained references.

## Source verification and remaining acceptance

Genuine missing-producer compile RED and consumer RED preceded implementation.136 focused tests pass with no skips. All bridge/Mixin sources compile against149 hash-verified genuine compile artifacts, two existing output roots and the pinned TF mapped artifact. The combined genuine Forge API test passes without launching Minecraft. Five actual Gson checkpoint payloads validate through JavaScript, including a fixture where a context gate changes cached g to77 after original writtenG9. That fixture documents separate capture times; it is not a native gameplay claim.

Tests cover assignment-before-observer bytecode with a sole original PUTFIELD, null exception, unknown/nonfinite values, no virtual Node query, exact source/context, independent shared IDs, default OFF and explicit thirteen-channel parsing, thread/window/event/byte/writer fences and reference release. A fresh frozen Java17/Forge1.20.1 private trial is pending. Earlier [R44 returned-Path acceptance](PATH-RETURNED-NODES-2026-10-04.md) does not validate this new producer. The full goal remains active and the PR remains Draft.
