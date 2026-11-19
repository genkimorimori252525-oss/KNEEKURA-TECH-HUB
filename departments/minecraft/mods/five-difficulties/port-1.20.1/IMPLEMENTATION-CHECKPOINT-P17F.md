# Implementation checkpoint — P17f Toziko

Date: 2026-11-20
Oracle: X1 `EntityToziko`, `ModelToziko`, `RenderToziko`, `THShotLib.pos_Random`, `CommonProxy`.

| X1 | Port |
|---|---|
| `EntityToziko` | `toziko` (`TozikoEntity`), spawn egg 0x60D683 / 0x376E91, biome modifiers forest 9 / plains 7 / swamp 20 |
| `ModelToziko` / `RenderToziko` | `client/mob/TozikoModel` (generated), `P17Renderers.SimpleBoss` |
| `THShotLib.pos_Random` | `X1Danmaku.pos_Random` |

## X1 behaviour kept on purpose

- Two phases: 40 HP normal, then card 40 at 44 HP (declares only; 200-tick loop); the second death is final.
- Normal: ticks 0–19 of every 80, 1 + level blue arrows (delay 1, end 20) with the Gagouji Cyclone Toziko
  special 4020, from `pos_Random` in `angle_Random` directions, slowing by 0.03 a tick; a random 16-tick
  sidestep at tick 24.
- `pos_Random` ignores its range and offsets by one random unit vector from a fresh `Random`, as X1.
- Drops on every player kill (not only spell cards): yellow arrow shot items with the Gagouji special 4000,
  power and point items.
- Model quirk kept: with no card motion the left arm's Y copies the right arm's Z.
- Natural spawns only in the dark, not peaceful, and only while it thunders.

## Receipts

- Server: `FIVE_DIFFICULTIES_P17_TOZIKO_PASS arrows=3`, P6/P8–P17 all `RUNTIME_SCENARIO_PASS` (1 local run).
- Client: `P7B_WORLD_SMOKE_PASS`; the P17 frame (fairy, sunflower fairy, phantom, Cirno, Wriggle, Toziko) was
  inspected by eye (not committed).
