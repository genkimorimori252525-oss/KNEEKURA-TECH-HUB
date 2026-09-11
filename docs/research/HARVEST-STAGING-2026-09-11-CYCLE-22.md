# KNEEKURA TECH HUB — Harvest Staging 2026-09-11 Cycle 22

Status: **STAGING / NON-CANONICAL**

This document records discovery candidates only. It does **not** promote any item to VALIDATED or canonical knowledge, authorize implementation, or override existing governance. GitHub popularity was used only to prioritize inspection; evidence and applicability were evaluated separately.

## Deduplication / selection notes

Before harvesting, existing research on `main` and open Harvest PR descriptions through Cycle 21 were checked. The recent open cycles already cover, among other things, retry throttling, generation freshness, async context propagation, resource lifetime tracking, cancellation propagation, KV-cache reuse, adaptive batching, incremental invalidation, deterministic fault simulation, overload degradation, deadlock detection, jobserver tokens, permission ceilings, lazy freeing, semantic cache determinism, deferrable waits, singleflight, and event-loop blocking guards.

The three findings below were selected because their core mechanism was not found in the existing harvested set:

1. cross-buffer edit transactions with unified undo/redo identity;
2. feedback-controlled elastic CPU budgeting with cooperative self-preemption;
3. cache identity that explicitly fingerprints files, dependency state, runtime engines, environment configuration, and normalization rules.

Popularity is not evidence of correctness. Star counts are a discovery-time snapshot and may change.

---

## Finding 1 — Zed: cross-buffer transactions as one undoable change unit

**Repository:** `zed-industries/zed`  
**Discovery-time popularity:** 90,071 GitHub stars  
**Repository URL:** https://github.com/zed-industries/zed  
**Pinned revision:** `1a84d5d92bd7d6c1cabb116062650af545783fe9`  
**Primary source:** `crates/multi_buffer/src/transaction.rs`  
**Pinned URL:** https://github.com/zed-industries/zed/blob/1a84d5d92bd7d6c1cabb116062650af545783fe9/crates/multi_buffer/src/transaction.rs  
**Relevant sections/functions:** `History`, `Transaction`, `start_transaction`, `end_transaction`, `group`, `group_trailing`, `MultiBuffer::undo`, `MultiBuffer::redo`

### Technique

Zed represents a higher-level edit transaction as a map from each affected buffer ID to that buffer's own transaction ID. The outer history keeps a single undo/redo entry that can span several underlying files/buffers. Nested transaction depth is tracked explicitly: only the outermost transaction creates/finalizes the aggregate history entry. Empty transactions are discarded, redo history is cleared on a committed new edit, and nearby transactions can be grouped within a bounded interval unless grouping has been explicitly suppressed.

Undo and redo then walk the recorded per-buffer transaction IDs, applying the corresponding operation to each still-present buffer. In other words, physical edits remain local to individual buffers, while the user-visible change unit is a higher-level transaction identity.

### Why it may be useful to KNEEKURA

AI/developer workflows often make logically atomic changes across several files: implementation + tests + fixture + documentation, or a generated patch touching several modules. Treating every file mutation as an unrelated operation makes rollback and review harder. A KNEEKURA equivalent could preserve a `changeSetId` that maps to exact per-file mutations so that one governed operation can be reverted, replayed, inspected, or attributed as one unit without requiring the storage layer itself to become a giant monolithic transaction.

This may be particularly useful for Code Police repair proposals, multi-file refactors, generated compatibility patches, and workspace tooling where the system should be able to say exactly which files belonged to one attempted change.

### Limitations / cautions

- Zed's transaction model is an editor undo model, not a distributed ACID transaction. A direct copy would not provide crash-safe atomic filesystem commits.
- Buffers may disappear; the implementation skips unavailable buffers during undo/redo. KNEEKURA would need a stricter policy when missing files imply integrity loss.
- Time-based grouping (300 ms by default in the inspected code) is a UI heuristic and should not define governance boundaries.
- Cross-file rollback can be unsafe if external side effects occurred between edits. GitHub mutations, process launches, package installs, or database writes require separate compensation/idempotency rules.
- Licensing must be considered before copying implementation code. The technique itself can be reimplemented independently.

### Applicability

**High** for workspace/editor-like multi-file mutations and repair proposal staging.  
**Medium** for Git commit construction, where Git already supplies a stronger atomic commit object.  
**Low** as a substitute for distributed transaction protocols.

### Uncertainty

The inspected file clearly establishes cross-buffer transaction aggregation and unified undo/redo behavior. This harvest does not establish all concurrency/crash semantics of Zed's complete persistence layer, so no stronger durability claim is made.

---

## Finding 2 — CockroachDB: feedback-controlled elastic CPU budgets with cooperative self-preemption

**Repository:** `cockroachdb/cockroach`  
**Discovery-time popularity:** 32,450 GitHub stars  
**Repository URL:** https://github.com/cockroachdb/cockroach  
**Pinned revision:** `8812064a015d2faf99d3fc7e15880f94042954b0`  
**Primary source:** `pkg/util/admission/elastic_cpu_granter.go`  
**Pinned URL:** https://github.com/cockroachdb/cockroach/blob/8812064a015d2faf99d3fc7e15880f94042954b0/pkg/util/admission/elastic_cpu_granter.go  
**Relevant sections/functions:** file-level design comment, `elasticCPUGranter`, `tryGet`, `setUtilizationLimit`, `computeUtilizationMetric`

### Technique

CockroachDB separates latency-sensitive foreground work from long-running "elastic" work. Elastic work obtains CPU-time tokens from a token bucket. The refill budget is derived from a target utilization multiplied by the number of processors, so the token unit represents actual CPU nanoseconds rather than merely a count of jobs.

The more distinctive part is the feedback loop: scheduler latency is measured and used to adjust the permitted elastic CPU percentage. When scheduling latency rises above the target, elastic utilization is reduced; when latency is healthy and allotted capacity is substantially used, the limit can rise. The design deliberately adjusts downward more aggressively than upward and smooths the measured p99 scheduler latency to reduce controller instability.

Long-running elastic work does not simply receive an unlimited permit after admission. It consumes a bounded CPU slice and then cooperatively preempts itself, returning a resumption key so it can continue later. The source comments explain that very large slices would let a request monopolize a core and build up runnable foreground goroutines, so bounded slices are part of the latency protection mechanism.

### Why it may be useful to KNEEKURA

A fixed `N workers` limit cannot distinguish a cheap task from one that burns a core for seconds. KNEEKURA has several plausible background/elastic workloads: repository indexing, static graph rebuilds, evidence compaction, similarity scans, large hashing jobs, offline rendering, and local-model preprocessing. A CPU-time budget plus cooperative resume points could let those jobs use spare capacity without making interactive Command Bridge, heartbeat, audit logging, or user-facing control paths sluggish.

The feedback idea is especially reusable: instead of tuning one permanent background-concurrency number for every PC and workload, the system could observe a foreground-health signal and slowly expand or rapidly shrink background work.

### Limitations / cautions

- CockroachDB's exact p99 target, sampling interval, 100 ms slice, adjustment deltas, and utilization bounds are experimentally chosen for its runtime and must **not** be copied as universal constants.
- Cooperative preemption only works where jobs expose safe yield/resume boundaries. Arbitrary third-party commands cannot necessarily be paused safely.
- CPU pressure is only one resource dimension. RAM, VRAM, disk I/O, thermal limits, API quota, and network bandwidth need independent accounting.
- Feedback controllers can oscillate or react too slowly if signals, smoothing, or adjustment rates are poorly chosen.
- A resumption key becomes part of correctness: stale or ambiguous resume state could repeat or skip work.
- This is complementary to the previously harvested overload manager / jobserver / I/O token techniques, not a replacement for them.

### Applicability

**High** for resumable CPU-heavy background loops under interactive foreground traffic.  
**Medium** for local AI preprocessing/indexing when the work can checkpoint.  
**Low** for indivisible external commands or hard real-time guarantees.

### Uncertainty

The source contains strong implementation-level and design-comment evidence for tokenized CPU slices, feedback adjustment, scheduler-latency motivation, and cooperative preemption. This harvest does not independently reproduce CockroachDB's production latency measurements, so the claimed benefit for KNEEKURA remains a candidate hypothesis until benchmarked locally.

---

## Finding 3 — Turborepo: cache identity must include declared ambient inputs, not only source files

**Repository:** `vercel/turborepo`  
**Discovery-time popularity:** 31,073 GitHub stars  
**Repository URL:** https://github.com/vercel/turborepo  
**Pinned revision:** `17b358add9d9b060f4c6b0c6d70d939ccec3baaa`  
**Primary source:** `crates/turborepo-task-hash/src/global_hash.rs`  
**Pinned URL:** https://github.com/vercel/turborepo/blob/17b358add9d9b060f4c6b0c6d70d939ccec3baaa/crates/turborepo-task-hash/src/global_hash.rs  
**Corroborating configuration/docs at same revision:** `skills/turborepo/references/configuration/global-options.md`, `skills/turborepo/references/environment/modes.md` (when present in the pinned tree)  
**Relevant sections/functions:** `GlobalHashableInputs`, `get_global_hash_inputs`, `collect_global_file_hash_inputs`, `collect_global_deps`, `calculate_global_hash`

### Technique

Turborepo builds a global cache fingerprint from more than file contents. The inspected implementation carries hashes/identity for global files, external and internal dependencies, runtime engines, explicitly hashable environment variables, passthrough/environment mode, framework inference, and selected global configuration. It also snapshots the execution-start environment and resolves the configured hashable variables from it.

A particularly useful detail is that `.gitattributes` is included when present because line-ending normalization changes file hashes; changing normalization rules therefore invalidates the cache. The expensive global-file hashing stage is also separated so it can run concurrently with independent dependency-hash computation.

The broader design principle is that cache correctness requires an explicit model of all ambient inputs that can change the result. Merely hashing source files is insufficient when environment variables, dependency resolution, runtime/toolchain versions, or normalization rules affect behavior.

### Why it may be useful to KNEEKURA

KNEEKURA has many artifacts that look content-addressable but can silently depend on more than repository bytes: parser version, Forge/Minecraft/YSM versions, model weights, OS/path normalization, feature flags, environment variables, tool configuration, renderer revision, or declared compatibility mode. An artifact key that records only `repo SHA` can therefore produce a false cache hit.

A reusable KNEEKURA pattern would define an explicit `ArtifactInputFingerprint` with source content plus declared ambient/toolchain inputs. The cache entry would be reusable only when all semantically relevant fingerprint components match. This is particularly applicable to Render Packs, static analysis indexes, compiled fixtures, generated evidence, and deterministic parser outputs.

### Limitations / cautions

- No hash scheme can protect correctness from an input the system failed to model. Hidden ambient dependencies remain the central risk.
- Hashing too many irrelevant variables causes unnecessary cache misses and destroys reuse.
- Passthrough values and secret handling need special care: secrets generally should not be stored in plaintext evidence merely to make a cache key.
- Toolchain/OS fingerprints must be normalized carefully; overly specific machine identity can make caches useless across equivalent environments.
- The source code contains project-specific assumptions around package managers, workspace globs, Git normalization, and JavaScript/Cargo integration that are not directly portable.
- This complements Cycle 20's semantic determinism gating: Cycle 20 asks whether a computation is safe to cache at all; this finding asks which declared inputs must define the cache identity once caching is permitted.

### Applicability

**Very high** for generated artifacts and analysis caches where reproducibility/provenance matter.  
**High** for cross-session/cross-worktree reuse.  
**Medium** for ephemeral caches where false hits are low impact.

### Uncertainty

The implementation directly establishes the listed global fingerprint inputs. The correct KNEEKURA fingerprint schema is not yet known and must be derived per artifact type; this finding should not be interpreted as authorization for one universal cache-key structure.

---

## Cross-finding synthesis (hypothesis only)

A potentially useful combined pattern is:

1. represent one AI repair/refactor as a higher-level change-set identity spanning all affected files;
2. run heavy preparatory analysis under an elastic, resumable CPU budget so interactive control paths retain responsiveness;
3. bind any reusable generated artifact to an explicit fingerprint of source + toolchain + environment inputs;
4. keep the whole chain reviewable and reversible without treating any successful cache hit or benchmark as canonical truth.

This synthesis is a **new hypothesis created during this harvest**, not evidence that the three projects endorse the combined architecture and not a VALIDATED KNEEKURA design.

## Governance disposition

- Harvest state: **STAGING / NON-CANONICAL**
- Human selection performed: **No**
- VALIDATED promotion performed: **No**
- Canonical Knowledge Entity/relation creation performed: **No**
- Production implementation performed: **No**
- Popularity treated as proof: **No**

Next governed action, if selected later, should be targeted validation/prototyping against KNEEKURA-specific workloads rather than direct implementation from popularity or analogy alone.
