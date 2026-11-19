# Implementation checkpoint — P15 danmaku / laser crafting tables

Date: 2026-11-19
Oracle: X1 `BlockDanmakuCraftingTable`, `ItemBlockDanmakuCraftingTable`, `ContainerDanmakuCrafting`,
`ContainerDanmakuCraftingLaser`, `SlotDanmakuCraftingA`, `SlotDanmakuResult`, `SlotLaserResult`,
`GuiDanmakuCrafting`, `GuiDanmakuCraftingLaser`, `GuiHandler`.

## Ported

| X1 | Port |
|---|---|
| crafting arithmetic (result NBT, per-slot consumption) | `core/x1/X1DanmakuCrafting` (pure, tested) |
| `BlockDanmakuCraftingTable` metadata 0 / 1 | `danmaku_crafting_table`, `laser_crafting_table` (`DanmakuCraftingTableBlock`) |
| both containers and their slots | `DanmakuCraftingMenu` (one class, shot / laser mode), two `MenuType`s |
| both GUIs | `DanmakuCraftingScreen` |

## X1 behaviour kept on purpose

- Slots and positions as X1: material, number (small power), speed (small power), copy (point), colour
  (dye / gunpowder / diamond), gravity (small power) and bound (big power) on the danmaku table; a 3×3 form
  grid of small powers; the result at (228, 35).
- Forms by grid pattern: centre = point, centre + top = random, top row = sector, ring = around, full =
  sphere (needs more than 2), plus-shape = ring (needs more than 2); an empty grid keeps the material's
  form, anything else makes nothing. A sphere of more than 32 makes nothing.
- byte / short arithmetic as X1 (speed 60 + 70 wraps and becomes 64; bound casts to byte), caps from the
  config (Shot / Laser Max Number), dyes through `sellectbleColor` in 1.7.10 dye-damage order.
- Consumption on take as `SlotDanmakuResult` / `SlotLaserResult`, including X1's odd branch for an
  untagged material with too many number powers (max − 1 are taken).
- The result is recomputed after every click (X1 `slotClick`); closing drops every input at the player.
- Shift-click uses X1's index ranges (10..46), copied from the vanilla crafting table and not matching
  this layout.
- Tables: hardness 1.5, resistance 1.0, wood, light 15.

## Receipts

Pure core: 11 suites PASS (new `X1_DANMAKU_CRAFTING_REGRESSION_PASS`: nine cases worked out from the X1
source).

Dedicated server (local; P5–P15 together, 0 failures):

```
FIVE_DIFFICULTIES_P15_CRAFT_PASS number=4 form=0 color=1
FIVE_DIFFICULTIES_P15_FIRE_PASS shots=4
FIVE_DIFFICULTIES_P15_LASER_PASS number=8 powerUsed=7
FIVE_DIFFICULTIES_P15_BLOCK_PASS light=15 opens=danmaku
FIVE_DIFFICULTIES_P15_RUNTIME_SCENARIO_PASS
```

Real client (local, private overlay): `FIVE_DIFFICULTIES_P15_CLIENT_RESOURCES_PASS tables=2`; the in-world
frame `p15_crafting.png` shows the danmaku crafting screen opened by using the placed block (X1 background,
labels and slots line up).

## Not covered

- Crafting recipes for the tables (P18).
- World checks are still on the project's own throwaway flat world; moving them to the TechHub Tank host
  is the next step (the host runs Forge 47.4.10; this port targets 47.4.6).
