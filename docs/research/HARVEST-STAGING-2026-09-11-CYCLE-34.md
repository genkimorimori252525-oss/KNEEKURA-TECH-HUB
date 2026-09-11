# KNEEKURA TECH HUB — Harvest Staging Cycle 34

Status: **STAGING / NON-CANONICAL / NOT VALIDATED**  
Date: 2026-09-11  
Purpose: evidence-backed OSS technique harvesting only. Popularity is used as a discovery prior, not as proof of correctness or fitness.

## Governance boundary

This memo records candidates for later review. Nothing here is promoted to canonical or VALIDATED knowledge, nothing is authorized for production implementation, and no main-branch merge is implied.

Existing main research plus recent open Harvest PRs through Cycle 33 were reviewed before selection. Obvious duplicates were rejected. In particular, this cycle intentionally does **not** repeat prior findings on Bloom filters, sparse indexes, workqueue coalescing, singleflight, backpressure, cooperative CPU budgeting, lockdep, sequence counters, retry throttling, context compaction, or deterministic simulation.

---

## Finding 1 — Kubernetes watch bookmarks as progress-only resume checkpoints

### Provenance

- Repository: `kubernetes/kubernetes`
- Popularity at inspection: 127,331 GitHub stars
- Repository URL: https://github.com/kubernetes/kubernetes
- Revision: `a6d4708e816967a7d0c64155d6a702ab19463607`
- Primary path: `staging/src/k8s.io/client-go/tools/watch/retrywatcher.go`
- Exact source URL: https://github.com/kubernetes/kubernetes/blob/a6d4708e816967a7d0c64155d6a702ab19463607/staging/src/k8s.io/client-go/tools/watch/retrywatcher.go
- Related path: `staging/src/k8s.io/client-go/tools/cache/reflector.go`
- Related search evidence: `ReflectorBookmarkStore.Bookmark(resourceVersion string)` allows stores to receive bookmark progress information.

### Technique

A long-lived change stream can advance its durable resume cursor even when no user-visible mutation occurs.

`RetryWatcher` requests `AllowWatchBookmarks: true`, tracks the `resourceVersion` from normal events **and** bookmark events, and restarts a broken watch from `lastResourceVersion`. Bookmark events themselves are not forwarded as ordinary consumer mutations; they primarily advance the internal restart point.

This separates two meanings that are often incorrectly fused:

1. **domain event** — something the consumer should act on, and
2. **progress checkpoint** — proof that the stream has safely advanced to at least version N.

### Why it may be useful to KNEEKURA

KNEEKURA has several long-lived or resumable observation paths where silence does not necessarily mean staleness: repository/event watchers, runtime evidence streams, Minecraft/Viewer observation bridges, remote job feeds, and durable worker status streams.

A progress-only checkpoint could let such consumers persist `observedThrough=<revision>` without inventing a fake business event. After a transport reset, the consumer could resume from the newest known-safe revision rather than relisting or replaying a much larger interval.

Potential abstraction:

```text
DATA(version, payload)      -> deliver + advance cursor
CHECKPOINT(version)         -> do not deliver as domain change; advance cursor only
STREAM_BREAK                -> reconnect from latest cursor
CURSOR_TOO_OLD              -> full recovery / relist path
```

This is particularly attractive for evidence ingestion where duplicate replay is expensive but omission is unacceptable.

### Limitations / failure modes

- Kubernetes explicitly notes that `RetryWatcher` is **not** resilient when the backing etcd cache no longer retains the requested resource version. A higher-level relist/recovery path is still required.
- A bookmark is not evidence that every external side effect associated with prior events has completed. It is only a stream-progress marker.
- The meaning of the version must be monotonic and authoritative for the observed stream. Arbitrary timestamps are not an adequate substitute.
- If a consumer advances the durable cursor before its own required state/evidence is committed, a crash can create an unrecoverable gap. Cursor advancement must therefore be ordered after the consumer's own durable acceptance point when losslessness matters.

### Applicability

Good fit:
- resumable event/watch streams;
- observation journals with monotonic revisions;
- remote polling/watch APIs that expose explicit progress tokens;
- reducing needless relist/replay after idle periods.

Poor fit:
- unordered feeds without an authoritative sequence;
- streams where every heartbeat/checkpoint must itself trigger domain work;
- sources whose resume token can silently skip uncommitted consumer work.

### Uncertainty

The Kubernetes implementation proves the pattern in a resource-versioned API, but KNEEKURA would need its own cursor semantics and crash-ordering proof. The technique should not be generalized to every heartbeat or timestamp without demonstrating monotonicity and replay guarantees.

### Distinction from prior harvests

This is not Cycle 21 `observedGeneration`: that pattern couples a computed result to the desired-state generation it observed. This finding is about a **stream resume frontier that can advance even without a domain mutation**.

It is also not Cycle 26 workqueue coalescing: that pattern collapses redundant work items. Bookmarks preserve stream progress even when there is no work item at all.

---

## Finding 2 — Tokio cooperative task budgets with progress-sensitive charging

### Provenance

- Repository: `tokio-rs/tokio`
- Popularity at inspection: 33,120 GitHub stars
- Repository URL: https://github.com/tokio-rs/tokio
- Revision: `7bb6f0734922cffa7e49049dfc4c10d84737db41`
- Primary path: `tokio/src/task/coop/mod.rs`
- Exact source URL: https://github.com/tokio-rs/tokio/blob/7bb6f0734922cffa7e49049dfc4c10d84737db41/tokio/src/task/coop/mod.rs
- Related test path: `tokio/tests/macros_join.rs`

### Technique

Tokio protects a cooperative executor from an always-ready task monopolizing execution by assigning a bounded per-poll work budget.

The module documents the starvation case directly: an async source that is continuously ready may never naturally return `Poll::Pending`. Tokio therefore introduces explicit cooperative yield points.

At the inspected revision:

- a task begins with `Budget(Some(128))`;
- operations call `poll_proceed()` before performing cooperative work;
- when the budget is depleted, the task registers its waker and returns `Poll::Pending`, yielding to the scheduler;
- the returned `RestoreOnPending` only permanently consumes budget if the caller later signals `made_progress()`;
- if the downstream operation could not actually make progress, the previous budget is restored.

That last property is important: **attempted work is not automatically charged as useful work**.

### Why it may be useful to KNEEKURA

Several KNEEKURA components can execute user-space loops where each individual operation is cheap but an unbounded run can starve unrelated work: graph walking, artifact scanning, event draining, parser loops, local worker routing, viewer/state reconciliation, and large batches of small filesystem/database operations.

A KNEEKURA adaptation could use a cooperative budget such as:

```text
enter scheduler slice with budget B
  before bounded leaf operation:
    require one token
    if no token -> yield/requeue
    perform operation
    if operation made progress -> commit token consumption
    else -> refund token
```

The valuable idea is not the literal value `128`; it is the separation of:

- bounded work allowance,
- explicit yield points,
- real-progress accounting,
- scheduler fairness.

### Limitations / failure modes

- Tokio states that the initial value is chosen somewhat arbitrarily and may need adjustment as more yield points are introduced. `128` is implementation tuning, not a portable constant.
- Yield points placed too early or too high in a deeply nested future tree can prevent leaf work from receiving enough budget. Tokio recommends placing voluntary yield points after useful work and generally in leaf futures.
- Cooperative budgeting does not preempt arbitrary CPU-bound code that never reaches a cooperative yield point.
- A malicious or simply unaware component can opt out (`unconstrained`) or perform expensive work between yield points.
- Counting operations assumes roughly bounded work per charged unit. If one "operation" can vary by orders of magnitude, token accounting may need weighted cost or wall-time protection.

### Applicability

Good fit:
- single-process cooperative schedulers;
- large loops composed of relatively bounded leaf operations;
- event drains and graph/query traversals where latency fairness matters;
- preventing one continuously-ready source from monopolizing an executor.

Poor fit:
- untrusted CPU-bound code without instrumentation;
- hard real-time scheduling;
- workloads where a single token can hide arbitrarily expensive work.

### Uncertainty

Whether KNEEKURA needs operation-count budgets, elapsed-time budgets, weighted tokens, or a hybrid must be measured. The reusable knowledge is the **progress-sensitive cooperative charging contract**, not Tokio's specific constants.

### Distinction from prior harvests

This is not Cycle 22 CockroachDB elastic CPU token budgeting. That finding allocates spare CPU capacity among background work using measured global resource availability. Tokio's mechanism instead prevents **one cooperative task from monopolizing a shared executor during a single scheduling slice**.

It is also not Cycle 32 RocksDB backpressure. Backpressure throttles producers because downstream debt is accumulating; cooperative task budgeting yields locally even when no backlog exists.

---

## Finding 3 — Git pseudo-merge reachability bitmaps for grouped graph-query acceleration

### Provenance

- Repository: `git/git`
- Popularity at inspection: 63,107 GitHub stars
- Repository URL: https://github.com/git/git
- Revision: `fa7f9290efe2bd22dd736689597b474b93798e11`
- Primary path: `Documentation/gitpacking.adoc`
- Exact source URL: https://github.com/git/git/blob/fa7f9290efe2bd22dd736689597b474b93798e11/Documentation/gitpacking.adoc
- Related implementation path: `pack-bitmap.c`

### Technique

Git accelerates repeated reachability queries by materializing compressed reachability summaries rather than traversing the object graph from scratch for every starting point.

The pseudo-merge extension tackles a second-order scaling problem: when there are too many ref tips to store/use one bitmap per tip efficiently, Git groups multiple ref tips and stores a bitmap representing the **reachability closure of the group**. Queries that cover the group can inflate one compressed bitmap and OR it into the result instead of decompressing/combining many individual bitmaps or performing expensive fill-in traversal.

Git also distinguishes relatively "stable" and "unstable" ref tips by age. Older tips may be grouped more aggressively because they are heuristically less likely to move; newer tips use smaller groups. The documentation explicitly marks pseudo-merge bitmaps as **experimental**.

### Why it may be useful to KNEEKURA

KNEEKURA's static graph/evidence graph can face queries of the form:

- "what is reachable from this set of roots?"
- "which artifacts depend on any member of this component group?"
- "which evidence nodes are covered by these selected sources?"
- "what is the transitive closure of this stable package/module cluster?"

If the same root sets or stable groups are repeatedly queried, a compressed group reachability summary can turn repeated graph walking into bitmap/set operations.

A possible KNEEKURA abstraction:

```text
stable group G = {root1, root2, ...}
closureBitmap(G) = all nodes reachable from any root in G

query roots fully cover G:
  result |= closureBitmap(G)
otherwise:
  exact/fill-in traversal for uncovered roots
```

This could complement, not replace, exact graph semantics.

### Limitations / failure modes

- Git explicitly considers pseudo-merge bitmaps experimental; configuration and concepts can change.
- Precomputed reachability consumes storage and build time. It only pays off if queries repeat enough to amortize materialization cost.
- Group summaries become stale when their root membership or underlying graph changes. KNEEKURA would need exact invalidation tied to graph revision/content identity.
- Grouping by age is a Git-specific heuristic. "Old" does not necessarily imply stable in KNEEKURA's domains.
- Bitmaps work best when the universe has a stable dense identity/index. Sparse/churning node identities can make remapping expensive.
- Partial group matches still require fill-in traversal or exact fallback; the summary must never invent reachability outside its proven closure.

### Applicability

Good fit:
- large immutable or revisioned graphs;
- repeated reachability/dependency queries;
- stable root groups with high query reuse;
- graph engines that already maintain compact numeric node IDs.

Poor fit:
- tiny graphs;
- extremely volatile graph identity;
- one-shot queries where summary construction costs more than traversal;
- correctness models that cannot reliably invalidate stale summaries.

### Uncertainty

KNEEKURA needs benchmark evidence before choosing bitmap representation, grouping policy, or maintenance strategy. The strongest transferable idea is **precompute exact closure summaries for high-reuse root groups and fall back to exact traversal outside coverage**, not Git's specific pseudo-merge heuristics.

### Distinction from prior harvests

This is not Cycle 28 changed-path Bloom filtering. Bloom filters provide a probabilistic **negative prefilter** and still require exact verification for positives. Pseudo-merge reachability bitmaps store an exact closure over a defined group and can directly contribute set members to the answer.

It is also not Cycle 27 sparse-index summarization. Sparse-index avoids expanding cold hierarchical state; pseudo-merge bitmaps accelerate repeated **transitive graph reachability** across many roots.

---

## Cross-finding hypothesis — progress, fairness, and graph cost should be explicit control planes

**NON-CANONICAL SYNTHESIS — requires independent validation.**

The three findings suggest a possible general control structure for KNEEKURA long-running engines:

```text
Progress plane:
  explicit monotonic CHECKPOINT tokens allow safe stream resume even during quiet periods

Fairness plane:
  bounded cooperative budgets prevent one always-ready task from monopolizing an executor

Graph-cost plane:
  stable, exact group summaries amortize repeated expensive reachability work
```

Together these could make long-lived workers easier to resume, less prone to starvation, and cheaper to query without weakening correctness. They should remain independent mechanisms: a progress checkpoint must not imply scheduler fairness, and a reachability cache must not determine stream authority.

## Review / promotion requirements

Before any promotion beyond STAGING:

1. identify a concrete KNEEKURA subsystem and failure/performance mode for each candidate;
2. build a bounded prototype or trace-driven model;
3. define invalidation/crash-ordering semantics explicitly;
4. measure benefit against a simple baseline;
5. run adversarial review for skipped events, starvation, stale-summary acceptance, and authority confusion;
6. preserve an exact fallback path where the optimization can be bypassed.

Until those gates are satisfied, all three findings remain research candidates only.
