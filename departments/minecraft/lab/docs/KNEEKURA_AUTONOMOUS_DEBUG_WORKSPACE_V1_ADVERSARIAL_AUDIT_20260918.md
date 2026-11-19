# KNEEKURA Autonomous Debug Workspace v1 — Adversarial Audit

Status: DESIGN AUDIT
Date: 2026-09-18 JST
Target plan: docs/KNEEKURA_AUTONOMOUS_DEBUG_WORKSPACE_V1_PLAN.md

## Purpose

This audit attacks the design from the perspective of silent false-debugging: cases where the system appears healthy, actions appear successful, or a fix appears verified while the underlying experiment is stale, contaminated, incomplete, or observing the wrong thing.

The audit is design-level only. It does not claim that unimplemented controls already work.

## Threat model

Primary failure classes:

- stale command applied to a newer run
- stale or cross-run Evidence joined as current
- incomplete Arena reset
- partial mutation reported as success
- crash during mutation leaving hidden world contamination
- reordered cross-process evidence creating false causality
- logging load changing the bug
- derived caches returning stale summaries
- AI inference presented as observed fact
- nondeterministic non-reproduction presented as a fix
- incomplete/truncated logs presented as complete
- multiple agents racing on one Arena
- AI altering the test/oracle/probe instead of fixing the target
- debug-only helpers making a false fix pass
- runtime bytes differing from the source the AI believes it launched

## Round 1 — Identity, reset, and action correctness

### Finding A1 — runId alone cannot fence stale mutations
Severity: BLOCKING

A command queued before restart could otherwise reach a newer Minecraft process.

Mitigation added:
- debugSessionId/runId/processEpoch/arenaEpoch/actionId on mutation
- stale-command rejection
- idempotency key
- expected target identity

Status: DESIGN MITIGATED

### Finding A2 — Arena reset could be incomplete
Severity: BLOCKING

Blocks/entities alone do not define a clean experiment. Scheduled ticks, helper state, client state, forced chunks, score/team state, time/weather, and third-party state may survive.

Mitigation added:
- reset-state classification
- baseline fingerprint
- ARENA_NOT_CLEAN
- fresh Arena / fresh world fallback

Status: DESIGN MITIGATED, implementation must prove reset coverage

### Finding A3 — backend acceptance is not world-state success
Severity: BLOCKING

A command may be accepted but partially applied.

Mitigation added:
- REQUESTED -> ACCEPTED -> APPLIED -> VERIFIED
- postcondition reread
- PARTIAL_APPLY
- mutation effect envelope

Status: DESIGN MITIGATED

### Finding A4 — process-local timestamps cannot prove cross-process causality
Severity: HIGH

Mitigation added:
- per-writer monotonic sequence
- explicit trace/action/packet IDs
- clock metadata
- timestamps treated as correlation data, not sole causal key

Status: DESIGN MITIGATED

## Round 2 — Concurrency, recovery, and render truth

### Finding B1 — multiple writers can invalidate each other's assumptions
Severity: BLOCKING

Mitigation added:
- single-writer Arena lease
- arenaRevision compare-and-reject
- serialized mutation queue
- independent Arenas for parallel experiments

Status: DESIGN MITIGATED

### Finding B2 — autonomous source editing could make the workspace unrecoverable
Severity: HIGH

Mitigation added:
- isolated worktree/branch
- patch checkpoints
- compile-before-restart gate
- external Supervisor
- bounded restart loop

Status: DESIGN MITIGATED

### Finding B3 — local reset may be unable to clean unknown state
Severity: HIGH

Mitigation added:
- reset retry
- fresh Arena
- immutable debug-world template regeneration

Status: DESIGN MITIGATED

### Finding B4 — absent YSM render evidence can be mistaken for YSM failure
Severity: BLOCKING for render diagnostics

Mitigation added:
- TARGET_TRACKED / IN_RENDER_RANGE / FRUSTUM_ELIGIBLE / RENDER_ENTERED / YSM_ENTERED / YSM_COMPLETED split
- explicit renderObservationMode
- camera automation recorded as perturbation

Status: DESIGN MITIGATED

### Finding B5 — localhost control surface is still an authority boundary
Severity: HIGH

Mitigation added:
- loopback default
- per-session capability token
- schema/size validation
- mutation allow-list
- no GET mutation
- browser Origin/CSRF protection when applicable

Status: DESIGN MITIGATED

## Round 3 — Evidence coherence and crash boundaries

### Finding C1 — a "current state" may combine values from different moments
Severity: BLOCKING

Mitigation added:
- evidenceCut
- coherence mode
- snapshot barrier for strict comparisons
- EVIDENCE_CONTEXT_CHANGED on identity changes during query

Status: DESIGN MITIGATED

### Finding C2 — crash during action creates an unknown result, not clean failure
Severity: BLOCKING

Mitigation added:
- OUTCOME_UNKNOWN
- durable action/idempotency ledger
- baseline verification before next experiment

Status: DESIGN MITIGATED

### Finding C3 — idempotency memory can be lost across reconnect
Severity: HIGH

Mitigation added:
- durable idempotency ledger
- payload conflict detection

Status: DESIGN MITIGATED

### Finding C4 — an invariant alarm is not itself a root cause
Severity: HIGH

Mitigation added:
- invariant identity/version
- Anomaly -> Finding -> Hypothesis boundary
- evidence IDs and limitations

Status: DESIGN MITIGATED

### Finding C5 — startup optimization could skip correctness checks
Severity: HIGH

Mitigation added:
DEBUG_READY is defined by minimum correctness gates, not merely elapsed time.

Status: DESIGN MITIGATED

## Round 4 — Reproducibility and evidence completion

### Finding D1 — one non-reproduction can look like a successful fix
Severity: BLOCKING

Mitigation added:
- randomness contract
- NONDETERMINISTIC_SOURCE_PRESENT
- repeated trials when required
- REPRODUCED / NOT_REPRODUCED / FIX_VERIFIED / REGRESSION / INCONCLUSIVE separation
- explicit acceptance predicate

Status: DESIGN MITIGATED

### Finding D2 — truncated files can look like complete evidence
Severity: HIGH

Mitigation added:
- finalization manifest
- hashes/sizes/last sequences/drop counts
- EVIDENCE_COMPLETE vs EVIDENCE_PARTIAL

Status: DESIGN MITIGATED

### Finding D3 — AI conclusions could overwrite measurement history
Severity: BLOCKING

Mitigation added:
- raw Evidence/RunSnapshot/finalization authority separated from Finding/Hypothesis/Conclusion writes
- append-only/content-addressed direction for canonical evidence

Status: DESIGN MITIGATED

### Finding D4 — paused integrated runtime can look like target AI failure
Severity: HIGH

Mitigation added:
- server/client tick-liveness
- pause/focus/screen state where observable
- RUNTIME_PAUSED / TICK_STALLED

Status: DESIGN MITIGATED

## Round 5 — Trusted observer and false-pass resistance

### Finding E1 — AI can "fix" the observer or test instead of the bug
Severity: BLOCKING

Mitigation added:
- Trusted Computing Base
- protected acceptance predicate registry
- trusted CLEAN_VERIFY observer identity
- source-edit allow roots
- observer-change -> REVERIFY_REQUIRED
- acceptance predicate hash/version binding

Status: DESIGN MITIGATED

### Finding E2 — FAST_DEBUG helpers can create a debug-only fix
Severity: BLOCKING

Mitigation added:
- target patch debug-dependency check
- CLEAN_VERIFY observer-only influence goal
- helper classification in RunSnapshot
- optional NORMAL_PARITY profile

Status: DESIGN MITIGATED

## TECH HUB patterns adopted

The plan now explicitly adopts these KNEEKURA TECH HUB-derived patterns:

1. Observation != Conclusion
2. immutable RunSnapshot / provenance
3. re-verification after dependency revision
4. multiple evidence-backed cause candidates without forced winner
5. incremental derived-state recomputation as an optimization principle, not a required library

Specific Salsa/Tree-sitter libraries are not required by v1.

## Residual risks

No additional design-level BLOCKING defect was identified in the final pass, but the following risks remain intentionally open until implementation evidence exists:

- exact reset coverage for third-party Mod state
- safe and useful render-camera automation
- actual Probe overhead under L3/L4
- cross-process event correlation quality under high load
- robust runtime attestation for dev class directories rather than packaged JARs
- behavior differences between Integrated Server and Dedicated Server
- nondeterminism that cannot be seeded or controlled
- observer hooks into obfuscated/private YSM/TLM internals
- external filesystem/native/network side effects outside Minecraft
- JVM/OS/GPU scheduling causes that observation cannot fully expose

These are not to be silently marked solved by implementation convenience.

## Implementation audit rule

Each implementation gate G1-G7 must receive a new adversarial audit against the executable behavior.

A design mitigation is not considered implemented until there is machine evidence or a focused test proving it.

Suggested audit checkpoints:

- after G1: launch identity / runtime attestation / crash recovery
- after G2: evidence cuts / lane health / drop truth / epoch fences
- after G3: action fencing / partial apply / reset fidelity / concurrency
- after G4: ring-buffer coverage / perturbation / render preconditions
- after G5: stale command rejection / durable idempotency / recovery
- after G6: AI inference separation / oracle protection / false-fix attacks
- after G7: clean/debug parity / re-verification / evidence finalization

## Current conclusion

The design is substantially stronger after the audit.

The largest remaining risk is no longer a known missing architecture boundary; it is whether implementation preserves these boundaries under real Minecraft/Forge/TLM/YSM behavior.

Therefore the next audit target should be executable G1/G2 behavior rather than adding more speculative framework.
