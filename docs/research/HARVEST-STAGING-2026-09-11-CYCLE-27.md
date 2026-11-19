# KNEEKURA TECH HUB — Harvest Staging Cycle 27

Status: **STAGING / NON-CANONICAL**  
Date: 2026-09-11

This memo records discovery candidates only. GitHub popularity was used to prioritize inspection, not as evidence of correctness. Existing main research and open Harvest PRs through Cycle 26 were checked first. Nothing below is VALIDATED, canonical, or authorized for production implementation.

## 1. Linux RCU — publish a replacement immediately, but defer reclamation until all pre-existing readers are gone

### Provenance
- Repository: `torvalds/linux`
- Repository URL: https://github.com/torvalds/linux
- Stars observed during harvest: **248,185**
- Revision: `08df884136f1c1197bab2a27814404fd329d9aac`
- Primary path: `Documentation/RCU/whatisRCU.rst`
- Pinned URL: https://github.com/torvalds/linux/blob/08df884136f1c1197bab2a27814404fd329d9aac/Documentation/RCU/whatisRCU.rst
- Relevant sections: `RCU OVERVIEW`, `synchronize_rcu()`, `call_rcu()`

### Technique
RCU explicitly splits update into **removal/publication** and **reclamation**. An updater can remove or replace a pointer so new readers can no longer acquire the old object, while readers that already observed the old object continue safely. Physical reclamation is delayed until a grace period proves that all read-side critical sections that existed before the removal have completed. Readers that start after removal do not delay reclamation because they cannot obtain the retired object.

This is distinct from tracking every consumer with an explicit reference/event. The reusable abstraction is **generation/grace-period reclamation**: retire an old generation from new discovery first, then free/recycle it only after every reader generation that could still hold it has quiesced.

### Why it may help KNEEKURA
Potential candidates include read-mostly immutable snapshots such as routing/config tables, Viewer manifests, registry snapshots, analyzer indexes, worker-directory snapshots, or other structures that are replaced wholesale while many readers continue using the prior version.

A KNEEKURA analogue might publish `generation N+1`, stop issuing new references to `N`, and keep `N` alive until all readers that began under `N` have crossed a known quiescent point. This can reduce reader-side coordination compared with taking a shared lock/refcount operation on every read.

### Limitations / uncertainty
- RCU is difficult to implement correctly; its memory-ordering details are kernel/runtime specific and must not be copied mechanically.
- It is suitable mainly for read-mostly state with clear read-side critical-section boundaries.
- Long-lived readers delay reclamation and can cause memory buildup.
- A reference must not escape its protected read-side lifetime unless an independent longer-lived ownership mechanism is acquired.
- This differs from Cycle 19 PyTorch consumer tracking: that approach records concrete asynchronous consumers; RCU instead waits for all pre-existing reader epochs to quiesce.
- Applicability is therefore **medium-high for immutable snapshot registries**, low for arbitrary mutable object graphs or authority-bearing state.

---

## 2. Git sparse-index — represent cold subtrees by one summary entry and expand only where an operation needs detail

### Provenance
- Repository: `git/git`
- Repository URL: https://github.com/git/git
- Stars observed during harvest: **63,102**
- Revision: `fa7f9290efe2bd22dd736689597b474b93798e11`
- Primary path: `Documentation/technical/sparse-index.adoc`
- Implementation anchors: `sparse-index.c`, `sparse-index.h`
- Pinned URL: https://github.com/git/git/blob/fa7f9290efe2bd22dd736689597b474b93798e11/Documentation/technical/sparse-index.adoc
- Relevant APIs/concepts: sparse-directory entries, `ensure_full_index()`, path-targeted expansion, progressive sparse-aware migration

### Technique
For repositories where HEAD contains millions of paths but only a much smaller populated subset matters to the current operation, Git avoids representing every cold file individually. An entire out-of-scope directory can be represented as one **sparse-directory entry** that points to the tree object. Detail is materialized from the tree only when a consumer actually needs paths inside that directory.

The design is also migration-safe: older/full-index assumptions are initially protected by `ensure_full_index()` guards, then commands are made sparse-aware incrementally and backed by compatibility tests. This avoids requiring every consumer to understand the compressed representation on day one.

The reusable idea is **hierarchical summary nodes plus demand expansion**, with an explicit compatibility fallback while consumers are converted.

### Why it may help KNEEKURA
Large repository/static graphs often contain huge cold regions that a particular question never touches. KNEEKURA could keep subtree summaries such as content hash, exported-symbol/fact signature, file count, language/type summary, or evidence coverage, and only materialize detailed descendants when a query crosses that boundary.

Possible targets include Static Graphs, repository viewers, dependency trees, large evidence catalogs, or Render/asset indexes. This could move some operations from total-repository scale toward the size of the actually visited working set.

A particularly useful engineering lesson is to add a **full-expansion compatibility path first**, then remove it subsystem-by-subsystem only after tests prove sparse-aware behavior. This reduces rollout risk.

### Limitations / uncertainty
- Summary entries must preserve every fact needed to decide whether expansion is necessary; an incomplete summary can hide relevant descendants.
- Repeated expand/collapse can become more expensive than retaining the full form for hot regions.
- Cross-subtree queries may still require broad expansion.
- The compressed representation increases API complexity because consumers must understand summary-versus-materialized states.
- Git's exact tree/index format is domain-specific; KNEEKURA should copy the hierarchy/lazy-materialization principle, not the file format.
- Applicability is **high for huge hierarchical indexes with small active working sets**.

---

## 3. SQLite WAL — readers pin a snapshot boundary; checkpointing advances only to the last frame safe with respect to active readers

### Provenance
- Repository: `sqlite/sqlite` (official Git mirror)
- Repository URL: https://github.com/sqlite/sqlite
- Stars observed during harvest: **10,450**
- Revision: `1eca07ed7386da8e8b927aff393f7836b5de64ba`
- Primary path: `src/wal.c`
- Pinned URL: https://github.com/sqlite/sqlite/blob/1eca07ed7386da8e8b927aff393f7836b5de64ba/src/wal.c
- Relevant sections: `READER ALGORITHM`, WAL reader marks, checkpoint `mxSafeFrame` computation

### Technique
A WAL reader records the last valid frame (`mxFrame`) when its read transaction starts and continues reading that snapshot even while later transactions append newer frames. During checkpointing, SQLite computes a safe frame boundary and does not copy WAL content into the main database past frames that may still be required by active readers. Thus compaction/checkpoint progress is constrained by the oldest relevant live snapshot, rather than assuming that old log material is reclaimable merely because newer state exists.

The reusable pattern is **snapshot-pinned compaction**: every live reader declares the historical boundary it may still need; cleanup advances only through the minimum safe point implied by those readers.

### Why it may help KNEEKURA
This could apply to append-only evidence journals, event logs, versioned artifact manifests, workflow histories, or observation streams where background compaction wants to remove/coalesce older records while readers/replayers may still be operating against an earlier snapshot.

A candidate KNEEKURA contract could track `readerSnapshotRevision` or an equivalent epoch. Compaction may summarize/delete records only through `safeRevision = min(active reader requirements, retention/governance constraints)`. Newer readers can see newer revisions without invalidating older readers mid-operation.

This is different from Cycle 12 etcd revision-aware watches. Etcd's captured idea tells a reconnecting consumer when requested history has already been compacted and therefore requires resynchronization. SQLite's candidate here is **how the compactor itself avoids crossing history still needed by active snapshots**.

### Limitations / uncertainty
- A stuck/abandoned reader can prevent compaction indefinitely unless reader leases/liveness are handled safely.
- Snapshot pinning has storage cost because old log data must remain retained.
- A reader registration must be crash-safe enough that cleanup does not incorrectly forget a still-live consumer; conversely stale registrations need conservative reclamation rules.
- SQLite's WAL/shared-memory locking is database-specific and not proposed for direct reuse.
- Applicability is **high for durable append-only histories with concurrent snapshot readers**, lower for latest-state-only telemetry.

---

## Cross-finding synthesis — hypothesis only

These findings suggest a possible non-canonical large-state lifecycle pattern:

1. keep broad hierarchical state compressed into summary nodes and expand only the region a query actually touches;
2. publish replacement immutable generations without forcing every reader to synchronize with the writer immediately;
3. retain retired generations/history until the reader population proves that older state is no longer reachable;
4. allow compaction only through the oldest still-required snapshot boundary.

This synthesis is an inference, not a validated KNEEKURA architecture. In particular, RCU-style in-memory grace periods and SQLite-style durable snapshot pins solve different lifetime domains and should not be conflated.

## Governance disposition
- Classification: **STAGING / NON-CANONICAL**
- Popularity treated as correctness evidence: **no**
- Duplicate screening against visible main/open Harvest backlog: **yes**
- Human selection performed: **no**
- VALIDATED promotion performed: **no**
- Canonical Knowledge Entity/relation created: **no**
- Production implementation performed: **no**

Next legitimate action is governed review and bounded KNEEKURA-specific validation if any candidate is selected.