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

## P13b — Hakurei gohei and the Yin-Yang Orb

Oracle: X1 `ItemOharaibouR`, `EntityOnmyoudama`, `RenderOnmyoudama`.

- `OharaibouRItem` (durability 89, block pose): holding right-click charges an orange Yin-Yang Orb two
  0.6-steps ahead of the eyes, +0.06 size per tick up to 3; it vanishes if the gohei leaves the hand.
  Release throws it (one tick of acceleration 1.0, limit 1.8, default gravity, BOUND04: it bounces until
  its end time 180) and costs 1 durability.
- `OnmyoudamaEntity`: damage size × 6; it hits nothing until it has been off its user's path for two ticks,
  then everything including its user (`userHitCheck` / `isUserHit`, now hooks on `THShotEntity` with the
  old behaviour as default). A block within its size above it reflects it downward. Its entity-hit
  special turns it round but returns false, so it is removed after a hit, as in X1.
- `OnmyoudamaRenderer`: spinning ball and the 1.4-block light (X1 never applies the light's size
  argument); the unused `renderLaser` sphere is not ported.

Receipts: `FIVE_DIFFICULTIES_P13_GOHEI_PASS size=0.88 maxDistance=57.54` (10 ticks of charge, release costs
1 durability, still bouncing after 60 ticks, a second charge vanishes when the gohei leaves the hand);
`FIVE_DIFFICULTIES_P13_CLIENT_RESOURCES_PASS items=4`; the P12 in-world frame shows an orb.

## P13c — wind gohei, Miracle Circle and Sanae's wind

Oracle: X1 `ItemOharaibouS`, `EntityMiracleCircle`, `RenderMiracleCircle`, `EntitySanaeWind` (its live
part: most of the file is commented-out older code), `RenderSanaeWind`.

- `OharaibouSItem` (durability 50, block pose): holding right-click draws a pentagram 3 blocks ahead every
  30 ticks (five colours). Released before 30 ticks it blows a wind (damage level / 5, at least 0.1;
  lifetime level × 3 within 15..120; WIND01) for 1 durability. After 30+ ticks it charges every miracle
  card in the main inventory that its pentagrams and level allow (Charge 1000): Miracle Fruit (any, Lv 20),
  Fafrotskies (60 ticks, 25), Youryoku Spoiler (90, 30), Moses (120, 35), Yasaka (150, 40), repairing the
  gohei 5 / 10 / 15 / 20 / 30. X1 sets Miracle Fruit's repair with setItemDamage (works in creative too,
  and could go below 0; 1.20 clamps at 0).
- `MiracleCircleEntity`: follows the player's view, spawns the next colour at count 30, turns 2.4° per
  tick once complete, vanishes when the player stops using the item. X1's Yasaka wind at release is
  commented out and so not ported.
- `SanaeWindEntity`: gravity = 0.2 × the user's last-tick displacement (never downward, −0.1 while
  sneaking); wind type 1 (unused by the item) turns 2° per tick at the user's speed.

Receipts: `FIVE_DIFFICULTIES_P13_WIND_PASS hitAfter=5 knockUp=2.00` (two pentagrams after 35 ticks, a
quick release blows a wind that knocks a husk up by 2.0 and costs 1 durability, the pentagrams vanish);
`FIVE_DIFFICULTIES_P13_MIRACLE_CHARGE_PASS cards=5` (a 160-tick release at level 40 charges cards 14–18 and
repairs the gohei from 40 to 0); `FIVE_DIFFICULTIES_P13_CLIENT_RESOURCES_PASS items=5`; the P12 in-world
frame shows a half-drawn pentagram and a wind.

