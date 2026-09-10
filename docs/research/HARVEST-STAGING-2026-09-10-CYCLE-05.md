# HARVEST STAGING — 2026-09-10 — CYCLE 05

> **STAGING / NON-CANONICAL**
>
> This document records research candidates only. Repository popularity is used only to prioritize inspection and is not evidence that a technique is correct, universally applicable, or suitable for KNEEKURA. Nothing here is a VALIDATED Claim. Normal human review, provenance, applicability, and governance rules still apply before promotion.

## Selection policy

This cycle deliberately avoided the previously staged React lanes, Kubernetes rate-limit/workqueue, VS Code disposable leak tracking, Linux ring-buffer exchange, TypeScript incremental invalidation, Ollama process lifecycle, TensorFlow cancellation, Node async causality, PyTorch flight recorder, Redis incremental rehash, Go sync.Pool, and Git lock-backoff findings.

Inspection was broadened to other widely used/high-popularity OSS projects and focused on techniques with reusable architectural value rather than product-specific behavior.

---

## Candidate 1 — Rust `OnceLock`: one-time publication of shared initialized state

### Provenance

- Repository: `rust-lang/rust`
- Revision inspected: `c4c4a576936e9e67717d0deb8e74e02dd5dd10de`
- Path: `library/std/src/sync/once_lock.rs`
- File blob SHA: `4b41fc4587829e24b95f2877dd64ad21cee844e3`
- Source URL: `https://github.com/rust-lang/rust/blob/c4c4a576936e9e67717d0deb8e74e02dd5dd10de/library/std/src/sync/once_lock.rs`

### Technique

`OnceLock<T>` separates uninitialized storage from the synchronization state that proves initialization is complete. The value is physically stored in `UnsafeCell<MaybeUninit<T>>`, while the associated `Once` tracks whether publication has completed. Readers can perform a non-blocking `get()` that returns no value while initialization is absent/in progress, or explicitly wait for completion. Writers race through a one-time initialization gate; after successful publication, callers observe the initialized value rather than repeatedly constructing it.

A useful design property is that initialization status is not inferred from the contents of the storage itself. State and payload have separate responsibilities: the synchronization primitive establishes when the payload is safe to expose.

### Possible KNEEKURA applicability

- process-wide configuration snapshots that must be initialized exactly once before use;
- lazily prepared immutable parser/model metadata;
- one-time publication of a resolved capability table or runtime environment description;
- avoiding ad-hoc `if global is None` races in multi-worker local services.

### Limitations / uncertainty

- This is useful only when the semantic requirement really is one-time initialization. Mutable/reloadable configuration needs a different lifecycle.
- `OnceLock` itself is a Rust standard-library primitive; KNEEKURA implementations in other languages should preserve the invariant rather than mechanically copying the implementation.
- Waiting initialization can still become a liveness problem if the initializer itself blocks indefinitely; one-time publication does not replace timeout/cancellation design.

---

## Candidate 2 — Prometheus WAL benchmark: isolate burst throughput from close/fsync cost

### Provenance

- Repository: `prometheus/prometheus`
- Revision inspected: `5a078d9d2e0b9a8342cdd56585306904a409511f`
- Path: `tsdb/wlog/wlog_test.go`
- File blob SHA: `2b3b5fb64750b10cea8fa4aed5b5452d7c8364c6`
- Source URL: `https://github.com/prometheus/prometheus/blob/5a078d9d2e0b9a8342cdd56585306904a409511f/tsdb/wlog/wlog_test.go`

### Technique

Prometheus has separate WAL benchmarks for batched and single-record logging. In the batched benchmark, records are accumulated and logged in groups. Crucially, the benchmark explicitly stops the timer before deferred close/fsync work so the measured number answers a narrow question: burst logging throughput. The source comment states that including close fsync makes batched and single benchmarks look very similar and hides the burst-throughput difference.

The reusable lesson is **measurement-boundary discipline**: decide exactly which cost a benchmark is intended to measure, and deliberately exclude teardown or durability work when that work would answer a different question. Durability cost should then be measured separately rather than silently contaminating the throughput benchmark.

### Possible KNEEKURA applicability

- benchmark Runner command dispatch separately from final artifact flush;
- benchmark event ingestion separately from PostgreSQL checkpoint/close cost;
- compare batch vs single telemetry/evidence writes without allowing teardown latency to dominate;
- maintain paired metrics such as `steady/burst throughput` and `end-to-end durable completion` instead of one ambiguous latency number.

### Limitations / uncertainty

- Excluding fsync is correct only for a benchmark explicitly labeled as burst/ingestion throughput. It would be misleading for an end-to-end durability claim.
- KNEEKURA should preserve both measurements when durability matters; this candidate is about separating questions, not hiding expensive work.
- Storage/filesystem behavior varies substantially across machines and CI runners.

---

## Candidate 3 — curl Happy Eyeballs: staggered parallel fallback instead of serial timeout

### Provenance

- Repository: `curl/curl`
- Revision inspected: `110936726e518ff843e0a2063db8143be07dd286`
- Path: `docs/cmdline-opts/happy-eyeballs-timeout-ms.md`
- File blob SHA: `f1abb37725764ae764b77a1d20036137d884546b`
- Source URL: `https://github.com/curl/curl/blob/110936726e518ff843e0a2063db8143be07dd286/docs/cmdline-opts/happy-eyeballs-timeout-ms.md`

### Technique

curl's Happy Eyeballs behavior gives IPv6 a short head start, but does not wait for a full failure/timeout before trying IPv4. If the first family has not connected within the configured delay, the alternate attempt starts **in parallel**, and the first successful connection wins. The documented default is 200 ms at the inspected revision.

The generic architecture pattern is **staggered racing fallback**: give the preferred route a short opportunity to succeed, then launch a safe alternate route before the preferred route is conclusively dead. This avoids turning a degraded-but-not-failed primary path into a long serial stall.

### Possible KNEEKURA applicability

Potentially useful where two semantically equivalent execution paths exist, for example:

- preferred local service first, then a remote/read-only fallback after a bounded head start;
- primary model endpoint followed by a compatible secondary endpoint;
- local cache/materializer path followed by a slower canonical reconstruction path;
- redundant metadata retrieval paths when latency matters and both produce independently verifiable output.

### Limitations / uncertainty

- Racing duplicates work and can increase load; it should not be applied to mutating/non-idempotent actions unless cancellation/idempotency is proven.
- The alternate path must have equivalent semantics or its result must be normalized/verified before acceptance.
- The head-start delay must be evidence-based. Too short wastes resources; too long recreates serial fallback latency.
- This candidate is an architectural analogy from network connection establishment, not evidence that KNEEKURA should race arbitrary workers.

---

## Cycle 05 triage summary

All three candidates remain research-only.

Most directly reusable candidates for KNEEKURA follow-up are:

1. **measurement-boundary discipline** for performance acceptance and regression benchmarks;
2. **staggered racing fallback** for read-only/equivalent routes where serial degradation is costly;
3. **one-time safe publication** for immutable shared runtime state.

No canonical Knowledge Entity, Claim promotion, ranking, automatic recommendation, or VALIDATED transition was performed in this cycle.
