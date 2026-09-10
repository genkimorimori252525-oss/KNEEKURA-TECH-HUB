# OSS Harvest Staging — 2026-09-10 / Cycle 03

Status: **STAGING / NON-CANONICAL**

This document contains discovery-stage research notes only. Nothing here is `VALIDATED` knowledge. Promotion must go through the existing KNEEKURA TECH HUB evidence and human-review gates.

## Selection policy for this cycle

- Existing Cycle 01 and Cycle 02 staging notes were checked first. This cycle intentionally avoids duplicating React priority lanes, Kubernetes retry/workqueue patterns, VS Code disposable ownership tracking, Linux tracing page swaps, TypeScript incremental invalidation, and Ollama model keep-alive lifecycle.
- GitHub popularity was used only to prioritize inspection. It is not evidence that a technique is correct or suitable for KNEEKURA.
- This cycle focuses on long-running and asynchronous systems: cancellation propagation, causal tracing across asynchronous boundaries, and bounded failure-history capture for distributed/hanging work.
- All inspected implementation evidence is pinned to exact repository revisions and file blob identities.

---

## H-2026-09-10-008 — Tokenized cancellation callbacks with parent-to-child propagation and safe deregistration

**Repository:** `tensorflow/tensorflow`

**Discovery metadata at capture:** 199,309 GitHub stars; Apache-2.0 repository license metadata.

**Pinned revision:** `eeb00a976c1ce5ff3faa389ef0382c9c63819ca5`

**Evidence:**

- path: `third_party/xla/xla/tsl/framework/cancellation.h`
- inspected region: approximately lines 30-220
- blob SHA: `900a784bf8b19893915c80f587ba47505fa71c12`
- source URL: `https://github.com/tensorflow/tensorflow/blob/eeb00a976c1ce5ff3faa389ef0382c9c63819ca5/third_party/xla/xla/tsl/framework/cancellation.h`

### Observed technique

TensorFlow/XLA's `CancellationManager` issues monotonically generated cancellation tokens. Callers register a cancellation callback under a token, then deregister that callback when the asynchronous operation completes normally.

The API deliberately distinguishes several race cases:

- registration can fail because cancellation already started; the caller must then perform its cancellation cleanup itself;
- `DeregisterCallback(token)` guarantees that a successfully deregistered callback will not subsequently run, and otherwise can block until an in-flight callback has completed;
- `TryDeregisterCallback(token)` provides a non-blocking alternative but explicitly gives up the stronger completion guarantee;
- a manager can be a child of another manager, so parent cancellation propagates into the child while retaining a separate manager identity for the nested execution.

The header also documents a crucial lock-order rule: a caller deregistering a callback must not hold a mutex needed by that callback, otherwise cancellation and completion can deadlock each other.

### Why it may be useful

The transferable idea is **make cancellation an explicit lifecycle protocol rather than a shared boolean flag**. A token identifies the exact cancellable operation, registration establishes the cleanup path, deregistration closes that path when normal completion wins the race, and parent/child managers give structured cancellation propagation.

Potential KNEEKURA applications include Durable steps, Runner commands, GitHub acquisition jobs, Minecraft observation operations, model inference requests, and any workflow where one parent task owns several cancellable asynchronous children.

This could help prevent two common failure classes:

1. an old cancellation signal tearing down a newer/reused operation;
2. a completion path freeing resources while a cancellation callback is still executing against them.

### Limitations / applicability

- Callback cancellation is cooperative; it cannot force arbitrary code or an uninterruptible native call to stop safely.
- Token and deregistration discipline adds lifecycle complexity. Missing deregistration can retain callbacks/resources; incorrect lock ordering can deadlock.
- Parent/child propagation assumes clear ownership. Shared work serving multiple parents may need reference counting, leases, or a different cancellation model.
- The exact TensorFlow implementation should not be copied wholesale; the useful candidate is the lifecycle contract and race semantics.

**Confidence:** high for the observed protocol; direct KNEEKURA adoption remains a design hypothesis until tested against one concrete asynchronous workflow.

---

## H-2026-09-10-009 — Preserve logical async causality separately from the current execution stack

**Repository:** `nodejs/node`

**Discovery metadata at capture:** 121,153 GitHub stars. GitHub repository license metadata is `NOASSERTION` at capture; Node.js uses its own repository licensing files and notices, so content-handling policy should remain separately reviewed if promoted.

**Pinned revision:** `43d3fe95581cb599611dc8e1aae9a79a900998b8`

**Evidence:**

- path: `lib/async_hooks.js`
- inspected region: approximately lines 170-280
- blob SHA: `31a390dfc912ae7e14c3b34625d05e5d87d9a260`
- source URL: `https://github.com/nodejs/node/blob/43d3fe95581cb599611dc8e1aae9a79a900998b8/lib/async_hooks.js`

### Observed technique

Node.js `AsyncResource` assigns each logical asynchronous resource its own `asyncId` and separately records the `triggerAsyncId` of the execution context that created or triggered it. The resource also captures the current async context frame.

When user code is run through `runInAsyncScope`, Node emits a `before` event, swaps in the captured context frame, executes the callback, and restores the prior frame in a `finally` block before emitting the corresponding `after` event. Destruction is likewise represented as an explicit lifecycle event.

The important distinction is that **logical causality is not inferred later from whichever thread/stack happens to be running the callback**. The parent/trigger identity is recorded when the asynchronous resource is created.

### Why it may be useful

Long KNEEKURA workflows cross many boundaries where an ordinary call stack disappears: ChatGPT command -> bridge -> Durable task -> local worker -> subprocess -> callback/event -> result. If each spawned operation records both its own immutable operation ID and the ID that triggered it, diagnostics can reconstruct a causal chain even when execution is asynchronous or concurrent.

Possible uses include:

- tracing which user/workspace command caused a later Runner action;
- linking retries to the original logical request rather than only to the retrying worker;
- explaining which task spawned a subprocess whose failure appears minutes later;
- separating `execution parent` from `resource owner` where those concepts differ.

A particularly useful design lesson is to capture causal identity at creation time and restore context with `try/finally`, instead of relying on mutable global "current task" state.

### Limitations / applicability

- Causal IDs improve observability but do not themselves guarantee ordering, ownership, or exactly-once execution.
- Context propagation adds metadata and instrumentation overhead; not every tiny operation needs a first-class trace node.
- A single trigger parent may be insufficient for fan-in work influenced by several predecessors; such systems may need explicit links to multiple causes.
- The Node.js API is runtime-specific. KNEEKURA should borrow the causal-identity principle, not necessarily its hook vocabulary.

**Confidence:** high for the observed async identity/context pattern; high conceptual relevance to multi-hop KNEEKURA workflows, but implementation scope should remain narrow until a concrete trace gap is reproduced.

---

## H-2026-09-10-010 — Keep a bounded pre-failure flight recorder so hangs can be diagnosed after the fact

**Repository:** `pytorch/pytorch`

**Discovery metadata at capture:** 102,889 GitHub stars. GitHub repository license metadata is `NOASSERTION` at capture; promotion should preserve separate license/content-handling review.

**Pinned revision:** `3ac1dd042e9483d047a01e548488fef4337f8202`

**Evidence:**

- path: `torch/csrc/distributed/c10d/FlightRecorderDetail.hpp`
- inspected region: approximately lines 1-260
- blob SHA: `ca67b47da46e63c6da3bb1b0a5872318e0e1930b`
- source URL: `https://github.com/pytorch/pytorch/blob/3ac1dd042e9483d047a01e548488fef4337f8202/torch/csrc/distributed/c10d/FlightRecorderDetail.hpp`
- related search evidence: `torch/distributed/flight_recorder/components/utils.py` describes monotonically increasing `record_id` values written into a ring buffer and cross-rank trace alignment.

### Observed technique

PyTorch's distributed Flight Recorder captures operation metadata continuously into a bounded circular buffer rather than waiting for a failure before beginning diagnostics.

For each recorded operation the inspected implementation stores, among other fields:

- monotonically increasing record identity;
- process-group identity/name and collective/P2P sequence identifiers;
- operation/profiling name;
- a captured traceback;
- input/output dtype, dimensionality, and sizes;
- start/end event references and discovery timestamps;
- operation timeout;
- thread identity and thread name.

Once the configured maximum number of entries is reached, the circular buffer overwrites old slots. Dumping reconstructs entries in logical order around the wrap point. The implementation also uses a reset epoch: clearing history can mark old entries obsolete without requiring their IDs to be globally reused, reducing ambiguity between records from before and after a reset.

An additional diagnostic detail is that traceback symbolization is separated from raw traceback capture; the source explicitly warns that symbolization may need the Python GIL and can risk blocking/deadlock, suggesting asynchronous symbolization when necessary.

### Why it may be useful

For hangs and timeouts, the most valuable evidence often exists **before** the failure is recognized. A bounded flight recorder provides a rolling window of recent operations while keeping memory usage predictable.

This maps strongly to KNEEKURA systems that can stall far from the originating action: Runner executions, Minecraft/YSM observation, Command Bridge/Durable transitions, local-model workers, Code Police scans, or long GitHub workflows.

A KNEEKURA-specific recorder could keep only lightweight facts such as:

`operation_id -> trigger_id -> kind -> target -> start -> state transitions -> worker/process identity -> bounded payload metadata`

and freeze/dump the ring when a watchdog, timeout, invariant failure, or user-requested diagnostic occurs. The PyTorch reset-epoch idea is also useful if diagnostic history can be reset while operation IDs or buffer slots continue being reused.

### Limitations / applicability

- A bounded ring intentionally loses older history. Capacity must reflect the longest useful pre-failure window rather than an arbitrary entry count.
- Capturing full stack traces or payload metadata on every operation can be expensive; sampling or tiered detail may be needed.
- Sensitive command arguments, repository content, tokens, or user data must not be copied into diagnostics merely because a recorder exists.
- In-memory rings do not survive process death. Critical failure capsules may need a crash-safe or periodically flushed outer layer.
- Cross-process/cross-machine alignment requires stable clocks/sequence IDs or another correlation mechanism; a local ring alone is insufficient.

**Confidence:** high for the bounded circular trace mechanism; very high diagnostic relevance, but retention/privacy/performance limits would need explicit KNEEKURA policy before implementation.

---

## Cross-finding synthesis (research hypothesis only)

These three findings form a coherent **long-running asynchronous reliability pattern**, but they should remain independent techniques rather than being prematurely bundled into a framework:

- **TensorFlow cancellation tokens:** make teardown races explicit and close the cancellation path when normal completion wins.
- **Node.js async trigger identity:** preserve causal ancestry when ordinary call stacks disappear.
- **PyTorch Flight Recorder:** retain a bounded window of what happened before a hang or timeout was detected.

Together they suggest a possible future diagnostic invariant for KNEEKURA:

> Every long-lived asynchronous operation can be identified, linked to what triggered it, cancelled through an explicit lifecycle, and reconstructed from a bounded pre-failure trace.

That is only a research hypothesis. A human review should first identify a concrete existing failure mode in one KNEEKURA subsystem before adopting any of these mechanisms.

## Promotion status

`STAGING_ONLY`

No Knowledge Entity, Claim maturity transition, canonical relation, recommendation winner, or automatic adoption decision was created by this harvest cycle.
