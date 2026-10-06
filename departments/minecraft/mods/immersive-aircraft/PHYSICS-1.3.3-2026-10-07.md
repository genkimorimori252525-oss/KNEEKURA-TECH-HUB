# Immersive Aircraft 1.3.3 — Flight / Runtime Mechanics

## Scope

Reference source:

- repository: `Luke100000/ImmersiveAircraft`
- tag: `1.3.3+1.20.1`
- commit: `550b38d3dfdbf5cb6ec3f78468e0e60725a47605`
- Minecraft: 1.20.1
- Forge build declaration: 47.0.3

This document describes the source-level behavior relevant to Kneekura-bird and Warfare Wings.
It does not claim byte identity with the distributed JAR.

## 1. The fixed-wing inheritance chain

```text
Minecraft Entity
  └─ VehicleEntity
      └─ DyeableVehicleEntity
          └─ InventoryVehicleEntity
              └─ EngineVehicle
                  └─ AircraftEntity
                      └─ AirplaneEntity
                          └─ Warfare Wings concrete airplane
```

Warfare Wings mainly supplies concrete entity/data/weapon content. The motion engine is here.

## 2. The most important fact: tick order

For a mob-piloted aircraft in Kneekura-bird, the effective 1.3.3 control/physics order is:

```text
AircraftEntity.tick()
  derive visual roll from previous smoothed lateral input
  water/trail work
  ↓
EngineVehicle.tick()
  ↓
InventoryVehicleEntity.tick()
  weapon slot/tick work
  ↓
VehicleEntity.tick()
  tickPilot()
    IA resets non-local/mob raw inputs to 0
    Kneekura-bird Mixin @TAIL writes AI x/y/z + engine target
  Minecraft Entity.tick()
  sync/interpolation bookkeeping
  updateVelocity()          <- AircraftEntity
  optional boost
  updateController()        <- AirplaneEntity -> AircraftEntity
  Minecraft Entity.move()
  block checks / contact state
  update smoothed x/y/z     <- AFTER movement
  damage particles etc.
  ↑ return
EngineVehicle.tick() continues
  update engine smoothing  <- AFTER movement
  consume/refuel fuel
```

Two transfer delays follow directly:

1. **steering delay** — the current raw X/Z command is smoothed only after the movement step, so
   physics consumed the previous smoothed control state;
2. **engine delay** — the physical thrust step reads the previous `enginePower`, while the engine
   smoother advances only after `VehicleEntity.tick()` returns.

A fast simulator that applies current commands to current motion without these phase relationships
will systematically overestimate responsiveness.

## 3. Input semantics and smoothing

`VehicleEntity.setInputs(x,y,z)` stores raw values:

- X: left/right control
- Y: throttle increment/decrement and braking trigger
- Z: fixed-wing push/pull pitch input

Fixed-wing controls use the airplane-specific push/pull bindings for Z.

Input smoothing uses `InterpolatedFloat(10)`, i.e. an exponential update factor of 0.1 per tick:

```text
smooth_next = 0.9 * smooth_previous + 0.1 * raw_input
```

Friction/rotation decay can additionally push smoothed X/Z toward zero during
`InventoryVehicleEntity.applyFriction()`.

### Kneekura-bird injection

Kneekura-bird injects at `VehicleEntity.tickPilot` TAIL. This is a well-chosen seam:

- IA has just zeroed inputs for a non-local/mob pilot;
- the AI overwrites them before the later physics/controller methods;
- the real input smoother, real entity orientation, real motion and real engine remain in use.

This is why the headless Forge validation is meaningful physics evidence.

## 4. Effective aircraft properties

`VehicleData` loads properties from datapack JSON by iterating the registered `VehicleStat`
instances. `VehicleProperties.get(stat)` then applies installed upgrade multipliers.

Important 1.3.3 registered fields include:

- `engineSpeed`
- `verticalSpeed`
- `yawSpeed`
- `pitchSpeed`
- `pushSpeed`
- `acceleration` default 1
- `durability` default 1
- `fuel` default 1
- `friction` default 0.015
- `glideFactor`
- `lift`
- `rollFactor`
- `groundPitch`
- `stabilizer` default 0
- `wind`
- `mass` default 1
- `groundFriction` default 0.95
- `waterFriction` default 0.9
- `rotationDecay` default 0.97
- `horizontalDecay` default 0.97
- `verticalDecay` default 0.97

### Upgrade composition

For multiplicative properties:

```text
effective = base * totalUpgrade
```

Upgrade aggregation starts at 1.0, applies negative modifiers multiplicatively first, then positive
modifiers additively, and clamps at zero.

Therefore a fast simulator must use **effective runtime properties**, not assume the raw Warfare
Wings JSON is always the value seen by physics.

## 5. The `driftDrag` trap

The aircraft JSON shipped by Immersive Aircraft itself and the supplied Warfare Wings artifact uses
a property named `driftDrag`.

The 1.3.3 `VehicleStat` registry, however, registers `friction`, not `driftDrag`.
`VehicleData` reads only the registered stat names and gives `friction` its default when absent.

For the inspected 1.3.3 path:

```text
JSON driftDrag
   └─ not requested by VehicleData
      └─ no runtime VehicleStat value produced

JSON friction absent
   └─ VehicleStat.FRICTION default = 0.015
```

No compatibility alias or preprocessing path was found in the inspected source.

This is contrary to some later community explanations that describe `driftDrag` as an active
sideslip parameter. For the 1.3.3 ANCHOR, source behavior takes precedence.

### Kneekura-bird consequence

`tools/parse_aircraft_stats.py` currently calculates theoretical top speed and energy retention
using `driftDrag` as friction. The file even records the 0.015 default but then feeds the JSON value
into the equations.

Those **theoretical** outputs are not source-faithful to the 1.3.3 loader.

The validated `flight_profiles.json` values were measured in the real runtime and are unaffected.
They remain authoritative.

## 6. Orientation and control authority

### Yaw

```text
yaw_next = yaw - effectiveYawSpeed * smoothedX
```

The mod directly changes yaw; there is no required bank-to-turn aerodynamic state.

### Pitch

While airborne:

```text
pitch_next = pitch + effectivePitchSpeed * smoothedZ
```

Then the additive stabilizer pulls pitch toward zero:

```text
pitch_next *= (1 - stabilizer)
```

### Roll

Airborne roll is derived primarily as a visual/control state from lateral input:

```text
roll = -smoothedX * rollFactor * (1 - inWaterLevel)
```

On ground, roll decays by a factor of 0.9.

The key tactical implication is that Immersive Aircraft 1.3.3 is not a conventional bank-angle
fighter-flight model. Turning performance is largely direct yaw authority plus how the changing nose
direction interacts with velocity alignment, friction and lift.

For "realistic-looking" air combat, doctrine can be realistic while the vehicle dynamics remain
arcade-like unless the underlying mod physics is changed.

## 7. Velocity-direction conversion ("lift")

`AircraftEntity.convertPower(forward)` is the heart of the fixed-wing feel.

Conceptually:

1. take the current velocity vector and speed;
2. compute alignment `a = abs(dot(forward, normalize(velocity)))`;
3. bend the normalized velocity direction toward the aircraft forward direction using the `lift`
   coefficient;
4. scale the speed by an alignment-sensitive friction factor.

Equivalent conceptual form:

```text
direction' = lerp(normalize(v), forward, lift)

alignment = abs(dot(forward, normalize(v)))

speed' = |v| * (alignment * friction + (1 - friction))

v' = direction' * speed'
```

This `lift` is not an upward force. It is a **velocity-vector alignment coefficient**. This is why
the aircraft can have meaningful slip/energy behavior despite the simple yaw/pitch controller.

## 8. Friction and custom gravity

After velocity conversion, `applyFriction()` applies environment decay and gravity.

Airborne default:

```text
decay = 1 - friction

vx' = vx * decay * horizontalDecay
vz' = vz * decay * horizontalDecay
vy' = vy * decay * verticalDecay + gravity
```

Water and ground select different decay rules.

The mod disables vanilla entity gravity and supplies its own.

### Fixed-wing gravity

For an `AirplaneEntity`:

```text
horizontalishSpeed = |v| * (1 - abs(forward.y))

gravityFactor = max(0, 1 - horizontalishSpeed * 1.5)

gravity = gravityFactor * (-0.04)
```

with optional Ad Astra gravity scaling beneath that.

Thus sufficient horizontal-ish speed suppresses downward acceleration, while low speed or strongly
vertical orientation restores gravity.

The often-quoted ~0.667 block/tick threshold is only a simplified horizontal-nose interpretation;
the actual term also depends on forward-vector vertical component.

## 9. Glide energy conversion

Before `convertPower`, descending motion can feed forward velocity:

```text
diff = previousY - currentY

if previousY != 0 and glideFactor > 0 and diff != 0:
    v += forward * diff * glideFactor * (1 - abs(forward.y))
```

This is another reason a scalar-speed simulator is insufficient for dogfight energy management.

## 10. Wind

When airborne and not touching water:

```text
windStrength =
    (configWindClear
     + |v|
     + rainLevel * configWindThunder
     + thunderLevel * configWindRain)
    * aircraftWind
```

Two deterministic-ish cosine-noise samples, scaled by mass-dependent time, perturb pitch and yaw.
A small fraction is also injected into horizontal velocity.

For deterministic AI tuning, the fast kernel should support:

- wind disabled for baseline parity;
- fixed seeded/noise-compatible wind for robustness tests.

Do not let unseeded environmental noise obscure policy regressions.

## 11. Engine model

`engineTarget` is a synchronized scalar in [0,1].

The engine smoother defaults to a 20-tick reaction constant, adjusted by effective acceleration:

```text
smoothingSteps = engineReactionSpeed / acceleration
```

Engine power is then:

```text
enginePower = smoothedEngineTarget * sqrt(fuelUtilization)
```

### Fuel utilization

When normal fuel consumption applies:

- utilization depends on the fraction of boiler/fuel slots that still contain buffered fuel;
- low fuel further multiplies utilization by 0.75;
- no fuel slots, disabled consumption or creative exemption can yield utilization 1.

Fuel consumption scales with:

```text
engineTarget * effectiveFuel * configFuelConsumption
```

and fractional consumption is probabilistic.

A deterministic fast simulator may model fuel continuously for search, but exact promotion must
still use the runtime semantics when fuel behavior matters.

## 12. Thrust and braking

After yaw/pitch control, fixed-wing thrust is:

```text
thrust = enginePower^2 * engineSpeed
v += forward * thrust
```

On ground, below full target, a separate push term may replace the normal thrust:

```text
push =
    pushSpeed
    / (1 + |v| * 5)
    * smoothedZ
    * (1 - enginePower)
```

### 1.3.3 braking

When raw movement Y is negative:

```text
engineTarget += 0.1 * movementY
v *= 0.95
```

The `0.95` is hard-coded at this release.

Later 1.20.1 source introduces a data-driven `brakeFactor`; importing that later behavior into the
1.3.3 surrogate would be a version error.

## 13. Movement and collision boundary

After custom velocity/controller work:

```text
move(MoverType.SELF, deltaMovement)
```

delegates actual block collision resolution to Minecraft `Entity.move`.

This boundary includes behaviors a standalone simulator should not pretend to reproduce exactly
without dedicated work:

- voxel/block collision resolution;
- steps and contact flags;
- unusual block shapes;
- fluids;
- loaded/unloaded world state;
- interactions with other entities.

A fast air-combat surrogate only needs a deterministic world-query abstraction for most policy
search. Exact movement parity remains a headless Forge concern.

## 14. Vehicle shapes and projectile hits

Vehicle JSON can define multiple additional bounding boxes. Immersive Aircraft rotates their
offsets using an orientation transform quantized to 256 angular steps.

The active `ProjectileUtilMixin` extends vanilla projectile entity-hit queries:

- it searches nearby `VehicleEntity` objects;
- it checks each additional aircraft AABB;
- it replaces the hit result when an additional vehicle shape is the nearer collision.

This means projectile hit geometry is **not** equivalent to one coarse aircraft sphere or the base
Minecraft entity box.

Fast simulation may begin with a conservative coarse hit volume for shot-opportunity tuning, but
exact hit probability must be calibrated or checked in Forge.

## 15. Collision damage is partly client-originated

`VehicleEntity.move` computes a predicted position, calls Minecraft movement, then checks the
difference if horizontal/vertical collision occurred.

But the damage calculation branch runs only on the client and sends a C2S `CollisionMessage` to
the server.

Consequences:

- a normal player-controlled client run can apply crash damage;
- a dedicated/headless mob-controlled GameTest still uses real `Entity.move` collision geometry,
  but does not automatically exercise the same local-player collision-damage message path;
- future `AircraftDamageAuthority` validation must distinguish **collision geometry** from
  **client-originated crash damage**.

This does not invalidate existing no-ground-contact route/dogfight qualifications; those tests are
primarily geometry/safety checks.

## 16. Damage / durability

Server vehicle health is normalized around 1.0.

Incoming damage is divided by:

```text
durability * config.damagePerHealthPoint
```

before health reduction.

On destruction, non-player-force damage can trigger configurable explosion/drop behavior.
Automatic regeneration is optional and off by default.

For AI, damage state should be read from the real vehicle when exact testing. A fast surrogate can
use normalized health/damage states without simulating visual wobble/particles.

## 17. Weapons and network boundary

### Fire request

Player firing sends:

```text
FireMessage(slot, mountIndex, direction)
```

The server verifies the player is riding an `InventoryVehicleEntity` and calls the selected
weapon's `fire(direction)`.

Kneekura-bird's server AI invokes the real weapon API without needing to fake a client input path.

### BulletWeapon

Server firing:

1. transforms weapon mount/barrel into world coordinates;
2. creates the projectile from the weapon-specific direction/speed;
3. **adds aircraft sampled speed** to projectile velocity;
4. spawns the projectile;
5. sends a visual FireResponse;
6. plays sound.

The aircraft speed source is a 10-tick sampled position delta, not literally the current
`deltaMovement`.

For a shooter-relative intercept solver, using the weapon's muzzle speed while subtracting ownship
velocity from target relative motion is consistent with the projectile inheriting aircraft speed.

### BombBay

The built-in bomb bay uses a separate slow release/cooldown path and can spawn configured entities.
Its own launch speed is zero before inherited aircraft velocity is added.

Do not reuse fixed-gun straight-line lead math for bombing.

## 18. Client/server synchronization

Relevant explicit message paths include:

- `EnginePowerMessage` C2S — client throttle target to server;
- `FireMessage` C2S — weapon slot/index/direction;
- `CollisionMessage` C2S — client-observed crash severity;
- `FireResponse` S2C — visual shot feedback.

Entity position/rotation interpolation remains part of the Minecraft entity synchronization path.
`VehicleEntity.handleClientSync()` uses a ten-step interpolation window for non-local views.

For a headless AI simulator, network serialization should not be reproduced in the decision core.
It belongs in the Minecraft adapter.

## 19. Exact/approximate boundary for Kneekura-bird

### Reproduce source-faithfully in fast code

- raw/smoothed input state;
- engine target and power smoothing;
- effective stats;
- yaw/pitch/stabilizer equations;
- velocity-vector alignment;
- friction/custom gravity;
- glide;
- hard-coded 1.3.3 brake behavior;
- thrust;
- optional deterministic wind;
- weapon time-of-flight / inherited shooter velocity.

### Approximate in the fast environment

- terrain as height field / raycast provider;
- aircraft-aircraft collision volumes;
- projectile hit volumes;
- ground contact / landing response;
- damage model when it is not the policy subject.

### Keep exact in Forge

- Minecraft block collision;
- complex voxel shapes;
- real additional AABB projectile tracing;
- real projectile entity ticks/hit callbacks;
- chunk/world loading;
- packet ownership/client sync;
- client-originated crash damage;
- any behavior whose discrepancy becomes decision-relevant.

## 20. Findings that should change existing Kneekura-bird assumptions

1. Do not use current Immersive Aircraft `1.20.1` branch as the 1.3.3 physics implementation.
2. Do not use Warfare Wings `driftDrag` as runtime friction for 1.3.3.
3. Do not collapse engine/input smoothing into instantaneous control.
4. Do not treat headless Forge crash-health behavior as identical to a real local player's crash path.
5. Do not model bullets as having only absolute muzzle velocity; preserve the aircraft-velocity
   inheritance or solve in the proper relative frame.
6. Continue trusting measured flight profiles over hand-derived theoretical performance.
