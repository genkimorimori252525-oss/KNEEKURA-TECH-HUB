# Implementation checkpoint — P17d Cirno

Date: 2026-11-20
Oracle: X1 `EntityCirno`, `ModelCirno`, `RenderCirno`, `CommonProxy` (spawns, egg).

| X1 | Port |
|---|---|
| `EntityCirno` | `cirno` (`CirnoEntity`), spawn egg 0x00FFE0 / 0x00E0E0, biome modifier `cirno_spawns` (2) |
| `ModelCirno` / `RenderCirno` | `client/mob/CirnoModel` (generated boxes), `P17Renderers.SimpleBoss` + status plate |

## X1 behaviour kept on purpose

- Four phases: normal 1 (38 HP, 7 aqua crystal rings of 2..8 every 50 ticks) → 「アイシクルフォール」 card 19
  (46 HP, yellow 3-way fans only from level 2) → normal 2 (32 HP, white / blue circles then 3 white laser fans,
  20 ticks of invulnerability) → 「パーフェクトフリーズ」 card 9 (58 HP, 4- or 5-way blue fans) → final.
- `applyPotionDamageCalculations` × 0.05 while invulnerable is ported, though invulnerability already rejects
  the hit first (dead code in X1 too).
- Spell-card kills drop 20 point + 20 power items in a wave, 17–18 + looting aqua crystal shot items; the last
  card also drops the icicle sword and an extend.
- `ModelCirno` mirrors `leftWing3` from `rightWing2`, not `rightWing3`; kept.
- Spawn: config rate, standing in a snow layer with ice within 5 × 5 one below. X1 biomes cold taiga (+hills),
  frozen river, ice mountains, ice plains → 1.20 `snowy_taiga`, `frozen_river`, `snowy_plains`.

## Test fix

1.20's 20-tick hurt cooldown rejects a second hit that is not larger than the last one. The Rumia check's
second hit therefore never landed (the test still passed, since the phase step does not look at health).
Both boss checks now reset `invulnerableTime` before each hit and require the phase to be down.

## Receipts

`FIVE_DIFFICULTIES_P17_CIRNO_PASS fired=35`, `FIVE_DIFFICULTIES_P17_RUMIA_PASS fired=54`, P6/P8–P17 all
`RUNTIME_SCENARIO_PASS` (1 local run). Client render not yet checked for Cirno.
