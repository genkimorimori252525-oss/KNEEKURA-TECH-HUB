# KNEEKURA TECH HUB Harvest Staging — Cycle 28

Status: **STAGING / NON-CANONICAL**

Date: 2026-09-11

This document records one evidence-backed harvesting pass. Popularity is used only as a discovery prior, never as validation. None of the findings below are promoted to VALIDATED or canonical knowledge, and none authorize production implementation.

## Duplicate-control note

Before selecting findings, the currently open Harvest PR backlog was reviewed through Cycle 27. The selected topics are intentionally distinct from recent entries such as sparse-index/RCU/WAL snapshot pinning, lockdep/rerere/workqueue coalescing, jump labels/extension bisect/Loom, Kafka epoch fencing, field ownership, fuzz minimization, cache determinism, singleflight, async-context propagation, resource lifetime tracking, adaptive batching, deferrable waits, generation freshness, and existing cache-fingerprint work.

---

## Candidate 1 — Git changed-path Bloom filters as a negative-query accelerator

### Provenance

- Repository: `git/git`
- Repository URL: https://github.com/git/git
- Stars observed during this harvest: **63,101**
- Revision inspected: `fa7f9290efe2bd22dd736689597b474b93798e11`
- Primary file: `Documentation/gitformat-commit-graph.adoc`
- Primary URL: https://github.com/git/git/blob/fa7f9290efe2bd22dd736689597b474b93798e11/Documentation/gitformat-commit-graph.adoc
- Supporting file: `t/t4216-log-bloom.sh`
- Supporting URL: https://github.com/git/git/blob/fa7f9290efe2bd22dd736689597b474b93798e11/t/t4216-log-bloom.sh
- Supporting implementation: `revision.c`
- Supporting URL: https://github.com/git/git/blob/fa7f9290efe2bd22dd736689597b474b93798e11/revision.c

### Technique

Git can store an optional changed-path Bloom filter per commit in the serialized commit graph. The filter represents paths changed between a commit and its first parent. Path-limited history queries can consult that compact probabilistic summary before performing more expensive tree-difference work.

The reusable pattern is not merely "use a Bloom filter". It is:

1. attach a compact negative-membership summary to each graph node,
2. consult that summary before expensive exact traversal,
3. skip exact work when the summary says the target is definitely absent,
4. still execute the exact check when the summary says the target may be present,
5. retain tests/metrics for false positives so the accelerator cannot silently change semantics.

Git's tests explicitly track both `definitely_not` and `false_positive`, and compare Bloom-assisted results against non-Bloom results. This is important evidence that the filter is an optimization layer rather than an authority layer.

### Why this may be useful to KNEEKURA

Large KNEEKURA graphs repeatedly answer questions of the form "could this subtree/file/entity have affected X?". A compact per-node or per-partition negative summary could cheaply rule out large portions of the graph before loading full evidence or parsing detailed state.

Potential applications include:

- path-sensitive repository history lookup,
- dependency-edge discovery where most candidates do not reference a queried symbol,
- evidence-pack search where most packs cannot contain a requested identity,
- large archive/index scans where a cheap summary can reject cold partitions.

This is complementary to Cycle 27 sparse-index work. Sparse-index reduces the materialized representation of cold state; Bloom-style summaries reduce the amount of exact work required to answer negative queries over that state.

### Limitations / risks

- Bloom filters can produce false positives. A positive result must never be treated as proof that an exact relationship exists.
- A poor hash policy, undersized filter, or extremely dense node can reduce usefulness.
- Git deliberately uses a degenerate all-ones filter for commits with more than 512 changed paths; that is an example of refusing to spend more index space where selectivity would be poor.
- Building and maintaining summaries has ingestion cost and additional provenance/versioning requirements.
- KNEEKURA would need to tie the summary format to an exact parser/index schema version so stale summaries are not interpreted under changed semantics.

### Applicability

Best fit: large mostly-negative search spaces where exact verification remains available and where query semantics are stable enough to define the indexed feature precisely.

Poor fit: small collections, high-positive-rate queries, or any governance decision where probabilistic membership would be mistaken for evidence.

### Uncertainty

The likely win depends heavily on KNEEKURA query selectivity and summary density. Benchmarking against real TECH HUB / CODE LAB query distributions would be required before adoption.

---

## Candidate 2 — OpenCode protected-recent-tail compaction with selective old tool-output pruning

### Provenance

- Repository: `anomalyco/opencode`
- Repository URL: https://github.com/anomalyco/opencode
- Stars observed during this harvest: **206,568**
- Revision inspected: `193de13a88d62a6409c6d385831180f1def527dc`
- Primary file: `packages/opencode/src/session/compaction.ts`
- Primary URL: https://github.com/anomalyco/opencode/blob/193de13a88d62a6409c6d385831180f1def527dc/packages/opencode/src/session/compaction.ts
- Documentation: `packages/web/src/content/docs/config.mdx`
- Documentation URL: https://github.com/anomalyco/opencode/blob/193de13a88d62a6409c6d385831180f1def527dc/packages/web/src/content/docs/config.mdx

### Technique

OpenCode does not treat all historical context as equally disposable. Its compaction logic establishes an explicit recent-context budget, walks backward through recent turns, and preserves a tail that fits that budget. Separately, optional pruning walks old completed tool calls backward and clears old tool outputs only after a protected amount of newer tool-output context has been retained.

At the inspected revision the implementation exposes several concrete safeguards:

- `preserveRecentBudget(...)` reserves a recent conversational tail based on usable context, bounded by minimum and maximum values.
- tail selection estimates context lazily from the newest turns backward instead of repeatedly estimating the entire session.
- pruning protects the most recent tool-output token budget (`PRUNE_PROTECT`).
- pruning does not begin until at least two user turns have been crossed.
- specific tools can be exempted from pruning (`PRUNE_PROTECTED_TOOLS`).
- previously compacted tool outputs are marked with a compaction timestamp rather than being indistinguishable from naturally empty output.
- pruning only happens when enough reclaimable material exceeds a minimum threshold, avoiding constant tiny rewrites.

The reusable idea is **tiered context retention**: keep recent/high-value interaction verbatim, summarize or compact older conversation state, and prune bulky historical tool payloads only behind explicit retention boundaries.

### Why this may be useful to KNEEKURA

KNEEKURA's AI/developer workflows can accumulate large volumes of GitHub search snippets, CI logs, command output, file reads, screenshots, and repeated diagnostic payloads. Keeping all of those verbatim forever is expensive and can crowd out the current task state.

A KNEEKURA-specific retention policy could distinguish:

- authority/governance facts that must never be silently discarded,
- current-step evidence that should remain verbatim,
- recent tool output that remains useful for local reasoning,
- old bulky output whose provenance can remain while the payload is moved to an artifact or replaced by a bounded summary.

This could reduce token/context pressure without pretending that information never existed.

### Limitations / risks

- Pruning the wrong tool output can erase the only evidence needed to audit a later conclusion.
- Token count is only a size signal; it does not measure epistemic value or governance importance.
- Summaries can omit details or introduce interpretation error.
- KNEEKURA therefore should never apply a simple age/size policy to canonical evidence, approval records, exact SHAs, mutation receipts, or failure reproducers.
- If payloads are removed from live context, provenance should still point to durable raw artifacts when those artifacts are required for audit.

### Applicability

Best fit: long-running AI sessions and developer workflows containing repeated or bulky tool payloads where raw evidence can be durably retained outside the active reasoning window.

Poor fit: short tasks, small contexts, or evidence that has no durable raw backing store.

### Uncertainty

OpenCode's concrete token thresholds are product-specific and should not be copied. The useful harvest is the retention hierarchy and explicit protection boundary, not the numeric constants.

---

## Candidate 3 — TensorFlow tf.data model-based autotuning under explicit CPU/RAM budgets

### Provenance

- Repository: `tensorflow/tensorflow`
- Repository URL: https://github.com/tensorflow/tensorflow
- Stars observed during this harvest: **199,704**
- Revision inspected: `8ea4ae9c8c329c2d09e51536f30af915e7c5c147`
- Primary implementation: `tensorflow/core/framework/model.cc`
- Primary URL: https://github.com/tensorflow/tensorflow/blob/8ea4ae9c8c329c2d09e51536f30af915e7c5c147/tensorflow/core/framework/model.cc
- Algorithm schema: `tensorflow/core/framework/model.proto`
- Schema URL: https://github.com/tensorflow/tensorflow/blob/8ea4ae9c8c329c2d09e51536f30af915e7c5c147/tensorflow/core/framework/model.proto
- Dataset integration: `tensorflow/core/kernels/data/model_dataset_op.cc`
- Integration URL: https://github.com/tensorflow/tensorflow/blob/8ea4ae9c8c329c2d09e51536f30af915e7c5c147/tensorflow/core/kernels/data/model_dataset_op.cc

### Technique

TensorFlow's `tf.data` runtime builds a performance model of the input pipeline and tunes parameters such as parallelism and buffering. The model exposes multiple optimization algorithms including hill climbing and gradient descent, while the dataset integration carries explicit CPU and RAM budgets into the optimization process.

The reusable pattern is **budget-constrained adaptive tuning**:

1. represent a pipeline as tunable nodes/parameters rather than fixed constants,
2. observe or model the performance impact of those parameters,
3. search for a better configuration,
4. keep optimization inside explicit resource budgets,
5. separate the optimization algorithm from the workload model so the policy can evolve independently.

This differs from Cycle 20 DuckDB's adaptive filter ordering. DuckDB learns a better local ordering from observed operator cost; TensorFlow coordinates multiple pipeline parameters against resource budgets and a pipeline-level performance model.

### Why this may be useful to KNEEKURA

Several KNEEKURA workloads currently contain manually chosen concurrency/buffer/batch values: repository scanning, parser parallelism, artifact hashing, local model preprocessing, render/observation pipelines, and evidence indexing.

Instead of hard-coding a value such as "8 workers" or "256 items/tick" for every machine and workload, a bounded tuner could explore safe parameter combinations while respecting declared CPU/RAM/VRAM/latency ceilings.

Potential applications:

- choose parser/indexing parallelism from observed throughput and host CPU pressure,
- tune batch sizes for hashing or evidence validation,
- adjust producer/consumer buffer sizes without exceeding memory ceilings,
- adapt local-model preprocessing concurrency to the current PC workload,
- periodically re-evaluate a configuration after hardware, model, repository, or workload changes.

### Limitations / risks

- Autotuning can oscillate or chase noise when measurements are unstable.
- A throughput objective can optimize the wrong thing if latency, responsiveness, power, or deterministic behavior matters more.
- Search itself consumes resources and can briefly try worse configurations.
- The model may be wrong outside the workload regime where observations were gathered.
- CPU and RAM are not enough for KNEEKURA workloads that also depend on VRAM, disk I/O, network limits, or UI responsiveness.
- Governance-sensitive or side-effecting steps must not be experimentally reordered merely for performance.

### Applicability

Best fit: repeatable, measurable, non-governance-critical pipelines with tunable numeric parameters and clear hard resource ceilings.

Poor fit: one-shot jobs, highly non-stationary workloads, irreversible mutations, or workflows whose correctness depends on a fixed execution shape.

### Uncertainty

The TensorFlow implementation is optimized for input pipelines, not general orchestration. KNEEKURA would need a much smaller tuner and explicit multi-resource guardrails. This is a design candidate, not evidence that automatic tuning will outperform current fixed settings on the user's machine.

---

## Cross-finding synthesis candidate — cheap exclusion, protected evidence, bounded adaptation

A possible higher-level pattern emerges from the three findings:

1. **Exclude cheaply before exact work** using negative summaries such as changed-path Bloom filters.
2. **Protect the high-value recent/evidence tail** instead of treating all accumulated context as equally disposable.
3. **Adapt numeric execution parameters only inside explicit resource ceilings** rather than maximizing throughput without bounds.

For a future KNEEKURA indexing/agent pipeline this could mean:

`probabilistic reject -> exact verifier -> evidence retention tier -> budget-aware worker/buffer tuner`

This synthesis is a new inference made during harvesting. It has no independent validation and must not be treated as canonical architecture.

## Governance disposition

- Discovery: completed for this cycle.
- Provenance: captured at exact revisions above.
- Duplicate screening: performed against open Harvest backlog through Cycle 27.
- Status: **STAGING / NON-CANONICAL**.
- Human selection: not performed.
- VALIDATED promotion: not performed.
- Canonical Knowledge Entity creation: not performed.
- Production implementation: not authorized or performed.
