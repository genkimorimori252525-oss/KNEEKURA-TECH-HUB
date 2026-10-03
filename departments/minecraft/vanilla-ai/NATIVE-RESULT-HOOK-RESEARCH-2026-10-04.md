# Native result hook research

Date: 2026-10-04 (Asia/Tokyo). ANCHOR: Minecraft 1.20.1, Forge 47.2.0, parchment 2023.08.20-1.20.1. This is static research, not native acceptance.

The genuine mapped Forge JAR is SHA256 `1b6e6a166fbc06c6d2422cd5cf515a508977479045095363d5b4c8b89cc7b4eb`. Exact class hashes:

| Class | SHA256 |
| --- | --- |
| `LivingEntity` | `914d4b6d230e1d1dd5159eb242108851be02ec636d703ac6aa15d7cda179ac11` |
| `EnderMan` | `816ad5449aefe2f441eb1f135350254d4ff899da2a432e41482b3a4a263b6937` |
| `Projectile` | `d3eb7ea9d1a7e4400b6836b45fd135725c831265f36d2f659ea4e7c8eaaded2c` |
| `AbstractArrow` | `f67f9918c99f7212110d271f06d0105818281d5f968e3aeb8afd0c386fb9fa4e` |

## Teleport

`LivingEntity.randomTeleport(DDDZ)Z` saves the old coordinates, checks loaded destination/ground, moves through `teleportTo`, and checks collision/liquid. On failure it restores the old coordinates and returns false; on success it may broadcast the event and stops the `PathfinderMob` navigation before returning true.

`EnderMan.teleport()` and `teleportTowards(Entity)` call its destination overload. Projectile-related `EnderMan.hurt` can attempt teleport instead of accepting ordinary damage. A pre-teleport Forge event is not a successful teleport result. A large sampled displacement is also not sufficient.

The bounded hook candidate is the original `LivingEntity.randomTeleport` RETURN, for the exactly selected Mob only. Record requested coordinates, returned coordinates and the actual boolean under the existing `control` burst channel and budget. A false return remains a failed attempt. Only a valid successful-return observation may label a Motion discontinuity `EXPLICIT_TELEPORT`; never create an additional sampled position from a callback. Base-method coverage excludes custom overrides that do not call this method.

## Projectile and damage

`Projectile.onHit(HitResult)` dispatches to entity/block handlers. Its base `onHitEntity` is empty; a base hook alone cannot describe every projectile subclass's result. `AbstractArrow.onHitEntity` performs the actual `Entity.hurt(DamageSource,F)Z` call and branches on the boolean. Piercing/discard/fire/shield and Enderman paths remain distinct.

`LivingEntity.hurt` can return early for invulnerability, cancellation, client side, death, fire immunity and invulnerability-window conditions. `actuallyHurt` calls Forge `onLivingHurt`, performs armor/magic/absorption calculations, then calls `onLivingDamage` before `setHealth`. Therefore even the damage event is not a post-health-change receipt. A successful `hurt` boolean and a positive health delta are separate facts; shield/absorption and subclass dispatch must not be collapsed into generic HP damage.

Use explicit original callback/result evidence and exact projectile/owner/target UUID relationships. `PROJECTILE_SPAWN` / `PROJECTILE_HIT` strings in the trigger API are not proof of existing producer hooks. Owned related-projectile tracking must be finite, opt-in and fenced to the selected generation; no world scan, arbitrary UUID expansion or second AI invocation.

## TF phase prerequisites

The exact TF source anchor remains `TeamTwilight/twilightforest@a7dd8f13c653e137f977f5ffaa870fcb20fc1625` and the prior original/mapped artifact proof.

- `SnowQueen.customServerAiStep`: SUMMON→DROP requires zero remaining summons and zero nearby minions; DROP→BEAM requires completed drops; BEAM→SUMMON requires damage while beaming. `setCurrentPhase` updates these counters. A short quiet fixture cannot guarantee a transition.
- `UrGhast.hurt`: actual health loss reduces `damageUntilNextPhase`; threshold triggers `switchPhase`. `setInTantrum` resets the threshold. Constructor/load calls occur before a selected burst and cannot fill a later missing capture.
- The prior r13 fixture set all TF Boss entities invulnerable. It proves cached adapter/native component observations, but cannot establish damage-driven Ur-Ghast phase transitions. Preserve that historical result; use a separately labeled private damageable trial for new acceptance.

## Independently sourced FRONTIER and community

Modern comparison: NeoForge branch `1.21.1`, exact commit `61045a61fca76876999281676a9e794688390a9e`, [LivingEntity patch](https://github.com/neoforged/NeoForge/blob/61045a61fca76876999281676a9e794688390a9e/patches/net/minecraft/world/entity/LivingEntity.java.patch), patch SHA256 `3b2bd4404291a91e33ea656f85a91084bb0ce6f288d78a8310fe11c299e2e141`. It introduces `DamageContainer` and separate `onLivingDamagePre` / `onLivingDamagePost`. That post hook is useful as a modern observation concept; it does not exist in the inspected Forge 1.20.1 method body. Do not import the modern API or treat it as a drop-in backport. Original-return instrumentation is the ANCHOR-compatible candidate; its result semantics still need testing.

Technical-community reports, retrieved 2026-10-04:

- [Paper #13318](https://github.com/PaperMC/Paper/issues/13318), opened 2025-11-17: reports angry piglins losing reliable pursuit after a short relog. Useful test idea: distinguish anger/target identity from actual navigation after process/player lifecycle changes.
- [Paper #13829](https://github.com/PaperMC/Paper/issues/13829), opened 2026-04-27: reports stale non-player anger targets in 1.21.11+ after a target disappears. Useful UI requirement: show target presence, persistent UUID and lifecycle boundary separately. Its `SpearUseGoal`/modern implementation is not ANCHOR evidence.

Both are unverified community reports. Neither establishes a Forge 1.20.1 bug, scheduler cause or terrain valuation rule. Terrain-specific community cases and broader FRONTIER comparison remain pending in the requirement matrix.
