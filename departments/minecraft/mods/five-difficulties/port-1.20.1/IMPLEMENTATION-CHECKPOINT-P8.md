# Implementation checkpoint — P8 generic THShot backend (Phase A)

Date: 2026-11-19
Oracle: X1 bundled sources (`EntityTHShot`, `THShotLib`, `ShotData`, `DanmakuConstants`,
`ItemTHShot`, `RenderTHShot`, `THKaguyaRenderLib`) from the canonical X1 archive
(`6307789d…e634`).

P8 is the danmaku foundation that spell cards, mobs and most items build on: one entity per
legacy shot, literal X1 numbers, server-authoritative like X1.

## What was ported

| X1 | Port |
|---|---|
| `DanmakuConstants`, `THShotLib.DAMAGE/SIZE/ways`, `ItemTHShot` tables, `RenderTHShot` colours | `core/x1/X1ShotTables` |
| `ShotData` | `core/x1/X1ShotData` |
| movement half of `EntityTHShot.onUpdate` (delay, time-stop guard, yaw rotation, `updateAngle`, `shotAcceleration`, `FALL01`, gravity, `timeProcess`) | `core/x1/X1ShotMotion` (pure, tested) |
| `createShot` / `createWideShot` / `createCircleShot` / `createRingShot` / `createRandomRingShot` / `createSphereShot`, incl. RANDOM / RAINBOW colour handling | `core/x1/X1ShotPatterns` (pure, tested) |
| `EntityTHShot` world side: owner checks, end time, `hitCheck` / `hitEntityCheck` / `onImpact`, shot-vs-shot cancellation, difficulty damage, `attackEntityFrom` | `forge/entity/THShotEntity` |
| `ItemTHShot.shootDanmaku` / `onItemRightClick` / colours / tooltip, X1 NBT keys | `forge/item/THShotItem` (6 items) |
| `RenderTHShot.renderNormalShot`, delay `renderLightEffect`, billboard | `forge/client/THShotRenderer`, `X1RenderTypes` |

Items in P8: small, tiny, medium, big, circle, heart shot (every X1 shot item drawn by
`renderNormalShot`). The renderer also covers the pearl form.

## X1 quirks kept on purpose (all pinned by tests)

- Speed goes through `MathHelper.sqrt_double`, i.e. float precision.
- Acceleration is applied along the stored unit angle, not the motion.
- The animation counter jumps to `lastTime` after the delay, so the end time **includes**
  the delay: `end=80` shots are removed on tick 83 whatever the delay.
- `setDead()` at end time does not return: the shot still moves and can hit on that tick.
- A one-way "Sector" shot fires at `-wide/2` (1.5° off the aim).
- Even-way circles add half a step so one shot stays on the aim.
- `createSphereShot` leaves a RANDOM colour resolved (never restored).
- Creative use creates the stack tag only after reading it, so later creative shots are red
  (Color 0).
- The client does not simulate shots; it follows server position updates (X1's client copy
  never received the shot parameters either).

## Receipts

Pure core (`tools/run-pure-core-tests.sh`, JDK 17): 9 suites PASS, including the new
`X1_SHOT_CORE_REGRESSION_PASS` (15 checks).

Dedicated server (local run of the CI step, 2026-11-19 14:14, fresh flat world):

```
FIVE_DIFFICULTIES_P8_MOTION_PASS ticks=12 x=-17.85 y=-52.31 speed=0.5048761963844299
FIVE_DIFFICULTIES_P8_END_TIME_PASS removedAtTick=13
FIVE_DIFFICULTIES_P8_HIT_PASS difficulty=EASY damage=1.6800003 ticks=10
FIVE_DIFFICULTIES_P8_ITEM_FORMS_PASS forms=6
FIVE_DIFFICULTIES_P8_RUNTIME_SCENARIO_PASS
FIVE_DIFFICULTIES_P6_RUNTIME_SCENARIO_PASS fullFrozenTicks=4 halfObservedDelta=3 homingTicks=11 homingHealthDelta=5.0
```

- MOTION: live positions equal the pure kernel **exactly** on every tick (3 delay ticks,
  acceleration to the limit, gravity).
- HIT: 2.4 (SMALL) × 0.7 (EASY, non-player owner) = 1.68 indirect-magic damage.
- ITEM_FORMS: a real item use through a fake player spawns 3 / 7 / 5 / 8 / 8 / 6 shots for
  Point / Random / Sector / Around / Sphere / Ring with Number 3 / 7 / 5 / 8 / 8 / 6.

Real client (local, private overlay):

```
P7b frame p8_shots.png ... 
FIVE_DIFFICULTIES_P7B_WORLD_SMOKE_PASS homingWarmDelta=0.00217 p8ColourfulDelta=0.11904 ...
FIVE_DIFFICULTIES_P7_CLIENT_RESOURCES_PASS canonicalTextures=7 watchLayer=ok itemModels=9
```

Reviewed by eye: all six forms × 8 colours render from the original X1 sprite strips in the
X1 colour order; BIG uses additive blending; the six shot items show the two-layer tinted icon.

CI runs the P8 server scenario together with P6 (`ScenarioShutdown` halts the server once
every enabled scenario has finished).

## Not ported yet (next gates)

- Other shot forms' renderers: scale, butterfly, star, rice, crystal, light, kunai, talisman,
  big light, oval, familiar, arrow, phantom, amulet, knife, wind, kishitu.
- Special shots except FALL01: homing, diffusion, bound, fire, explosion, wind.
- Shot-material bonus drop, `danmakuRemove`, player power, danmaku-mob damage multipliers.
- The danmaku crafting table (it writes the NBT that shapes the item patterns).
- Lasers (`EntityTHLaser`), spell cards.
