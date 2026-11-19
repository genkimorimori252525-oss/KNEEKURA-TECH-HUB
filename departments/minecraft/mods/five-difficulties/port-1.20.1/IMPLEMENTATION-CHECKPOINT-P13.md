# Implementation checkpoint — P13 danmaku-weapon items (Mini Hakkero, Nuclear Control Rod, Dragon Neck Jewel)

Date: 2026-11-19
Oracle: X1 `ItemMiniHakkero`, `EntityMiniHakkero` (item constructor), `ItemNuclearControlRod`,
`THShotLib.createNuclearShot`, `EntityNuclearShot` (held branch), `ItemDragonNeckJewel`,
`EntityDragonNeckJewel`, `RenderRyuuLightningBolt`, `THKaguyaLib.itemEffectFinish`.

## Ported

| X1 | Port |
|---|---|
| `ItemMiniHakkero` + `EntityMiniHakkero(world, user, damage)` | `MiniHakkeroItem`, `MiniHakkeroEntity` item constructor |
| `ItemNuclearControlRod` | `NuclearControlRodItem` (wired into `NuclearShotEntity.controlRod`) |
| `ItemDragonNeckJewel` + `EntityDragonNeckJewel` + `RenderRyuuLightningBolt` | `DragonNeckJewelItem`, `DragonNeckJewelEntity`, `DragonNeckJewelRenderer` |
| `THKaguyaLib.itemEffectFinish` | `X1ItemEffects.itemEffectFinish` |

`THShotEntity` now routes the forward hit through an overridable `onImpact(entity, block, motion)`, as
X1's `EntityTHShot.onImpact` (behaviour unchanged for every existing shot).

## X1 behaviour kept on purpose

- Mini Hakkero: needs 32 fire charges counted over the whole main inventory (taken one at a time from the
  first stack) and no normal cube at the hakkero spot, found with `(int)` casts (truncation, not floor).
  Its Master Spark is 40 long and explosive (EXPLOSION01); the hakkero returns to the inventory after 109
  ticks (creative players get nothing back; a full inventory drops it). The held stack is spent except in
  creative (1.7.10 restores the stack size there).
- Nuclear Control Rod: the shot starts at size 0.3 beside the player and grows 0.06 per tick while held;
  if the rod leaves the hand it explodes at its size. Release fires it (acceleration 0.2, limit 0.8),
  pushes the player back by min(charge, 100) / 25 and costs 1 of 36 durability.
  `createNuclearShot` passes the first speed as the acceleration (both 0 here).
- Dragon Neck Jewel: durability 300 is its charge; a throw needs damage < 229 and costs 70; sneaking at
  damage 0 throws five colours (−40°..+40°) and costs 299; +20 every 20 ticks of the holder. It glints.
  A jewel that hits a block on its forward ray bursts twice (super.onImpact runs blockHitSpecialProcess,
  then onImpact bursts again): five lasers and ten light shots each time. Shots it touches never burst it.
- The jewel's colour fields are never read by its renderer, which flickers between thKaguyaTerrain cells
  16–20.

## Receipts

Pure core: 10 suites PASS.

Dedicated server (local; P5–P13 together, 0 failures):

```
FIVE_DIFFICULTIES_P13_HAKKERO_PASS chargesLeft=8 returnedAfter=109
FIVE_DIFFICULTIES_P13_ROD_FIRE_PASS size=1.45 flown=7.89
FIVE_DIFFICULTIES_P13_ROD_EXPLODE_PASS
FIVE_DIFFICULTIES_P13_JEWEL_PASS jewels=6 lasers=60 lights=120
FIVE_DIFFICULTIES_P13_RUNTIME_SCENARIO_PASS
```

- HAKKERO: refused with 20 fire charges; with 40, 32 are used, the item is spent, one explosive ID-24
  Master Spark appears, and the item is back in the inventory 109 ticks later.
- ROD: 20 ticks of charge grow the shot to 1.45 next to the player; release costs 1 durability and the
  shot flies 7.89 blocks in 10 ticks; a second charge explodes when the rod leaves the hand.
- JEWEL: one throw costs 70; the five-colour throw is refused below full charge; one recharge tick
  restores 20; the five-colour throw costs 299. All six jewels landed on the forward ray: 60 lasers,
  120 light shots (two bursts each).

Real client (local, private overlay): `FIVE_DIFFICULTIES_P13_CLIENT_RESOURCES_PASS items=3` (three item
models, their textures and the terrain atlas); the P12 in-world frame now also shows a Dragon Neck Jewel.
The world smoke turns off pause-on-lost-focus: an unfocused window had opened the pause menu over the
first frame in one local run.

## Not covered

- The recoil and durability are applied as X1 does, but no client-side check of the recoil was made.
- `EntityTHHenyoriLaser` is dead code in X1 (its registration and its only use in ItemHoutou are commented
  out) and is not ported.
