# P1 Mixin hook boundary

P0 intentionally does not inject into Minecraft tick methods.

The Forge-facing entry points are:

- `SakuyaTimeStopRuntime` — one pure `SakuyaTimeStopService` per `ServerLevel`
- `TimeStopHooks.shouldCancelNormalTick(...)`
- `TimeStopHooks.shouldUseStoppedProjectileTick(...)`

P1 will add the smallest Roundabout-derived interception set only after the X1 runtime oracle is recorded:

1. `ServerLevel.tickNonPassenger`
2. `ServerLevel.tickPassenger`
3. generic projectile tick marker/substitution
4. client interpolation freeze

Block/fluid/chunk/particle/animated-texture stopping stays disabled until X1 evidence requires it.

No Roundabout Stand/JoJo class is a dependency of the port.
