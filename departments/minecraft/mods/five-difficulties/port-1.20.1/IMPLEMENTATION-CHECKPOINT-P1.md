# Five Difficulties X1 Preservation Port — P1 implementation checkpoint

Date: 2026-10-07

Branch:
`jolly/five-difficulties-1201-port-p1-2026-10-07`

Parent:
`jolly/five-difficulties-1201-port-p0-2026-10-07`

## P1 purpose

Move from generic preservation infrastructure to the first **evidence-backed X1-specific behavior contracts** without inventing missing raw asset/API details.

## Exact X1 provenance bridged

Earlier PR #93 analysis head:
`cb83cee43c241b45e473f01e00263adf4d1c188f`

Canonical core artifact:
- `五つの難題MOD+ ver2.90.1.X1-1.7.10`
- SHA-256 `6307789d5f2f43b762bcc7d5aa03d67207eaa237fb124447e7ea951aa856e634`
- 4,596,892 bytes
- 956 ZIP entries
- 276 classes
- 266 bundled Java sources

See `X1-EVIDENCE-BRIDGE.md`.

## Implemented — red Homing Amulet contract

Static ORIGINAL_SOURCE / ORIGINAL_BINARY analysis retained by PR #93 is now encoded as pure Java:

Normal:
- 5 shots
- 100-degree total spread
- shot size 0.4
- damage 5
- speed 0.7
- RED AMULET
- HOMING01
- about 4 degrees/tick bounded steering

Focused/Shift:
- 2 shots
- 20-degree total spread
- shot size 1.0
- damage 8
- speed remains 0.7
- RED AMULET
- HOMING01
- about 4 degrees/tick bounded steering

Still intentionally unresolved:
- legacy numeric shot type;
- legacy numeric color ID;
- lifetime ticks;
- exact THShotLib per-projectile angular placement inside the declared total span.

Therefore P1 does **not** yet convert this contract into a live `LegacyShotSpec`/Forge projectile.

## Implemented — Sakuya Watch / StopWatch contract

Shared field:
- 40-block range.

Watch item mode stored in legacy item damage:

Mode 0:
- max use duration 20 ticks;
- creative effect: HALF_SPEED;
- survival full-charge: limited HALF_SPEED;
- retained atlas nominal limited duration: ~160 ticks.

Mode 1:
- max use duration 48 ticks;
- creative effect: FULL_STOP;
- survival full-charge: limited FULL_STOP;
- retained atlas nominal limited duration: ~100 ticks.

Other retained time contracts:
- spell-card stop: nominal ~60 ticks;
- disposable StopWatch: nominal ~40 ticks.

The "~" durations are encoded as `X1_STATIC_INFERENCE`, not falsely promoted to exact values.

The following remain explicitly unresolved X1 policy:
- block ticks;
- fluid ticks;
- BlockEntities;
- random chunk ticks;
- particles;
- animated textures;
- world day time;
- delayed damage/release semantics;
- other-player multiplayer policy.

Roundabout remains an engineering donor only.

## Verification

Pure Java regression suite includes:
- `LegacyPatternCoreRegression`
- `SakuyaTimeStopCoreRegression`
- `HomingAmuletContractRegression`
- `SakuyaWatchContractRegression`

P1 CI overlays the committed source onto the exact official:
- Minecraft 1.20.1
- Forge 47.4.6
- Java 17
- MDK SHA-1 `1a1c045f235262ff617e285ea2156571ea93bfbe`

and runs:
- pure Java regressions;
- `compileJava jar`.

GitHub Actions run **37517412134** completed **SUCCESS** on implementation commit
`23fba25caf635d5b6de2beb2a99db9782008d0d6`.

Verified:
- all four pure Java regressions: PASS;
- exact official Forge 1.20.1-47.4.6 MDK download + SHA-1 verification: PASS;
- `compileJava jar`: PASS;
- bounded evidence artifact upload: PASS.

### P1 CI failure/repair note

The first P1 CI attempts failed before Forge compilation because the shell runner contained a literal
`\\n` between two Java commands, producing an invalid main-class token ending in
`SakuyaTimeStopCoreRegressionnjava`.

This was a test-harness defect, not a preservation-core failure.

Repair:
- commit `23fba25caf635d5b6de2beb2a99db9782008d0d6`;
- rewrote `run-pure-core-tests.sh` with one explicit Java command per line;
- rerun 37517412134 passed the complete pipeline.

## Not implemented yet

- original X1 raw archive rematerialization in the current Project surface;
- original PNG bullet/item assets;
- exact ShotData numeric mapping;
- exact THShotLib fan placement formula for Homing Amulet;
- Homing projectile steering runtime;
- real projectile EntityType/renderer;
- Sakuya Watch/StopWatch Forge items;
- real time-stop ServerLevel Mixins;
- existing-projectile/new-knife X1 runtime oracle;
- client interpolation freeze;
- Master Spark / lasers / spell cards / other items;
- multiplayer runtime verification.

## Next gate

P2 should not broaden to all content.

Preferred next sequence:
1. recover/rematerialize a byte-identical X1 core archive or source excerpt matching the canonical SHA;
2. extract exact `ShotData` numeric mapping + `THShotLib` fan placement;
3. build one live red Homing Amulet projectile/render path with the original texture;
4. separately record the X1 Sakuya runtime oracle;
5. only then enable minimal Roundabout-derived time-stop Mixins.

This keeps visual/gameplay preservation ahead of optimization.
