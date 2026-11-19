# Implementation checkpoint — P16j silver knives, and 1.7.10 box intercepts

Date: 2026-11-20
Oracle: X1 `ItemSilverKnife`, `EntitySilverKnife`, `RenderSilverKnife`, `THKaguyaLib.createSilverKnife`,
`CommonProxy.registerDispenser` (knife part), 1.7.10 `AxisAlignedBB.calculateIntercept`.

## Ported

| X1 | Port |
|---|---|
| `ItemSilverKnife` damage 0..3 | `silver_knife_blue/red/green/white` (white not in the creative tab, as X1) |
| `EntitySilverKnife` + renderer | `SilverKnifeEntity`, `P16Renderers.SilverKnife` (existing `SilverKnifeModel`) |
| `createSilverKnife` | `SilverKnifeEntity.createSilverKnife` |
| knife dispenser behaviour | `X1ShotItems.registerDispenser` (common setup) |

## X1 behaviour kept on purpose

- Thrown at 0.28 with acceleration half the start speed; it waits until its count passes 2 (white: 30 more
  ticks), then flies with drag 0.95 (0.8 in water) and gravity 0.008 × count; count keeps rising, also while
  the knife sits in a block.
- Living hits deal 4 as a mob attack; a target still in hurt time loses 4 health directly (X1 `heal(-4)`).
  Players are never hit. The knife flies back at −0.21 and is spent if white.
- Hard blocks (approximated: pickaxe-mineable, glass, ice) bounce a fast knife — red keeps 0.25 × speed per
  bounce, the others nearly stop; slow knives and soft blocks take the knife in, and it can be picked up.
  An entity hit reads the block at (0, 0, 0), as X1's entity MovingObjectPosition carries zero coordinates.
- A green knife sheds a white knife every other tick (ticks 3..59) while faster than 0.08, carrying its
  acceleration; X1 drops the normalised angle, so the child speed is the parent speed squared.
- Dispensers fire knives at 0.58 along an unnormalised direction.
- X1's `attackEntityFrom(DamageSource, int)` never overrides the float method, so knives cannot be knocked
  back by attacks; not ported.

## 1.20 difference fixed across the port

1.20 `AABB.clip` misses when the segment starts inside the box; 1.7.10 `calculateIntercept` still hits where
the segment leaves it. Knives tunnelled through a zombie because of this. `forge/shot/X1Hit.intercept` restores
the 1.7.10 rule and now backs every entity hit test that used `clip`: `THShotEntity`, `THLaserEntity`,
`NuclearShotEntity`, `OnmyoudamaEntity`, `GapItem`, the death scythe and the spell-card declaration.
After the change P5–P16 passed 3 runs in a row (10 scenarios each, 0 FAIL). The P9 homing check, which
failed intermittently before, passed all 3. Whether this change fixed it is a hypothesis; it is not
measured.

## Receipts

```
FIVE_DIFFICULTIES_P16_SILVER_KNIFE_PASS whites=5
```
