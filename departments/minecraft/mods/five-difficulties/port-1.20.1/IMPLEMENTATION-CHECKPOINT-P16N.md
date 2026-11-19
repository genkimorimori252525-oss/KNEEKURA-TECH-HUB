# Implementation checkpoint — P16n Kinkakuji ceiling

Date: 2026-11-20
Oracle: X1 `ItemKinkakuzi`, `EntityKinkakuzi`, `RenderKinkakuzi`, `ModelKinkakuzi`.

## Ported

| X1 | Port |
|---|---|
| `ItemKinkakuzi` (金閣寺の一枚天井, glint) | `kinkakuzi` (`X1EffectItems.Kinkakuzi`) |
| `EntityKinkakuzi` | `KinkakuziEntity` (time since hit, direction and damage synced, as X1's watchers 17–19) |
| `RenderKinkakuzi` + `ModelKinkakuzi` | `P16Renderers.Kinkakuzi`, layer `kinkakuzi` |

## X1 behaviour kept on purpose

- Thrown from the head at 0.2 forward and 0.7 up (sneak 1.0); the item is used up. X1 plays "random.drr",
  which 1.7.10 does not have, so it is silent; the port is silent too.
- A 6 × 0.3 box centred on its position (1.7.10 `yOffset = height / 2`), solid like a boat. Out of water it
  falls 0.04 a tick, in water it rises; drag 0.99 / 0.95 / 0.99 unless pushed into a wall fast; halved on the
  ground; yaw turns at most 20° a tick toward its travel.
- Rideable (right-click); the rider steers like a boat: forward input adds speed × 0.05 along the rider's yaw,
  speed up to 0.35, the speed multiplier eases between 0.07 and 0.35 over 35 ticks. The rider sits 0.5 to the
  side (cos/sin of yaw) and 0.3 up.
- Server side, anything below it within 0.5 (other than the rider, items, XP orbs, shots and the thrower)
  takes `(int)(drop × 40) + 2` indirect magic damage while it is not rising; it pushes boats and other ceilings.
- Hits add damage × 10; over 40 (or any creative hit) it breaks, dropping its item unless creative.

## 1.20 adaptation

- Movement runs on the controlling side as for 1.20 boats (the riding player's client, otherwise the server);
  the landing drop is measured between server ticks.

## Receipts

Dedicated server (local; P5–P16 together, 10 scenarios PASS, 0 FAIL):

```
FIVE_DIFFICULTIES_P16_KINKAKUZI_PASS rise=3.82 dealt=16.0
```
