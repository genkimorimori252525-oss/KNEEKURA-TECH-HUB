# KNEEKURA TECH HUB — Harvest Staging Cycle 21

Status: **STAGING / NON-CANONICAL**

This memo is research staging only. Popularity was used to prioritize inspection, not as evidence of correctness. Existing main research plus open Harvest PRs through Cycle 20 were checked first to avoid obvious duplication. No finding below is promoted to VALIDATED/canonical knowledge and no production implementation is authorized by this memo.

## Selection notes

- Broad GitHub discovery first considered highly starred engineering repositories, then filtered for concrete implementation evidence and KNEEKURA relevance.
- Obvious duplicates of prior harvests were rejected, including earlier findings on cancellation propagation, retry throttling, overload degradation, queue isolation, cache determinism, incremental invalidation, crash-loop handling, and resource-release verification.
- The three findings below are distinct in mechanism: duplicate-call suppression, status-freshness coupling, and event-loop misuse detection with source attribution.

---

## Finding 1 — Go: per-key singleflight duplicate suppression

**Repository:** `golang/go`  
**Popularity snapshot:** 138,406 GitHub stars at harvest time (discovery signal only)  
**Repository URL:** https://github.com/golang/go  
**Exact revision:** `be1160f2a446665d6c0ccd2344c0cbe365bbc3a4`  
**Source path:** `src/internal/singleflight/singleflight.go`  
**Pinned source:** https://github.com/golang/go/blob/be1160f2a446665d6c0ccd2344c0cbe365bbc3a4/src/internal/singleflight/singleflight.go  
**Relevant symbols:** `Group.Do`, `Group.DoChan`, `call`, `ForgetUnshared`

### Technique

Go's internal `singleflight` package keeps one in-flight call per key. When a duplicate request arrives for the same key, it does not start another copy of the expensive function; it waits for the original and receives the same value/error. The implementation records duplicate consumers, supports channel delivery, and deletes the in-flight map entry when the original completes.

### Why it may be useful

KNEEKURA frequently has work that can be requested concurrently but is semantically identical: resolving one repository/ref, hashing the same artifact, loading identical model metadata, building one immutable snapshot, or querying one read-only source. A per-key singleflight layer can collapse a burst of N identical requests into one actual operation while preserving N callers.

This is narrower than caching: no long-lived reused result is required. It specifically removes duplicate *simultaneous* work, so it can reduce CPU, disk, API quota, lock contention, and duplicate evidence-fetch traffic without introducing a persistent stale-cache surface.

### Limitations / hazards

- The key must include every input that changes semantics. An under-specified key can incorrectly merge non-equivalent requests.
- Sharing the original error means a single transient failure is fanned out to all duplicate waiters.
- Waiter cancellation/deadlines require policy beyond this small implementation; one caller cancelling should not automatically destroy work still needed by other waiters.
- Side-effecting mutations should generally not be deduplicated this way unless their idempotency and authority semantics are explicitly proven.
- This mechanism does not replace persistent result caching or distributed coordination across separate hosts.

### KNEEKURA applicability

Strong candidate for read-only/idempotent operations inside one process or coordination domain: exact-ref lookup, immutable artifact construction, duplicate repository metadata fetches, expensive deterministic parsers, and model-load metadata probes. A KNEEKURA version should expose `shared=true/false` or equivalent telemetry so evidence can distinguish an actual execution from a joined execution.

### Uncertainty

The implementation evidence proves duplicate suppression semantics in Go's process-local `Group`; it does not prove that identical semantics are correct for every KNEEKURA workload, nor does it address cross-process/distributed singleflight.

---

## Finding 2 — Kubernetes: bind reported status to the exact desired-state generation it observed

**Repository:** `kubernetes/kubernetes`  
**Popularity snapshot:** 127,319 GitHub stars at harvest time (discovery signal only)  
**Repository URL:** https://github.com/kubernetes/kubernetes  
**Exact revision:** `1b2ebe523cdc23272f02130599f2c378fbf3ea8a`  
**Primary source path:** `pkg/apis/autoscaling/types.go`  
**Pinned source:** https://github.com/kubernetes/kubernetes/blob/1b2ebe523cdc23272f02130599f2c378fbf3ea8a/pkg/apis/autoscaling/types.go  
**Corroborating implementation example:** `pkg/controller/disruption/disruption.go`  
**Pinned example:** https://github.com/kubernetes/kubernetes/blob/1b2ebe523cdc23272f02130599f2c378fbf3ea8a/pkg/controller/disruption/disruption.go  
**Relevant field/concept:** `ObservedGeneration`

### Technique

Kubernetes status conditions can carry `observedGeneration`: the resource `.metadata.generation` that the controller used when producing that condition. Its own API comment gives the critical interpretation: if the current generation is 12 but a condition's observed generation is 9, that condition is out of date with respect to the current desired state.

This turns freshness from a timestamp guess into an explicit causal link between **which desired configuration existed** and **which status was computed from it**.

### Why it may be useful

KNEEKURA has several asynchronous control paths where a result can arrive after the user or another controller has already changed the request: Runner state, model configuration, evidence-generation jobs, Render Pack builds, branch/ref selections, or staged runtime observations. A status can be perfectly recent in wall-clock time yet still describe an obsolete configuration.

Attaching an `observedRevision` / `observedGeneration` to status/evidence would let consumers reject stale success mechanically instead of inferring freshness from timestamps or message order.

### Limitations / hazards

- The generation itself must increment reliably on every semantically relevant desired-state change.
- This marks causal freshness, not factual correctness. A controller may have observed the latest generation and still produced a wrong result.
- If only part of a composite input is generation-tracked, hidden dependencies can still make a status stale.
- Consumers must actually compare current generation with observed generation; merely storing the field provides no protection.
- For immutable Git objects, exact SHA may be a stronger identity than a monotonically increasing integer; KNEEKURA should not force one numbering model everywhere.

### KNEEKURA applicability

Strong candidate for any `spec/config -> asynchronous work -> status/evidence` contract. Possible mappings include `requestedConfigRevision -> observedConfigRevision`, `taskGeneration -> resultGeneration`, or simply exact input SHA sets. Especially useful before accepting "ready", "validated", "loaded", or "capture complete" states from workers.

### Uncertainty

Kubernetes demonstrates the freshness contract clearly, but a KNEEKURA schema should likely generalize it to multi-input identities rather than copy `ObservedGeneration` literally.

---

## Finding 3 — Home Assistant: detect forbidden blocking calls at the event-loop boundary and attribute them to source code

**Repository:** `home-assistant/core`  
**Popularity snapshot:** 90,363 GitHub stars at harvest time (discovery signal only)  
**Repository URL:** https://github.com/home-assistant/core  
**Exact revision:** `d5b6bd957d47fa3cfacfee2884e18613d8d592f5`  
**Source path:** `homeassistant/util/loop.py`  
**Pinned source:** https://github.com/home-assistant/core/blob/d5b6bd957d47fa3cfacfee2884e18613d8d592f5/homeassistant/util/loop.py  
**Relevant symbols:** `protect_loop`, `raise_for_blocking_call`, `_PREVIOUSLY_REPORTED`

### Technique

Home Assistant wraps functions that must not execute on the asyncio event-loop thread. `protect_loop` checks the current thread identity against the event-loop thread; if a protected blocking call occurs there, `raise_for_blocking_call` captures the offender filename, line number, source line, integration attribution, and traceback. It can warn or raise depending on strictness. It also records previously reported `(integration, filename, line)` keys so repeated violations can be downgraded from warning-with-traceback to debug logging instead of flooding logs.

### Why it may be useful

A common async-system failure is not a deadlock but accidental synchronous work on the control/event-loop thread: filesystem calls, subprocess waits, large hashing, blocking network clients, sleeps, or heavyweight parsing. Symptoms can look like random latency, missed heartbeats, stalled UI, or runner timeouts.

A KNEEKURA boundary guard could make this class of bug fail close to the offending call and preserve actionable provenance rather than waiting for a global watchdog to report only that "the loop stalled".

### Limitations / hazards

- A wrapper/deny-list only catches operations routed through protected entry points; unknown blocking functions can escape detection.
- Thread-identity checks do not measure how long a supposedly non-blocking operation actually takes.
- Strict raising is suitable for tests/development but can be too disruptive in production; warn/fail policy must be environment-sensitive.
- Source-stack attribution has runtime overhead and can expose noisy internal frames unless filtered carefully.
- Deduplicating repeated reports reduces log floods but can also hide frequency; counters/metrics should accompany suppression.

### KNEEKURA applicability

Useful around Browser/Command Bridge loops, async GitHub orchestration, local Runner control, WebSocket/RPC dispatch loops, and any single-threaded coordinator. Pairing a boundary guard with existing hang/watchdog telemetry would separate "known forbidden sync call" from "unknown loop stall" and provide faster defect localization.

### Uncertainty

Home Assistant's mechanism is Python/asyncio-specific. The reusable idea is the policy boundary plus provenance-rich detection, not the exact thread check or traceback implementation. JavaScript, JVM, Rust, or native workers would need runtime-specific equivalents.

---

## Cross-finding synthesis — hypothesis only

A possible KNEEKURA runtime contract emerges, but it is **not validated**:

1. Give every desired configuration an exact generation/revision identity.
2. Collapse truly identical simultaneous read-only work by full semantic key.
3. Require results/status to declare the generation/revision actually observed.
4. Guard the coordinator/event loop so expensive synchronous work cannot silently block progress.
5. Preserve telemetry showing whether a request executed, joined a singleflight, or was rejected as stale.

This synthesis is a derived hypothesis, not source-proven canonical architecture.

## Governance disposition

- Classification: `STAGING / NON-CANONICAL`
- Human selection: not performed
- VALIDATED promotion: not performed
- Canonical Knowledge Entity/relation creation: not performed
- Production implementation: not performed
- Next legitimate step: review, reproduce/benchmark where relevant, and ingest only through the existing governed discovery-to-knowledge path.
