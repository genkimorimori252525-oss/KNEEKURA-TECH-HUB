# KNEEKURA TECH HUB — Harvest Staging Cycle 32

> Status: **STAGING / NON-CANONICAL**
>
> This document is a research holding area only. Nothing here is VALIDATED, canonical, approved for production, or authorized for automatic implementation. Promotion must follow the existing KNEEKURA governance and discovery-to-knowledge rules.

Date: 2026-09-11

## Harvest scope and duplicate guard

This cycle searched for reusable engineering knowledge across highly starred GitHub repositories, using popularity only to prioritize inspection order. Evidence quality, applicability, and non-duplication remain more important than star count.

Before recording the findings below:

- the open KNEEKURA-TECH-HUB harvest PR inventory was checked; the latest staged cycle found was Cycle 31 / PR #67;
- known Cycle 22–31 topics were excluded from selection;
- repository code search on `main` found no matches for `seqcount seqlock`, `LFU decay`, or `write stall backpressure`;
- an open-PR search for `seqlock`, `seqcount`, `LFU`, `write stall`, and `backpressure` returned no matches.

This is a best-effort duplicate check. Search absence is not proof that no semantically equivalent idea exists under different terminology.

---

## Finding 1 — Sequence-number validated lockless snapshots

### Provenance

- Repository: `torvalds/linux`
- Repository URL: https://github.com/torvalds/linux
- Stars observed at harvest: **248,212**
- Revision: `08df884136f1c1197bab2a27814404fd329d9aac`
- Commit URL: https://github.com/torvalds/linux/commit/08df884136f1c1197bab2a27814404fd329d9aac
- Primary path: `Documentation/locking/seqlock.rst`
- Exact source URL: https://github.com/torvalds/linux/blob/08df884136f1c1197bab2a27814404fd329d9aac/Documentation/locking/seqlock.rst
- Relevant sections: `Introduction`, `Sequence counters (seqcount_t)`, `Sequential locks (seqlock_t)`

### Technique

Linux sequence counters let readers take a logically consistent snapshot without acquiring a conventional read lock. A reader:

1. reads a sequence number;
2. copies the protected data;
3. reads/checks the sequence number again;
4. accepts the snapshot only if the sequence stayed valid and unchanged; otherwise it retries.

Writers mark the sequence odd while an update is in progress and even after completion. The documentation also describes a conditional mode in which a reader first attempts the lockless path and can switch to a locking read after retry pressure becomes excessive.

The useful abstraction is broader than the Linux primitive itself: **optimistic snapshot + version validation + bounded/fallback retry**.

### Why it may be useful for KNEEKURA

Candidate uses include small, read-mostly state where readers need a mutually consistent group of values but writes are infrequent, for example:

- runtime health/status snapshots;
- read-mostly scheduler metrics;
- immutable-generation metadata pointers plus separately safe payloads;
- Viewer/Bridge status structures where locking every poll would be disproportionately expensive.

A high-level KNEEKURA variant could expose a monotonically increasing generation around an update, copy plain-value state, and retry if generation changed. It does **not** require copying Linux's low-level memory-ordering implementation.

### Limitations / safety boundary

Linux explicitly documents important limits:

- raw sequence counters do not serialize multiple writers; writer serialization must exist separately;
- writers must not be left preempted/interrupted while the sequence is odd, or readers can spin for a long time;
- the basic technique cannot safely protect data containing pointers that a writer may invalidate while a reader follows them;
- high write rates can cause reader retry starvation; Linux therefore documents a locking fallback variant.

For KNEEKURA, this should therefore be considered only for small snapshot-like data with clearly defined lifetime rules. It is not a generic replacement for mutexes, RCU, transactions, or ownership fencing.

### Applicability hypothesis

Potentially useful for high-frequency status reads and metrics snapshots. Less suitable for mutable object graphs, resource ownership changes, or state carrying externally visible side effects.

### Uncertainty

The performance benefit in KNEEKURA is unmeasured. A normal mutex or immutable snapshot swap may be simpler and fast enough. Promotion should require profiling plus a race-focused test plan.

### Duplicate distinction

- Different from Cycle 27 RCU: RCU primarily delays reclamation until old readers leave; seqcount validates that a copied snapshot did not overlap a write.
- Different from Cycle 25 Loom: Loom explores interleavings in tests; seqcount is a runtime consistency mechanism.
- Different from Cycle 26 lockdep: lockdep detects problematic lock-order graphs; seqcount may avoid a reader lock entirely but introduces retry semantics.

---

## Finding 2 — Tiny probabilistic LFU counters with explicit time decay

### Provenance

- Repository: `redis/redis`
- Repository URL: https://github.com/redis/redis
- Stars observed at harvest: **76,322**
- Default branch observed: `unstable`
- Revision: `669b2a1316f5b35ecf964281b77c054ff28dc934`
- Commit URL: https://github.com/redis/redis/commit/669b2a1316f5b35ecf964281b77c054ff28dc934
- Primary path: `src/evict.c`
- Exact source URL: https://github.com/redis/redis/blob/669b2a1316f5b35ecf964281b77c054ff28dc934/src/evict.c
- Relevant functions: `LFULogIncr`, `LFUDecrAndReturn`
- Supporting path: `src/db.c`
- Supporting function: `updateLFU`

### Technique

Redis approximates access frequency with a compact counter instead of incrementing an unbounded exact integer on every hit.

`LFULogIncr` makes an increment progressively less likely as the counter rises, saturating at 255. This logarithmic/probabilistic update lets a tiny counter distinguish a useful range of access frequencies.

`LFUDecrAndReturn` separately applies time decay: elapsed decay periods lower the stored frequency before it is used for eviction decisions. `updateLFU` composes decay followed by probabilistic increment on an actual access.

The reusable idea is: **approximate hotness in very little state, and decay historical popularity so old winners do not remain permanently privileged**.

### Why it may be useful for KNEEKURA

Candidate uses include bounded caches or retention rankings where exact hit counts are unnecessary:

- parsed-source/index fragment caches;
- rendered/intermediate artifact caches;
- repository search result caches;
- local-model auxiliary resource caches;
- frequently reused evidence/navigation summaries.

Compared with an exact ever-increasing counter, decay allows recently useful items to overtake formerly hot but now-unused items. Compared with keeping detailed access histories, the metadata cost stays tiny.

### Limitations / safety boundary

- The count is approximate and randomized; two equally used objects need not receive identical counters.
- The 8-bit counter intentionally loses information at high frequencies.
- Decay parameters and the logarithmic factor are workload-specific policy, not universal constants.
- It is appropriate for ranking/eviction heuristics, not governance, billing, evidence counts, security decisions, or anything requiring exact accounting.
- A frequency-only policy can retain frequently accessed large objects even when their cost is disproportionate; size/cost may need to be considered separately.

### Applicability hypothesis

Useful when KNEEKURA has many cacheable objects, hit-rate matters, and per-object metadata must stay cheap. It could complement—not replace—hard retention rules for canonical evidence or workflow-critical artifacts.

### Uncertainty

No evidence yet shows that KNEEKURA's cache populations are large enough for probabilistic LFU metadata to outperform simpler LRU/TTL policies. Before promotion, compare hit rate, metadata overhead, churn, and worst-case retention under representative traces.

### Duplicate distinction

- Different from Cycle 28 Git Bloom filters: Bloom filters answer approximate membership/negative filtering; Redis LFU approximates relative reuse frequency.
- Different from Cycle 29 lease-rooted GC: leases express logical liveness/retention authority; LFU is only a heuristic for disposable cache eviction.
- Different from Cycle 22 Turborepo cache identity: cache identity decides whether an artifact is reusable; LFU decides which reusable cache entries are worth retaining.

---

## Finding 3 — Multi-stage backpressure from pressure signal → acceleration → delay → stop

### Provenance

- Repository: `facebook/rocksdb`
- Repository URL: https://github.com/facebook/rocksdb
- Stars observed at harvest: **32,080**
- Revision: `a844cbf5b7bfd1c3289652c1fa0e4bb85ded02bf`
- Commit URL: https://github.com/facebook/rocksdb/commit/a844cbf5b7bfd1c3289652c1fa0e4bb85ded02bf
- Primary path: `docs/components/write_flow/07_flow_control.md`
- Exact source URL: https://github.com/facebook/rocksdb/blob/a844cbf5b7bfd1c3289652c1fa0e4bb85ded02bf/docs/components/write_flow/07_flow_control.md
- Referenced implementation paths: `db/write_controller.h`, `db/write_controller.cc`, `db/column_family.cc`, `db/db_impl/db_impl_write.cc`, `include/rocksdb/write_buffer_manager.h`
- Relevant sections: `Write Stall Conditions`, `WriteController`, `Rate Limiting Algorithm`, `WriteBufferManager`, `Monitoring Write Stalls`

### Technique

RocksDB does not wait for overload to become catastrophic and then abruptly fail. It derives pressure from concrete backlog signals such as:

- immutable memtable count;
- Level-0 file count;
- pending compaction bytes;
- shared memtable memory usage.

It then responds in stages:

1. **Compaction pressure:** increase background compaction parallelism before writes are stalled.
2. **Delay:** when debt grows further, rate-limit incoming writes using a credit-based limiter.
3. **Stop:** at hard thresholds, block writes until background work catches up.

The documented rate is also adjusted according to whether compaction debt is worsening or improving, and stall duration/counts are exposed as metrics.

The reusable architecture is: **measure downstream debt, attempt recovery capacity first, progressively throttle producers, and reserve hard stop for the unsafe region**.

### Why it may be useful for KNEEKURA

KNEEKURA has several producer/consumer boundaries where unchecked input can create unbounded debt:

- GitHub discovery producing more repositories/evidence than parsers or reviewers can ingest;
- file watchers producing refresh jobs faster than indexing can finish;
- runtime observation producing evidence faster than persistence/compaction can absorb it;
- local execution queues producing GPU/CPU work faster than workers can retire it;
- artifact generation producing temporary data faster than cleanup/GC can reclaim it.

A KNEEKURA adaptation could define explicit pressure metrics and three states such as `NORMAL → THROTTLED → STOPPED`, optionally with an earlier `RECOVERY_BOOST` state when safe extra capacity exists.

### Limitations / safety boundary

- Thresholds are workload-specific and RocksDB's concrete values/ratios must not be copied blindly.
- More background parallelism can worsen CPU, RAM, disk, or thermal contention; acceleration must itself obey resource budgets.
- Backpressure can increase user-visible latency and may produce priority inversion if all producers are treated identically.
- Hard stop needs cancellation/shutdown escape paths so blocked work cannot deadlock system teardown.
- Debt signals must correspond to the true bottleneck; throttling on the wrong metric can reduce throughput without improving recovery.

### Applicability hypothesis

Strong candidate for bounded work pipelines where downstream service rate can temporarily fall below arrival rate. Especially relevant to long-running Runner/Bridge/indexing workflows.

### Uncertainty

KNEEKURA has not yet established which debt metric best predicts instability for each pipeline. Promotion should require telemetry first, then offline replay or controlled overload tests to choose thresholds and hysteresis.

### Duplicate distinction

- Different from Cycle 22 CockroachDB elastic CPU budgeting: that finding tunes background CPU share from scheduler latency; RocksDB regulates producer admission from accumulated downstream debt.
- Different from Cycle 30 Moby restart backoff: restart backoff spaces retries after failure; RocksDB backpressure acts before/while a healthy pipeline approaches saturation.
- Different from Cycle 26 workqueue coalescing: coalescing reduces duplicate work; backpressure bounds arrival rate when remaining work is still genuinely necessary.

---

## Cross-finding synthesis — candidate only

A possible KNEEKURA pattern suggested by this cycle is a three-layer control loop:

1. **Cheap observation:** maintain read-mostly pressure/status snapshots with generation validation where appropriate.
2. **Cheap ranking:** when disposable cached state exceeds budget, approximate current reuse value with decaying hotness rather than permanent historical counts.
3. **Pressure response:** when non-disposable work debt grows, increase safe recovery capacity first, then throttle producers, then stop admission at a hard boundary.

This synthesis is an inference made during harvesting, not a property asserted by the source projects and not a validated KNEEKURA architecture.

## Governance disposition

All three findings remain **STAGING / NON-CANONICAL**.

No finding in this cycle has been:

- promoted to VALIDATED;
- written into canonical knowledge;
- implemented in a KNEEKURA production component;
- granted authority to mutate runtime policy;
- merged to `main` by this harvesting cycle.

Recommended next governance step, if any finding is selected later: create a focused evaluation item with representative workload evidence, measurable acceptance criteria, and explicit rejection conditions before promotion.
