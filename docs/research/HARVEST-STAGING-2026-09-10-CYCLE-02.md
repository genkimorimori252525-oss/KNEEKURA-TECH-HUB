# OSS Harvest Staging — 2026-09-10 / Cycle 02

Status: **STAGING / NON-CANONICAL**

This document contains discovery-stage research notes only. Nothing here is `VALIDATED` knowledge. Promotion must go through the existing KNEEKURA TECH HUB evidence and human-review gates.

## Selection policy for this cycle

- Existing `HARVEST-STAGING-2026-09-10.md` was checked first to avoid duplicating the React lane, Kubernetes rate-limit/workqueue, and VS Code disposable-graph findings.
- GitHub popularity was used only to prioritize inspection. It is not treated as evidence of correctness or applicability.
- This cycle deliberately sampled different technical domains: kernel tracing/concurrency, incremental compilation/cache invalidation, and heavyweight local-model resource lifecycle.
- Source code/documentation is pinned to exact revisions and file blob identities.

---

## H-2026-09-10-005 — Swap a private reader page into a shared ring instead of copying records out

**Repository:** `torvalds/linux`

**Discovery metadata at capture:** 247,654 GitHub stars. Repository-level GitHub license field is `NOASSERTION`; the inspected documentation file itself declares `GPL-2.0 OR GFDL-1.2-no-invariants-only`.

**Pinned revision:** `50d05c7c76c96b90462f24debacca971d2e86713`

**Evidence:**

- path: `Documentation/trace/ring-buffer-design.rst`
- inspected region: approximately lines 15-210
- blob SHA: `c5d77fcbb5bcc8ddc6ae78192c66c5b51c8a8127`
- source URL: `https://github.com/torvalds/linux/blob/50d05c7c76c96b90462f24debacca971d2e86713/Documentation/trace/ring-buffer-design.rst`

### Observed technique

The Linux tracing ring-buffer design gives the reader a page that normally lives outside the shared ring. When the reader needs fresh data and its private page is empty, it swaps that page with the current head page. The formerly shared head page becomes reader-owned, while the old reader page is inserted back into the ring.

The same design explicitly separates overwrite mode from producer/consumer mode and relies on constrained writer nesting: a writer may be interrupted by another writer, but nested writers complete in stack order before the interrupted writer resumes.

### Why it may be useful

The broader transferable idea is **ownership transfer instead of element-by-element copying**. When producer and consumer can exchange ownership of coarse buffers/pages, the consumer can inspect a stable batch without keeping the producer locked for the whole read and without copying every record into a second temporary structure.

Potential KNEEKURA-adjacent applications include high-volume runtime evidence capture, render/telemetry snapshots, event tracing, and bounded diagnostic streams where data naturally arrives in batches.

### Limitations / applicability

- The Linux algorithm depends on strict concurrency assumptions; its exact lockless mechanics should not be transplanted to arbitrary multi-writer/multi-reader workloads.
- Page-sized ownership transfer is useful only when batching latency and memory overhead are acceptable.
- Overwrite mode and producer/consumer mode lose different data under pressure, so loss semantics must be chosen deliberately.
- KNEEKURA would need workload-specific benchmarks before adopting page/buffer swapping over simpler queues.

**Confidence:** high that the ownership-swap design is documented; KNEEKURA applicability is a research hypothesis.

---

## H-2026-09-10-006 — Reuse incremental state narrowly, but expand invalidation when dependency scope becomes global

**Repository:** `microsoft/TypeScript`

**Discovery metadata at capture:** 110,979 GitHub stars; Apache-2.0 license.

**Pinned revision:** `0b832e12235cc3db14a4be6501827c2f8a8a8569`

**Evidence:**

- path: `tsc/internal/execute/incremental/programtosnapshot.go`
- inspected region: approximately lines 120-250
- blob SHA: `27bfffb552b1ceaafaf5a36ba121912be741cc67`
- source URL: `https://github.com/microsoft/TypeScript/blob/0b832e12235cc3db14a4be6501827c2f8a8a8569/tsc/internal/execute/incremental/programtosnapshot.go`

### Observed technique

The incremental compiler copies reusable diagnostics/signatures for unchanged files instead of recomputing everything. But it deliberately widens invalidation when the old dependency assumptions are no longer safe.

Examples in the inspected code include:

- an unchanged file may reuse diagnostics and emit signatures;
- deletion of a file that affected global scope marks the remaining source set changed;
- loss of global-scope behavior similarly expands the change set;
- compiler-option changes are classified by whether they affect emit, and only the required emit kinds are marked pending when safe.

The principle is not simply "cache aggressively". It is **reuse only while the dependency boundary remains provable; fall back to broader recomputation when a change can escape the local boundary**.

### Why it may be useful

This maps well to systems that cache expensive analyses, rendered artifacts, repository scans, dependency graphs, or AI-derived intermediate results. A KNEEKURA component could retain narrow caches for ordinary local changes while explicitly defining "global invalidators" such as schema changes, policy-version changes, parser-version changes, environment changes, or canonical identity changes.

That can provide most of the performance benefit of incremental execution without pretending every change is safely local.

### Limitations / applicability

- Correctness depends on accurately classifying dependency scope; a missed global invalidator can create stale-but-plausible results.
- Broad invalidation can become expensive if global events are common.
- TypeScript's exact file/signature rules are compiler-specific and should not become a generic KNEEKURA invalidation API without concrete need.
- The inspected repository is undergoing implementation evolution; this exact Go path/revision should be treated as the pinned evidence, not an eternal TypeScript architecture contract.

**Confidence:** high for the observed invalidation strategy; medium for direct transfer until KNEEKURA cache boundaries are enumerated.

---

## H-2026-09-10-007 — Manage heavyweight model processes with active-use reference counts plus idle keep-alive expiration

**Repository:** `ollama/ollama`

**Discovery metadata at capture:** 180,540 GitHub stars; MIT license.

**Pinned revision:** `159b1c3331a176abf7e8484e44d517db726707db`

**Evidence:**

- path: `server/sched.go`
- inspected regions: approximately lines 30-220 and 220-500
- blob SHA: `c1a95c3399f6bcdaee22254a14fd44ae0900b26e`
- source URL: `https://github.com/ollama/ollama/blob/159b1c3331a176abf7e8484e44d517db726707db/server/sched.go`

### Observed technique

Ollama separates "loaded" from "actively in use" for expensive model runners. A runner has a reference count guarded by a mutex. Handing a loaded runner to a request increments the reference count and cancels any pending expiration timer. When the request context finishes, the scheduler decrements the count.

If the count reaches zero, the runner is either unloaded immediately when its session duration is zero, or kept warm with an expiration timer. A later request can reuse the still-loaded runner and cancel that idle timer. Expiration events re-check the reference count before unloading, so a resource that became active again is not torn down merely because an old timer/event fired.

The scheduler also distinguishes a stable logical model key from process identity; during unload it checks the process ID so a stale expiration event for an older process does not delete a newer loaded runner occupying the same model key.

### Why it may be useful

This is a useful lifecycle pattern for **expensive, reusable local resources** whose startup cost is high but which must eventually release scarce capacity. Potential KNEEKURA uses include local LLM/TTS processes, Minecraft observation hosts, browser workers, GPU renderers, heavyweight analyzers, and other local execution workers.

The transferable structure is:

1. logical resource identity;
2. active-use reference count;
3. configurable idle grace period;
4. timer cancellation/reset on reuse;
5. stale-event identity check before destructive unload.

This can reduce cold-start churn without allowing idle workers to remain resident forever.

### Limitations / applicability

- Reference-count correctness depends on every acquisition having a matching completion path; leaked references prevent cleanup.
- Timers and asynchronous expiration create race surfaces and need identity/version checks, as Ollama itself demonstrates.
- Keep-alive duration should reflect startup cost and memory/VRAM pressure rather than be copied from another system.
- Distributed resources generally need leases/heartbeats rather than in-process reference counts alone.

**Confidence:** high for the observed lifecycle mechanism; parameter choices are workload-specific.

---

## Cross-finding synthesis (research hypothesis only)

These findings share one useful theme without implying they should become one framework: **optimize the common path while keeping a conservative escape hatch when ownership or validity becomes uncertain.**

- Linux transfers whole-buffer ownership to avoid unnecessary copying, but only under explicit reader/writer constraints.
- TypeScript reuses unchanged analysis state, but deliberately broadens invalidation when a change can affect global scope.
- Ollama keeps expensive model processes warm, but re-checks active ownership and process identity before destructive cleanup.

For KNEEKURA, the possible design lesson is to make optimization boundaries explicit and pair every fast path with a fail-safe path that preserves correctness when its assumptions no longer hold.

## Promotion status

`STAGING_ONLY`

No Knowledge Entity, Claim maturity transition, canonical relation, recommendation winner, or automatic adoption decision was created by this harvest cycle.
