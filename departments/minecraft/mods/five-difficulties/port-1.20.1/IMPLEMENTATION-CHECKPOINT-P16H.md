# Implementation checkpoint — P16h tools

Date: 2026-11-20
Oracle: X1 `ItemBuddhaStoneBowl`, `ItemByoukiheiyuMamori`, `ItemKabenuke`, `ItemHisyaku`.

## Ported (`X1ToolItems`)

| X1 | Port |
|---|---|
| `ItemBuddhaStoneBowl` (仏の御石の鉢) | `buddha_stone_bowl` |
| `ItemByoukiheiyuMamori` (病気平癒守) | `byoukiheiyu_mamori` |
| `ItemKabenuke` (壁抜けの鑿) | `wall_passing_chisel` |
| `ItemHisyaku` full / empty (船幽霊の柄杓) | `ship_ghost_dipper`, `ship_ghost_dipper_empty` |

## X1 behaviour kept on purpose

- Bowl: stone tool damage (4 + 1), digs everything at 4, harvests what a stone pickaxe can, glint, and never
  wears (X1 skips the damage on hits and digs).
- Charm: stack 16, 24-tick use; clears all effects and gives Regeneration IV for 3 s, nothing while hurt; a
  creative click works at once too.
- Chisel (config "Can Use Wall-Passing Chisel"): from the clicked block, walks up to 16 blocks against the face
  and moves the player into the first air block with air above (or air below, one lower); bedrock stops it;
  1 durability per pass. The position is set directly, then sent, as X1.
- Dipper: sneak swaps full / empty keeping the damage. Full pours a water source next to the face it points at
  (or at the player's feet when it points at nothing), also over a solid block there (X1's `isBlockSolid`
  check), costing 2; in the nether it only fizzes. Empty removes the source it points at and stays empty.

## Receipts

Dedicated server (local; P5–P16 together, 10 scenarios PASS, 0 FAIL):

```
FIVE_DIFFICULTIES_P16_BOWL_CHARM_PASS
FIVE_DIFFICULTIES_P16_CHISEL_PASS landedDx=5.00
FIVE_DIFFICULTIES_P16_DIPPER_PASS
```
