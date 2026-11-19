# Implementation checkpoint — P17e Wriggle; P17 client frame

Date: 2026-11-20
Oracle: X1 `EntityWriggle`, `ModelWriggle`, `ModelTouhouDefault`, `RenderWriggle`, `CommonProxy`.

| X1 | Port |
|---|---|
| `EntityWriggle` | `wriggle` (`WriggleEntity`), spawn egg 0x15224F / 0x83C826, biome modifier `wriggle_spawns` (20, 1–3) |
| `ModelWriggle` (on `ModelTouhouDefault`) | `client/mob/WriggleModel` (hand-written part tree), `P17Renderers.SimpleBoss(...).bright()` |

## X1 behaviour kept on purpose

- Three phases: 30 HP normal → card 35 at 36 HP (the number X1 gives it; adds blue medium sphere bursts of
  16 / 24 / 32 by level, height 2) → card 34 「リトルバグストーム」 at 42 HP (declares only, height 4) → final.
- Normal attack: yellow / aqua rice with the bug-storm specials 3450 / 3451 (delay 3, end 15), then a 5-way
  yellow fan whose deceleration grows each tick (counters 62–71), 147-tick loop.
- Dead X1 branches kept: the sidesteps at counters 24 and 67 sit behind earlier `else if`s and never run; the
  hard-mode extra rice uses `angle`, not the `angle2` it computes.
- Extra hurt wrapper (another magic reduction, motion × 0.01) as Rumia; drops only on spell-card kills.
- `getBrightness` 1.0: the renderer draws her at full light.
- Spawns in the dark (not peaceful) with water within 5 × 5 one below; X1 birch forest (+hills), forest
  (+hills), jungle (+hills), jungle edge, river → 1.20 `birch_forest`, `forest`, `jungle`, `sparse_jungle`, `river`.
- `ModelTouhouDefault` rebuilds the body / head / arm / leg pivots every frame from shoulder 2.4, body 7,
  legs 12; the port's `setupAnim` does the same. X1 sets `mirror` after `addBox`, so nothing is mirrored.

## Shared changes

- `DanmakuMobEntity` now carries X1's `NORMAL_ATTACK02..05` and `SPELLCARD_ATTACK02..06` (Cirno's local copies
  removed).
- Client world smoke gained a P17 frame (fairy, sunflower fairy, phantom, Cirno, Wriggle; normal difficulty
  for that frame only, since X1 danmaku mobs remove themselves in peaceful).

## Receipts

- Server: `FIVE_DIFFICULTIES_P17_WRIGGLE_PASS fan=5`, CIRNO / RUMIA / FAIRY / SUNFLOWER / PHANTOM / BANISH,
  P6/P8–P17 all `RUNTIME_SCENARIO_PASS` (1 local run).
- Client: `P7B_WORLD_SMOKE_PASS`, `P17_CLIENT_FRAME colourfulDelta=0.01852`; the frame was inspected by eye
  (not committed). Cirno drifted 2 blocks toward the camera in that frame despite no AI (z 7.0 → 5.03);
  not yet investigated.
