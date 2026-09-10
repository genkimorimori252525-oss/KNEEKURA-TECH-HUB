# OSS Harvest Staging — 2026-09-10 / Cycle 04

Status: **STAGING / NON-CANONICAL**

This document contains discovery-stage research notes only. Nothing here is `VALIDATED` knowledge. Promotion must go through the existing KNEEKURA TECH HUB evidence and human-review gates.

## Selection policy for this cycle

- Existing Cycle 01–03 staging notes were checked first to avoid duplicating React bitset lanes, Kubernetes rate limiting/workqueue, VS Code disposable ownership, Linux tracing ring pages, TypeScript invalidation, Ollama keep-alive, TensorFlow cancellation, Node.js async causality, and PyTorch flight-recorder findings.
- GitHub popularity was used only as an inspection-priority signal, never as proof of correctness.
- This cycle sampled three different operational concerns: bounded data-structure migration, allocation reuse under GC pressure, and diagnosable concurrent file locking.
- All implementation evidence is pinned to exact revisions and file blob identities.

---

## H-2026-09-10-011 — Incrementally migrate a resized hash table and explicitly bound empty-bucket scan work

**Repository:** `redis/redis`

**Discovery metadata at capture:** 76,296 GitHub stars. GitHub repository license metadata is `NOASSERTION` / Other at capture, so license/content-handling remains separately review-required if promoted.

**Pinned revision:** `21ce96878529bf8b31298ec417407c578c1e6278`

**Evidence:**

- path: `src/dict.c`
- inspected region: approximately lines 260–420
- blob SHA: `67a7c80b2032a02021934f207225f2e7d731fb4d`
- source URL: `https://github.com/redis/redis/blob/21ce96878529bf8b31298ec417407c578c1e6278/src/dict.c`

### Observed technique

Redis does not require a normal hash-table resize to move every key in one large blocking operation. It prepares a second table, records a `rehashidx`, and incrementally moves buckets from the old table into the new table. Both tables coexist until the old table is empty; only then is the new table promoted into the primary slot.

A subtle but important safeguard is inside `dictRehash(d, n)`: one requested rehash step means moving up to a bounded number of buckets, but sparse tables can contain long runs of empty buckets. Redis therefore also caps empty-bucket visits at `n * 10`; the function is explicitly designed so sparse-table scanning cannot turn a nominally small maintenance step into unbounded blocking work.

### Why it may be useful

The transferable idea is **split expensive structure migration into resumable bounded units, and bound not only useful work but also the search/scan needed to find that work**.

Potential KNEEKURA applications include:

- rebuilding large in-memory indexes or lookup maps;
- migrating caches after schema/key-layout changes;
- refreshing large repository/entity indexes without one long pause;
- background compaction where sparse/empty regions would otherwise make per-step cost unpredictable.

A particularly useful lesson is that `N items per tick` is not a sufficient latency bound if locating those N items can itself scan an unbounded region.

### Limitations / applicability

- During migration, reads/writes must understand both old and new structures; this increases transient complexity.
- The exact two-table algorithm is hash-table-specific and should not become a generic migration framework without a concrete KNEEKURA pressure point.
- Bounded per-step work trades peak pause time for longer total migration duration and temporary memory overhead.
- Correctness under concurrent access depends on the surrounding synchronization model; Redis's assumptions should not be transplanted blindly.

**Confidence:** high for the observed incremental/bounded rehash mechanism; direct KNEEKURA applicability remains a hypothesis.

---

## H-2026-09-10-012 — Shard reusable objects by execution context, then age them through a one-GC-cycle victim cache

**Repository:** `golang/go`

**Discovery metadata at capture:** 137,994 GitHub stars; BSD-3-Clause license metadata.

**Pinned revision:** `e51216de8e26247ee0f3d2cfa576233b0d29f542`

**Evidence:**

- path: `src/sync/pool.go`
- inspected region: approximately lines 45–330
- blob SHA: `178dc8b019952fc16be2690c3d6e165e3af7a910`
- source URL: `https://github.com/golang/go/blob/e51216de8e26247ee0f3d2cfa576233b0d29f542/src/sync/pool.go`

### Observed technique

Go's `sync.Pool` keeps reusable temporary objects in per-P local shards. Each local shard has a private fast slot plus a shared chain; a caller first checks its local/private state and can later steal from other shards. This reduces pressure on one global synchronized pool and favors temporal locality.

The more unusual part is GC integration. At the beginning of a GC, current primary caches are moved into `victim` caches while the prior victim generation is dropped. On lookup, primary caches are preferred and the victim cache is consulted only afterward. The result is a deliberately weak, GC-cooperative reuse policy: cached objects can survive one collection cycle as fallback reuse candidates, but the pool does not promise permanent retention.

The API contract reinforces this by explicitly allowing `Get` to ignore pooled values and behave as though the pool were empty.

### Why it may be useful

The transferable design is **treat reuse caches as expendable performance hints, not ownership stores**, while sharding the common path to avoid unnecessary contention.

Potential KNEEKURA-adjacent uses include temporary byte buffers, parser scratch space, serialization buffers, image/render scratch allocations, or short-lived analysis objects where reconstruction is cheap and memory pressure should be allowed to win.

The victim-generation idea is also interesting as a middle ground between `drop everything immediately` and `retain indefinitely`: recently idle resources get one extra reuse opportunity, then age out naturally.

### Limitations / applicability

- This pattern is unsuitable for resources whose presence is semantically required; pooled objects may disappear at any time.
- Resource types with external handles, explicit close/dispose requirements, or large scarce GPU/OS allocations need stronger lifecycle management than `sync.Pool` semantics.
- Per-execution-context sharding depends on the runtime scheduler model; KNEEKURA should copy the contention-avoidance principle, not Go's P-specific machinery.
- Reuse can retain more memory than expected during bursts, so measurement is still required.

**Confidence:** high for the observed sharding/victim-cache lifecycle; applicability is strongest for cheap-to-recreate temporary allocations.

---

## H-2026-09-10-013 — Make lock contention bounded, jittered, and diagnosable with owner-PID sidecar evidence

**Repository:** `git/git`

**Discovery metadata at capture:** 63,097 GitHub stars. GitHub repository license metadata is `NOASSERTION`; promotion must keep license/content-handling review separate.

**Pinned revision:** `b8242b093d9e941a34460d715e3ce616a34ac3fe`

**Evidence:**

- path: `lockfile.c`
- inspected regions: approximately lines 1–330
- blob SHA: `100f60377174efee3493ef2a392b7193ea75ea55`
- source URL: `https://github.com/git/git/blob/b8242b093d9e941a34460d715e3ce616a34ac3fe/lockfile.c`

### Observed technique

Git's lock-file path uses exclusive lock creation and distinguishes `lock exists` from unrelated I/O failures. When retrying a held lock, it does not spin continuously: the implementation uses increasing quadratic backoff with randomized wait time around each backoff interval (roughly 75%–125%) and a cap on the multiplier. Timeout modes explicitly support one-shot, bounded-time, or indefinite retry behavior.

The same file optionally creates a small PID sidecar for a lock. When lock acquisition fails, Git can read that PID, test whether the process still appears to exist, and report whether the lock appears actively held or stale. The diagnostic text still warns that PID reuse prevents this from being absolute proof.

### Why it may be useful

The transferable pattern is **separate contention control from contention diagnosis**:

1. exclusive acquisition prevents conflicting writers;
2. bounded/jittered retry avoids hot spinning and reduces synchronized retry collisions;
3. explicit timeout policy prevents accidental infinite waits;
4. lightweight owner evidence makes stale-lock incidents explainable rather than leaving only `resource busy`.

This maps well to KNEEKURA local resources such as workspace leases, one-writer state files, Runner request/status files, local materialization caches, model-process ownership markers, or any filesystem-mediated coordination point.

The sidecar evidence idea is especially useful when a local PC wakes from sleep or a process crashes and a lock artifact survives: diagnostics can distinguish `probably live owner`, `probably stale owner`, and `unknown`, rather than automatically deleting the lock.

### Limitations / applicability

- PID liveness is advisory evidence only; PIDs can be reused and containers/namespaces complicate interpretation.
- File locking semantics differ across filesystems and operating systems; correctness must match the actual Windows/Linux environment used by KNEEKURA.
- Randomized backoff reduces collisions but does not provide fairness.
- An indefinite retry option should not become the default for autonomous workers unless there is a separate watchdog/lease policy.

**Confidence:** high for the observed retry and PID-sidecar diagnostics; direct adoption should be tested against one existing KNEEKURA lock/lease path before implementation.

---

## Cross-finding synthesis (research hypothesis only)

The three findings share a useful operational principle: **make expensive or contended maintenance degrade gradually instead of turning into a long opaque pause.**

- Redis bounds each migration slice and even caps empty-space scanning.
- Go makes temporary reuse opportunistic and allows GC pressure to reclaim cached objects rather than turning the cache into ownership.
- Git backs away from contested locks, bounds waiting policy, and preserves enough owner evidence to diagnose stale contention.

For KNEEKURA, this suggests a possible review lens rather than a new framework: whenever a background operation can become large or contested, ask whether its work is bounded, whether retained optimization state is expendable, and whether blocked ownership is diagnosable.

These are independent research candidates. They should not be bundled into production architecture without a reproduced pressure point.

## Promotion status

`STAGING_ONLY`

No Knowledge Entity, Claim maturity transition, canonical relation, recommendation winner, or automatic adoption decision was created by this harvest cycle.
