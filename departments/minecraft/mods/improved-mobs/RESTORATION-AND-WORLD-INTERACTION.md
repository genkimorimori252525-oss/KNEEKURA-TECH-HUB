# Improved Mobs — terrain restoration, drops, TNT and chest interaction

ANCHOR `029b8c20302a76bac1af9f5140e2abb6f73fea5c` — SOURCE-CONFIRMED, runtime not run.

## The built-in restoration *actually does*

[BlockRestorationData.java](https://github.com/Flemmli97/ImprovedMobs/blob/029b8c20302a76bac1af9f5140e2abb6f73fea5c/common/src/main/java/io/github/flemmli97/improvedmobs/utils/BlockRestorationData.java) extends Minecraft `SavedData`, stored per `ServerLevel` as `ImprovedMobsRestoration`. Two-level maps are keyed by packed `ChunkPos` and packed `BlockPos`. Each `SavedBlock` has:
- prior `BlockState`;
- `level.getGameTime()`;
- a list of computed item drops (`Block.getDrops`), **not** original BlockEntity NBT.

On successful mining threshold in [BlockBreakGoal](https://github.com/Flemmli97/ImprovedMobs/blob/029b8c20302a76bac1af9f5140e2abb6f73fea5c/common/src/main/java/io/github/flemmli97/improvedmobs/ai/BlockBreakGoal.java), if `restoreDelay>0`, the code records the original state first, sets `canHarvest=false`, then invokes `level.destroyBlock(markedLoc, canHarvest)`. The scheduled recovery is therefore the MOD's block-breaking path, not arbitrary world destruction.

`EventCalls.tick(ServerLevel)` invokes the data's tick **every server level tick**, even when difficulty scaling is off. The restore tick visits every pending chunk group in memory and iterates its positions if the chunk is loaded:
- if block is **AIR** and elapsed time exceeds configured `restoreDelay`, call `setBlock(pos, originalBlockState, Block.UPDATE_ALL)` and remove entry;
- if cell is AIR but not due, occasionally emits a red particle;
- if current state is **not AIR**, emit remembered block drops and remove entry instead of restoring at original position;
- when block at same location was previously registered again, old record's drops may be emitted before replacement.
- saved entries are encoded to NBT by chunk on server save; `setDirty()` marks updates.

**Crucial limits:** `restoreDelay=0` by default (disabled); no block-entity NBT return even for chests; no guaranteed restoration of attached blocks, fluids, falling blocks, scheduled ticks, TNT explosion damage, arbitrary mod edits, or player's later edits. Using merely “AIR/not AIR” to decide recovery is unsafe for full-base restoration.

## Significant source risk

`BlockRestorationData.restore` stages the original entry BEFORE `destroyBlock`, but there is no observed success-only transaction/rollback of that staged record when `destroyBlock` fails. Does not prove a release bug (a failed break may leave the original block and later cause the non-AIR cleanup); still needs exact fail-path tests.

`tick` has a per-tick iteration over stored loaded-cell records, not a global expiry-heap as in Zombies Break & Build. It does group by chunk and skip unloaded chunks; performance risk is proportional to pending dirty cells and tick cadence; no measured TPS or latency asserted.

## Other world interactions to distinguish

- `StealGoal` searches nearby eligible tile inventories only without an active target and uses CrossPlatformStuff`canLoot`/lootRandomItem; Forge `ContainerCap` tracks player-opened tiles; this is **inventory mutation**, outside BlockState restoration.
- Mob TNT, lava bucket and flint&steel item use are separate attack paths; 1.13.5 changelog confirms `tntBlockDestruction` configuration bug fix. Restoring directly mined blocks **does not guarantee** that TNT explosions or lava/fire restore too.
- `breakTileEntities=true` default is particularly risky combined with `restoreDelay>0` if users assume chest inventory restoration. The 1.11.7 changelog explicitly warns block entity data is not restored.

Sources: [EventCalls.java](https://github.com/Flemmli97/ImprovedMobs/blob/029b8c20302a76bac1af9f5140e2abb6f73fea5c/common/src/main/java/io/github/flemmli97/improvedmobs/events/EventCalls.java), [StealGoal.java](https://github.com/Flemmli97/ImprovedMobs/blob/029b8c20302a76bac1af9f5140e2abb6f73fea5c/common/src/main/java/io/github/flemmli97/improvedmobs/ai/StealGoal.java), [ItemAIs.java](https://github.com/Flemmli97/ImprovedMobs/blob/029b8c20302a76bac1af9f5140e2abb6f73fea5c/common/src/main/java/io/github/flemmli97/improvedmobs/ai/util/ItemAIs.java), [Changelog.md](https://github.com/Flemmli97/ImprovedMobs/blob/029b8c20302a76bac1af9f5140e2abb6f73fea5c/Changelog.md).

## Comparison against previously investigated source

[Zombies Break & Build ANCHOR](https://github.com/XTiK555/ZombieBreakAndBuild/tree/73a8022609d2d1554d0c1a89406dc97f7ed8aa3d) retains typed `BrokenReappearBlockStorageEntry` and `BuildDisappearBlockStorageEntry`, with original NBT, expiration index and alternate recovery. While stronger for timed block-management, it is still not an atomic *exact* restoration proof.

For a future KNEEKURA product, preserve independent study categories: **world snapshots**, **temporary construction**, **temporary destruction**, **projectile/explosion side effects**, **inventory mutation**, **protected claims**, **crash consistency**, **recovery conflicts**. Do not implement or commit final design based on this report.
