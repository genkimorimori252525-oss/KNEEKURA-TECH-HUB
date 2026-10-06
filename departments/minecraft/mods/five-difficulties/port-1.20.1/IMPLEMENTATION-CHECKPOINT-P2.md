# Five Difficulties X1 Preservation Port — P2 implementation checkpoint

Date: 2026-10-07

Branch:
`jolly/five-difficulties-1201-port-p2-2026-10-07`

Parent:
`jolly/five-difficulties-1201-port-p1-2026-10-07`

Status: **P2 COMPLETE — first live X1 projectile path compiled on Forge 1.20.1**

## Canonical X1 reacquisition

Historical Google Drive bundle was recovered again.

Outer bundle:
- `5難題+アドオン達.zip`
- 4,548,944 bytes
- SHA-256 `9d8ea665ab8b925437fa2294f34051b8b9bdc6e9036c540f5c2a77432b689a98`

Canonical inner X1:
- `五つの難題MOD+ ver2.90.1.X1-1.7.10`
- 4,596,892 bytes
- SHA-256 `6307789d5f2f43b762bcc7d5aa03d67207eaa237fb124447e7ea951aa856e634`

Both exactly match the earlier PR #93 receipts.

Canonical Homing assets:
- shot PNG SHA-256 `badfeba690c2dee69ddb38c9f3a0fe538643ca1d439121e95959fd7dfb93b4d9`
- item PNG SHA-256 `650f71239534ef521bea3e1e29893ed1cb8302721854c44d0536b76be02f5773`

The original bytes are not committed to public TECH-HUB.

## Exact X1 red Homing Amulet contract

Resolved from canonical source:

- `FORM_AMULET = 27`
- `RED = 0`
- `HOMING01 = 10`
- delay = 0 ticks
- lifetime = 90 ticks
- first/limit speed = 0.7
- acceleration = 0
- gravity = 0
- spawn distance = 0.5
- base angle = 0

Normal:
- 5 shots
- 100° total fan
- logical/hit size 0.4
- damage 5

Focused/Shift:
- 2 shots
- 20° total fan
- logical/hit size 1.0
- damage 8
- speed still 0.7

Exact X1 `THShotLib.createWideShot` math is implemented in `X1WideShotGeometry`.

For +Z aim:
- normal offsets: -50, -25, 0, +25, +50°
- focused offsets: -10, +10°

## Homing implementation

Pure `X1HomingMath` and live Forge projectile implement:
- ~24-block candidate search volume;
- animal/villager exclusion;
- owner/source exclusion;
- LOS/block rejection;
- target score `distance * abs(sin(angle/2))`;
- max 4° steering per tick;
- X1 shot-origin Y math;
- preserved speed magnitude.

Exact anti-parallel vectors are fail-safe rather than allowed to produce NaN.

## Collision implementation

P2 no longer delegates the red projectile to the generic modern `ProjectileUtil` hit geometry.

The live projectile reproduces the X1 collision shape concept:
- extend the movement sweep by half the logical `ShotData.size`;
- inflate target AABB by half shot size;
- choose nearest intersected candidate;
- exclude animals/villagers/owner;
- accept LivingEntity and EnderDragonPart;
- run three diameter block probes at the current shot center when the main sweep misses.

Modern BlockState projectile side effects/game-event emission are intentionally not called on an X1 default block hit; the shot is discarded like the old default path.

Deferred:
- generalized THShot-vs-THShot cancellation/damage subtraction;
- Five Difficulties mob-specific damage multipliers;
- generalized shared THShot runtime.

## Visual implementation

The live renderer reconstructs canonical `RenderHomingAmulet` behavior:

- original source texture is 64×32;
- left 32×32 half only, U 0..0.5;
- X rotation by projectile pitch;
- Y rotation `180 - animationCount*23`;
- first red pass scale 0.5;
- second matrix scale ×0.55, effective 0.275;
- second tint: RGB (255,25,25), alpha 0.6;
- blend: ONE / ONE_MINUS_SRC_COLOR;
- culling disabled during draw;
- exact X1 vertex/UV orientation.

Critical fidelity distinction:
- `ShotData.size` controls logical hit geometry;
- red renderer scale remains 0.5 in both normal and focused modes.

Thus focused red does **not** become 2.5× larger visually merely because logical size changes from 0.4 to 1.0.

## Private asset overlay

`tools/import-private-x1-assets.py`:
- accepts the canonical outer bundle or canonical inner X1 ZIP;
- verifies the archive SHA;
- verifies each PNG SHA;
- copies only the two required PNGs into the local 1.20.1 resource overlay.

Copied PNG paths are gitignored.

## Live Forge content

Implemented:
- `HomingAmuletItem`
- `HomingAmuletProjectile`
- EntityType registration
- Item registration
- combat creative-tab placement
- entity renderer registration
- item JSON + JA/EN names
- server-side firing
- normal vs Shift/focus topology
- arrow-like firing sound
- X1 item consumption
- velocity tracking/sync configuration

The live projectile uses an indirect-magic DamageSource consistent with the old `causeIndirectMagicDamage(projectile,user)` family.

## Verification

Latest completed GitHub Actions validation:

- run **37521984099**
- conclusion: **SUCCESS**

Verified:
- pure Java preservation regressions: PASS
- canonical X1 geometry/homing regressions: PASS
- exact official Forge 1.20.1-47.4.6 MDK SHA verification: PASS
- `compileJava jar`: PASS
- bounded evidence artifact upload: PASS

Separate local raw-byte verification again reproduced the exact outer/inner/PNG SHA-256 values above.

This is still **compile/package validation**, not a claim that Minecraft client runtime appearance has been visually compared in-game.

## Not yet verified/runtime-complete

- actual 1.20.1 client launch with private PNG overlay;
- side-by-side X1 vs 1.20.1 screenshots;
- multiplayer projectile behavior;
- X1 projectile-vs-projectile cancellation;
- Five Difficulties-specific mob damage multiplier;
- blue/diffusion Homing Amulet metadata variant;
- generalized THShot base;
- high-density optimization.

## Next gate — P3 Sakuya Time Stop

P3 should now switch focus to the other high-risk preservation primitive:

1. inspect canonical X1 `EntitySakuyaWatch`, `EntitySakuyaStopWatch` and `THKaguyaTimeStopEventHandler` directly;
2. convert the previously approximate 160/100/60/40 timing values into exact static values where possible;
3. identify exactly which entity/tick categories X1 freezes/slows;
4. implement the smallest Roundabout-derived ServerLevel/entity/projectile Mixin layer needed for those exact X1 rules;
5. keep JoJo-specific stored-damage/cooldown/lore behavior out;
6. compile first, then perform bounded Minecraft runtime verification.

No all-content port or bullet batching should precede this time-stop parity gate.
