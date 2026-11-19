# Let Me Despawn — source comparisons around item-pickup persistence

User's actual target: **`letmedespawn-1.20.x-forge-1.5.0.jar`**, [CurseForge file 6311230](https://www.curseforge.com/minecraft/mc-mods/let-me-despawn/files/6311230) uploaded **2025-03-16**, supports Forge **1.20.1–1.20.4**. **The exact 1.5.0 Forge source commit is unavailable in the inspected original GitHub repo, and the JAR bytes/hash are NOT uploaded.** **All technical code findings below are strictly COMPARATIVE**, not ANCHOR-confirmed in 1.5.0.

## Two version-separated public source snapshots

1. **HISTORICAL Forge:** [`frikinjay/let-me-despawn@af665026e2fb60d8715c4b6910db2cbf16f7090d`](https://github.com/frikinjay/let-me-despawn/tree/af665026e2fb60d8715c4b6910db2cbf16f7090d), `forge` branch dev **Minecraft 1.18 Forge 38.0.17**, source mod **`forge-1.0.3`**; Git tree `0442b75e5d6d3ecb8d0efc6163fdb86008603686`, **17 blobs / 2 Java**. [`MobMixin`](https://github.com/frikinjay/let-me-despawn/blob/af665026e2fb60d8715c4b6910db2cbf16f7090d/src/main/java/com/frikinjay/lmd/mixin/MobMixin.java) changes item equip handling so picked gear alone doesn't enforce persistence; on `checkDespawn` returns equipped items, avoiding deletion. It excludes items with Vanishing Curse from ground drop. No 1.20.1 inference.
2. **COMPARATIVE newer platform:** [`frikinjay/let-me-despawn@b37f7ccee129d0500a9bd8d4d7ba513b7056f887`](https://github.com/frikinjay/let-me-despawn/tree/b37f7ccee129d0500a9bd8d4d7ba513b7056f887), `main` source mod **`1.4.4`** in `gradle.properties`, dev **Minecraft1.21 NeoForge/Fabric**, git tree `2addbb28b2097d69e4716ea09bb3bab18c5c5e93`, **42 blobs / 10 Java**, version documented October2024 before file 1.5.0 March2025; source latest branch Oct2025 Spigot merge but not equivalent to target. [`MobMixin`](https://github.com/frikinjay/let-me-despawn/blob/b37f7ccee129d0500a9bd8d4d7ba513b7056f887/common/src/main/java/com/frikinjay/letmedespawn/mixin/MobMixin.java) injects `setItemSlotAndDropWhenKilled`, `checkDespawn`, `remove`; [`LetMeDespawn.setPersistence`](https://github.com/frikinjay/let-me-despawn/blob/b37f7ccee129d0500a9bd8d4d7ba513b7056f887/common/src/main/java/com/frikinjay/letmedespawn/LetMeDespawn.java) uses item custom NBT `picked`, config mob name exclusions and custom name to choose persistence. It depends on `Almanac` compatibility/lifecycle, unlike old simple Mixin. This **is not proof** target 1.5.0 uses identical Mixin locations, events, item-ownership or config.

Source license [LGPL-3.0](https://github.com/frikinjay/let-me-despawn/blob/b37f7ccee129d0500a9bd8d4d7ba513b7056f887/LICENSE). It is **not** possible to promote code of different versions as demonstrated Minecraft 1.20.1 Forge 1.5.0 behavior.

## LMD-CONCEPT-01 — selective despawn restoring dropped equipment

**Behavior hint**: mob picking up equipment sets `persistenceRequired`, potentially trapping many hostile mobs forever loaded. Performance goal: enable ordinary distance/despawn checks for **unimportant picked-item entities**, while preserving named/special mobs, player-facing essential actors and items.

Comparative source (above) demonstrates:
- **Guard** by mob's name/config/gear tracking, then allow server's regular `Mob.checkDespawn`.
- **Cleanup on genuine despawn**: spawn collected equipment as `ItemEntity`, ensure each item returned **exactly once**. Old source skips Curse of Vanishing; new source has two removal paths (`checkDespawn` and `remove`) with different item handling, so equality/duplication/cancellation requires code+runtime audit before reuse.
- **Effects**: lower persistent **entity count** when distance rules permit; does not automatically reduce costs of named mobs, raids, bossbars, tamed mobs, or special raid wave actors. **Removing active encounter attackers just to improve MSPT would be a design failure.**
- **Event/interop**: newly dropped ItemEntity may later be merged by [Get It Together, Drops!](../get-it-together-drops/README.md), so keep player ownership/stack/timer semantics. Can't assert both released JARs work together.
- **Technical risk**: `remove` may be invoked for death, dimension transition, unload or manual cleanup, not only normal despawn. Without a specific `RemovalReason` check, ordinary code may copy/drop items unexpectedly. This is a **comparative source risk inference only**, not a verified bug in 1.5.0.

## Actual target release adds a separate guard absent from inspected sources

[1.5.0 release notes](https://www.curseforge.com/minecraft/mc-mods/let-me-despawn/files/6311230) explicitly mention **configuring equipment in a mob's HEAD slot that prevents despawning**. This control is **release-description evidence**; matching class, NBT data, registration and default not verified by source. Must protect bosses, named mobs and special encounter roles before adopting conceptual despawn rules.

## Exact 1.5.0 Issue hint (not a confirmed fix)

[Issue #66](https://github.com/frikinjay/let-me-despawn/issues/66) specifically names **Forge 1.20.1/1.5.0**, DynamicTrees 1.4.9 + BiomesOPlenty 19.0.0.96; reporter sees Endermen holding blocks persist on top of rainforest trees. **User report**, not independent reproducible KNEEKURA result. A comment says “Fixed in 1.26.9.1” (a vastly newer MC/loader target), which **cannot** establish backport/fix in 1.5.0. Closed Issue is not source proof. No related 1.5.0 code diff found.

## Planned tests before adoption

On exact Forge 1.20.1 binary: entity count after distance unload for (unnamed hostile picked gear, named, boss, players' equipment, Enderman carrying block, mob in rideable vehicle); compare entity inventory and world item count before/after, Curse of Vanishing, unload/reload, teleport/dimension transition, repeated `Mob.remove`, no item duplication/loss, raid-wave actor exclusions, TPS p95/p99. **No runtime trial, measured performance, or exact release code acquired**.
