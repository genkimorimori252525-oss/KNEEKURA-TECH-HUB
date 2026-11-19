# Implementation checkpoint — P16i armour

Date: 2026-11-20
Oracle: X1 `ItemFireRatRobe`, `ItemMarisaHat`, `ItemKappaCap`, `ItemKerobou`, `ModelMarisaHat`, `ModelSuwakoHat`,
the armour materials in `THKaguyaItems`.

## Ported (`X1ArmorItems`, `client/X1HatModels`)

| X1 | Port |
|---|---|
| `ItemFireRatRobe` (HINEZUMI chest, unbreakable) | `fire_rat_robe`, armour texture `hinezumi_1` |
| `ItemMarisaHat` (MARISA helmet, 40) + `ModelMarisaHat` | `marisa_hat`, layer `marisa_hat` |
| `ItemKappaCap` (HINEZUMI helmet, 500) | `kappa_cap`, armour texture `hinezumi_1` (as X1) |
| `ItemKerobou` (SUWAKO helmet, 620) + `ModelSuwakoHat` | `suwako_hat`, layer `suwako_hat` |

## X1 behaviour kept on purpose

- Materials keep X1's reductions (HINEZUMI 1/2/2/2, MARISA and SUWAKO 1/1/1/1) and enchantability 0; each item's
  own durability wins over the material, as X1's `setMaxDamage`.
- Fire rat robe: puts out the wearer's fire every tick; held, a hit burns the target for 20 s and right-click
  guards and puts out the user's fire instead of equipping; unenchanted robes get Fire Protection V; glint.
- Marisa hat: item entities within 5 of the wearer are touched (picked up as usual).
- Kappa cap: in water ×1.2 speed (rising only), each axis capped at 0.5, mends 3; wet on land mends 1; dry wears
  1 a tick but stops at 498, so it never breaks.
- Suwako hat: unenchanted hats get Thorns X (held or worn).
- Hat models: X1 renders only `bipedHead`: the plain head cube (UV 0,0 of the hat texture) plus the hat boxes
  inflated 0.4 and mirrored; no headwear layer.

## Receipts

Dedicated server (local; P5–P16 together, 10 scenarios PASS, 0 FAIL):

```
FIVE_DIFFICULTIES_P16_ARMOUR_PASS
```
