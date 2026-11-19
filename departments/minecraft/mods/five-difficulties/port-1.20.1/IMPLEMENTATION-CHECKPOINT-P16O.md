# Implementation checkpoint — P16o Marisa's broom

Date: 2026-11-20
Oracle: X1 `ItemMarisaBroom`, `EntityMarisaBroom`, `RenderMarisaBroom`.

## Ported

| X1 | Port |
|---|---|
| `ItemMarisaBroom` (魔法の箒) | `magic_broom` (`X1EffectItems.MarisaBroom`) |
| `EntityMarisaBroom` | `MarisaBroomEntity` (hit state synced, as X1's watchers 17–19) |
| `RenderMarisaBroom` | `P16Renderers.MarisaBroom` (tessellated rod and brush; X1's `ModelMarisaBroom` is unused) |

## X1 behaviour kept on purpose

- Right-click places the broom at the feet (entity 0.8 above its 0.5-high box, X1's `yOffset`) and gets on
  it unless already riding or sneaking; the item is used up; silent ("random.drr" does not exist in 1.7.10).
  A melee hit adds 2 mob damage.
- X1 reads the movement keys only on the client, but the ridden movement runs only on the server, where
  "forward" is fixed on and the others off, and the client copy is never told it is ridden. In play the broom
  therefore always accelerates 0.04 along the rider's look and by the rider's pitch, speeds over 0.8 multiply
  by themselves, drag 0.99 / 0.95 / 0.99, half speed in water, no fall damage for the rider. The port keeps
  this: the server moves the broom (no controlling passenger), clients interpolate.
- Empty: × 0.9 sideways, −0.03 a tick, pitch eases back by 1, +0.06 on the ground. Hits over 40 break it into
  its item (creative: nothing). The rider sits 0.65 below the entity, as X1's offsets add up on the server.

## Receipts

Dedicated server (local; P5–P16 together, 10 scenarios PASS, 0 FAIL):

```
FIVE_DIFFICULTIES_P16_BROOM_PASS dx=1.75 dy=0.79
```
