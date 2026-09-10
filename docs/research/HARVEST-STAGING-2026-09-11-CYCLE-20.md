# KNEEKURA TECH HUB — Harvest Staging Cycle 20

Status: **STAGING / NON-CANONICAL**  
Governance: discovery only; no VALIDATED/canonical promotion and no production implementation authorization. Popularity is used only as a discovery prior, never as correctness evidence.

## Duplicate-avoidance scope

Checked the existing `docs/research` staging area on `main` and open Harvest PRs through Cycle 19 / PR #55. The findings below were selected because they are not obvious duplicates of the already staged topics.

## 1. ClickHouse — cache admission must include semantic determinism, not only structural query identity

- Repository: `ClickHouse/ClickHouse`
- Popularity at retrieval: 49,806 GitHub stars
- Revision: `dde96d25ff835ada5185fc9a6e308d6db2cfeb6a`
- Path: `src/Processors/QueryPlan/ReadFromMergeTree.cpp`
- Section/function: `isDeterministicAllowingTopKFilter`
- Source URL: https://github.com/ClickHouse/ClickHouse/blob/dde96d25ff835ada5185fc9a6e308d6db2cfeb6a/src/Processors/QueryPlan/ReadFromMergeTree.cpp

### Technique
ClickHouse's query-condition-cache admission logic explicitly rejects non-deterministic `COLUMN` nodes, including query-time constants such as `now()` / `today()`. The source comment explains the failure mode: a query can otherwise write a cache entry with a captured time-dependent value and later reuse that entry after the value has changed.

### Why it may be useful for KNEEKURA
A cache key can be structurally identical while its hidden semantic inputs have changed. KNEEKURA caches for analysis facts, evidence queries, model preprocessing, rendered views, or tool results should distinguish pure/replay-safe inputs from time-, environment-, filesystem-, network-, model-version-, or session-dependent inputs. A candidate rule is: cache reuse requires both key equality and an explicit determinism/freshness proof for all captured dependencies.

### Limitations
Determinism classification is only as good as the dependency model. Misclassifying a hidden input as deterministic can produce stale or false evidence. Conversely, rejecting every uncertain operation can erase most cache benefit.

### Applicability
High for evidence caches, derived-analysis caches, repository metadata snapshots, and any memoized operation whose result can depend on ambient state.

### Uncertainty
The ClickHouse rule is specific to its query-condition cache. Mapping it to KNEEKURA requires defining which ambient inputs are canonical dependencies and how freshness/version identity is represented.

## 2. DuckDB — online hill-climbing for execution order, with automatic rollback and semantic safety barriers

- Repository: `duckdb/duckdb`
- Popularity at retrieval: 41,133 GitHub stars
- Revision: `ddb3a18f017d7eebec6ce2e73ef3861f4f99f4d2`
- Paths: `src/execution/adaptive_filter.cpp`, `src/include/duckdb/execution/adaptive_filter.hpp`
- Main section/functions: `AdaptiveFilter::BeginFilter`, `AdaptiveFilter::EndFilter`, `AdaptiveFilter::AdaptRuntimeStatistics`
- Source URL: https://github.com/duckdb/duckdb/blob/ddb3a18f017d7eebec6ce2e73ef3861f4f99f4d2/src/execution/adaptive_filter.cpp

### Technique
DuckDB begins from a heuristic filter order, measures actual monotonic runtime, occasionally swaps adjacent filters, observes a trial window, and keeps the swap only if mean runtime improves. If runtime does not improve, it reverses the swap and reduces that swap's future likelihood while retaining a small exploration probability. Crucially, it disables permutation entirely when expressions can throw or contain an expression barrier, because reordering could change observable semantics.

### Why it may be useful for KNEEKURA
This is a compact pattern for safe runtime adaptation: start from a static heuristic, make one bounded reversible change, measure real execution, keep only demonstrated wins, and keep semantic barriers outside the optimization space. It could apply to read-only analyzer ordering, cheap-vs-expensive evidence predicates, scan stages, or other commutative work where ordering affects cost but not meaning.

### Limitations
Short measurement windows are noisy; changing workloads can make yesterday's learned order wrong. Exploration itself costs work. The method is unsafe if operations have side effects, exceptions whose order matters, hidden dependencies, or governance-sensitive sequencing.

### Applicability
Medium-to-high for repeated, independent, read-only stages with measurable latency and genuinely order-independent semantics.

### Uncertainty
The exact warmup/observe/execute intervals and adjacent-swap strategy are DuckDB-specific. KNEEKURA would need its own noise model, minimum improvement threshold, reset rules, and explicit semantic-equivalence gate.

## 3. Apache Airflow — park long waits outside scarce worker slots, then resume from a durable continuation point

- Repository: `apache/airflow`
- Popularity at retrieval: 46,811 GitHub stars
- Revision: `6a6a24f2e1a10ac51c9a0c5910cb08b21d9121d2`
- Primary path: `airflow-core/docs/authoring-and-scheduling/deferring.rst`
- Supporting examples: provider operators/sensors using `defer(..., method_name="execute_complete")`
- Primary source URL: https://github.com/apache/airflow/blob/6a6a24f2e1a10ac51c9a0c5910cb08b21d9121d2/airflow-core/docs/authoring-and-scheduling/deferring.rst
- Example source URL: https://github.com/apache/airflow/blob/6a6a24f2e1a10ac51c9a0c5910cb08b21d9121d2/providers/dbt/cloud/docs/operators.rst

### Technique
Airflow deferrable tasks move long asynchronous waiting to a triggerer instead of occupying a normal worker slot. Provider documentation explicitly notes that deferring releases the worker slot while the external job continues. When the trigger fires, execution resumes through a named continuation such as `execute_complete` rather than keeping the original worker blocked for the entire wait.

### Why it may be useful for KNEEKURA
KNEEKURA has many potentially long waits: GitHub CI, runner availability, model loading, external jobs, filesystem events, or Minecraft/runtime observation. A task that is merely waiting should not monopolize an expensive worker/model slot. Persisting a typed continuation plus trigger condition could let the worker return to the pool and later reacquire capacity only when useful work can resume.

### Limitations
Deferral is not free: continuation state must be serializable/durable, triggers must be reliable, duplicate wakeups must be idempotent, and resumed work may run on a different worker. Any in-memory-only state or unrecoverable resource ownership breaks the model.

### Applicability
High for long external waits and condition watches; low for CPU-bound operations that are actively computing rather than waiting.

### Uncertainty
Airflow's triggerer architecture is not a direct fit for every KNEEKURA runtime. The reusable idea is separation of `WAITING` from `RUNNING` resource ownership; exact persistence, wakeup, and lease semantics require independent design.

## Cross-finding synthesis (hypothesis only)

A possible KNEEKURA runtime contract emerges from the three findings: **admit cache reuse only when semantic dependencies are safe; permit runtime optimization only inside an explicitly commutative/reversible region; and release scarce execution capacity whenever a task is merely waiting.** This synthesis is a new inference from the harvested evidence, not validated knowledge.

## Governance disposition

All three findings remain **STAGING / NON-CANONICAL**. No human selection was bypassed, no VALIDATED state was assigned, no canonical Knowledge Entity or relation was created, and no KNEEKURA production code was changed.
