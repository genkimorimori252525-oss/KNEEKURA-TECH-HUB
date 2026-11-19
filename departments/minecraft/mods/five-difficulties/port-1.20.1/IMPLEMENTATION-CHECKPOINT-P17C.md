# Implementation checkpoint — P17c Rumia, boss plate; the P9 / P13 flakes

Date: 2026-11-20
Oracle: X1 `EntityRumia`, `ModelRumia`, `RenderRumia`, `RenderTHBoss`, `THShotLib.explosionEffect`.

| X1 | Port |
|---|---|
| `EntityRumia` | `rumia` (`RumiaEntity`), spawn egg, biome modifiers `rumia_spawns` (4) / `rumia_dark_forest_spawns` (7) |
| `ModelRumia` / `RenderRumia` | `client/mob/RumiaModel` (generated boxes), `P17Renderers.Rumia` (12-wide darkening sphere) |
| `RenderTHBoss` | `client/THBossRenderer` (frame, health or spell-card bar, name and card name above the boss) |

## X1 behaviour kept on purpose

- Two phases: 36 HP normal attack (blue then red circles with 1 + level rings, sidestep, tiny rainbow sweep,
  step back, 127-tick loop), then on "death" 「ムーンライトレイ」 (card 28) at 44 HP with tiny white rings; the
  second death is final with explosions every 9 death ticks. Each phase change clears enemy danmaku within 40
  (X1) and gives 60 ticks of invulnerability.
- 1.7.10 ran `onDeath` (drops) on every phase death; the port clears 1.20's `dead` flag when a phase starts
  so `die()` runs again, as X1.
- X1's Rumia wraps the base `attackEntityFrom` once more: three magic-damage reductions and motion × 0.000001
  on a hit; kept.
- Spawns like a monster in the dark, behind the boss switch.

## Test harness change: the long-standing P9 / P13 flakes

The dedicated-server scenarios run on a superflat world at y = −60. 1.20 spawns slimes in slime chunks below
y 40 regardless of light, so random slimes could become the homing target (P9) or catch the wind (P13). Both
checks failed in 2 of 2 local runs while P17 was being added. After `spawn-monsters=false` in the scenario
server properties (local script and CI) all 11 scenarios passed 4 runs in a row. The slime cause is a
hypothesis: the improvement is measured, the cause itself was not observed directly. The scenarios still
spawn every mob they test themselves.

P17 also moved to (+130, 0): X1's phase changes clear danmaku within 40, which reached P10's laser at (24, 0).

## Receipts

`FIVE_DIFFICULTIES_P17_RUMIA_PASS fired=54` (3 rings of 18 at level 2), with P5–P17: 11 scenarios PASS × 4.
