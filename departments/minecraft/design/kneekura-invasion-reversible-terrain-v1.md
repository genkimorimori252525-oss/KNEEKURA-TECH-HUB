# KNEEKURA Invasion MOD — Reversible Siege Terrain v1 (RESEARCH DESIGN, not implementation)

Date: 2026-10-11  
Target: Minecraft **1.20.1 + Forge**  
Purpose: future **Nexus/tower-defense style invasion** where attacker mobs can alter terrain tactically, but invasion-owned damage and scaffolds vanish/revert later without corrupting the defended world's authored buildings.

**Status: DESIGN_ONLY.** No code written, compiled or run for KNEEKURA Invasion. Source-backed lessons are under [../mods/epic-mob-siege-nightmare/](../mods/epic-mob-siege-nightmare/). Existing KNEEKURA [Minecraft current handoff](../CURRENT-HANDOFF-2026-10-02.md) and [bounded LAB reset contract](../lab/docs/KNEEKURA_BOUNDED_ARENA_SOURCE_SLICE.md) remain authoritative; the LAB reset only proves bounded controlled-world restoration, not full persistent production-world rollback.

## 0. Two invariant families

### Combat / tower defense

- Defend a **Nexus/core** against escalating waves of attackers with distinct roles; avoid turning every mob into the same behavioral template.
- Tactical tools are **BREACH, PILLAR, BRIDGE, LADDER, TUNNEL, SIEGE_PROJECTILE, REPATH**; roles differ in cost/eligibility/speed and the current objective.
- Normal traversable paths are preferred when they are cheaper. Mobs cooperate and share reservations: one wall-breaking worker can be supported by escorts.
- Action planner/AI is swappable: historical Invasion Mod style explicit action edges and modern ZBB reactive stuck tactics remain separate donor strategies.

### Terrain permanence

1. **Every invasion-owned mutation within approved scope is journaled *before* mutation**, including blockstate and supported block entity NBT. A mutation without durable journal approval **must not execute**.
2. Built scaffold/towers/bridges are removed at configurable time or encounter teardown; destroyed original blocks are reconstructed at **the same original coordinates**. These two classes are independently controllable.
3. Changes unrelated to the invasion, especially player construction, must not be overwritten silently. Record a **CONFLICT** and apply a disclosed resolution rule.
4. No item duplication: temporary breaking/restoration normally suppresses block/BlockEntity drops and cancels demolition methods that would emit uncontrolled inventory drops.
5. Everything is server-authoritative; no player network packet supplies privileged original snapshots, block edit authority or delete/recover triggers.
6. Exact rollback guarantee is confined to **eligible, managed region cells**. Unsupported storage/physics/modded blocks must be rejected or their destruction disabled. Never market all of Minecraft as fully reversible.
7. Pending recovery may survive server restart. Unloaded chunk does not justify forced chunk loading or deletion of the journal.
8. Server must not silently continue unlimited terrain editing after journal corruption, persistence failure, conflict storm or budget exhaustion: **fail closed** and notify.

## 1. Architecture — independent bounded services

```text
InvasionDirector (Nexus, waves, team/roles)
       |
       v
PathDecisionAdapter --- normal path / action-augmented path / tactical fallback
       |
       v
TerrainActionArbitrator
   candidate BRIDGE / PILLAR / BREAK / TUNNEL
   cost + protection + chunk + collision + reservation
       |
       v
EncounterTerrainEditService (the only write authority)
   ├─ RegionPolicy / Ownership / PerCellReservations
   ├─ BeforeImageJournal (dimension + pos + original state/NBT)
   ├─ DurableWriteAhead (PREPARED → COMMITTED)
   ├─ WorldMutationExecutor (main server thread)
   ├─ LootAndPhysicsPolicy / protected block adapter
   └─ SnapshotObserver / mutation evidence
       |
       v
ExpirationScheduler (per-dimension, chunk bucket, due-time heap)
   ├─ RESTORE_ORIGINAL
   ├─ REMOVE_TEMP_BUILD
   ├─ CONFLICT / RETRY / BLOCKED
   └─ ReplayAndReconcile (server startup, normal chunk load)
```

No global `//undo`, no whole-world timestamp rewind and no arbitrary fake-player actions by default.

## 2. Data contract (proposed)

One durable per-cell **first-write before-image** + per-encounter layered mutations and generation ID:

```text
mutationId: UUID
encounterId: UUID
actorId: UUID | invasion-effect ID
dimension: ResourceKey<Level>
pos: BlockPos
baseline: { BlockState, BlockEntityNBT?, blockType, originalFingerprint }
expectedCurrent: { BlockState, generation, lastMutationId }
kind: TEMP_PLACED | TEMP_BROKEN | TRANSFORMED_BY_INVASION
createdAtGameTick; dueAtGameTick
scope: {NexusId, approvedRegionId, chunk, allowedMaterialClass}
transaction: PREPARED | APPLIED | REVERT_PENDING | REVERTED | CONFLICT | RETRY
ownerRevision, journalDigest, rollbackReceipt
```

Do not key solely by `BlockPos`; dimension and encounter ownership are required. The **first** write to a cell preserves baseline exactly once; later invasion edits form an ordered overlay linked to that baseline. Reverted temporary blocks must reveal the original state only when no later authorized temporary action owns the cell.

Inventory/NBT support is **opt-in by block-type capability**; an ordinary cobblestone/stone-only prototype can safely exclude block entities entirely. Double blocks (doors/beds), redstone, signs, containers, fluids, falling blocks and scheduled ticks need explicit compound acceptance or initial denial.

## 3. Mutation protocol

### A. Planning

- Validate active Nexus encounter, actor role, eligible loaded chunk, block bounds, protection mod policies (native Forge events + explicit integration), safe type allow/deny list, server performance budget and per-cell reservation.
- Fetch current baseline state *before* any block removal. Cache after approval only inside correct dimension and generation.
- Simulate geometry for collision support: no scaffold inside protected occupied space or player head; allow block reach/path re-evaluation.

### B. Write-ahead entry

- Write `PREPARED` record to a **durably flushed bounded journal** / transactional file before editing. Storing only in ordinary Minecraft `SavedData` and waiting for autosave cannot guarantee power-loss consistency.
- Re-read expected block + permission before applying; abort if another source changed it.
- On main server thread execute the single approved mutation via safe edit adapter; verify post-state; persist `APPLIED` / outcome with receipt. If outcome is uncertain, reconcile on next start rather than blindly rerun.
- For explosion-like attacks, capture the approved affected-cell set *before* applying and disallow uncontrolled cascades or non-managed damage. If effects cannot be bounded/reverted, replace with non-terrain-damaging visual/collision gameplay.

### C. Cleanup

- Process expiration in loaded chunks and bounded budget per tick.
- If cell still matches an invasion-owned expected revision, restore **original** state/NBT at its original coordinate, suppress unintended drops and schedule safe neighbor updates; record/verify receipt.
- If occupied by an unrelated player placement, mark `CONFLICT`; do not overwrite the player's work, delete state or 'give back' blocks as a substitute for terrain restoration.
- If a temporary block is a support under an entity, defer removal briefly or use a controlled, non-destructive fail-safe; no forced suffocation/fall cascade due to cleanup.
- Keep pending records if chunk unloaded; retry on normal load under bounded scheduling. Do not force load an unlimited world.
- On restart scan incomplete PREPARED/APPLIED/revert records, check actual world state, and determine **NO_ACTION, APPLY_CONFIRM, REVERT, CONFLICT** idempotently.
- On encounter cancellation, death, Nexus victory/loss or admin stop, use the **same** scheduler with higher priority rather than bypassing invariants.

### D. Provenance and conflicts

If player intentionally modifies a previously damaged cell after a battle, two goals conflict: "exact pre-battle world" versus "preserve post-battle edits". This v1 chooses **preserve third-party edits; flag exact restoration as pending**, with admin-preview/retry options; no silent overwrites. Later UX could offer region-specific negotiated policy, but a hidden auto-overwrite default is forbidden.

## 4. Performance model and safety budgets

Values here are **future configurable design parameters**, not observed or universal constants:

- `maxConcurrentEncounters`, `maxMutatedCellsPerEncounter`, `maxCellsPerActor`, `maxActiveAttackers`.
- `maxPathCandidatesPerTick`, `maxBlockBreakAttemptsPerTick`, `maxPendingRestoresPerTick`.
- A tick-ordered expiration index per dimension with chunk buckets; no full-world scan.
- Replay/restoration must be monotonic, observable and interruptible under server load; no uncontrolled force-chunk-tickets.
- Metrics: `p95PlanningMs`, `p95MutationMs`, `p95RestoreMs`, `pendingDirtyCells`, `staleJournalEntries`, `conflictsByReason`, `recoveredAfterRestart`, real TPS, world size and NBT bytes.
- Attackers plan against predicted costs and stable generation IDs; stale plans get invalidated on block changes.
- Redstone/fluid/neighbor secondary effects are **out of guarantee** unless explicitly recorded/captured. v1 should disable unsupported terrain effects by attack policy.

## 5. Staged roadmap (order locked by validation, not dates)

**Phase A — Source/binary & references**  
Obtain `NESM-1.20.1-1.0.1.jar` exact SHA and bytecode; examine mining/placement and target/stuck tactics. Validate JujutsuCraft 50.1 domain teardown *separately* rather than importing unproven semantics. Compare 1.20.1 ZBB (pin `73a80226...`) with 1.7.10 Invasion Mod path actions.

**Phase B — Deterministic journal kernel**  
Independent pure-Java reference model and unit tests for first-write capture, layered per-cell mutations, TTL ordering, reentrant saves, conflict matrix, journal failure and replay idempotence. *No mod gameplay until this passes.*

**Phase C — Forge world adapter**  
Disposable 1.20.1 test world. Stone/glass/air eligible subset, non-BlockEntity and no fluids; one zombie and one Nexus. World writes through `EncounterTerrainEditService` only. Demonstrate original location restore vs temporary bridge disappearance.

**Phase D — Tactical AI**  
Stuck detector + candidate `BREAK/BRIDGE/PILLAR`; upgrade to action-augmented path cost for engineer roles as measured. Add per-cell reservations and multi-actor coordinator.

**Phase E — Compound terrain and attacks**  
Doors, beds, fluids, fallers, TNT/creepers, claims, tile entities, chunk boundaries; each either has fully proven replay or remains explicitly forbidden.

**Phase F — Siege game integration**  
Wave Director, role classes, defendable Nexus, progression, TD economy, UX for construction expiration and visual repair, with strict separation of AI, combat, world rollback.

**Phase G — Evidence gates / release candidate**  
Dedicated server, two clients, repeated saves, forced crash injection, world rollback readback, TPS and packet tests, restart with unloaded chunks, third-party protected region behavior. No published 'complete restoration' claim until recorded acceptance.

## 6. LAB verification matrix

| Test ID | Required observations | Pass condition |
|---|---|---|
| T01 | Destroy ordinary original stone then wait TTL | exact blockstate at exact cell restored; no loot clone |
| T02 | Build a 10-block pillar/bridge then wait TTL | all temporary blocks gone without deleting pre-existing blocks |
| T03 | One cell broken / built / broken by two actors | first baseline restored once; no duplicate mutation |
| T04 | Server crash immediately after journal PREPARED | recovery idempotent; no unaudited lost original |
| T05 | Server crash immediately after APPLIED | recovery idempotent; original state restored when safe |
| T06 | Player edits conflict cell | no overwrite; persistent visible conflict and explicit admin resolution |
| T07 | Temporarily unload target chunk | no forced loads; queued restore occurs when chunk naturally loads |
| T08 | Multi-block door / water / sand / chest | either exact restore with NBT/protocol proof **or mutation denied** |
| T09 | protected claim and `mobGriefing` policy | no bypass; test against real owner/claims implementations |
| T10 | 1 / 10 / 50 / 100 attackers, repeated waves | measured bounded CPU/TPS/memory and no stuck writes |
| T11 | 2 clients, dedicated Forge server | all edits and restoration server authoritative; no unauthorized edit packet |
| T12 | water tank cleanup and experiment restoration | LAB receipt complete, no leakage to non-disposable world |

Every case needs exact source revisions, release artifact hashes, environment, state snapshots, side-effect inventory, world hashes, cleanup receipts and independently reviewed statuses **PASS / FAIL / INCONCLUSIVE / NOT_RUN**. All currently NOT_RUN.

## 7. Source inventory / reuse constraints

- [Epic Mob Siege: Nightmare CurseForge 1.0.1](https://www.curseforge.com/minecraft/mc-mods/epic-mob-siege-nightmare/files/7273546) — gameplay description, ARR port, no exact artifact yet.
- [XTiK555/ZombieBreakAndBuild 1.20.1](https://github.com/XTiK555/ZombieBreakAndBuild/tree/73a8022609d2d1554d0c1a89406dc97f7ed8aa3) — source-backed independent tactical/build/restore patterns, LGPL-3.0; do not copy code absent compliance review.
- [Doenerstyle/Invasion-Mod legacy](https://github.com/Doenerstyle/Invasion-Mod/tree/0bccc286114ffae9f9224892ab1fe451fc97ef08) — legacy action nodes/engineer planner.
- [AMPerez04/MineZero Forge 1.20.1](https://github.com/AMPerez04/MineZero/tree/84084b48e2dc5141e821177f53f8c29563a03093) — checkpoint/BlockEntity NBT comparison, not in-game invasion rollback.
- [WorldEdit history docs](https://worldedit.enginehub.org/en/latest/usage/general/history/) — undo indirect-effects limitation.
- [JujutsuCraft 50.1](https://www.curseforge.com/minecraft/mc-mods/sorceryfight) and [JJCV addon changelog](https://www.curseforge.com/minecraft/mc-mods/jujutsu-craft-v/files/6973339) — domain teardown inspiration, **not** code/bytecode-confirmed general restoration.

All techniques must be independently implemented, with source provenance and explicit permissions review. This design is not an implementation task executed in this PR.
