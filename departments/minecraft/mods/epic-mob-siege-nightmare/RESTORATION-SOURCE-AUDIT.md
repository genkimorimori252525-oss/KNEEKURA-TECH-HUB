# Primary source audit — time-based undo of zombies' terrain edits

**Direct code basis:** [XTiK555/ZombieBreakAndBuild pinned 1.20.1 source `73a8022609d2d1554d0c1a89406dc97f7ed8aa3`](https://github.com/XTiK555/ZombieBreakAndBuild/tree/73a8022609d2d1554d0c1a89406dc97f7ed8aa3), LGPL-3.0, not the Epic Mob Siege release JAR. This is an actual related-system implementation, not an assumed Epic internal feature.

## Exact code flow observed

**Build path**
1. `BuildAction.canExecute` tests cooldown, chunk loaded, allowed mob and destination replaceability.
2. `BuildAction.execute` saves previous `BlockState` and optional block-entity NBT, sets temporary state, emits successful-placement event.
3. `BuildDisappearBlockStorageManager` registers a `BuildDisappearBlockStorageEntry(placedState, oldState, oldNbt)` if `builtBlocksDisappearing` config true.
4. Expiration tries to restore old state/NBT if current block matches the original temporary block *type* or is air. If restoration fails, postpones the stored record. Unexpected other block type generally is not overwritten.

**Break path**
1. `BreakAction.canExecute` checks cooldown, chunk present, stored build-protection guard, non-air block, hardness/unbreakability.
2. `BreakAction.execute` computes total partial damage; on threshold, emits **about-to-break** event, then `level.destroyBlock(pos, dropLoot)` and success/failure event. When auto-restore is enabled, it sets `dropLoot=false`, avoiding basic block-loot duplication.
3. `BrokenReappearBlockStorageManager` snapshots block state and block-entity NBT *before* breaking into a pending entry, and commits it on successful mutation (or restores NBT on failed break).
4. Expiration restores at original cell if it can be replaced, or removes a temporary zombie build at that cell first.
5. If collision prevents restoration, the source attempts **item drop → nearest player inventory/drop → adjacent placement**, otherwise extends the expiration record. These fallbacks preserve some resources but **do not guarantee exact spatial restoration**.

**Time and durability**
- `PersistentExpiringBlockStorage` persists `pos`, `stored_at` tick and typed state using a `SavedData` and Minecraft `Codec` in each `ServerLevel`.
- `ExpirationIndex` uses tick-ordered buckets, avoiding an every-tick full map scan of all recorded changes.
- `MainCommon.onLevelTickPost` processes damaged, protected, broken/restoration and built/disappear stores using configurable durations.
- `BrokenReappearBlockStorage` emits a 'will restore' notice 16 ticks before expiration.
- Code also tracks falling-block migration to preserve linked records on landing, with `FallingBlockStorageTracker` and `FallingBlockEntityMixin`.
- Java code **is not proof** that crash interrupts after successful world mutation but before save have no data loss. `SavedData` normally persists on Minecraft saves; there is no confirmed write-through WAL durability for every prior-world-change at this layer.

Primary links:
- [BreakAction.java](https://github.com/XTiK555/ZombieBreakAndBuild/blob/73a8022609d2d1554d0c1a89406dc97f7ed8aa3/common/src/main/java/com/tik/zbb/ai/action/actions/breakk/BreakAction.java)
- [BuildAction.java](https://github.com/XTiK555/ZombieBreakAndBuild/blob/73a8022609d2d1554d0c1a89406dc97f7ed8aa3/common/src/main/java/com/tik/zbb/ai/action/actions/build/BuildAction.java)
- [BrokenReappearBlockStorageManager.java](https://github.com/XTiK555/ZombieBreakAndBuild/blob/73a8022609d2d1554d0c1a89406dc97f7ed8aa3/common/src/main/java/com/tik/zbb/blockstorage/storages/broken/BrokenReappearBlockStorageManager.java)
- [BuildDisappearBlockStorageManager.java](https://github.com/XTiK555/ZombieBreakAndBuild/blob/73a8022609d2d1554d0c1a89406dc97f7ed8aa3/common/src/main/java/com/tik/zbb/blockstorage/storages/buildDisappear/BuildDisappearBlockStorageManager.java)
- [PersistentExpiringBlockStorage.java](https://github.com/XTiK555/ZombieBreakAndBuild/blob/73a8022609d2d1554d0c1a89406dc97f7ed8aa3/common/src/main/java/com/tik/zbb/blockstorage/PersistentExpiringBlockStorage.java)
- [ExpirationIndex.java](https://github.com/XTiK555/ZombieBreakAndBuild/blob/73a8022609d2d1554d0c1a89406dc97f7ed8aa3/common/src/main/java/com/tik/zbb/blockstorage/ExpirationIndex.java)
- [FallingBlockStorageTracker.java](https://github.com/XTiK555/ZombieBreakAndBuild/blob/73a8022609d2d1554d0c1a89406dc97f7ed8aa3/common/src/main/java/com/tik/zbb/blockstorage/FallingBlockStorageTracker.java)

## Comparison: Minecraft 1.20.1 checkpoint-based MineZero

[AMPerez04/MineZero 1.20.1 Forge `84084b48e2dc5141e821177f53f8c29563a03093`](https://github.com/AMPerez04/MineZero/tree/84084b48e2dc5141e821177f53f8c29563a03093) has:
- `event/BlockChangeListener.java`: records player placement and break with door/bed dual block pairing;
- `event/NonPlayerChangeHandler.java`: listens for explosion pre-detonation and caches affected blocks; tracks other environmental changes;
- `checkpoint/WorldData.java`: maintains chunk-indexed saved blocks, optional block-entity NBT, per-dimension indexing and checkpoint time;
- `checkpoint/CheckpointManager.java`: restores saved blocks and block-entity NBT and extends restoration to player/world entities.

Source locators:
- [WorldData.java](https://github.com/AMPerez04/MineZero/blob/84084b48e2dc5141e821177f53f8c29563a03093/src/main/java/boomcow/minezero/checkpoint/WorldData.java)
- [CheckpointManager.java](https://github.com/AMPerez04/MineZero/blob/84084b48e2dc5141e821177f53f8c29563a03093/src/main/java/boomcow/minezero/checkpoint/CheckpointManager.java)
- [NonPlayerChangeHandler.java](https://github.com/AMPerez04/MineZero/blob/84084b48e2dc5141e821177f53f8c29563a03093/src/main/java/boomcow/minezero/event/NonPlayerChangeHandler.java)

Checkpoint rollback's *scope* is much wider than siege attack undo; avoid wholesale resurrection of entities/inventories or loss of unrelated player building. Use only bounded event journal concepts.

## Important implementation gaps to design around (requirements, not proven bugs)

1. **Global hooks miss bypass mutations.** Vanilla events and project-specific wrappers do not necessarily capture `setBlock` by arbitrary mods. Guarantee only mutations routed through an authoritative invasion `TerrainEditService`, plus bounded explosion policy.
2. **Loot dupes.** Restore a mined chest after its drops already landed → dupes. Suppress drops of reversible blocks, track inventory contents and restrict unsupported containers by default.
3. **Unrelated player edits.** Existing record at location may conflict with later player placement/breaking. Guard by expected-current block state and ownership; do not overwrite without a policy.
4. **Same block kind ≠ same state.** Treating type match as ownership can overwrite a player-replaced same-type block with different properties; record a mutation ID and expected-state fingerprint, not only `is(blockType)`.
5. **Diverse physics.** Falling sand, flowing fluids, fires, redstone/neighbor updates, entity spawning and block entities cause side effects outside `setBlock`; capture/disable/contain explicitly rather than promise universal undo.
6. **Crash consistency.** Per-dimension `SavedData` is a useful persistence carrier but is not by itself a transactional write-ahead log. Before an invasion edit, write bounded undo evidence durably, then mutate on server thread; reconcile after crashes.
7. **Budget and chunk safety.** Do not force-load arbitrary terrain. Preserve pending edits for unloaded chunks until normal load, rate-limit cleanup, report pending state; do not drop entries due to inactivity.
8. **Overlapping encounters / attackers.** Multiple mobs must share a single original-state entry per cell, with encounter owners/reference counts and serialized per-cell mutations. Prevent later zombie temporary blocks from hiding a pending original restoration.

## KNEEKURA-specific decision candidate

Adopt conceptual **before-image journal + idempotent per-cell revert**, with two policy categories:
- `TEMP_PLACED`: remove the attacker-created block after configured lifetime and reconstruct its original state if it replaced a prior cell.
- `TEMP_BROKEN`: rebuild the exact prior blockstate plus block-entity NBT at its **original position**, not at a nearby location.

Conflict handling must pause and disclose rather than silently overwrite legitimate player edits. Block types that cannot meet guarantee should be **ineligible for destruction**, not deleted with an unkept promise.
