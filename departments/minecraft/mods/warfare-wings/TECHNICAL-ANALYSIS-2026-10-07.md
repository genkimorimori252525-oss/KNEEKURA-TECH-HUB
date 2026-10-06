# Warfare Wings 1.1.4 — Technical Analysis (2026-10-07)

## Scope and evidence boundary

This is a static analysis of the exact user-supplied ANCHOR JAR pinned in
[ANCHOR-JAR-EVIDENCE.json](ANCHOR-JAR-EVIDENCE.json). No supplied-artifact Minecraft runtime was
started in this batch.

Public project/release pages are reconnaissance. The existing Kneekura-bird repository and the
public Immersive Aircraft source are dependency/context evidence. Older runtime results are not
silently promoted to this supplied binary because artifact identity differs from the public runtime
artifact previously described by Kneekura-bird.

## 1. Architecture in one sentence

Warfare Wings is a data-heavy WWII aircraft/weapon addon whose concrete airplane entities inherit
their movement engine from Immersive Aircraft.

The key reuse boundary is therefore:

```text
Warfare Wings aircraft JSON
  -> per-aircraft coefficients / geometry / seats / weapon mounts
Warfare Wings concrete Entity
  -> Immersive Aircraft AirplaneEntity
     -> AircraftEntity
        -> EngineVehicle / VehicleEntity
           -> Minecraft Entity movement / collision / synchronization

Warfare Wings weapon
  -> Immersive Aircraft BulletWeapon
     -> Immersive Aircraft network / mount / ammo abstractions
```

## 2. Aircraft data surface

The supplied JAR contains 90 `data/warfare_wings/aircraft/*.json` files. Twenty-four are base
aircraft and 66 are scheme/livery variants.

All 90 contain an `ai` object in this supplied artifact.

Base role split:

- fighter: 14
- bomber: 5
- attacker: 4
- torpedo_bomber: 1

Base doctrine split in the current data:

- energy_fighter: 11
- turn_fighter: 3
- attacker: 4
- escort: 6

The six `escort` values are attached to the five heavy bombers plus G4M and should be treated as
current project metadata, not evidence that Warfare Wings implements an escort AI.

Representative values:

| Aircraft | role | doctrine | engineSpeed | yawSpeed | pitchSpeed | lift | drag/friction field | mass |
|---|---|---|---:|---:|---:|---:|---:|---:|
| A6M | fighter | turn_fighter | 0.075 | 3.8 | 3.5 | 0.135 | 0.008 | 5.4 |
| P-51D | fighter | energy_fighter | 0.100 | 3.0 | 3.0 | 0.150 | 0.010 | 6.5 |
| B-17 | bomber | escort | 0.045 | 1.2 | 1.1 | 0.280 | 0.020 | 18.0 |

Other important physical/data fields observed across base definitions include `fuel`,
`durability`, `pushSpeed`, `glideFactor`, `rollFactor`, `groundPitch`, `wind`,
bounding boxes, passenger positions and weapon/inventory mounts.

### AI metadata warning

The `ai` block is not a native Warfare Wings public-release behavior proof. Kneekura-bird's own
runtime-gap note states that its previously inspected public 1.1.4 runtime JAR had 90 aircraft JSON
entries and zero `ai` blocks. Together with the binary hash mismatch, the safest interpretation is
that this supplied JAR is an alternate/repacked/project-modified artifact. Exact origin remains
UNKNOWN.

## 3. Flight physics ownership

Representative Warfare Wings aircraft classes such as the A6M, P-51D and B-17 extend
`immersive_aircraft.entity.AirplaneEntity`.

The public Immersive Aircraft `1.20.1` source branch makes the inherited control structure clear.
This branch is useful implementation evidence but is not asserted here to be byte-identical to the
exact Immersive Aircraft 1.3.3 binary used by Kneekura-bird's historical GameTests.

### 3.1 Vehicle tick

At the dependency level, `VehicleEntity.tick()`:

1. samples the pilot / input state;
2. calls `updateVelocity()`;
3. calls `updateController()`;
4. moves the entity with Minecraft's entity movement path;
5. performs block/contact work and client interpolation.

This matters for a simulator because a policy should output the same normalized control contract
rather than directly mutate an alternate physics model.

### 3.2 Orientation controls

`AircraftEntity.updateController()` applies:

- left/right input to yaw using the aircraft `yawSpeed`;
- push/pull input to pitch using `pitchSpeed` while airborne;
- stabilizer decay to pitch;
- roll is visually derived from interpolated lateral control and `rollFactor`.

The existing Kneekura-bird policy's X/Y/Z control vocabulary therefore maps naturally onto a
standalone simulator state/action contract.

### 3.3 Velocity and energy behavior

`AircraftEntity.updateVelocity()` provides:

- glide conversion from vertical change into forward-direction acceleration via `glideFactor`;
- velocity-direction conversion using `lift`;
- friction/decay;
- ground-pitch behavior;
- wind perturbation based on `wind`, weather, velocity and `mass`.

`AirplaneEntity` adds:

- speed-dependent gravity reduction;
- throttle target adjustment;
- braking when negative engine input is used;
- thrust along the aircraft forward direction based on squared engine power and `engineSpeed`;
- low-speed ground push behavior via `pushSpeed`.

A high-throughput surrogate does not need to reproduce every Minecraft class, but it must preserve
the observable consequences of these coupled terms closely enough that combat tactics transfer.

## 4. Weapons and projectile model

### 4.1 Fixed machine gun

`WarfareWingsMG extends immersive_aircraft.entity.weapon.BulletWeapon`.

Direct bytecode observations from the supplied JAR:

- projectile velocity override: **4.7 blocks/tick** (~94 blocks/s at 20 TPS);
- inaccuracy override: **0**;
- convergence point: aircraft-forward point at **80 blocks**;
- ammo expenditure delegates to Immersive Aircraft gunpowder-ammunition configuration;
- sound delegates to `immersive_aircraft.Sounds.CANNON`;
- bullet creation delegates movement/collision to a `WWFBulletEntity`.

`WWFBulletEntity` extends Minecraft `AbstractHurtingProjectile`, carries scale and damage, follows
the projectile hit hooks, and updates visual yaw/pitch from velocity.

### 4.2 Bombs

The Warfare Wings bomb-bay family also extends `BulletWeapon`, but the selected bomb bay returns a
TNT-derived bomb entity and has zero launch velocity in its own override. Gravity/motion and
explosion semantics therefore need a separate ballistic model from the fixed gun model.

This is important for future dive/level/torpedo mission simulation: do not represent every weapon as
the fighter gun's straight-line intercept model.

## 5. Networking and client/server boundary

No Warfare Wings-local packet/message/payload class family was found in the supplied class tree.
The selected weapon path constructs Immersive Aircraft's `FireMessage` and sends it through that
dependency's `NetworkHandler`.

Likewise the aircraft movement/synchronization path is inherited through Immersive Aircraft /
Minecraft entities.

Engineering consequence: for AI research, networking should remain an adapter concern. The policy
and fast simulator should exchange state/actions, while only the Minecraft adapter translates a
selected fire/control action into the real entity/network API.

## 6. Mixins / transformations

Both shipped Warfare Wings mixin configs have empty `mixins` and `client` arrays. No
Warfare Wings behavior in this supplied artifact depends on an active local Mixin injection path.

This simplifies offline reproduction: the important dynamic closure is ordinary inheritance plus
the dependency/runtime, not hidden Warfare Wings bytecode patches.

## 7. Rendering / models / animation-visible state

The supplied JAR includes:

- 101 client classes;
- dedicated aircraft renderer classes for base/scheme entities;
- projectile/bomb renderers;
- 106 item model JSON files;
- 91 entity textures.

The entity classes expose animation-related state such as gear states, trails, engine/rotation
variables and other renderer-facing values. These are useful for visual validation but are not
required in the headless combat decision loop.

The standalone air-combat simulator should therefore keep rendering as an optional observer layer.
A simple aircraft mesh/arrow may consume the same simulation state, but no AI decision should depend
on that renderer.

## 8. Audio

No Warfare Wings-local `sounds.json` or sound-registration class family was found in this JAR.
The inspected machine-gun path uses Immersive Aircraft's cannon sound. Audio is NOT_APPLICABLE to
the proposed AI simulation core.

## 9. What must be preserved for air-combat AI

The minimum transferable state is not a whole Minecraft world. It is approximately:

```text
AircraftState
  position xyz
  velocity xyz
  forward/up/right orientation
  yaw/pitch/roll + useful rates
  engine power + engine target
  onGround / AGL
  health/damage/fuel if mission policy reads them
  ammo / weapon cooldown

AircraftProfile
  measured top/cruise/climb/stall/turn/recovery/approach values
  Warfare Wings physical coefficients
  dimensions / collision radius or boxes
  role / faction / doctrine

SensorFrame
  ownship state
  visible targets and relative states
  line-of-sight
  terrain clearance samples
  nearby aircraft separation
  mission/order state

ControlCommand
  x / y / z
  engine target
  fire/drop request
```

World support can initially be limited to a deterministic terrain-height/raycast abstraction and
aircraft collision volumes. Minecraft blocks, registries, rendering, recipes, GUI and packet details
do not belong in the fast dynamics core.

## 10. Static finding states

| Finding | Basis | State |
|---|---|---|
| Warfare Wings delegates airplane physics to Immersive Aircraft inheritance | supplied class hierarchy + dependency source | EVIDENCE_BACKED static relationship |
| all supplied aircraft JSONs contain AI metadata | direct JAR read | EVIDENCE_BACKED for this artifact |
| public 1.1.4 and supplied artifact are not safely interchangeable | SHA-1 conflict + repo provenance conflict | EVIDENCE_BACKED mismatch / exact public bytes unavailable |
| machine-gun 4.7 block/tick and 80-block convergence | supplied bytecode | EVIDENCE_BACKED static |
| no active Warfare Wings mixins | supplied config bytes | EVIDENCE_BACKED static |
| supplied artifact runs correctly in Minecraft | not tested | UNKNOWN |
| fast surrogate can replace exact physics | explicitly rejected | NOT CLAIMED |
