# KNEEKURA TECH HUB — Harvest Staging Cycle 16

Status: **STAGING / NON-CANONICAL**

This document records evidence-backed candidates only. GitHub popularity was used only as a discovery-priority signal, not as evidence of correctness. No item below is promoted to VALIDATED/canonical knowledge and no production implementation is authorized by this memo.

## Duplicate-screening note

Existing main staging material and the open harvest PR backlog were checked before selection. Prometheus was explicitly rejected for this cycle because it had already been harvested in Cycle 05. Recent cycles already cover single-flight, circuit breakers, priority/admission queues, watchdogs, generation replacement, WAL/revision recovery, structured telemetry, deadlock handling, and related patterns; the candidates below were chosen for distinct mechanisms.

---

## Candidate 16-A — Child authority must never exceed parent authority

- Repository: `denoland/deno`
- Repository URL: https://github.com/denoland/deno
- GitHub stars observed during harvest: 108,399
- Revision: `336da420f4343cbb1dcbd5eed9d075ff555ed6ee`
- Source paths / sections:
  - `runtime/ops/worker_host.rs` — worker creation calls `parent_permissions.create_child_permissions(...)`
  - `runtime/permissions/lib.rs` — `create_child_permissions` and `ChildPermissionError::Escalation` (`Can't escalate parent thread permissions`)
  - `tests/unit/worker_test.ts` — worker permission-escalation rejection coverage
- Provenance URLs:
  - https://github.com/denoland/deno/blob/336da420f4343cbb1dcbd5eed9d075ff555ed6ee/runtime/ops/worker_host.rs
  - https://github.com/denoland/deno/blob/336da420f4343cbb1dcbd5eed9d075ff555ed6ee/runtime/permissions/lib.rs
  - https://github.com/denoland/deno/blob/336da420f4343cbb1dcbd5eed9d075ff555ed6ee/tests/unit/worker_test.ts

### Technique

Treat delegated authority as a monotone-decreasing capability relation: a child worker may inherit or receive a subset of the parent's permissions, but requesting a capability outside the parent's authority is an explicit error rather than an implicit prompt or silent widening.

### Why it may be useful to KNEEKURA

This maps naturally to Jolly / Durable / Runner / helper-agent authority. A parent task that is read-only should be structurally incapable of creating a child that can mutate GitHub, execute unrestricted local commands, or access unrelated resources. It reduces the risk that authority expands simply because work was delegated another layer down.

### Applicability

- agent → sub-agent delegation
- Durable task → local worker delegation
- GitHub read/write capability delegation
- repository-scoped tools
- filesystem or process execution scopes
- any future plugin-host capability model

### Limitations / uncertainty

Deno's permission model is runtime-specific and contains its own scope semantics, prompts, and resource types. KNEEKURA should reuse the invariant, not Deno's exact permission representation. A real KNEEKURA design must define ordering/subset semantics for heterogeneous capabilities and must specify how temporary elevation, if ever allowed, is separately authorized and audited.

---

## Candidate 16-B — Estimate destruction cost and offload only expensive frees

- Repository: `redis/redis`
- Repository URL: https://github.com/redis/redis
- GitHub stars observed during harvest: 76,309
- Revision: `669b2a1316f5b35ecf964281b77c054ff28dc934`
- Source path / sections:
  - `src/lazyfree.c` — `LAZYFREE_THRESHOLD`, `lazyfreeGetFreeEffort`, `freeObjAsync`, `lazyfreeFreeObject`
- Provenance URL:
  - https://github.com/redis/redis/blob/669b2a1316f5b35ecf964281b77c054ff28dc934/src/lazyfree.c

### Technique

Redis does not push every free operation to a background thread. It first estimates the destruction effort, and only sufficiently expensive objects are asynchronously reclaimed; small frees remain synchronous. The actual background operation then releases the object and updates accounting.

### Why it may be useful to KNEEKURA

Large cleanup operations can create latency spikes even when the actual job is already complete. KNEEKURA can apply the same principle to heavyweight disposable state: large parsed ASTs, temporary evidence bundles, expanded assets, Render Pack generations, model-side buffers, or large in-memory indexes. Cheap cleanup can stay synchronous for simplicity; only expensive destruction needs background disposal.

### Applicability

- large transient analysis graphs
- Viewer / Render Pack generation cleanup
- model or asset cache eviction
- temporary evidence bundle disposal
- large decompressed or parsed repository data

### Limitations / uncertainty

Redis's threshold value (`64`) and its effort metric are data-structure-specific and must not be copied. Background freeing can temporarily increase peak memory because logical removal and physical reclamation are separated in time. KNEEKURA would need explicit backlog/pressure accounting so cleanup cannot fall permanently behind or compete with higher-authority evidence retention.

---

## Candidate 16-C — Propagate one concurrency token pool across process boundaries

- Repository: `rust-lang/cargo`
- Repository URL: https://github.com/rust-lang/cargo
- GitHub stars observed during harvest: 15,463
- Revision: `e7506208ff1b7f01062e410c419f95628dfdb31b`
- Source paths / sections:
  - `src/compiler/build_runner/mod.rs` — reuse jobserver from environment, otherwise create a token pool and immediately account for the current process
  - `src/compiler/job_queue/mod.rs` — acquired jobserver tokens gate queued work
  - `src/compiler/timings/report.rs` — explicitly distinguishes active work from work ready-but-waiting for a jobserver token
- Provenance URLs:
  - https://github.com/rust-lang/cargo/blob/e7506208ff1b7f01062e410c419f95628dfdb31b/src/compiler/build_runner/mod.rs
  - https://github.com/rust-lang/cargo/blob/e7506208ff1b7f01062e410c419f95628dfdb31b/src/compiler/job_queue/mod.rs
  - https://github.com/rust-lang/cargo/blob/e7506208ff1b7f01062e410c419f95628dfdb31b/src/compiler/timings/report.rs

### Technique

Use a shared jobserver token pool so nested tools and child processes participate in one concurrency budget instead of each independently assuming it may use all CPUs. When Cargo inherits an existing jobserver it participates in that pool; otherwise it creates one itself and accounts for its own running process. The scheduler separately tracks work that is runnable but blocked only on token availability.

### Why it may be useful to KNEEKURA

KNEEKURA increasingly composes tools that can themselves fan out: repository analyzers, compilers, test runners, model workers, extraction helpers, and possibly child agents. Independent `N workers` limits at every layer multiply into oversubscription. A propagated host-level token pool could make nested work respect one global CPU/process concurrency envelope while still allowing each subsystem to manage its own logical queue.

### Applicability

- nested repository-analysis tools
- compiler/test invocations launched by workers
- local helper processes
- CPU-heavy deterministic executors
- multi-agent workflows that spawn local subprocess work

### Limitations / uncertainty

Cargo's jobserver primarily models fungible execution slots, not RAM, VRAM, network bandwidth, API quotas, or heterogeneous GPU jobs. KNEEKURA would likely need multiple resource classes or weighted tokens. This also does not replace the separate priority, fairness, or parent resource ceilings harvested in earlier cycles; it complements them by preventing process-tree concurrency multiplication.

---

## Cross-candidate synthesis — NON-CANONICAL hypothesis

A possible KNEEKURA execution contract suggested by these three independent patterns is:

1. delegation may only narrow authority;
2. nested local execution shares a host-level concurrency budget rather than multiplying worker counts;
3. after work completes, expensive destruction may be decoupled from the foreground path, but its backlog remains resource-accounted.

This synthesis is an inference, not upstream-proven behavior and not an adoption decision.

## Governance disposition

- Discovery: completed for the evidence listed above.
- Provenance capture: completed to repository + exact revision + source path/section level.
- Duplicate screening: performed against known harvest backlog; one duplicate candidate (Prometheus) was rejected.
- Validation: **not performed**.
- Human selection: **not performed**.
- Canonical promotion: **not authorized / not performed**.
- Production implementation: **not authorized / not performed**.
