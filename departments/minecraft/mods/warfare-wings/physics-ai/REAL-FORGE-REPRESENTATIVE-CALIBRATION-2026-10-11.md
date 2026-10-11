# Exact-original Forge representative aircraft and weapon audit — 2026-10-11

This is a **measured local Forge 1.20.1 / 47.4.20 result**, not source-only
simulation. The original owner-controlled Warfare Wings binary SHA-256 is
`dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43`;
the IA 1.3.3 binary SHA-512 is
`7b74442e161bb74538e0d8da34a81616daeea56a0da62db86113a78b3bf3c2b3a6b0e12f12454fd7c96092762f6b212ba57cb87eb1af2b242a4d5df4eca03055`.
Neither game binary nor locally measured runtime CSV is committed to this repository.

## New actual GameTests

`RepresentativeCalibrationGameTests` extends the unchanged existing A6M
neutral-input acceleration GameTest with P-47N, Spitfire, IL-2 and B-17.
Each airframe uses the same **0.7-block/tick +Z initial speed**, zero
yaw/pitch and neutral rotation controls, target throttle `1.0`, level flat
terrain, disabled wind/fuel drain/collision damage, and **400 successive
real aircraft entity updates (401 recorded snapshots)** at 20 Hz.

The new tests do not change the 24-airframe sequential smoke, original A6M
trace, 2v2 or 340-tick operational B-17 escort. Like the old A6M recorder,
the four aircraft force-load their moving chunk corridor and reject skipped
entity ticks rather than mistaking a frozen flight for progress.

The local original-binary Forge GameTest now executes **20 required tests**:
19 PASS (including the four additional 401-sample calibrations and the
two-plane long strike/RTB mission), 1 FAILED
(the existing B-17 95-block protectee corridor still sees **101/340**
intrusion ticks; closest enemy **66.0293** blocks). This was a clean test
completion, not a server crash. The testing framework correctly returns
nonzero because one required operational mission failed.

## Source V3 vs exactly matching real neutral-controls

`tools/verify_representative_calibrations.py` validates the real Forge trace
schema, 401 samples, continuity, anti-frozen-state checks and exact 24-plane
source anchor. Then it independently generates a reaction-time-corrected
`ReactionCalibrationTraceMain` prediction for each aircraft and calls the
same `compare_traces.py` comparator used for the A6M. It does **not** accept
or assert physical parity as a Boolean.

| Actual plane | Original engine response | Speed RMSE (blocks/s) | Final origin-aligned drift (blocks) | Yaw RMSE (deg) | Pitch RMSE (deg) | Engine-power RMSE |
|---|---:|---:|---:|---:|---:|---:|
| P-47N | 100 ticks | 0.606908 | 4.165318 | 0.971544 | 1.005549 | 0.000000186 |
| Spitfire | 100 ticks | 0.352142 | 6.277028 | 0.478756 | 0.474677 | 0.000000186 |
| IL-2 | 100 ticks | 0.483190 | 6.429974 | 0.833825 | 0.801075 | 0.000000186 |
| B-17 | 150 ticks | 0.680716 | 15.052741 | 1.855266 | 1.752852 | 0.000000261 |

The measured RMSE values come from the local 401-sample `runtime.csv`
and generated source CSVs, not estimated aircraft facts. B-17's greater
position drift and yaw/pitch disagreement are reasons to **retain an
uncertainty band in 3D intercept/landing policies**. These are initial-speed
neutral controls only: bank-induced turn, control saturation, true stall
threshold, gun recoil, collision and damaged-aircraft performance remain
unestablished. Atlas v2 report/golden remains unchanged; Atlas v3 remains
an explicitly labeled source prediction rather than accepted exact dynamics.

The generated JSON summary is
`run-gametest/ww-physics-traces/cal-401/representative-calibrations.json`
in the ignored local test folder and the same path in the remote runtime
artifact if upload succeeds. Missing/short/wrong-airframe/frozen fixture
tests run in pure-Java/Docker CI; a fixture PASS is not evidence of flight.
The 2026-10-11 owner-runner CI at `f8f6778` independently exposed a Windows
MAX_PATH failure: the original absolute Spitfire source output path was
263 characters (P-47N's was 259). Java17 exited zero after reporting its
Spitfire trace, but the Python reader could not find the overlong path.
The new shorter `cal-401` output directory keeps the corresponding Spitfire
path at 243 characters, and the standalone verifier refuses all long source
or comparator output paths before executing Java. This corrects artifact
delivery only, not the separate strict 95-block B-17 protection failure.

## Exact binary weapon callpath audit and authorization boundary

`tools/audit_exact_weapon_failclosed.py` checks both original hashes,
disassembles pinned original `WarfareWingsMG`, `WarfareWingsBombBay`, and IA
`InventoryVehicleEntity` methods, and verifies the following:

- The WW MG and bomb methods call `spentAmmo(...)` before `BulletWeapon.fire`.
- IA's `fireWeapon(int slot,int index,Vector3f direction)` dispatches from a
  weapon map/list to `Weapon.fire` without proving AI-legal fitted mounts,
  server-enforced rate limits, target line-of-sight or friendly exclusion.
- No class with `Torpedo` in its name was found in the exact WW `.class`
  archive inventory; this alone does not prove that every sea-attack
  mechanism is absent, but it cannot authorize a torpedo implementation.

The audit **does not** prove server-authoritative fire timing, actually
installed ammunition, projectile owner/kill attribution, damage or safe
muzzle lane. It always returns
`FAIL_CLOSED_NO_AUTONOMOUS_WEAPONS_AUTHORIZED` for these incomplete evidence
contracts. The real AI deliberately sends neither MG shots nor bomb/torpedo
releases; no fake hits, deaths or ordinance mission success are produced.

## New real 840-tick two-plane strike → egress → return mission

`OperationalStrikeRtbGameTests` operates a real independently piloted IL-2
(`STRAFE`) and B-17 (`LEVEL_BOMB`) on the same Minecraft server for **840
consecutive aircraft entity ticks each**, with separate initial predeclared
targets 185 blocks ahead and home coordinates 130 blocks behind. The
controllers must physically approach their objectives until they naturally
enter the existing 75-block unarmed egress radius. The test then requests
RTB only when **both** aircraft have independently reached the EGRESS phase,
never by teleporting or moving the target near the aircraft. The accepted
mission requires sustained ingress, real egress, latched RTB, a physical
home-distance reduction and safe mutual separation. An inconclusive mission
fails as a GameTest instead of crashing the server.

Independent full-column CSV analysis with `tools/verify_long_strike_receipts.py`
reproduced the following exact observed quantities:

| Flight | Ingress ticks | Egress ticks | Return ticks | Nearest target | Reduction in home distance |
|---|---:|---:|---:|---:|---:|
| IL-2 | 188 | 123 | 529 | 74.846991 blocks | 200.450578 blocks |
| B-17 | 299 | 12 | 529 | 74.572029 blocks | 195.288866 blocks |

Both CSVs contain **841 synchronized actual GameTime samples**. Nearest
mutual aircraft separation remained **145.883357 blocks**. The verdict is
`NO_WEAPON_GEOMETRIC_APPROACH_EGRESS_RTB_PASSED`, explicitly **not** bomb
delivery, strafing hits, target destruction, fuel refilling, touchdown,
weapon-damage attribution, or completed landing. The new independent
acceptance is included in the original-JAR GitHub Actions workflow.

## Remaining practical blockers

Achieve B-17 95-block containment and moving fighter interceptions under
unmodified initial geometry and measured limits, validate real full-rate
turn/stall across the different airframes, independently verify installed
weapon mounts/projectile ownership/cooldown/LOS/friendly firing corridors,
execute real damage/kill/hit GameTests only after this evidence exists, and
make autonomous landing distinct from a mere return-home waypoint.
