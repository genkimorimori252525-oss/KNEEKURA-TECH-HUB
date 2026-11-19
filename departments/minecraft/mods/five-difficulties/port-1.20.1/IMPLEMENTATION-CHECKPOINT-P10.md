# Implementation checkpoint — P10 lasers and the special-shot registry

Date: 2026-11-19
Oracle: X1 `LaserData`, `EntityTHLaser`, `EntityTHSetLaser`, `RenderTHLaser`, `THShotLib` laser
emitters, `ItemTHLaser`, `SpecialShotRegistry` / `ISpecialShot`.

## Ported

| X1 | Port |
|---|---|
| `LaserData` | `core/x1/X1LaserData` |
| `createLaserA`, `createWideLaserA`, `createCircleLaserA`, `createRingLaserA`, `createRandomRingLaser`, `createSphereLaserA` | `core/x1/X1LaserPatterns` (pure, tested) |
| `EntityTHLaser.updateAngle` | `X1ShotMotion.laserAngle` |
| `EntityTHLaser` (laser A: length growth, segment hit, block cut, GUNGNIR special) | `forge/entity/THLaserEntity` |
| `EntityTHSetLaser` (laser B: pinned to a set entity, +6 length per tick, sweeps with the yaw rotation) | `forge/entity/THSetLaserEntity` |
| `createLaserB` | `X1LaserSpawner.createLaserB` |
| `RenderTHLaser` (normal tube, Gungnir spear, Laevateinn blade, Master Spark beam, delay light) | `THLaserRenderer`, `X1LaserModels` (vertex tables verbatim) |
| `ItemTHLaser` (laser / short / long; dye in the next hotbar slot picks the colour) | `THLaserItem` |
| `SpecialShotRegistry` + `ISpecialShot` | `X1SpecialShotRegistry`, consulted first by THShot / THLaser |

`THShotEntity` is now open for subclasses (`initShot`, `afterX1Tick`, protected hit hooks).
The render-state mapping became a generic `Spec(blend, depthWrite, cull, depthAlways)` so the
laser's culled passes and Master Spark's `GL_ALWAYS` depth test map one-to-one.

## X1 quirks kept on purpose

- `createLaserA` resolves RANDOM / RAINBOW into the caller's LaserData and never restores it.
- A wide laser re-rolls RANDOM per ray; the circle emitter makes `way + 1` lasers over 360°
  (first and last coincide); the sphere emitter puts the backward laser at the front position.
- Laser length grows by `speed * 2` after `super.onUpdate()`, so it also grows during the delay;
  lengths are stored as `(int) (length * 10000)`.
- Player-shot lasers never hit players (`source instanceof EntityPlayer`).
- The set laser constructor uses `laser.color` as the shot ID (Laevateinn passes `RED + 16`).

## Fix found on the way (affects P8 / P9 too)

Vanilla `Projectile.lerpMotion` re-derives the client rotation from the velocity packet while
`yRotO == 0`, i.e. right after spawn. Static shots and lasers were therefore drawn with yaw 0
on the client (lasers pointed away from the camera). X1 rotations come only from the server, so
`THShotEntity.lerpMotion` now only applies the motion.

## Receipts

Pure core: 10 suites PASS (new `X1_LASER_CORE_REGRESSION_PASS`).

Dedicated server (local; P5/P6/P8/P9/P10 together):

```
FIVE_DIFFICULTIES_P10_GROWTH_PASS length=5.0
FIVE_DIFFICULTIES_P10_HIT_PASS damage=3.5
FIVE_DIFFICULTIES_P10_CUT_PASS max=2.0
FIVE_DIFFICULTIES_P10_SET_LASER_PASS swept=50.0 length=10.0
FIVE_DIFFICULTIES_P10_ITEM_FORMS_PASS forms=6
FIVE_DIFFICULTIES_P10_RUNTIME_SCENARIO_PASS
```

- GROWTH: 2.4 after 2 ticks (0.6 × 2 per tick), capped at 5.0.
- HIT: a stationary laser hurts a husk on its segment for 5 × EASY 0.7 and survives the hit.
- CUT: a stone block 2.0 blocks away cuts length and max to 2.0.
- SET_LASER: pinned at set entity + 6 up, full length 10 after two ticks, sweeps 10°/tick,
  dies with its set entity.
- ITEM_FORMS: Point 3 / Random 5 / Sector 4 / Around 4→5 / Sphere 8 / Ring 6.

Real client: the in-world frame shows the eight laser colours, Spear the Gungnir, Laevateinn,
a set laser and a laser in its delay.

## Not covered

- Master Spark is drawn by its own entity in X1 (P12); the `id >= 24` laser branch is ported
  but not shown yet.
- The registry has no entries until the spell cards register theirs (P11+).
