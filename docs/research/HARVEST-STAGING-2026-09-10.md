# OSS Harvest Staging — 2026-09-10

Status: **STAGING / NON-CANONICAL**

This document contains discovery-stage research notes only. Nothing here is `VALIDATED` knowledge. Promotion must go through the existing KNEEKURA TECH HUB evidence and human-review gates.

## Selection policy for this cycle

- GitHub repositories with high star counts were inspected first.
- Popularity was used only as a discovery-priority signal, not as evidence that a technique is correct or generally applicable.
- Existing Hub content was searched for the inspected repository names and technique keywords; no matching prior harvest entry was found.
- All source code below is pinned to exact repository revisions and file blob identities.

---

## H-2026-09-10-001 — Bitset priority lanes for low-overhead scheduler state

**Repository:** `react/react`

**Discovery metadata at capture:** ~249,643 GitHub stars; MIT license.

**Pinned revision:** `a58f939795502a579c02d584600df5369d864c3b`

**Evidence:**

- path: `packages/react-reconciler/src/ReactFiberLane.js`
- inspected region: approximately lines 30-220
- blob SHA: `19c873e70fc69b9e9efd8741a46340accf13ff4d`
- source URL: `https://github.com/react/react/blob/a58f939795502a579c02d584600df5369d864c3b/packages/react-reconciler/src/ReactFiberLane.js`

### Observed technique

React represents scheduler priority classes as individual bits in a fixed-width integer. Related priorities are combined into masks such as `SyncUpdateLanes`, `TransitionLanes`, `RetryLanes`, `NonIdleLanes`, and `UpdateLanes`. Selection can therefore use bitwise intersection and highest-set/lowest-set-bit style operations rather than repeatedly walking object collections.

The same representation also preserves categories such as synchronous, input-continuous, default, transition, retry, idle, offscreen, deferred, and hydration work without forcing them into one mutable queue object.

### Why it may be useful

This pattern is attractive when a system has a **small, bounded set of priority classes** and frequently needs to answer questions like "does any urgent work exist?", "which class wins?", or "which classes belong to this group?". It can reduce allocation and make set operations extremely cheap.

Possible KNEEKURA-adjacent applications include compact scheduling state for local workers, render/update priorities, or bounded orchestration flags where the category set is intentionally fixed.

### Limitations / applicability

- Best for a small fixed universe of states; it becomes awkward when priorities are dynamic or user-defined.
- Bit assignments become a compatibility contract and require disciplined synchronization with diagnostics/tooling.
- Compactness can reduce readability if semantic helper names are not maintained.
- This observation does **not** establish that bitsets outperform ordinary queues for KNEEKURA workloads; benchmarking would be required before adoption.

**Confidence:** high that the representation is present; applicability to KNEEKURA remains a hypothesis.

---

## H-2026-09-10-002 — Compose per-item exponential backoff with a global token bucket

**Repository:** `kubernetes/kubernetes`

**Discovery metadata at capture:** ~126,874 GitHub stars; Apache-2.0 license.

**Pinned revision:** `b0e6417568f530e79579c5bcd6bbeac799a47669`

**Evidence:**

- path: `staging/src/k8s.io/client-go/util/workqueue/default_rate_limiters.go`
- inspected region: approximately lines 35-180
- blob SHA: `1f9567881c7614ac02349f053699984846b54608`
- source URL: `https://github.com/kubernetes/kubernetes/blob/b0e6417568f530e79579c5bcd6bbeac799a47669/staging/src/k8s.io/client-go/util/workqueue/default_rate_limiters.go`

### Observed technique

The default controller rate limiter combines two independent controls using a max/composition policy:

1. **Per-item exponential failure delay** (`baseDelay * 2^failures`, capped by a maximum delay).
2. **Overall token-bucket rate limiting** for aggregate retry throughput.

The per-item limiter also tracks failure counts and provides an explicit `Forget(item)` operation to clear retry history after recovery.

### Why it may be useful

The two controls solve different failure modes. Per-item backoff prevents one persistently failing key from hot-looping, while the global bucket prevents a large population of failing keys from creating a retry storm.

This is especially relevant to autonomous workers, repository crawlers, API polling, external-service reconciliation, and Runner orchestration. A KNEEKURA worker fleet could potentially use this structure to isolate noisy failures without allowing aggregate retry traffic to explode.

### Limitations / applicability

- Backoff parameters are workload-specific; Kubernetes defaults should not be copied blindly.
- Exponential backoff alone can synchronize clients; jitter may be required in distributed deployments depending on the surrounding implementation.
- Failure state consumes memory until forgotten; lifecycle discipline matters for unbounded key spaces.
- A global bucket can delay healthy retries during broad incidents, which may or may not be desirable.

**Confidence:** high for the mechanism; parameter transferability is low without measurement.

---

## H-2026-09-10-003 — Dirty/processing dual-set queue prevents concurrent duplicate work without losing updates

**Repository:** `kubernetes/kubernetes`

**Pinned revision:** `b0e6417568f530e79579c5bcd6bbeac799a47669`

**Evidence:**

- path: `staging/src/k8s.io/client-go/util/workqueue/queue.go`
- inspected region: approximately lines 170-310
- blob SHA: `9bffddd634c1a7444a849011c80b528f6af30472`
- source URL: `https://github.com/kubernetes/kubernetes/blob/b0e6417568f530e79579c5bcd6bbeac799a47669/staging/src/k8s.io/client-go/util/workqueue/queue.go`

### Observed technique

The queue separates two concepts:

- `dirty`: items that need processing.
- `processing`: items currently being processed.

When an item is added while already processing, it is marked dirty but not queued a second time concurrently. `Get()` moves the key into `processing` and clears its dirty mark. `Done()` removes the processing mark and checks whether the key became dirty again during execution; if so, it is queued exactly for another pass.

This gives a useful reconciliation invariant: **coalesce duplicate notifications while a key is waiting, never process the same key concurrently, but do not lose a change that arrives while the key is being processed.**

### Why it may be useful

This is a strong pattern for systems whose work is keyed by repository, entity, file, task, or resource identity. It can simplify repeated event handling compared with spawning a job per event.

Potential KNEEKURA uses include repository harvest queues, Code Police repository scans, durable project reconciliation, ingestion pipelines, and any subsystem where multiple triggers can target the same logical object.

### Limitations / applicability

- It intentionally coalesces repeated notifications, so it is unsuitable when every individual event must be processed exactly once.
- Correctness assumes the worker's processing step reconstructs or reads sufficiently current state rather than depending solely on the dropped intermediate events.
- Shutdown and retry semantics must remain explicit; this pattern is not a substitute for durable persistence if process loss must survive restarts.

**Confidence:** high for the queue invariant; adoption depends on event semantics.

---

## H-2026-09-10-004 — Treat resource cleanup as a tracked object graph and report root leaks

**Repository:** `microsoft/vscode`

**Discovery metadata at capture:** ~191,521 GitHub stars; MIT license.

**Pinned revision:** `a0a429cd4ac624c0add568597f00b052c225ae56`

**Evidence:**

- path: `src/vs/base/common/lifecycle.ts`
- inspected region: approximately lines 120-360
- blob SHA: `a75cbb1cce3099e07bff3cc9c751d634ae30dfdd`
- source URL: `https://github.com/microsoft/vscode/blob/a0a429cd4ac624c0add568597f00b052c225ae56/src/vs/base/common/lifecycle.ts`

### Observed technique

VS Code's disposable infrastructure does more than define `dispose()`. Its optional tracker records parent/child ownership between disposable resources, identifies still-living objects, removes leaks that are merely children of another leaking root, and groups/report stack-trace prefixes to make common leak origins visible.

The file also centralizes batch disposal and deliberately aggregates multiple disposal failures rather than stopping cleanup after the first thrown exception.

### Why it may be useful

For long-running UI, plugin, watcher, process, socket, or worker systems, leaks often arise from **ownership ambiguity** rather than raw allocation. Tracking the ownership graph can make diagnostics substantially more actionable than a flat list of undisposed resources.

This may be particularly useful in KNEEKURA components that repeatedly create sessions, browser/worker bridges, filesystem watchers, model processes, or Minecraft-side observation resources. A debug-only ownership tracker could reveal which top-level session failed to release descendants.

### Limitations / applicability

- Capturing creation stack traces and ownership links adds debug overhead and should normally be gated or sampled.
- Parent graphs must avoid cycles or handle them explicitly.
- A disposable abstraction only catches resources that participate in the lifecycle contract; unmanaged native/external resources can still leak.
- Root-cause grouping is diagnostic evidence, not proof that the earliest/root object is itself the bug.

**Confidence:** high for the diagnostic structure; KNEEKURA integration remains untested.

---

## Cross-finding synthesis (research hypothesis only)

These four findings suggest a potentially reusable reliability toolkit without requiring a shared framework:

- **React lane bitsets:** cheap representation of a bounded priority universe.
- **Kubernetes dual rate limiting:** control both pathological keys and aggregate retry pressure.
- **Kubernetes dirty/processing queue:** coalesce keyed work without losing mid-flight invalidation.
- **VS Code disposable ownership graph:** make lifetime failures explainable instead of merely observable.

A future human review could test these independently against actual KNEEKURA pressure points. They should not be bundled into a new abstraction merely because they were discovered together.

## Promotion status

`STAGING_ONLY`

No Knowledge Entity, Claim maturity transition, canonical relation, recommendation winner, or automatic adoption decision was created by this harvest cycle.
