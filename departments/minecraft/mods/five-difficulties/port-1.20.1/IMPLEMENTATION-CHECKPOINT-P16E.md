# Implementation checkpoint — P16e Aja red stone

Date: 2026-11-20
Oracle: X1 `ItemAjaRedStone`, `EntityAjaRedStoneEffect`, `RenderAjaRedStoneEffect`.

## Ported

| X1 | Port |
|---|---|
| `ItemAjaRedStone` (special 351) | `aja_red_stone` (`X1EffectItems.AjaRedStone`) |
| `EntityAjaRedStoneEffect` | `AjaRedStoneEffectEntity` (light power synced, as X1's data watcher 19) |
| `RenderAjaRedStoneEffect` | `P16Renderers.AjaRedStoneEffect` |

## X1 behaviour kept on purpose

- Each right-click spawns an effect 1.2 ahead of the eyes; every tick it adds the light level at its
  (int)-truncated block (sky light after darkening, or block light) to its total.
- On release `total / 40` (max 30) becomes a red laser: width damage × 0.01, length damage × 0.3, damage, end 60,
  first 0.1 / limit 4 / accel 0.3, special 351. With nothing gathered it fires nothing and stays.
- Special 351: an undead hit burns for the shot damage in seconds and the damage rate doubles (lasers in X1
  ignore the rate), with a fizz.
- Render: light² random red rays, length light² / 120, the rotation step `sin(360 / n)` used as radians.

## Receipts

Dedicated server (local; P5–P16 together, 10 scenarios PASS, 0 FAIL):

```
FIVE_DIFFICULTIES_P16_AJA_RED_STONE_PASS idleLight=15
```

## Not covered

- Renderer seen only by compilation so far (client frames planned at the end of P16).
