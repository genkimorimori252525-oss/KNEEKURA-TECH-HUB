# Immersive Aircraft — Analysis Workspace

## Current entry point

**Minecraft 1.20.1 + Forge 1.3.3 physics-focused ANCHOR mapped; compiled-JAR byte equivalence remains unproven in this session.**

This workspace exists because Warfare Wings delegates its airplane motion, control, weapon base classes,
vehicle data and much of its synchronization to Immersive Aircraft. For Kneekura-bird, Immersive
Aircraft is therefore the physics/runtime foundation rather than a secondary dependency.

Start with:

- [ANCHOR-RELEASE-EVIDENCE.json](ANCHOR-RELEASE-EVIDENCE.json)
- [PHYSICS-1.3.3-2026-10-07.md](PHYSICS-1.3.3-2026-10-07.md)
- [KNEEKURA-BIRD-SURROGATE-BRIDGE-2026-10-07.md](KNEEKURA-BIRD-SURROGATE-BRIDGE-2026-10-07.md)
- [FAILURE-REPAIR-HISTORY.md](FAILURE-REPAIR-HISTORY.md)

Shared procedure: [ANALYSIS-WORKFLOW.md](../../ANALYSIS-WORKFLOW.md) and
[ANALYSIS-SPEC-v1.md](../../ANALYSIS-SPEC-v1.md).

## ANCHOR release identity

Target runtime used by historical Kneekura-bird validation:

- project: Immersive Aircraft
- Minecraft: 1.20.1
- loader: Forge
- release: `1.3.3+1.20.1`
- Modrinth project: `x3HZvrj6`
- Modrinth version: `GsVmbbkj`
- CurseForge project: `666014`
- CurseForge file: `6742170`
- filename: `immersive_aircraft-1.3.3+1.20.1-forge.jar`
- published: 2025-07-07
- known SHA-512 from a published packwiz manifest:
  `7b74442e161bb74538e0d8da34a81616daeea56a0da62db86113a78b3bf3c2b3a6b0e12f12454fd7c96092762f6b212ba57cb87eb1af2b242a4d5df4eca03055`

Kneekura-bird's historical validation workflow explicitly downloads Modrinth version
`GsVmbbkj` into `flight-test-mods/immersive_aircraft-1.3.3+1.20.1-forge.jar`. This ties the
existing route/dogfight evidence to the immutable release ID rather than only to a filename.

### Byte-verification boundary

The raw public JAR could not be materialized into the current tool runtime. Therefore this batch does
**not** claim a locally recomputed SHA-256/SHA-1, full JAR class inventory, or byte-for-byte
source-build equivalence. Raw binaries are not committed to Tech Hub.

## Source ANCHOR

GitHub tag/ref:

`1.3.3+1.20.1`

resolves to:

`550b38d3dfdbf5cb6ec3f78468e0e60725a47605`

The tag's build metadata declares Minecraft 1.20.1, Forge 47.0.3, Fabric/Forge targets and Java 17.
The root build computes the package version from the Git tag at HEAD, and the Forge resource task
expands that version into `META-INF/mods.toml`.

Association state:

- **SOURCE_RELEASE_ASSOCIATION_STRONG**
- **COMPILED_CLASS_IDENTITY_UNPROVEN**

Do not silently upgrade this to exact binary equivalence.

### Why exact tag source matters

The live `1.20.1` branch is already 29 commits ahead of the 1.3.3 tag and changes core physics
classes including `VehicleEntity`, `EngineVehicle`, `InventoryVehicleEntity`,
`AirplaneEntity` and `VehicleStat`.

Concrete example: the 1.3.3 tag uses a hard-coded airplane braking multiplier of `0.95`; later
1.20.1 source data-drives a `brakeFactor` stat. For Kneekura-bird parity work, the 1.3.3 tag is the
physics reference, not current branch source.

## Source/release discrepancy retained

The public cumulative changelog describes 1.3.3 as fixing rudder orientation. However the Git tag
`1.3.3+1.20.1` is only one commit ahead of tag `1.3.2+1.20.1`, and that one commit changes only
`VehicleEntity` by restoring the protected static `ZERO_VEC4` field used by addons.

This means the source tag is strongly associated with the release but cannot, without binary/resource
comparison, prove that every distributed 1.3.3 resource byte is represented by the tagged tree.

## Main findings

1. Immersive Aircraft fixed-wing flight is an intentionally compact arcade physics model rather than
   a conventional aerodynamic 6-DOF solver.
2. Steering directly changes yaw and pitch; visual roll is derived from smoothed lateral input.
3. The unusual `lift` term bends the velocity vector toward the aircraft forward vector; it is not
   an upward lift-force coefficient.
4. Gravity is custom and speed-dependent. Vanilla gravity is disabled for the vehicle.
5. Input smoothing and engine-power smoothing happen **after** the movement phase that consumed the
   previous smoothed state, producing a material temporal lag.
6. Minecraft `Entity.move` remains the authoritative block-collision solver.
7. Projectile hit detection is extended by a Mixin so custom vehicle bounding boxes can be hit.
8. Normal crash damage is partly client-originated: the client computes collision severity after
   movement and sends a `CollisionMessage` to the server.
9. Weapons are server-spawned; `BulletWeapon` adds aircraft sampled velocity to the spawned
   projectile velocity.
10. Vehicle JSON field `driftDrag` is **not a registered 1.3.3 VehicleStat key**. The registered
    key is `friction`, default `0.015`. Because `VehicleData` iterates registered stat names,
    `driftDrag` is ignored by the 1.3.3 loader unless another layer rewrites it before loading.
    No such rewrite was found in the inspected path.

## Kneekura-bird consequence

The old fast simulator should not be replaced by a general Minecraft clone. It should be upgraded
into a **source-faithful Immersive Aircraft 1.3.3 microkernel** around a shared AI policy, while
headless Forge remains the parity oracle.

The existing measured 24-aircraft `flight_profiles.json` remains runtime authority. A discovered
legacy theoretical parser uses `driftDrag` as friction despite the 1.3.3 loader behavior; those
theoretical numbers must not override the measured profiles.

## Facet status

| Facet | State | Note |
|---|---|---|
| release identity | EVIDENCE_BACKED | immutable Modrinth/CurseForge IDs + known SHA-512 |
| raw JAR byte identity | NOT_ANALYZED in current runtime | raw bytes unavailable here |
| source release association | EVIDENCE_BACKED / strong association | exact tag, version-producing build, release date |
| compiled source↔binary equivalence | UNKNOWN | no binary comparison |
| input/tick/engine ordering | EVIDENCE_BACKED source | exact 1.3.3 tag |
| flight equations | EVIDENCE_BACKED source | exact 1.3.3 tag |
| Minecraft collision boundary | MAPPED | IA source + vanilla Entity.move boundary |
| weapons/network | EVIDENCE_BACKED source | selected relevant classes |
| projectile extra hitboxes | EVIDENCE_BACKED source | active ProjectileUtilMixin |
| crash damage in headless tests | MAPPED limitation | normal damage message is client-originated |
| performance envelopes | EVIDENCE_BACKED via Kneekura-bird historical measurements | exact runtime version ID |
| failure/repair history | PARTIAL | bounded 1.3.0–1.3.3 / relevant issue review |
| current-source portability | MAPPED first pass | 29-commit divergence retained |
