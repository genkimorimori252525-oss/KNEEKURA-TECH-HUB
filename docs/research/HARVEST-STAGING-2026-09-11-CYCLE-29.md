# KNEEKURA TECH HUB Harvest Staging — Cycle 29

Status: **STAGING / NON-CANONICAL**

Date: 2026-09-11

This document records one evidence-backed harvesting pass. Popularity is used only as a discovery prior, never as validation. None of the findings below are promoted to VALIDATED or canonical knowledge, and none authorize production implementation.

## Duplicate-control note

The open Harvest backlog was reviewed through Cycle 28 before selection. The findings below were screened against recent topics including Bloom-filter negative acceleration, protected context compaction, budgeted autotuning, sparse-index/RCU/WAL snapshot pinning, lockdep/rerere/workqueue coalescing, jump labels/extension bisect/Loom, Kafka epoch fencing, field ownership, fuzz minimization, cache determinism, singleflight, async-context propagation, resource lifetime tracking, deferrable waits, generation freshness, lease/fencing patterns, and cache-fingerprint work.

---

## Candidate 1 — Ollama residency-aware model scheduling with bounded eviction and one-shot OOM recovery

### Provenance

- Repository: `ollama/ollama`
- Repository URL: https://github.com/ollama/ollama
- Stars observed during this harvest: **180,636**
- Revision inspected: `b68b112bd8868d6278250d7d4bdfafa5cbf035c8`
- Primary file: `server/sched.go`
- Primary URL: https://github.com/ollama/ollama/blob/b68b112bd8868d6278250d7d4bdfafa5cbf035c8/server/sched.go
- Relevant sections: `Scheduler`, `processPending`, `findRunnerToUnload`, `evictAllAndWait`, `runnerRef` expiry/ref-count handling

### Technique

Ollama treats loaded model runners as a managed residency set rather than as processes that are either simply present or absent. The scheduler keeps explicit state for loaded runners, enforces a bounded number of resident models, refreshes GPU/system information before new placement decisions, updates free-space estimates from currently loaded models, and tests whether a requested model can coexist with the current resident set before loading it.

A loaded runner is reused when it is compatible with the request. When space is needed, a runner is selected for expiration. The scheduler does not blindly tear down a runner that still has active users: expiration interacts with a runner reference count, and a runner whose `refCount` is still positive is marked to expire rather than immediately treated as reusable space.

The inspected revision also contains a bounded OOM recovery path. If loading crashes in a way interpreted as an out-of-memory condition while other models are resident, the scheduler can evict the other resident runners, wait for the unloads to complete, and retry the requested load once. An explicit `oomRetryAttempted` flag prevents that recovery path from becoming an infinite eviction/retry loop.

The reusable pattern is therefore:

1. model expensive resources as a residency set with explicit ownership/state,
2. reuse compatible residents before loading duplicates,
3. refresh real capacity information before placement,
4. evict only through a lifecycle that respects active references,
5. wait for physical unload before assuming capacity has returned,
6. allow a narrowly bounded recovery retry for transient placement failure,
7. record that retry so persistent failures fail rather than loop forever.

### Why this may be useful to KNEEKURA

KNEEKURA increasingly has local-model and GPU-sensitive workloads: local LLM workers, TTS, render/vision jobs, embedding/indexing processes, and potentially multiple execution tiers sharing one PC. A residency manager could keep frequently used models warm without letting every caller independently spawn a model process and overcommit VRAM.

Potential applications include:

- STANDARD/HEAVY local-model routing,
- TTS model residency and controlled handoff,
- GPU render-worker reuse,
- keeping one hot model alive for a bounded idle window,
- evicting idle residents when a higher-priority model must fit,
- waiting for confirmed unload before launching a replacement,
- one-shot recovery when a placement estimate proves too optimistic.

The strongest transferable idea is not Ollama's exact model-count heuristic. It is the explicit distinction between **logical eviction request**, **active references**, and **physical capacity actually returned**.

### Limitations / risks

- Ollama's concrete model-per-GPU defaults and placement assumptions are product-specific and should not be copied directly.
- VRAM estimation can still be wrong because allocator fragmentation, context size, backend behavior, and non-model GPU consumers can change real capacity.
- Eviction can cause latency spikes if the scheduler repeatedly unloads and reloads large models.
- A reference count protects active users only if all users participate correctly in the ownership protocol.
- A one-shot OOM retry is safer than an unbounded loop, but repeated OOMs still need clear failure evidence rather than silent degradation.
- KNEEKURA would need priority/fairness rules so a long-lived warm model cannot starve more important work.

### Applicability

Best fit: expensive reusable workers whose startup cost is high and whose memory footprint must be coordinated globally.

Poor fit: cheap stateless processes, resources with negligible warm-start value, or systems where exact capacity cannot be observed well enough to make residency decisions useful.

### Uncertainty

The current Ollama scheduler is evolving quickly. The useful harvest is the lifecycle contract around residency, references, capacity refresh, unload completion, and bounded recovery—not a claim that Ollama's present heuristic is optimal for KNEEKURA.

---

## Candidate 2 — Terraform lineage + serial state identity to reject stale or unrelated destructive writes

### Provenance

- Repository: `hashicorp/terraform`
- Repository URL: https://github.com/hashicorp/terraform
- Stars observed during this harvest: **49,635**
- Revision inspected: `799c8d896356c5e9623b8545d0c1d20187f27f7c`
- Primary file: `internal/states/statefile/file.go`
- Primary URL: https://github.com/hashicorp/terraform/blob/799c8d896356c5e9623b8545d0c1d20187f27f7c/internal/states/statefile/file.go
- Validation logic: `internal/states/statemgr/migrate.go`
- Validation URL: https://github.com/hashicorp/terraform/blob/799c8d896356c5e9623b8545d0c1d20187f27f7c/internal/states/statemgr/migrate.go
- Relevant sections: `File.Serial`, `File.Lineage`, `SnapshotMeta.Compare`, `CheckValidImport`

### Technique

Terraform state carries two different pieces of identity metadata:

- `Lineage`: minted for a new state lineage and then kept stable, so snapshots from unrelated histories are not accidentally compared as if they were versions of the same state.
- `Serial`: incremented as that state changes, so snapshots within one lineage can be ordered.

`SnapshotMeta.Compare` classifies two snapshots as newer, older, equal, unrelated, or legacy. `CheckValidImport` then refuses unsafe state replacement unless explicitly forced: it rejects an unrelated lineage, rejects an older serial over a newer serial, and even rejects a different payload that claims the exact same lineage and serial. A same-lineage/same-serial write is accepted only if the serialized states are equal.

The reusable pattern is stronger than a simple version counter:

1. assign a stable lineage identity to a state history,
2. assign a monotonic revision within that lineage,
3. compare lineage before revision,
4. reject writes from unrelated histories even if their numeric revision looks newer,
5. reject stale revisions,
6. reject same-revision/different-content anomalies,
7. make any bypass an explicit exceptional operation rather than the normal path.

### Why this may be useful to KNEEKURA

KNEEKURA has several places where a numeric generation alone may be insufficient: workflow snapshots, knowledge-store snapshots, workspace state, generated indexes, runner coordination state, and derived artifact manifests.

A `lineage + serial + content identity` contract could prevent failures such as:

- restoring an old workspace snapshot over newer state,
- importing a snapshot from another project because its revision number happens to be larger,
- accepting two different payloads that both claim to be revision 42,
- resuming a workflow against state that came from a different reset/reinitialization lineage,
- confusing a newly-created repository/index with an older incarnation that reused the same local path.

This complements Cycle 24 Kafka-style epoch fencing. Fencing rejects writes from an obsolete active owner; Terraform's pattern verifies that a durable state snapshot actually belongs to the same history and is a valid successor.

### Limitations / risks

- Lineage is identity metadata, not proof that the state itself is correct.
- Serial monotonicity must be enforced consistently; multiple independent writers cannot safely invent serials without coordination.
- Force/bypass operations can defeat the protection and therefore need strong audit/governance treatment.
- Legacy states without lineage reduce the strength of the check.
- KNEEKURA may need a cryptographic content digest in addition to lineage/serial when exact payload identity matters across systems.
- This does not replace locking or transactional persistence; Terraform's own migration comments explicitly note that callers still need locks where supported.

### Applicability

Best fit: durable snapshots that evolve as one logical history and may be imported, restored, migrated, or written by more than one process over time.

Poor fit: ephemeral immutable artifacts already addressed purely by content hash, or append-only event streams where replacement is not an operation.

### Uncertainty

KNEEKURA has multiple state domains with different authority models, so one global lineage counter would probably be too coarse. The pattern likely needs separate lineage domains for workflows, indexes, knowledge snapshots, and other independently resettable state.

---

## Candidate 3 — containerd lease-rooted garbage collection for temporary-but-still-live resources

### Provenance

- Repository: `containerd/containerd`
- Repository URL: https://github.com/containerd/containerd
- Stars observed during this harvest: **21,283**
- Revision inspected: `f6132dbe1f482cbe0aebc4bd3d8d7a184fb4a2aa`
- Primary documentation: `docs/garbage-collection.md`
- Primary URL: https://github.com/containerd/containerd/blob/f6132dbe1f482cbe0aebc4bd3d8d7a184fb4a2aa/docs/garbage-collection.md
- API definition: `api/services/leases/v1/leases.proto`
- API URL: https://github.com/containerd/containerd/blob/f6132dbe1f482cbe0aebc4bd3d8d7a184fb4a2aa/api/services/leases/v1/leases.proto

### Technique

containerd performs strict garbage collection: a resource that is neither otherwise referenced nor held by a lease is eligible for collection. A lease is an explicit temporary root that says a snapshot/content resource may still be needed even when no permanent object currently references it.

The caller owns lease lifecycle. A lease can be tied to an operation/context, given an expiration as a crash-safety backstop, or deleted deliberately when the operation finishes. Resources can also describe reference edges with GC labels, allowing the collector to traverse from roots to dependent content rather than treating every blob independently.

The reusable pattern is:

1. make garbage collection aggressive by default,
2. require temporary users to declare liveness explicitly,
3. root all intermediate resources created by a live operation under a lease,
4. allow lease expiration to recover from crashed clients that never clean up,
5. maintain explicit dependency edges so retaining a root also retains required descendants,
6. delete the lease when the operation is truly finished, making the temporary graph collectible.

This reverses the common cleanup model. Instead of asking "which old temp files should we delete?", the system asks "which resources have an active durable reason to stay?" and treats everything else as collectible.

### Why this may be useful to KNEEKURA

KNEEKURA generates many intermediate artifacts that can outlive a single function call but should not become permanent storage: cloned repositories, extracted indexes, render packs under construction, downloaded model shards, temporary evidence bundles, screenshots, generated fixtures, and multi-step workflow outputs.

A lease-rooted artifact store could let a workflow say:

`workflow/operation lease -> artifact A -> derived B -> derived C`

As long as the lease is active, GC must preserve that graph. Once the workflow commits the final artifact or abandons the operation, the lease disappears and unreachable intermediates become eligible for collection.

Potential benefits:

- safe cleanup after crashes,
- fewer ad-hoc `finally { delete temp }` paths,
- explicit provenance between an operation and the temporary resources it owns,
- protection against deleting an intermediate artifact while a later step still needs it,
- bounded retention through expirations when a client dies without cleanup.

This differs from Cycle 27 RCU/WAL lifetime findings. Those protect data from reclamation while readers of a known generation remain active. containerd leases are a broader client-declared liveness root for resources that may not currently have any permanent reference at all.

### Limitations / risks

- A forgotten non-expiring lease creates storage leaks.
- An expiry that is too short can collect resources during a legitimately long operation.
- Lease renewal after process/network pauses needs carefully defined ownership and fencing so stale clients cannot indefinitely extend abandoned work.
- Reference graphs must be accurate; missing an edge can make a required descendant collectible.
- A lease proves liveness intent, not artifact correctness or governance status.
- Sensitive evidence may need retention rules stronger than ordinary GC liveness, including immutable audit retention independent of a workflow lease.

### Applicability

Best fit: temporary or intermediate artifacts shared across asynchronous/multi-step work where process lifetime is shorter than artifact lifetime.

Poor fit: canonical evidence and records subject to explicit long-term retention, or tiny short-lived temp data already safely scoped to one process.

### Uncertainty

The containerd design is optimized for content/snapshot graphs, while KNEEKURA has heterogeneous files, DB rows, model caches, and evidence objects. A future implementation would need a small common resource identity/reference model before lease-rooted GC would be safe.

---

## Cross-finding synthesis candidate — identity, liveness, and residency as separate contracts

A useful higher-level distinction emerges from the three findings:

1. **Terraform-style state identity** answers: "Is this snapshot actually a successor in the same history?"
2. **containerd-style leases** answer: "Does some live operation still have a declared reason for this resource to exist?"
3. **Ollama-style residency management** answers: "Should this expensive live resource remain physically loaded right now, and when has its capacity actually been returned?"

These are three different questions and should not be collapsed into one generic `active=true` flag.

A future KNEEKURA resource/state protocol could therefore model:

`lineage/revision identity -> operation lease/liveness -> physical residency/refcount`

For example, a local-model artifact can belong to a verified model lineage, be protected by a workflow lease while work is pending, and still be unloaded from VRAM when not actively referenced. Conversely, unloading it from VRAM must not imply that the durable artifact is garbage, and an active lease must not imply that a stale state revision is valid.

This synthesis is a new inference made during harvesting. It has no independent validation and must not be treated as canonical architecture.

## Governance disposition

- Discovery: completed for this cycle.
- Provenance: captured at exact revisions above.
- Duplicate screening: performed against open Harvest backlog through Cycle 28.
- Status: **STAGING / NON-CANONICAL**.
- Human selection: not performed.
- VALIDATED promotion: not performed.
- Canonical Knowledge Entity creation: not performed.
- Production implementation: not authorized or performed.
