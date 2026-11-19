# Implementation checkpoint — P16l Hisou sword

Date: 2026-11-20
Oracle: X1 `ItemHisou`, `EntityHisou`, `RenderHisou`, `ModelHisou`.

## Ported

| X1 | Port |
|---|---|
| `ItemHisou` (hisou 0/200/4/0, animated texture) | `scarlet_perception_sword` (`X1Weapons.HisouSword`), its `.mcmeta` imported privately |
| `EntityHisou` | `HisouEntity` (number and spin synced, as X1's watchers 17 / 18) |
| `RenderHisou` + `ModelHisou` | `P16Renderers.Hisou`, layer `hisou` |
| `thKaguya.item.kishitu` | same key in the port's lang files |

## X1 behaviour kept on purpose

- Temperament: each hit stores the kind of the target; hitting the same kind again deals 10 more (mob
  attack, magic crit). The tooltip shows it. The port stores the 1.20 entity translation key where X1 stored
  `entity.<Name>.name`.
- Leaves dig at 15, wool at 10; leaves broken above y 128 drop a heavenly peach 1 in 25. Glint.
- Right-click declares 「全人類の緋想天」 (card 7, level 2) and the sword becomes eight sword entities that
  follow the user for 100 ticks, spinning by `num / 3 × 39` degrees a tick. Sword 8 fires a random ring of
  8 red kishitu shots (special 700) every tick, then hands the item back with its damage.
- Rendered additively with alpha `num / 8`.
- X1's half-made ride on the user (its `updateRidden` slowing the user) never runs in 1.7.10; not ported.

## Receipts

Dedicated server (local; P5–P16 together, 10 scenarios PASS, 0 FAIL):

```
FIVE_DIFFICULTIES_P16_HISOU_PASS shots=8
```
