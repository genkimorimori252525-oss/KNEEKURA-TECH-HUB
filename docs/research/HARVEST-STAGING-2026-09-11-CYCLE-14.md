# KNEEKURA TECH HUB — Harvest Staging Cycle 14

Status: **STAGING / NON-CANONICAL**
Date: 2026-09-11

This memo records discovery candidates only. GitHub stars were used as an exploration-order signal, never as evidence of correctness. No item below is VALIDATED, canonical, or approved for implementation. Thresholds and heuristics from source projects are not assumed transferable without local evidence.

## Duplicate check

Cycle 14 was screened against the previously harvested themes known through Cycles 01–13. Findings that merely repeated lease scheduling, single-flight, priority/admission gates, hierarchical circuit breakers, cooperative budgets, generation replacement, immutable activation, revision watches, worker multiplexing, sequence counters, rate limiting, or prior crash-evidence patterns were excluded.

## Finding 14-A — Observe resource reclamation convergence before reusing capacity

- Repository: `ollama/ollama`
- Repository popularity at discovery: ~180.6k GitHub stars (ordering signal only)
- Revision: `c951dabec40c9ad31fa14ae6ae1a8d15b1b5fb2f`
- File blob: `c1a95c3399f6bcdaee22254a14fd44ae0900b26e`
- Path: `server/sched.go`
- Sections/functions: `waitForVRAMRecovery`, `updateFreeSpace`, `load`, `availableMemoryForPlacement`
- URL: https://github.com/ollama/ollama/blob/c951dabec40c9ad31fa14ae6ae1a8d15b1b5fb2f/server/sched.go

### Technique

Ollama does not assume that terminating a model runner immediately makes its reported VRAM reusable. Before unloading, it captures a GPU-memory baseline, then polls for free-memory recovery and waits for observed convergence before allowing the scheduler to proceed. The implementation treats roughly 75% recovery of the runner's estimated VRAM as sufficient and bounds the wait with a timeout. Separately, when GPU telemetry and Ollama's own accounting disagree, `updateFreeSpace` uses the smaller free-memory estimate when its known-runner prediction is more conservative.

The same scheduler also performs pre-flight VRAM prediction before spawning another model and bounds OOM recovery: automatically derived context/batch settings may be reduced and retried, or other runners evicted, but retry state prevents an unbounded OOM loop.

### Why it may be useful

A process exit is an event, not necessarily proof that an asynchronously managed resource has converged to a reusable state. GPU drivers, filesystem cleanup, network leases, subprocess trees, and external runtimes may lag. KNEEKURA could distinguish `owner exited` from `capacity observed reusable`, reducing false capacity decisions during LLM/TTS/model-host transitions.

### Applicability

Potentially useful for model runners, TTS/LLM switching, GPU-backed viewers, large memory-mapped assets, or other resources whose release is externally observable but not instantaneous.

### Limitations / uncertainty

The 250 ms polling interval, 5 s recovery timeout, ~75% recovery threshold, and 80% fit headroom visible in this revision are Ollama-specific heuristics, not transferable constants. CPU, Metal, and integrated-GPU paths differ. Internal memory prediction can also be wrong, and unrelated GPU applications can invalidate an internal-only model. KNEEKURA would need hardware-specific measurements before adopting any threshold.

## Finding 14-B — Crash-loop budget with contextual attribution before auto-restart

- Repository: `microsoft/vscode`
- Repository popularity at discovery: ~191.5k GitHub stars (ordering signal only)
- Revision: `deb09014775f6ca2e73ffd0c7e0b0331aeefd242`
- File blob: `514873c2d59e4e43249c7f19d227c4165456268a`
- Path: `src/vs/workbench/services/extensions/common/abstractExtensionService.ts`
- Sections/classes: `_onRemoteExtensionHostCrashed`, `_logExtensionHostCrash`, `ExtensionHostCrashTracker`
- URL: https://github.com/microsoft/vscode/blob/deb09014775f6ca2e73ffd0c7e0b0331aeefd242/src/vs/workbench/services/extensions/common/abstractExtensionService.ts

### Technique

VS Code isolates extension execution behind extension hosts and treats repeated host crashes differently from isolated crashes. `ExtensionHostCrashTracker` keeps only crashes from a rolling five-minute window. A remote extension host may be restarted automatically while the recent crash count remains below the configured limit; after repeated crashes, automatic restart stops and the system surfaces the condition instead of entering a permanent restart loop. Before/around that recovery path, `_logExtensionHostCrash` records which extensions had actually begun activation in the crashed host, preserving useful attribution rather than only reporting a process exit code.

### Why it may be useful

Self-healing becomes dangerous when the failure is deterministic: an unconditional restart loop can consume CPU, flood logs, repeatedly mutate state, or hide the original defect. A time-windowed restart budget converts repeated failure into a different operational state. Capturing the active workload set at failure time also makes the breaker diagnosable.

### Applicability

Potential fit for KNEEKURA plugin hosts, local workers, browser/command bridges, Minecraft observation helpers, AI model workers, and any restartable subprocess boundary.

### Limitations / uncertainty

VS Code's three-crashes/five-minutes policy is product-specific. A KNEEKURA worker handling destructive or externally visible operations may require zero automatic retries unless idempotency is proven. Conversely, stateless workers may tolerate more. Host-level attribution identifies what was running but does not prove which extension caused the crash. This should therefore remain evidence, not blame assignment.

## Finding 14-C — Tune from an immutable runtime snapshot, then commit only within fresh resource authority

- Repository: `tensorflow/tensorflow`
- Repository popularity at discovery: ~199.3k GitHub stars (ordering signal only)
- Revision: `528790339f17f91050e1de913635f502b40177c4`
- File blob: `286ed2bcb87e1cd66141f6bd5d1ff1d49fc9d09b`
- Path: `tensorflow/core/framework/model.cc`
- Sections/functions: `Model::Optimize`, `Node::Snapshot`, `Model::OptimizeStageBased*`, `Model::OptimizeHillClimbHelper`, `RamBudgetManager::RequestModelAllocation` usage
- URL: https://github.com/tensorflow/tensorflow/blob/528790339f17f91050e1de913635f502b40177c4/tensorflow/core/framework/model.cc

### Technique

TensorFlow `tf.data` autotuning first snapshots the live pipeline model and explores tunable parallelism/buffer parameters on that snapshot instead of directly mutating live state throughout the search. Stage-based tuning prioritizes the currently slowest stage, tentatively increments parallelism, recomputes timing, and rolls the tentative change back if it does not improve the critical stage. RAM-budget checks can abort an optimization before publishing parameter state. Importantly, the code performs a final `RamBudgetManager::RequestModelAllocation(...)` before `UpdateStateValues(...)`, with an explicit comment that an earlier RAM-budget snapshot may already be stale.

### Why it may be useful

This separates three actions that are often mistakenly collapsed: `observe current system`, `simulate/propose a better configuration`, and `publish the change`. Re-checking resource authority at commit time protects against a concurrent actor consuming the capacity that was available when planning began. Rejecting non-improving tentative moves also turns auto-tuning into evidence-driven change rather than monotonic "more parallelism is better" behavior.

### Applicability

Potential fit for KNEEKURA worker-count tuning, batch sizes, evidence-ingestion parallelism, scanner concurrency, buffer sizing, model context/batch tuning, and other runtime knobs where a proposed optimization can be evaluated before activation.

### Limitations / uncertainty

TensorFlow's analytical timing model and RAM estimators are domain-specific and include explicit assumptions/TODOs. A snapshot can become stale, which is exactly why the final allocation check matters; even so, resource admission alone does not guarantee the proposed setting remains performance-optimal. KNEEKURA would need its own objective function, workload measurements, rollback criteria, and authority gate. This is a control-pattern candidate, not an endorsement of TensorFlow's formulas or constants.

## Cross-finding synthesis (non-canonical hypothesis)

A reusable safety pattern suggested by these independent systems is:

1. **Plan against a snapshot rather than mutate while exploring.**
2. **Re-check scarce-resource authority immediately before activation.**
3. **After releasing scarce resources, observe convergence instead of trusting the release command alone.**
4. **If activation repeatedly fails, consume a bounded recovery budget and escalate rather than loop forever.**
5. **Preserve contextual evidence about what was active when recovery was triggered.**

This synthesis is an inference produced during harvesting. It is not directly asserted by any one source and is therefore especially non-canonical pending independent review/testing.

## Governance disposition

- Discovery only: yes
- Evidence/provenance captured: yes
- Human selection performed: no
- VALIDATED promotion: no
- Canonical Knowledge Entity creation: no
- Automatic implementation into KNEEKURA products: no

Next governed action, if selected later: independently reproduce the relevant behavior, define KNEEKURA-specific invariants/thresholds, then pass the existing support/validation gates before any canonical promotion.