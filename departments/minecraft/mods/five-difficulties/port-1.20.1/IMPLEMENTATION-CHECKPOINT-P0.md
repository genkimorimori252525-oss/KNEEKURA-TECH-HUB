# Five Difficulties X1 Preservation Port — P0 implementation checkpoint

Date: 2026-10-07

Branch:
`jolly/five-difficulties-1201-port-p0-2026-10-07`

Target:
- Minecraft 1.20.1
- Forge 47.4.6
- Java 17
- private preservation/research use

## Implemented

### Deterministic legacy-pattern core

Pure Java, no Minecraft dependency:

- `Vec3d`
- `LegacyShotSpec`
- `LegacyLaserSpec`
- `ShotSpawn`
- `LaserSpawn`
- `PatternContext`
- `PatternSink`
- `PatternFrame`
- `LegacyPattern`
- `LegacyPatternRuntime`
- `LegacyPatterns.fan`

The numeric legacy type/color fields intentionally remain raw until the exact X1 archive/source mapping is repinned.

The runtime is a strict integer-tick clock and does not interpolate or skip ticks.

### Sakuya time-stop pure core

JoJo/Minecraft-independent:

- `TimeStopFlags`
- `SakuyaTimeStopInstance`
- `TimeStopSubject`
- `TimeStopPolicy`
- `SakuyaTimeStopService`
- `StoppedProjectileState`
- explicit `TimeStopDecision`

P0 engineering policy:
- source moves in own stop;
- in-range Living entities freeze;
- existing projectiles freeze;
- source-created projectiles during stop use a special projectile path;
- ItemEntity/block/fluid/chunk/particle/texture/day-time behaviors remain unasserted/off by default.

`LEGACY_X1_UNRESOLVED` projectile mode intentionally throws instead of guessing unmeasured legacy behavior.

### Roundabout-derived projectile engineering mode

`ROUNDABOUT_DECELERATE` captures the donor concept:
- proximity slowdown;
- per-step speed-multiplier decay;
- collision hold;
- original resume velocity retained.

This is an engineering reference mode, not an X1 fidelity claim.

### Forge boundary

Added:
- `@Mod` bootstrap;
- DeferredRegister boundary;
- SimpleChannel boundary;
- one `SakuyaTimeStopService` per `ServerLevel`;
- Minecraft Entity → pure `TimeStopSubject` adapter;
- hook methods for future Mixins.

No tick-cancelling Mixin is active in P0.

## Verification

Local Java 17 regression:

`LEGACY_PATTERN_CORE_REGRESSION_PASS`

`SAKUYA_TIMESTOP_CORE_REGRESSION_PASS`

The GitHub workflow:
`.github/workflows/five-difficulties-port-p0.yml`

uses the exact official Forge 1.20.1-47.4.6 MDK (SHA-1 `1a1c045f235262ff617e285ea2156571ea93bfbe`) and overlays only this port's `src` tree before running `compileJava jar`.

GitHub Actions run **37515589105** completed **SUCCESS** on commit
`b2212641513de7f68a9697fafdc6534148ec821f`.

Verified in that run:
- pure Java preservation-core regressions: PASS;
- exact official Forge 1.20.1-47.4.6 MDK download + SHA-1 verification: PASS;
- `compileJava jar`: PASS;
- bounded evidence artifact upload: PASS.

A successful compile/package is still **not** Minecraft runtime verification.

## Deliberately not implemented yet

- original X1 source/assets import;
- source/archive SHA receipt for X1;
- real Shot Entity/Renderer;
- real Laser Entity/Renderer;
- Master Spark;
- all registered spell cards;
- red Homing Amulet;
- Sakuya clock/item UI;
- actual ServerLevel tick Mixins;
- projectile marker synchronization;
- client interpolation freeze;
- X1 recipes/items/mobs;
- X1 sound hooks;
- virtual/batched bullet optimization.

## Next implementation gate — P1

Before real content parity work:

1. repin exact X1 archive/hash and regenerate source↔class inventory;
2. extract the exact legacy shot/color/type tables and first representative item;
3. record X1 Sakuya runtime oracle for at least:
   - existing projectile;
   - newly thrown knife;
   - mob;
   - ItemEntity;
   - time-resume tick;
4. add the smallest tick-cancellation Mixins:
   - ServerLevel non-passenger;
   - passenger;
   - projectile created-during-stop marker/substitute tick;
5. implement one visual shot Entity/Renderer using the original asset and compare against X1.

No high-density optimization should precede parity of that first representative technique.
