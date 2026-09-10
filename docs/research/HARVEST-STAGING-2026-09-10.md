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

---

# Cycle 11 append — 2026-09-10

Status: **STAGING / NON-CANONICAL**

This append is discovery material only. Star counts below were used to prioritize inspection, not as evidence of correctness. Cycle 01-10 topics and Draft PR summaries were checked first; the findings below were selected as non-duplicate technique families. No Knowledge Entity or validated/canonical claim is created here.

## C11-01 — Work-stealing DFS stack to reduce traversal working-set memory

**Repository:** `BurntSushi/ripgrep`

**Discovery metadata at capture:** 68,146 GitHub stars; repository metadata reports Unlicense.

**Pinned revision:** `3fce3b5bb0236da2df6d99672afb8a719642eca7`

**Evidence:**

- path: `crates/ignore/src/walk.rs`
- section: parallel walker `Worker` and its work-stealing `stack`
- source URL: `https://github.com/BurntSushi/ripgrep/blob/3fce3b5bb0236da2df6d99672afb8a719642eca7/crates/ignore/src/walk.rs`

### Observed technique

The parallel directory walker deliberately uses a **work-stealing stack** rather than a channel. The implementation comment states that the stack preserves depth-first traversal, which substantially reduces peak memory by keeping fewer file paths and fewer gitignore matchers resident at once. Parallelism is retained through work stealing rather than by abandoning locality and queueing a broad frontier.

### Why it may be useful

Large repository scans can consume surprising memory when breadth-first or producer-heavy traversal discovers a huge frontier faster than consumers process it. A depth-first local stack with stealing can preserve parallel work while constraining the active working set.

Possible KNEEKURA applications include repository crawling, recursive evidence collection, asset discovery, and Code Police scans where directory-local state is expensive and exact event ordering is not semantically significant.

### Limitations / applicability

- Depth-first traversal can change latency distribution: files in other branches may be discovered later than with breadth-first traversal.
- Work stealing adds synchronization and implementation complexity; on small trees a simple serial walk may be better.
- The memory advantage depends on directory topology and per-directory state. It must be benchmarked on KNEEKURA repositories rather than assumed.
- This is unsuitable where strict global traversal order is part of the contract.

**Confidence:** high that ripgrep intentionally uses this structure for working-set reduction; KNEEKURA benefit is unmeasured.

## C11-02 — Separate concurrency budgets for independent workload classes

**Repository:** `hashicorp/terraform`

**Discovery metadata at capture:** 49,631 GitHub stars. GitHub repository metadata reports license `NOASSERTION`; source handling should therefore remain locator/summary based unless independently authorized.

**Pinned revision:** `91d26c7ab817693a710a35639cf7995369d42986`

**Evidence:**

- path: `internal/terraform/eval_context.go`
- section: `EvalContext.PolicySemaphore()` contract
- source URL: `https://github.com/hashicorp/terraform/blob/91d26c7ab817693a710a35639cf7995369d42986/internal/terraform/eval_context.go`

### Observed technique

Terraform exposes a **policy-evaluation semaphore separate from the provider-operation semaphore**. The contract explicitly says the separation exists so policy evaluations do not consume provider parallelism slots.

The reusable idea is not the specific semaphore implementation, but **concurrency-domain isolation**: workloads with different latency, failure, or importance characteristics receive independent admission budgets instead of competing under one global limit.

### Why it may be useful

A single global worker cap can allow a slow auxiliary class to occupy every slot needed by a critical class. KNEEKURA could potentially separate budgets for, for example, interactive command handling, evidence acquisition, model inference, background indexing, or policy/audit work while still enforcing a higher parent machine ceiling separately.

### Limitations / applicability

- Too many independent pools can strand capacity and reduce utilization.
- Separate semaphores do not by themselves prevent total RAM/VRAM/CPU exhaustion; they should coexist with global resource ceilings where needed.
- Capacity ratios are workload-specific and can create starvation if misconfigured.
- Terraform's exact policy/provider split reflects Terraform's architecture and should not be copied literally.

**Confidence:** high for the isolation intent; the right KNEEKURA workload classes and budgets are unknown pending measurement.

## C11-03 — Generation-based live worker replacement with fail-safe reconfiguration

**Repository:** `nginx/nginx`

**Discovery metadata at capture:** 31,616 GitHub stars; BSD-2-Clause license.

**Pinned revision:** `df5269cc425f4cb1288fb8ca9f7e22166103feee`

**Evidence:**

- path: `src/os/unix/ngx_process_cycle.c`
- section: `ngx_master_process_cycle`, `ngx_reconfigure` branch
- source URL: `https://github.com/nginx/nginx/blob/df5269cc425f4cb1288fb8ca9f7e22166103feee/src/os/unix/ngx_process_cycle.c`

### Observed technique

On reconfiguration, the master first attempts to initialize a new cycle. If that initialization fails, it restores/continues with the prior cycle instead of destroying the working generation. If initialization succeeds, it starts the new worker generation, gives the new processes a short opportunity to start, and only then signals the old workers to shut down gracefully.

The reusable pattern is **prepare new generation → fail closed to old generation if preparation fails → activate new generation → drain old generation**, rather than mutating a live worker set in place.

### Why it may be useful

This can reduce interruption and partial-state failure when restarting long-lived components. Potential KNEEKURA applications include replacing local model workers, Minecraft observation hosts, browser/command bridges, plugin hosts, or other services where a new generation can be health-checked before the old generation is retired.

### Limitations / applicability

- NGINX's fixed short startup pause is implementation-specific; KNEEKURA should prefer an explicit readiness predicate where available rather than copying a time delay.
- Running old and new generations concurrently temporarily increases resource use and may be impossible for large GPU models.
- In-flight ownership, sockets/ports, file locks, and external side effects need explicit handoff semantics.
- Graceful draining does not guarantee zero-loss behavior unless the protocol itself supports transfer/retry of in-flight work.

**Confidence:** high for the NGINX process-generation pattern; direct applicability varies sharply by worker type and resource footprint.

## Cycle 11 synthesis (research hypothesis only)

The three findings point to three different places where system shape can control failure pressure without adding a large framework: use locality-preserving traversal to limit working set, isolate concurrency classes so auxiliary work cannot monopolize critical capacity, and replace live workers by generation rather than destructive in-place mutation. They are independent candidates and should be tested separately.

## Cycle 11 promotion status

`STAGING_ONLY`

No `VALIDATED` claim, canonical Knowledge Entity, canonical relation, implementation mandate, or automatic adoption decision was created by Cycle 11.