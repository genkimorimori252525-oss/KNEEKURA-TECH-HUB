# Warfare Wings / Immersive Aircraft — exact engine-reaction evidence (2026-10-11)

## Status and provenance

**SOURCE-BYTECODE VERIFIED for all 24; exact-jar GameTest measured A6M throttle; physics parity remains scenario-specific.**

Warfare Wings ANCHOR SHA-256:
`dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43`

Immersive Aircraft 1.3.3 original SHA-512:
`7b74442e161bb74538e0d8da34a81616daeea56a0da62db86113a78b3bf3c2b3a6b0e12f12454fd7c96092762f6b212ba57cb87eb1af2b242a4d5df4eca03055`

The exact WW 1.1.4 `<airframe>Entity.getEngineReactionSpeed()`
overrides are verified with `javap -c -p` for each aircraft, and matched
against `WarfareWingsEngineReaction.java` by
`tools/verify_engine_reaction_bytecode.py`. No original binary is committed.

| Reaction ticks | Aircraft |
|---:|---|
| 100 | A6M, Bf 109, D4Y, F4U, F6F, Fw 190, IL-2, Ju 87, Ki-61, Ki-84, MC.202, MiG-3, P-40E, P-47N, P-51D, SBD, Spitfire, Yak-3 |
| 120 | G4M, He 111 |
| 150 | B-17, B-29 |
| 170 | G10N2 |
| 200 | G10N1 |

These are **MOD source physical parameters**, not historical aircraft
spool-up measurements. Do not infer national fighter tactics from them.

The verified IA source code path is
`EngineVehicle.tick()` calling
`enginePower.setSteps(getEngineReactionSpeed()/VehicleStat.ACCELERATION)`
then `InterpolatedFloat.update(getEngineTarget())`.
`InterpolatedFloat.setSteps(ticks)` stores `1/ticks`,
and `decay(value, rate)` produces
`next = previous * (1-rate) + target * rate`.
Thus for ordinary `ACCELERATION=1` aircraft,
`power[69] = 1-(1-1/100)^69 = 0.500163` for A6M, matching the actual
Minecraft engine-power trace at tick 69.

## A6M, same original JAR, 400-tick neutral-pilot throttle envelope

The **previously reported** real speed peak 25.0815 blocks/s came from an
invalid source/runtime trace: aircraft chunk unloading froze the entity
after tick 223, but the global server clock and recorder continued to tick.
Never present this as a completed 400-tick flight measurement.

`RuntimeTraceManager` now preloads a forward corridor, verifies that the
**real entity tickCount advances by exactly one every sample**, and releases
only the chunk tickets its own test acquired, even after abort. The
completed owner-JAR local Forge GameTest independently proved 13 required
tests PASS, and the corrected 401-row A6M trace has non-repeated position
and engine samples through tick 400:

| Measure (401 samples) | Old source / 20t response | Exact-WW 100t response source | Real exact-JAR Minecraft |
|---|---:|---:|---:|
| First engine power ≥50% | tick 14 | tick 69 | tick 69 |
| Tick 400/peak speed (blocks/s) | 33.6700 | 32.1310 | 31.7603 |
| Speed RMSE relative to real (blocks/s) | 10.9859 | **0.1554** | — |
| Final speed absolute error (blocks/s) | 1.9097 | **0.3707** | — |
| Engine power RMSE relative to real | 0.2589 | **0.00000019** | — |
| Reaction-source origin-aligned position drift at final (blocks) | — | **2.621** | reference |

The GameTest spawns in a different world coordinate origin than the
standalone source model; the **raw absolute** position difference includes
this fixture offset and is not an acceptable dynamics error metric.
`compare_traces.py` now reports **origin-aligned drift** separately, and
rejects repeated real physics snapshots or nonconsecutive game times for
throttle calibration. A stale-source fixture reproduces the old failure
and is rejected by `test_compare_traces.py`.

The old Atlas v2 golden files deliberately **retain the historical
20-tick default source predictions**. They are not silently overwritten.
`Ia133Microkernel.tickWithReaction`, `ReactionCalibrationTraceMain`
and `WarfareWingsEngineReaction` are the new explicitly source-corrected
calibration route. The engine reaction path has separate 24-aircraft
deterministic tests. A new exact-parameter experimental Atlas or
multi-aircraft mission model should be clearly versioned before
adoption; do not mislabel old Atlas metrics as original-binary physics.

## Reproduction and next gates

After the exact user-owned binaries have been staged **outside Git**:

```powershell
python ../tools/verify_engine_reaction_bytecode.py --jar flight-test-mods/warfare_wings-1.1.4-1.20.1-forge.jar --javap "$env:JAVA_HOME/bin/javap.exe"
```

The repository source/CI builds the new Java catalog and response variant
without the JAR. The owner's runtime workflow regenerates both the
unchanged legacy source throttle trace and the opt-in exact-response
`a6m-throttle-step-v1-reaction-source.csv`, comparing both against a
**live completed** 401-row owner-JAR GameTest.

Only the A6M's one neutral-pilot throttle envelope has the above close
observed numerical agreement. Still required:

- Identical true-tick, origin-aligned 401-tick profiles for P-47N, IL-2
  and B-17, repeated at least twice to estimate runtime variance
- Equal-speed 90° turns, loaded armaments, collision/terrain, stall margins
  and multiplayer flight control under the original binary
- Experimental revised 24-type Atlas that explicitly consumes each
  aircraft's source reaction speed without rewriting V2 provenance
- Actual friendly-fire/ammunition/mount API acceptance; no real shots,
  bombs or torpedoes have been issued by the live AI

The current original behind-bomber escort experiment still fails its
unchanged 95-block protection gate even when source AI/flight safety
regressions pass. Do not convert that operational failure into success.
