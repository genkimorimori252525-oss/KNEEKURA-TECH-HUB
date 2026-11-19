# Implementation checkpoint — P9 all shot forms, special shots, literal Homing / Diffusion Amulet

Date: 2026-11-19
Oracle: X1 bundled sources (`RenderTHShot`, `ModelSilverKnife`, `EntityTHShot.homing / bound /
diffusion / entityHitSpecialProcess / blockHitSpecialProcess`, `ItemHomingAmulet`, `ItemTHShot`).

## Correction to P2 (found while reading `ItemHomingAmulet`)

X1's Homing Amulet item does **not** fire `EntityHomingAmulet`. It calls
`THShotLib.createWideShot` with `ShotData.shot(FORM_AMULET, RED, …, HOMING01)`, i.e. generic
`EntityTHShot` amulets drawn by `RenderTHShot.renderAmuletShot`. `EntityHomingAmulet` +
`RenderHomingAmulet` belong to the Houtou item (`ItemHoutou`).

P2 took the item's numbers from `ItemHomingAmulet` but the behaviour and the visual from
`EntityHomingAmulet` / `RenderHomingAmulet`. P9 rewires the item literally
(`HomingAmuletItem`, now with the damage-1 **Diffusion Amulet** as `diffusion_amulet`).
`HomingAmuletProjectile` (the `EntityHomingAmulet` port) stays registered for Houtou and is still
covered by the P6 scenario.

## Ported

- `THShotRenderer`: every `RenderTHShot` form — scale, butterfly, small star / star, rice,
  crystal, light / big light, kunai, arrow, talisman, oval, familiar, phantom, amulet
  (homing / diffusion texture), knife (`ModelSilverKnife` box-for-box), wind, kishitu — plus
  `getEntityTexture`. 1.7.10 Tessellator calls go through `X1Tess`; GL state changes map to five
  render types (cutout, SRC_ALPHA/ONE, ONE/ONE_MINUS_SRC_COLOR with and without depth writes,
  ONE/ONE). Switching render type flushes the batch, so X1's draw order is kept.
- Special shots in `THShotEntity`: HOMING01, DIFFUSION01, FALL01, BOUND01–04, FIRE,
  EXPLOSION01, WIND01, including X1's `damageRate`.
- All 19 `ItemTHShot` subtypes as items, plus the Diffusion Amulet.

## X1 quirks kept on purpose

- Homing rotates about the **raw** cross product (length = sin of the bearing error), so small
  errors turn much less than the 4°/tick clamp and the angle vector shrinks
  (pure test `homingNonUnitAxisQuirk`).
- Homing only steers because `speed()` is float-rounded: `0.699999988 < 0.7` lets acceleration
  fire, then the motion snaps to `angle * 0.7` (pure test `homingSteersThroughFloatAcceleration`).
- `blockHitSpecialProcess` also runs in the three cross-section probes, so one floor contact can
  spend more than one bounce (BOUND02 showed 1 visible bounce in the scenario).
- Wind shots use a fresh `Random` every frame (the flicker is part of the look).
- X1 `ja_JP.lang` typo `thKaguya,color.4` is used with the intended key.

## Receipts

Pure core: 9 suites PASS; `X1_SHOT_CORE_REGRESSION_PASS` now includes homing score / clamp /
raw-axis quirk / float-acceleration steering and bounce reflection.

Dedicated server (local, fresh flat world, P5/P6/P8/P9 together):

```
FIVE_DIFFICULTIES_P9_HOMING_PASS homingMin=0.769 controlMin=2.057 hit=false
FIVE_DIFFICULTIES_P9_DIFFUSION_PASS peak=88 aliveAtTick24=88
FIVE_DIFFICULTIES_P9_BOUND_PASS bounces=1 removedAtTick=51
FIVE_DIFFICULTIES_P9_FIRE_PASS fireTicks=40
FIVE_DIFFICULTIES_P9_WIND_PASS vy=2.0
FIVE_DIFFICULTIES_P9_RUNTIME_SCENARIO_PASS
```

- HOMING: the item fires five THShot amulets (HOMING01, size 0.4, damage 5); a HOMING01 amulet
  on the 25° ray bends toward a target at 37° (closest 0.77 blocks) while an identical control
  passes 2.06 blocks away.
- DIFFUSION: each of the two amulets bursts at tick 16 into 20 + 16 + 8 blue amulets (88).
- FIRE: (int) 2.4 = 2 s = 40 fire ticks. WIND: +2.0 vertical launch.

Real client (local, private overlay): the in-world frame shows all 18 remaining forms; the GUI
smoke resolves 23 item models and shows the 19 tinted shot icons and the Diffusion Amulet.

## Not covered

- EXPLOSION01 is ported but not runtime-tested (it would damage the test world).
- No X1 1.7.10 runtime frame exists to compare colours and shapes against.
- Remaining: the `ISpecialShot` registry (spell cards), shot-material bonus drop, player power,
  danmaku crafting table, lasers, spell cards, X1 mobs.
