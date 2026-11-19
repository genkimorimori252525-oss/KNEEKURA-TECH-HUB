# Implementation checkpoint — P12 the spell cards with their own entities

Date: 2026-11-19
Oracle: X1 `THSC_MusouFuuin`, `THSC_MasterSpark`, `THSC_SatuzinDoll`, `THSC_HikouchuuNest`,
`THSC_Fafurotskies_no_Kiseki`; `EntityMusouFuuin`, `EntityMiniHakkero`, `EntitySukima`,
`EntityNuclearShot`, `EntityDanmakuCreeper`; `RenderMusouFuuin`, `RenderMiniHakkero` (+ `ModelMiniHakkero`,
`ModelMiniHakkero2`), `RenderSukima`, `RenderNuclearShot`.

All 35 cards X1 registers are now registered under their X1 names and IDs.

## Ported

| X1 | Port |
|---|---|
| 0 霊符「夢想封印」 + `EntityMusouFuuin` | `EntityCards.MusouFuuin`, `MusouFuuinEntity`, `P12Renderers.MusouFuuin` |
| 1 恋符「マスタースパーク」 + `EntityMiniHakkero` (spell-card constructor) | `EntityCards.MasterSpark`, `MiniHakkeroEntity`, `P12Renderers.MiniHakkero` (two baked layers) |
| 8 メイド秘技「殺人ドール」 + `EntitySakuyaWatch(world, user, TIME_STOP_IN_SPELLCARD)` | `EntityCards.SatuzinDoll`, `SakuyaTimeStopRuntime.startSpellCardX1` |
| 10 幻巣「飛光虫ネスト」 + `EntitySukima` (colours 16 / 17 / 32+) | `EntityCards.HikouchuuNest`, `SukimaEntity`, `P12Renderers.Sukima` |
| 15 奇跡「ファフロッキーズの奇跡」 + `EntityNuclearShot` + `EntityDanmakuCreeper` | `EntityCards.Fafrotskies`, `NuclearShotEntity`, `DanmakuCreeperEntity` (vanilla creeper renderer, as X1) |

## X1 behaviour kept on purpose

- Musou Fuuin orbs (shot ID 0, end 40) grow 0.1 per tick, brake ×0.8 for 15 ticks, then turn at most
  12° per tick toward the target's eyes; when the target is gone they fly straight on.
- The Mini Hakkero sits one block ahead of the user's eyes; its Master Spark is a set laser of ID 24
  (width 4.2, length 60, damage 8, delay 30, end 120). The hakkero leaves at tick 109.
- Master Spark's stars: 7 per tick from tick 30 to 98. X1 overwrites the look vector in place and rotates
  it by 2π, which the 1.7.10 sine table makes the identity.
- Satuzin Doll's time stop starts at card time 36 without the item's duplicate check (only its own user's
  watch blocks it). While the card is inside it, each tick pushes the card's end back one tick, and at
  times 51 / 59 / 67 each blue or red knife has a 25% chance to become a green knife aimed at the target.
- The time stop ends when no player is within its range (X1 `playerCount == 0`).
- Hikouchuu Nest tries up to four random spots per tick (rays from the user's feet); each gap fires one
  purple laser at its tick 5 and closes after tick 9.
- Fafrotskies keeps its roll in the shot's limitSpeed. At the shot's end time: ≤70 eight knives, ≤80 a
  fish, ≤90 a creeper, otherwise a chicken; on 25 December a Hanabeeper, on 1–3 January a nuclear shot,
  both from the real clock.
- Nuclear shot: damage is size × 8 every tick, it hits every entity on its path without stopping,
  cancels other users' shots by full damage, and its block test is inverted (a forward block hit keeps it
  flying); only a block inside one of its three centre lines removes it.
- Hanabeeper: the vanilla tick runs only for the first 20 ignited ticks; at 30 it bursts into three
  spheres of light shots (`Danmaku Level` 2: 20 ways, size 0.3, damage 5), then plays a 40-tick death
  while still alive. Saved with `Fuse` 200.
- `RenderNuclearShot` divides its delay-light colour by 255 twice (almost black); kept.

## Fixes found on the way

- `X1Tess.color` now clamps each channel to 0..1 as the 1.7.10 Tessellator does. 1.20 byte packing
  wrapped negative values, which affected the rainbow colours (`-sin × 2`) of the P11 spell-card circle
  and of Musou Fuuin.
- New render state `SRC_ALPHA, SRC_ALPHA` (`RenderSukima`'s dark back faces), plus culled variants for
  the nuclear shot.

## Receipts

Pure core: 10 suites PASS.

Dedicated server (local; P5/P6/P8/P9/P10/P11/P12 together, 0 failures):

```
FIVE_DIFFICULTIES_P12_CARDS_PASS 0:orbs=17,min=1.47 1:hakkero=1,spark=1,stars=483 8:stop=1,green=93,ran=171 10:gaps=152,lasers=152 15:knives=80,cod=0,creepers=0,chickens=0
FIVE_DIFFICULTIES_P12_FAFROTSKIES_PASS knives=8 cod=1 creeper=1 chicken=1 dec25=hanabeeper jan2=nuclear
FIVE_DIFFICULTIES_P12_CREEPER_PASS burstAt=30 shots=60 removedAfter=60
FIVE_DIFFICULTIES_P12_NUCLEAR_PASS hitAt=1 stoppedAt=21 x=10.00
FIVE_DIFFICULTIES_P12_RUNTIME_SCENARIO_PASS
```

- CARDS: each card declared alone (its declaration and time stop reach 40 blocks). Musou Fuuin: 17 orbs,
  one came within 1.47 of the target's eyes. Master Spark: one hakkero (gone by tick 109), one ID-24 set
  laser, 483 stars. Satuzin Doll: a spell-card time stop of its user, 93 green knives, the card ran 171
  ticks (110 + the 61-tick stop). Hikouchuu Nest: 152 gaps, 152 lasers. Fafrotskies: 10 shots, one outcome
  for all ten (this run rolled knives).
- FAFROTSKIES: every outcome forced through the shot's limitSpeed and a date seam (`Fafrotskies.today`).
- CREEPER: the Hanabeeper bursts at its tick 30 (60 shots) instead of exploding; removed 60 ticks later.
- NUCLEAR: a size-3.2 shot kills a husk on its path and flies on; a stone wall 12 blocks ahead stops it at
  10.0 (its horizontal centre line reaches the wall).

Satuzin Doll's user joins the level (`addNewPlayer`, as the P6 scenario does): X1's watch looks up its
user in the world and ends when no player is in range.

Real client (local, private overlay):

- `FIVE_DIFFICULTIES_P12_CLIENT_RESOURCES_PASS spellCards=35 hakkeroModels=2`: 35 card item models, the
  hakkero / gap textures and both hakkero layers.
- In-world frame `p12_entities.png` (colourful delta 0.040): nuclear shot, gap, three Musou Fuuin orbs and
  the Mini Hakkero with its rings and the Master Spark delay light.

## Not covered

- The Gap item's warp gaps (colours 0–15: warp search, entity warp, dye and remorse-rod interaction), the
  Mini Hakkero item, the Nuclear Control Rod (held / growing nuclear shot) and the Sakuya Watch return on
  `itemEffectFinish` arrive with the items (P16).
- X1 calls `itemEffectFinish` (which returns a Sakuya Watch item) even for a spell-card time stop that
  ends with no player in range; the P3 controller does not. Not checked against X1 at runtime.
- `Danmaku Level` is fixed at its default 2 until the config (P14).
