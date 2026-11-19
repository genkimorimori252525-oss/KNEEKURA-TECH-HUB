# Implementation checkpoint — P16f Nazrin pendulum

Date: 2026-11-20
Oracle: X1 `ItemPendulum`, `EntityPendulum`, `RenderPendulum`.

## Ported

| X1 | Port |
|---|---|
| `ItemPendulum` | `nazrin_pendulum` item (`X1EffectItems.Pendulum`) |
| `EntityPendulum` | `PendulumEntity` (search angle × 100 and count synced, as X1's watchers 16 / 17) |
| `RenderPendulum` | `P16Renderers.Pendulum` |
| `thKaguya.msg.pendulum1..3` | same keys in the port's lang files (X1 text) |

## X1 behaviour kept on purpose

- Searches for the block item in the hotbar slot right of the pendulum (nothing in slot 9); sneak = high
  sensitivity (±24 instead of ±12). The pendulum leaves the inventory and a chat line names the block.
- Every 60 ticks it counts matching blocks in the cube (capped at 32); with any found it turns
  `count / 3` per tick and its yaw 3 per tick; the renderer swings it `count / 48` out.
- Returns to the inventory (dropped if full, nothing for creative) when the user sneaks after 10 ticks or is hurt;
  dropped on the ground with no user.

## Difference forced by 1.20

- X1 compares localized names; the port compares the block's translation key (servers cannot localize), so
  1.7.10 metadata variants that shared a name are separate blocks here.

## Receipts

Dedicated server (local; P5–P16 together, 10 scenarios PASS, 0 FAIL):

```
FIVE_DIFFICULTIES_P16_PENDULUM_PASS found=5
```

## Deferred

- `ItemCursedDecoyDoll` / `EntityCursedDecoyDoll` extend X1's `EntityDanmakuMob`; they move to P17 with the mobs.
