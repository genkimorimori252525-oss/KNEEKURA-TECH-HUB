# QB-MOD / Garnet-MOD 1.6.4.082 — Unfinished / debug / dead-code catalog

Date: 2026-10-07

Purpose: preserve design archaeology without falsely reporting commented/TODO/reserved code as shipped gameplay.

Primary evidence:
- QB-MOD SHA-256 `52b1ba0774e098795dcf1ed9a489c66414ea725235978171f48a10db7287ba4e`
- Garnet-MOD SHA-256 `5f778c8949dcce95dcd56dacd9242f117bc17f03879bab48cb667ba2a3c82778`

## 1. Oktavia familiar summoning is deliberately disabled in this snapshot

`EntityOktavia` overrides:

`canSummon()`

with:

`//TODO`
`return -1; //20;`

It also has:

`getServant() → new EntityAnthony(world)`

with another TODO marker.

Because the common `EntityMajo` summon path requires `canSummon() > 0`, this servant path is disabled.

What can be safely said:
- author left a concrete intended servant factory;
- comment suggests a possible former/planned cap of 20;
- **Oktavia does not use this common servant-summon path in 1.6.4.082**;
- its shipped pressure instead comes from `EntityMajoAIOktavia` spawning Wheel hazards.

Do not merge “20 Anthony servants” into the player-facing feature list.

## 2. Mami Ribbon item had an unfinished pull mechanic

`ItemMamiRibbon` contains a fully commented-out `onItemRightClick`.

The commented design:
- keeps an `isConnect` boolean on the Item singleton;
- first use:
  - plays bow sound;
  - finds `EntityItem` within a 12-block expanded box;
  - creates `EntityFishHook` for each;
  - sets each hook's `bobber` to the item entity;
  - sets `isConnect=true`;
- next use:
  - damages ribbon by 1;
  - clears the connection flag.

The Japanese TODO literally says:
`TODO いずれ引き寄せ機能`
(“eventually, pulling-in functionality”).

Status:
**NON-EXECUTABLE DESIGN TRACE**.

Engineering lesson:
- the intended mechanic used vanilla fishing-hook linkage as a generic tether;
- however the proposed state is stored on the shared Item object, not per ItemStack/player, which would be unsafe if enabled as written.

## 3. Mami Ribbon block visual TODO

`BlockMamiRibbon` contains a commented custom `shouldSideBeRendered` override under:

`TODO 見た目をどうするか？`
(“what should the appearance be?”)

The proposed logic would suppress a face when the adjacent block is the same ribbon block.

Status:
**unfinished connected-surface visual idea**.

This suggests the author considered making adjacent ribbon blocks visually merge, but the shipped block uses the simpler non-normal/non-opaque behavior.

## 4. Grief Seed forced-clearance update TODO

After deleting an obstructing block, `EntityGriefSeed.forcedSpawnMajo` retains commented code around:
- `setBlockAndMetadataWithUpdate`;
- explicit neighbor notification.

The active code already uses `worldObj.setBlock(..., 0)`.

Status:
**old block-update implementation experiment / cleanup trace**.

Do not infer missing neighbor notifications without checking 1.6.4 `World#setBlock` semantics; this comment is not proof of a runtime defect.

## 5. Garnet throwable TNT impact TODO

`EntityGarnetThrowable`:
- on block impact, if the embedded block is TNT;
- contains commented call:
  `Block.tnt.onBlockDestroyedByExplosion(...)`;
- active behavior simply replaces the TNT block with air.

Status:
**unfinished TNT-special interaction**.

The shipped behavior destroys TNT instead of explicitly invoking explosion-destruction behavior from that commented line.

## 6. Debug stdout left in active AI

### Oktavia

`EntityMajoAIOktavia.spawnWheel` prints:
- `false` on failed candidate tests;
- `true` on success.

A single Wheel spawn can test up to 20 candidate positions and the boss emits repeated waves.

Status:
**active debug logging / performance-noise candidate**.

### Charlotte second-form wander

`EntityMajoAICharlotteWander.initPosition` prints its candidate counter every search-loop iteration.

Position search:
- random offset in a 40×40×40 cube around Charlotte;
- accepts distance squared 100..900 and Y>10;
- scans a 3×3×3 region for air;
- after >30 candidate checks that reach the distance/Y branch, breaks even if none is valid.

The counter does not increment for distance/Y rejection, so total RNG attempts are not strictly capped at 31, though ordinary overworld geometry should eventually satisfy the coarse filter.

Status:
**active debug output plus bounded-ish random position search**.

### Garnet tameable

Owner chat feedback also mirrors messages to stdout.

Status:
**legacy logging side effect**, lower severity than the tight candidate loops.

## 7. Reserved Oriko / Yuma / Jewel slots

`mod_QB` declares/configures IDs for:
- Oriko Soul Gem / entity;
- Yuma Soul Gem / entity;
- Jewel entity.

But the supplied Java tree contains no usable:
- `EntityOriko`;
- `EntityYuma`;
- `EntityJewel`;

and no player-facing registration/instantiation path for these reserved slots.

Status:
**RESERVED / INCOMPLETE CONTENT TRACE**.

They must not be counted as implemented characters/entities.

## 8. Grief Seed Walpurgis switch default is dead through the active RNG selector

`chooseMajo()`:
- `nextInt(5)` yields 0..4;
- cases 0..4 cover five witches;
- default returns Walpurgisnacht.

Distributed bytecode preserves the same structure.

Status:
**executable code with unreachable switch default through this call path**.

This is different from commented code:
- the bytecode exists;
- Java type construction exists;
- active selector cannot choose it.

It may be a remnant of an older/larger random range.

## 9. Homulilly apparent TNT selection has one reachable random result

`EntityHomulillyAIAttack.attackTNT` uses `nextInt(1)`.

Java guarantees the result is always 0.

Distributed bytecode contains the same constant and call.

Status:
**live branch shape with one unreachable alternative**.

Strong candidate for either:
- accidental bound;
- remnant of a removed second attack pattern.

Historical intent remains unknown.

## 10. Source-only stale imports in Garnet

Two Garnet Java sources reference/import unrelated Korezon/Kuko packages in source, but the shipped compiled classes do not retain those external references in their constant pools/method surfaces.

Status:
**source-release cleanliness issue**, not a runtime binary dependency for the distributed classes checked.

This matters if reconstructing or recompiling the original source tree from scratch.

## 11. TexturePack Madoka UF filename defect

Alternate TexturePack contains an intended Madoka UF texture whose first character is full-width U+FF4D `ｍ`, not ASCII `m`.

Status:
**asset packaging defect candidate**, not code dead-path.

The base renderer requests ASCII `madokaUF.png`.

## 12. Abstract ItemMadomagiWeapon retains an overridden legacy right-click implementation

`ItemMadomagiWeapon` contains a concrete `onItemRightClick` despite being an abstract base.

Its default path:
- damages the held weapon by 32;
- if the item ID is Sayaka Cutlass, applies Regeneration for 600 ticks at amplifier 4;
- if the item ID is Kyouko Spear, creates an `EntitySpear2`.

However the concrete subclasses present in the supplied tree are:
- `ItemSayakaCutlass`;
- `ItemKyoukoSpear`;
- `ItemKirikaClaw`.

All three override `onItemRightClick`, and none calls `super.onItemRightClick`.

Their active behavior has diverged:
- Sayaka Cutlass checks existing Regeneration, costs 48 durability and then applies the buff;
- Kyouko Spear has its own Spear2 launch plus enchantment propagation;
- Kirika Claw implements its own multi-Claw launch.

Therefore the base implementation is best classified as:

**IMPLEMENTED_BUT_SHADOWED_BY_ALL_CURRENT_CONCRETE_SUBCLASSES**

It survives in source/bytecode as an older generic weapon implementation, but no current concrete weapon reaches it through ordinary virtual dispatch.

This is useful design archaeology because it shows a likely refactor path:
`one generic ID-switch weapon base → character-specific subclass implementations`.

It must not be reported as an additional active player control path.

## 13. Preservation categories

Use these labels for future archaeology:

- **IMPLEMENTED** — active source and executable path;
- **IMPLEMENTED_BUT_UNREACHABLE_FROM_SELECTOR** — bytecode exists but current branch/range cannot reach it;
- **COMMENTED_DESIGN** — source preserved inside comments, not compiled behavior;
- **TODO_DISABLED** — active override explicitly blocks the planned system;
- **RESERVED_SLOT** — config/ID/name exists without implementation;
- **DEBUG_ARTIFACT** — logging/instrumentation left in active code;
- **SOURCE_ONLY_STALE** — Java release source contains references absent from distributed binary behavior;
- **ASSET_PATH_DEFECT** — resource packaging mismatch.

This distinction prevents the TECH-HUB from turning archaeological hints into false gameplay claims.