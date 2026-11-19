# Implementation checkpoint — P16k Yuuka's parasol

Date: 2026-11-20
Oracle: X1 `ItemYuukaParasol`, `EntityYuukaParasol`, `RenderYuukaParasol`, `ModelYuukaParasol`.

## Ported

| X1 | Port |
|---|---|
| `ItemYuukaParasol` (durability 60, special 350) | `yuuka_parasol` (`X1ShotItems.YuukaParasol`) |
| `EntityYuukaParasol` | `YuukaParasolEntity` (mode synced, as X1's watcher 19) |
| `RenderYuukaParasol` + `ModelYuukaParasol` | `P16Renderers.YuukaParasol`, layer `yuuka_parasol` |

## X1 behaviour kept on purpose

- Release the guard: 45 scale shots in a flower (power `(10 + held) / 10`, over 4 becomes 5, upward 1.4,
  speed 0.23 − sin(phase) × 0.02, gravity −0.02) and 11 more at 0.66 × power and upward 1.1; red or yellow at
  random; 1 durability.
- Special 350: on a block, if the block at the shot's (int)-truncated position 0.3 lower is grass and the one
  above is air, a yellow shot plants a dandelion and a red one a poppy. X1 truncates toward zero, so below
  y = 0 it reads one block higher; kept.
- A hit throws the target 3 away and 1 up and deals 7 as a mob attack; 1 durability.
- Sneak right-click puts the parasol (the item itself) up 1.6 above the eyes, at most one per player within
  20. It is a solid 2 × 2 × 2 box. Mode 0 cuts the fall distance to 0.7 a tick. Sneaking after 10 ticks tilts
  it (mode 1), then folds it (mode 2), then returns it with its damage.
- X1's half-made ride (`ridingEntity` set without mounting) is undone by 1.7.10 on the first tick, so its
  `updateRidden` fall braking never runs. Not ported.

## Receipts

Dedicated server (local; P5–P16 together, 10 scenarios PASS, 0 FAIL):

```
FIVE_DIFFICULTIES_P16_PARASOL_PASS shots=56
```
