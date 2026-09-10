# KNEEKURA TECH HUB — Harvest Staging Cycle 17

Status: **STAGING / NON-CANONICAL**  
Date: 2026-09-11  
Governance: discovery evidence only. Popularity was used only to prioritize inspection. Nothing in this memo is VALIDATED, canonical, or authorized for production adoption.

## Scope and duplicate check

Before harvesting, the current `main` research staging area and the open Harvest PR backlog through Cycle 16 were checked. Recent staged themes already include durable scheduling/leases, priority admission, lazy loading, live-config rollback, idempotency, circuit breakers, crash evidence, cache lifetime locks, cooperative budgets, condition-driven waits, watchdog dumps, stale-reference quarantine, graceful worker replacement, revision-aware watches, spilling, multiplex workers, immutable generations, fair queuing, I/O token buckets, runtime resource revalidation, crash-loop budgets, Trace2 telemetry, overload degradation, deadlock repair, permission ceilings, asynchronous destruction, and process-tree jobserver tokens. The candidates below were selected because they add materially different mechanisms.

## Candidate 17-A — Interface-shape signatures to stop unnecessary dependency invalidation

- Repository: `microsoft/TypeScript`
- Popularity at inspection: 110,992 GitHub stars
- Repository URL: https://github.com/microsoft/TypeScript
- Revision inspected: `0b832e12235cc3db14a4be6501827c2f8a8a8569`
- Primary path: `tsc/internal/execute/incremental/affectedfileshandler.go`
- Primary section/functions: `computeDtsSignature`, `updateShapeSignature`, `getFilesAffectedBy`, `forEachFileReferencedBy`
- Source URL: https://github.com/microsoft/TypeScript/blob/0b832e12235cc3db14a4be6501827c2f8a8a8569/tsc/internal/execute/incremental/affectedfileshandler.go
- Blob SHA observed: `73289380cc51d2a4b55af6be2eddc51dc35a55d9`

### Technique

The incremental builder distinguishes a file changing internally from its externally visible *shape* changing. It computes a declaration-oriented signature, compares that signature with the previous snapshot, and only propagates invalidation through reverse references when the shape actually changed. If the changed file's shape remains equivalent, the affected set can stop at that file instead of conservatively reprocessing every transitive dependent. Global-scope changes remain a conservative exception and can invalidate the wider program.

### Why it may be useful for KNEEKURA

Repository analysis, Render Pack generation, schema extraction, static graph generation, or knowledge indexing can often distinguish between an implementation-only edit and an edit that changes the public facts consumed by downstream stages. KNEEKURA could maintain an explicit `output-shape signature` for stage boundaries and propagate invalidation only when that contract changes. This may reduce repeated whole-repository or whole-graph rebuilds without pretending unchanged output when the observable contract changed.

A useful adaptation would be: source hash answers "did this input file change?" while stage-signature answers "did the facts exported to dependents change?". Downstream work should depend on the latter where safe.

### Limitations / uncertainty

TypeScript's `.d.ts` representation is a language-specific approximation of observable type shape. KNEEKURA would need domain-specific canonicalization for each artifact type; a bad signature that omits semantically relevant facts could create false negatives, which are worse than extra work. Global effects, side effects, tool-version changes, configuration changes, and nondeterministic stages must remain conservative invalidation boundaries. The exact TypeScript strategy should not be copied mechanically.

---

## Candidate 17-B — Red/green dependency evaluation: recompute changed dependencies before propagating invalidation

- Repository: `rust-lang/rust`
- Popularity at inspection: 118,003 GitHub stars
- Repository URL: https://github.com/rust-lang/rust
- Revision inspected: `018018e881e2db0956f229dbb543e21f058d1ce7`
- Documentation path: `src/doc/rustc-dev-guide/src/queries/incremental-compilation-in-detail.md`
- Implementation path referenced by the guide: `compiler/rustc_middle/src/dep_graph/graph.rs`
- Relevant algorithm: `try_mark_green`
- Documentation URL: https://github.com/rust-lang/rust/blob/018018e881e2db0956f229dbb543e21f058d1ce7/src/doc/rustc-dev-guide/src/queries/incremental-compilation-in-detail.md
- Documentation blob SHA observed: `9893edd54b950155da586843baa3319da15dcc4e`

### Technique

Rust's incremental compiler does not automatically invalidate a dependent merely because one of its inputs changed. Its dependency graph marks a node green when its previous cached result is proven reusable and red when re-evaluation shows that its result actually changed. For an unknown dependency, the system recursively tries to prove it green; if that cannot be done from already-known state, it re-runs the dependency and compares the result. If the recomputed result is still equivalent, invalidation stops there rather than cascading upward.

The same documentation also highlights a second necessary property for cross-run caches: persisted references need stable identities. Session-local sequential IDs may shift after unrelated edits, so Rust converts important identities to stable forms before persistence and maps them back in the new session.

### Why it may be useful for KNEEKURA

This is a stronger generalization of simple timestamp/hash invalidation. A KNEEKURA analysis DAG could distinguish:

1. input changed,
2. node must be re-evaluated,
3. node's *observable result* changed,
4. dependents must therefore be invalidated.

That separation is useful for static-analysis graphs, evidence extraction, derived metadata, Viewer preparation, and other pipelines where many source edits do not alter every derived fact. Stable cross-run node identities are equally important if cached evidence or dependency edges survive process restarts.

### Limitations / uncertainty

The technique relies on queries behaving close to pure functions and on dependency edges being complete. Hidden dependencies such as environment variables, tool versions, network state, filesystem state, clock/randomness, or mutable global state can make a node appear green incorrectly. Result equality can itself be expensive. KNEEKURA would need explicit impurity boundaries and versioned environment/configuration inputs before adopting this pattern. This candidate overlaps conceptually with 17-A but is retained because it provides a general dependency-graph evaluation rule rather than TypeScript's language-specific shape-signature propagation rule.

---

## Candidate 17-C — Deterministic whole-system simulation plus deliberate fault injection

- Repository: `apple/foundationdb`
- Popularity at inspection: 16,692 GitHub stars
- Repository URL: https://github.com/apple/foundationdb
- Revision inspected: `10a002f6bc47996fb378da0fb2d93df5e0187e32`
- Runtime entry evidence: `fdbserver/fdbserver.cpp` — simulation role prints/uses an explicit random seed and binds deterministic randomness
- Simulator implementation: `fdbrpc/sim2.cpp`
- Simulated cluster setup: `fdbserver/SimulatedCluster.cpp`
- Fault-injection workload example: `fdbserver/workloads/MachineAttrition.cpp`
- Simulator URL: https://github.com/apple/foundationdb/blob/10a002f6bc47996fb378da0fb2d93df5e0187e32/fdbrpc/sim2.cpp
- Cluster URL: https://github.com/apple/foundationdb/blob/10a002f6bc47996fb378da0fb2d93df5e0187e32/fdbserver/SimulatedCluster.cpp
- Workload URL: https://github.com/apple/foundationdb/blob/10a002f6bc47996fb378da0fb2d93df5e0187e32/fdbserver/workloads/MachineAttrition.cpp

### Technique

FoundationDB contains a simulator that runs distributed-system behavior under controlled simulated time/process/network/filesystem conditions. The simulation path uses deterministic randomness keyed by an explicit seed, while workloads deliberately exercise rare failure states such as process/machine attrition and reboot/delete variants. A failing interleaving can therefore be associated with a seed and replayed rather than being left as a one-off timing accident.

### Why it may be useful for KNEEKURA

KNEEKURA has several concurrency-heavy boundaries where real-time-only testing can hide races: Runner leases, command/result delivery, multi-agent mutation, worker restart, cache cleanup, Viewer/runtime observation, and recovery after interrupted writes. A small deterministic scheduler/fault harness could make tests such as "worker dies after durable receipt but before result publication" or "lease expires while an old callback is still queued" reproducible from a seed.

The important reusable pattern is not "simulate Minecraft" or "copy FoundationDB's simulator". It is to make nondeterministic scheduling/failure choices explicit inputs, record them, inject failures at named boundaries, and replay the exact sequence.

### Limitations / uncertainty

FoundationDB's simulation infrastructure is large and deeply coupled to its actor runtime. Reproducing its scope would be disproportionate for KNEEKURA. A smaller deterministic harness should target only critical state machines first. Simulation also proves behavior only within the modeled failure space; missing real OS/GPU/filesystem/network behavior still requires live tests. Some design documentation currently present in the FoundationDB tree is AI-generated, so this harvest intentionally relies on real runtime/simulator/workload source paths rather than treating that generated prose as authoritative evidence.

---

## Candidate 17-D — Retry throttling whose budget degrades on failures and heals on successes

- Repository: `grpc/grpc`
- Popularity at inspection: 45,303 GitHub stars
- Repository URL: https://github.com/grpc/grpc
- Revision inspected: `a65db1b513baec11e0d9a726cd4f482f780c88e9`
- Primary path: `src/core/client_channel/retry_throttle.cc`
- Primary class/functions: `RetryThrottler`, `RecordFailure`, `RecordSuccess`, `Create`
- Source URL: https://github.com/grpc/grpc/blob/a65db1b513baec11e0d9a726cd4f482f780c88e9/src/core/client_channel/retry_throttle.cc
- Blob SHA observed: `7ac5bf5c80af13ce163194f7e2fb263ae02955aa`
- Supporting test: `test/core/client_channel/retry_throttle_test.cc`
- End-to-end test: `test/core/end2end/tests/retry_throttled.cc`

### Technique

gRPC's retry throttler maintains a bounded token state. Each failure removes one token; retries are allowed only while the resulting token level remains above half the configured maximum. Successful calls add tokens back according to a configured ratio, capped at the maximum. When throttling parameters change, the replacement throttler can initialize its state proportionally from the previous token fraction so a live configuration change does not accidentally erase an already-observed unhealthy condition.

### Why it may be useful for KNEEKURA

This differs from a simple fixed retry count or crash-loop budget. It represents recent service health as a slowly degrading/healing state and can suppress retry storms across many otherwise independent requests. Candidate applications include GitHub/API operations, Runner RPC, local model-server calls, browser bridge calls, or artifact fetches: repeated failures reduce retry authority for that target; sustained success restores it.

A KNEEKURA adaptation should probably scope budgets by failure domain (for example endpoint/service/runner) rather than globally, and combine the throttle with exponential backoff and idempotency rules.

### Limitations / uncertainty

The `half of maxTokens` threshold and token arithmetic are gRPC policy details, not universal constants. A health bucket can also hide recovery if success traffic is too sparse, so half-open/probe behavior may be needed for KNEEKURA. Retry throttling does not make unsafe operations retryable: mutations still require idempotency keys, fencing/authority checks, or explicit non-retry rules. It also should not suppress high-value diagnostic reporting merely because execution retries are disabled.

---

## Cross-candidate synthesis — NON-CANONICAL hypothesis only

A possible KNEEKURA pattern suggested by this cycle is:

`stable node identity → explicit dependency graph → re-evaluate only changed inputs → compare observable output/shape → propagate invalidation only on real output change → exercise the state machine under seeded deterministic failures → throttle recovery traffic if the downstream target remains unhealthy`

This synthesis is an inference made during harvesting, not a statement that the referenced projects use this combined architecture. It therefore remains explicitly STAGING / NON-CANONICAL and requires independent design review and validation.

## Governance disposition

- Discovery evidence captured: yes
- Exact repository URLs captured: yes
- Revisions fixed where available: yes
- File/path/function provenance captured: yes
- Limitations and uncertainty recorded: yes
- Popularity treated as truth: no
- Duplicate check against visible harvest backlog: yes
- Human selection performed: no
- VALIDATED promotion performed: no
- Canonical Knowledge Entity/relation created: no
- Production code modified: no

Next permitted step is human/governed review of these staged candidates.