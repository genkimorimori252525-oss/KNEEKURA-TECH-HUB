# KNEEKURA TECH HUB — Harvest Staging 2026-09-10 Cycle 06

> Status: **STAGING / NON-CANONICAL**
>
> These findings are research candidates only. GitHub popularity is used only to prioritize inspection; it is not evidence of correctness, suitability, or validation. Promotion to canonical / VALIDATED knowledge requires the normal human-governed acceptance path.

## Selection policy

- Existing Cycle 01–05 staging was checked first. This cycle avoids the already-harvested React lanes, Kubernetes rate-limit/workqueue, VS Code disposable graph, Linux ring-page swap, TypeScript incremental invalidation, Ollama process keep-alive, TensorFlow cancellation, Node async causality, PyTorch flight recorder, Redis incremental rehash, Go sync.Pool, Git lock backoff/PID evidence, Rust OnceLock, Prometheus benchmark-boundary, and curl Happy Eyeballs findings.
- New repositories were chosen from high-star implementation-heavy GitHub projects not previously sampled in the staging set.
- Star counts below are discovery metadata observed on 2026-09-10 and may change.

---

## Candidate 1 — Moby keyed single-flight for duplicate remote resolution

**Repository:** `moby/moby` — 72,073 stars observed 2026-09-10

**Pinned revision:** `c3065211177705ada59a9ccf8b5c182f286f8c97`

**File:** `daemon/internal/builder-next/adapters/containerimage/pull.go`

**Pinned source:** https://github.com/moby/moby/blob/c3065211177705ada59a9ccf8b5c182f286f8c97/daemon/internal/builder-next/adapters/containerimage/pull.go

### Technique

The image source owns a `flightcontrol.Group[*resolveRemoteResult]`. `resolveRemote` derives a synchronization key from the image reference plus fully formatted platform (`getconfig::<ref>::<platform>`) and executes the expensive remote config resolution through `Group.Do`. Parallel callers resolving the same image/platform therefore share one in-flight operation instead of issuing duplicate remote work. The puller also uses a flight-control group around its resolve path.

### Why this may be useful to KNEEKURA

KNEEKURA frequently has multiple observers, retries, UI refreshes, or scheduled tasks that may ask for the same expensive fact nearly simultaneously. A keyed single-flight layer could collapse identical in-flight GitHub fetches, exact-SHA evidence preparation, model metadata loading, Render Pack preparation, or runner capability probes while still allowing different keys to proceed independently.

### Important distinction

This is not a durable cache. It only coalesces overlapping work. Once the in-flight call completes, future callers may execute again unless a separate cache exists. Treating it as a cache would create false persistence assumptions.

### Limitations / uncertainty

- The `flightcontrol` implementation itself comes from Moby BuildKit, so this Moby file proves integration/use but not every internal cancellation and waiter semantic of the dependency.
- Key correctness becomes part of correctness: two operations must only share work when every input that can affect the result is represented in the key.
- Side-effecting operations should not be coalesced merely because their parameters look similar unless shared execution is semantically safe.

### KNEEKURA applicability candidate

A good first application would be read-only exact-SHA evidence preparation: `(repository, exactSha, evidenceKind, normalizedOptions)` -> one in-flight producer, multiple waiters. Do **not** apply automatically to writes, commits, deployments, or commands with per-caller authority.

---

## Candidate 2 — Traefik non-blocking latest-value channel plus refresh throttling

**Repository:** `traefik/traefik` — 64,801 stars observed 2026-09-10

**Pinned revision:** `d48621ce0b6fd221b20bdb6c22e652e7498e5db6`

**Files:**

- `pkg/provider/aggregator/ring_channel.go`
- `pkg/provider/aggregator/aggregator.go`

**Pinned sources:**

- https://github.com/traefik/traefik/blob/d48621ce0b6fd221b20bdb6c22e652e7498e5db6/pkg/provider/aggregator/ring_channel.go
- https://github.com/traefik/traefik/blob/d48621ce0b6fd221b20bdb6c22e652e7498e5db6/pkg/provider/aggregator/aggregator.go

### Technique

Traefik's `RingChannel` is intentionally non-blocking for producers. It stores only one buffered message; when input outruns output, a newer input replaces the buffered value, discarding the older pending value. Its loop first attempts output before accepting another input, reducing avoidable drops when both directions are ready. The provider aggregator can wrap providers with a per-provider or global throttle duration: one message is forwarded and the consumer then sleeps for that duration before accepting the next buffered output.

This is effectively a **latest-state coalescer** rather than an event log: intermediate configuration states may be discarded while the newest pending state survives.

### Why this may be useful to KNEEKURA

Some KNEEKURA signals describe current state rather than historical events: runner online/offline state, UI refresh state, model availability, repository-head observations, live telemetry snapshots, or rapidly repeated configuration refresh requests. For these streams, back-pressuring every producer or processing every transient intermediate value can waste work and increase latency. A one-slot latest-value channel plus bounded refresh frequency can keep the system responsive while converging toward current truth.

### Limitations / uncertainty

- **Never use this for audit/evidence/event streams.** Dropping intermediate values is the design, so it is incompatible with append-only evidence, command receipts, governance decisions, or anything where every transition matters.
- Traefik explicitly notes scheduler timing can still cause values to be discarded even when an ideal schedule might have delivered them.
- Throttling adds intentional latency; the duration must match the semantics of the state source.

### KNEEKURA applicability candidate

Separate channels by semantic type: `STATE_LATEST` may use coalescing; `EVENT_DURABLE` must not. Encoding that distinction in the type/contract would prevent accidental evidence loss.

---

## Candidate 3 — Syncthing CPU-relative worker ceiling and bounded pending-data configuration

**Repository:** `syncthing/syncthing` — 88,442 stars observed 2026-09-10

**Pinned revision:** `2ca95cf1498104113fdfde46df4107f2450a0f71`

**File:** `lib/model/folder_sendrecv.go`

**Pinned source:** https://github.com/syncthing/syncthing/blob/2ca95cf1498104113fdfde46df4107f2450a0f71/lib/model/folder_sendrecv.go

### Technique

The send/receive folder normalizes its worker configuration before starting the pull pipeline. If `Copiers` is zero it uses a default, then caps the effective value at `2 * runtime.NumCPU()` to create a known upper bound. It separately normalizes `PullerMaxPendingKiB`: zero selects a default, and any non-zero value smaller than one protocol block is raised to at least one block. The resulting bounded values size the copier, puller, finisher, and database-update pipeline channels/workers.

### Why this may be useful to KNEEKURA

Long-running local systems often fail not because one task is too expensive, but because user configuration or automatic scaling permits too many simultaneous tasks. A machine-relative hard ceiling gives an explicit maximum even if the configured value is pathological. Separately validating queue/buffer parameters against a minimum meaningful work unit prevents configurations that are technically positive but operationally impossible.

This pattern fits local parsers, evidence extraction workers, screenshot/frame processing, model preprocessing, repository scanners, and other pipelines where concurrency and in-flight data both affect memory/CPU pressure.

### Limitations / uncertainty

- `2 * NumCPU` is a Syncthing-specific policy, not a universal optimum. CPU-bound, I/O-bound, GPU-bound, and memory-bound KNEEKURA jobs need different ceilings.
- CPU count alone does not model RAM, VRAM, disk bandwidth, remote API limits, or thermal constraints.
- Raising a configured pending-data floor is only safe when the minimum unit is structurally required and clearly documented.

### KNEEKURA applicability candidate

Use **resource-derived ceilings** rather than copying Syncthing's multiplier: e.g. `min(userLimit, cpuBudget, memoryBudget, providerRateBudget)`, with each worker class declaring its limiting resource and minimum viable work-unit size.

---

## Cross-cycle notes

These three findings are deliberately complementary rather than variants of earlier findings:

- Moby: deduplicate **simultaneous identical read work**.
- Traefik: coalesce **rapid superseding state updates**.
- Syncthing: bound **pipeline parallelism and in-flight resource pressure**.

They should not be collapsed into one generic "queue optimization" rule because their loss, replay, and side-effect semantics differ materially.

## Governance status

- No Knowledge Entity was created or promoted.
- No VALIDATED status was assigned.
- No implementation change to KNEEKURA production systems was made.
- This file is evidence-preserving research staging only.