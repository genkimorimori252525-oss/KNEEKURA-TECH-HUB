# Warfare Wings Tactical AI → Real Forge 1.20.1 Aircraft Bridge

Status: **exact-JAR Forge 1.20.1 GameTest measured; current 19/20 tests PASS, B-17 operational protection FAILED**. The pinned owner Warfare Wings JAR and matching IA JAR were hash-verified and tested locally. This remains an experimental Forge integration with no weapon firing and no claim of full source/microkernel-to-Minecraft parity.

## Current development integration — common observed CPA / guarded large-squadron 3D safety

The original owner-local Java17/Gradle8.8 Forge 47.4.20 was **run again on the
new integrated shared-CPA/high-side/4+-radio-wingman safety source**, with
both exact original JAR checks in place, identical aircraft starting
positions, and unrelaxed original acceptance gates. The authentic native
GameTest runner **completed all 20 tests: 19 PASS / 1 B-17 FAILED** and
returned nonzero exactly as the strict game test demands. The original
five-aircraft B-17 remained **FAILED: 81/340 real physical ticks inside
the 95b protectee radius, nearest 65.02005004882812b**. Independent
read-only actual Minecraft control/position receipt verifier separately
measured **81/340, 65.020052b**. This is a genuine unresolved protection
failure, not an instrumentation/start geometry adjustment.

The same original re-execution independently confirmed:

| Original-JAR requirement | Current measured result | Verdict |
|---|---|---|
| Original 280tick 2v2 simultaneous four aircraft | Min pair **13.183515b**; zero pairs within 6b, source-observed engagement | PASS geometric only |
| B-17 + two genuine P-47N escorts vs two A6M, original 340tick | Min B17-attacker **65.020052b**, **81/340** inside 95b; all 5 aircraft physically update | **FAILED** protection |
| Original 3 B-17/escort independent current hostile FOV/LOS selection receipts | Actual target ranking with two concurrently visible opponents per actor; all 341 states checked | PASS provenance/contact, **NOT** protection |
| Original 840tick IL-2 and B-17 attack ingress, egress and returning | 841 actual Entity states each; nearest IL2/B17 separation **145.883357b** | PASS approach/egress/RTB geometry, no weapon/landing claim |
| 35 actual original-JAR recorded-control Physics Twin replays | 24 distinct airframes, 5,880 paired ticks; max final position error **0.001775711195b** under distinct 0.01b free-air gate | PASS only free-air open-loop recorded-control physics |
| Actual weapon slots/ammo/muzzle-friendly corridor/owner/kill attribution | Original bytecode and **every** real no-fire Frame source constructor inspected; missing end-to-end safety proof | **FAIL-CLOSED**, no autonomous MG/bomb/torpedo |

The **single pure Java** `ObservedProtectedAssetThreatSelection` now owns
the original 48tick observed-CPA threat score and 8b re-sighting-based
choice hysteresis. The exact Forge `LiveThreatPriority` delegates to it;
the external SOURCE Twin explicitly supplies only each actor's own freshly
visible hostile contacts and legitimate current same-team B-17 state.
Previously the Twin's unrelated **75-point cross-wingman target-load
penalty** gave the right P-47N `control_x=+0.109868` toward raider-2 on t1,
while REAL observed controls gave **-1.0 toward raider-1**. The common
selection independently reproduces **t1=-1.0** and subsequent t2 actual
yaw **0.268753497° SOURCE vs 0.268753499° REAL**. This is evidence for
the scoped causal control-decision/actuation consistency only; full 340tick
closed-loop Twin and REAL B-17 outcomes still diverge.

External 24-unique-source stress now explicitly runs 64 independently seeded
simultaneous 24-aircraft ×240tick cases under the original 6b pair and
95b asset gates. The guarded 4+-ally observation/radio-mode vertical
deconfliction improved source under6b from **5/64 seeds / 30 pair ticks /
min1.699b to 0/64 seeds / 0 pair ticks / min6.926b**; nonetheless
**all 64 B-17 protection scenarios remain FAILED**. Both the real
340tick original and the exact SOURCE 190tick aft/forward original gates
are unchanged. A separate bounded high-side source escort waypoint (only
if actual observed enemy >=12b below a spooling engine) reduced distinct
original SOURCE V3 aft B-17 exposure from 54 to 52 of 190 ticks, **still
FAILED**, with prepared forward zero ingress still PASS. No aircraft is
teleported, no hit or kill is spoofed and historical airframe nationality
remains non-authoritative for friend/foe orders.

## Latest owner-runner independent evidence — `7b5bc29` (2026-10-11)

The owner-controlled exact-original-JAR GitHub Actions
[#38125436950](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/38125436950)
completed **FAILURE for the correct strict B-17 operational reason**. All
**20 native GameTests actually completed (19 PASS, 1 B-17 FAILED)**; the
native 340tick escort violation remained **81 intrusion ticks inside 95b**,
with nearest hostile **64.882500b** on this owner-runner invocation. The
preceding owner-local run of the same source measured 81 ticks and 65.020050b;
do not silently substitute one run's closest-approach number for the other.
These are original real aircraft physical measurements, not SOURCE Twin
mission outcomes. The original minimum 6b pair separation and 30b actor
net-displacement gates were not relaxed.

The new independent workflow output gates were:

| Required original-owner workflow stage | Outcome |
|---|---|
| Exact original Forge GameTests | **FAILURE**, real 95b B-17 breach |
| Real 2v2/B-17 geometric acceptance | **FAILURE**, B-17 breach |
| Original 3-actor multi-contact FOV/LOS threat selection | SUCCESS |
| Four original 401-sample A6M-independent P-47N/Spitfire/IL-2/B-17 calibration comparisons | SUCCESS |
| Real 840tick IL-2/B-17 ingress, egress and RTB | SUCCESS, no weapons |
| Real 35-trace / 24-airframe independent recorded-control free-air Twin | SUCCESS, 5,880 samples; maximum final drift **0.002047870b** against a distinct 0.01b physical gate |
| Original private evidence artifact upload | SUCCESS |

In the previous owner CI
[#38124509010](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/38124509010),
the four-401sample step also failed because the absolute generated Spitfire
CSV pathname was 263 characters on Windows. Commit `7b5bc29` shortened its
destination to `cal-401` and added an early fail-closed MAX_PATH-budget check.
The new owner run independently verifies that this was a generated-file-path
failure, not a Forge physics error. The four legacy source-vs-Forge calibration
differences are still reported as measurement-only, without an invented parity
PASS threshold. **Autonomous guns, bombs and torpedoes remain prohibited.**

## 2026-10-11 continuation — visible protected-asset threat selection and owner-runner gate

The owner-controlled GitHub Actions run
[#38121994663](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/38121994663)
is **FAILED before any original Forge GameTests ran**. Its pinning and
24-engine-reaction bytecode checks passed, but the former static weapon-gate
regular expression only understood the older 14-argument
`new TacticalAirAI.Frame(..., surface, false, 0)` call. The new, legitimately
observed same-team leader-velocity parameter produces a 15-argument Frame
ending `..., surface, false, 0, observedLeaderVelocity`, so the old regex
incorrectly rejected a still-unarmed pilot. Its GameTests, physics replay and
long-strike acceptance were **SKIPPED**, not failed real flights. A revised
`audit_no_fire_frame` now checks **every** real Frame constructor by balanced
argument parsing: in either permitted overload, index 12 must be the literal
`false` and index 13 the literal zero. It also rejects direct original
`fireWeapon` calls. All ten source adversarial parser tests and the
**actual pinned WW/IA original-binary bytecode audit** pass; autonomous fire
remains **DISABLED**, regardless of aircraft mission.

The live pilot formerly picked the nearest physically visible hostile to
**itself**, even when the protected B-17 was at risk from a *different*
opponent. `LiveThreatPriority` now uses only contacts which independently
passed real `LiveAirSensor` 240-block range, 150-degree **full** FOV and block
line-of-sight plus the explicitly allied leader's measured Entity position
and velocity. For B-17 and an escort with its same-team leader, it extrapolates
the measured relative geometry for a bounded **48 ticks** and selects the
minimum predicted close approach (with a small earlier-threat weighting).
Non-escort patrol/2v2 still uses nearest personally observed hostile; an
explicit UUID target continues to require real FOV/LOS. A visible enemy is
never inferred from an airframe's nation or global omniscient entity state.
This is a **new tactical hypothesis**, not actual proven 95b protection.

New original-control CSV fields `visible_hostile_count` and
`contact_selection=VISIBLE_CPA_TO_PROTECTED_ASSET` make the observed actor
selection inspectable. Source `verifyObservedThreatPriority` runs 15 Java17
vector/same-velocity/urgency/tie/unobserved assertions. Independent
`tools/verify_live_threat_receipts.py` demands three original
**341-state B-17/escort real GameTest recordings**, contiguous original
physics and server clocks, at least one genuinely recorded two-contact
frame for each, and rejects missing/fabricated source-only or hidden-contact
claims. Synthetic bad-receipt tests cannot certify real sensing. The new
Owner-Forge workflow fails closed on this extra gate *in addition to*, never
instead of, the unchanged 95b/6b/30b/840tick and original-JAR gates.

The previous owner Windows Gradle setup step took almost ten minutes to
restore remote caches. The next owner workflow preserves **Gradle 8.8** and
the locally pinned artifact SHA checks, but requests `cache-disabled: true`
for `gradle/actions/setup-gradle@v4` on this permanent self-hosted runner.
This only bypasses remote Gradle cache transfer; it does not bypass Gradle,
Forge tests, source compilation or any real-game acceptance requirement.

### Fresh owner-local original-JAR GameTest after protected-asset CPA (2026-10-11)

The latest **local** Java17 / Gradle8.8 Forge 47.4.20 run executed **all
20 unchanged original GameTests: 19 PASS / one B-17 escort FAILED**. Its
live pilot now passes every currently FOV/LOS-visible hostile to the
collision safety model rather than including only the one strategy selected;
unseen and unassigned enemy positions remain excluded. The native GameTest
reported `B17_95_BLOCK_PROTECTION_BREACH intrusionTicks=105
minDistance=52.68007278442383`; a fully separate synchronized CSV reader
measured **104/340** inside 95 blocks with a **52.680071b** minimum, because
the native and independent sample horizons differ at one endpoint.
**Neither passed the original zero-intrusion gate.** The preceding local
strategy had **49/340** and a minimum **82.570680b**; this source tactic
and observed-CPA policy combination demonstrably **WORSENED** protection.
The original 30b escort net-displacement condition was not reported failed
in this run, and no safety/mission threshold or opening geometry was altered.

The same new live GameTest demonstrates the actual observed selector:

| Real 340tick actor | Confirmed enemy-sighting ticks | Both hostile aircraft visible simultaneously |
|---|---:|---:|
| B-17 | 168 | 141 |
| P-47N left escort | 304 | 104 |
| P-47N right escort | 112 | 91 |

`tools/verify_live_threat_receipts.py` independently checks the complete
**341 authentic actor samples per case**, original server/Entity tick clocks,
explicit ally team, ID-shaped actual sensor sightings and
`VISIBLE_CPA_TO_PROTECTED_ASSET` decisions, and **PASS**. This confirms the
new selector operated under real Forge conditions, but **does not prove it
chose the right target or succeeded at the B-17 mission**. Eight synthetic
adversarial tests reject absent/short/forged contacts, invisible enemy
reports and invalid team data; those fixtures are not Minecraft evidence.
Real 2v2 remains **PASS** (all original 6b separations), both original IL-2
and B-17 physically complete **840tick no-ordnance ingress/egress/RTB
guidance PASS**, and independent source open-loop replay of the new exact
real record again gets **35/35 / 24 aircraft / 5,880 ticks PASS**, maximum
0.001775711195b final discrepancy under the distinct 0.01b free-flight
threshold. **This does not certify closed-loop strategic/weapon/voxel
collision parity**. Proprietary source JARs and raw owner-runtime CSV bodies
remain gitignored and must not be pushed.

### Original-Forge target-choice hysteresis — latest owner-local evidence

Comparing the saved, unchanged original 340tick pilot CSVs exposed distinct
**enemy-target changes at physics ticks 47 and 109**, during which the two
currently FOV/LOS-visible opponents' constant-velocity CPA priority scores
differed by only approximately **0.00b and 0.02b**. The protected bomber's
steering direction and real yaw reversed rapidly, which was associated with
a worsening of its minimum actual enemy clearance. This is a specific
measured cause candidate, **not proof of causal benefit**.

`LiveThreatPriority.chooseStable()` now retains the previously followed
hostile **only when that hostile independently passes the real range/FOV/
voxel LOS check again on this exact server tick**, and only if the currently
visible best competitor improves CPA urgency by **no more than 8 blocks**.
This is a bounded tactical-selection deadband, not an operational 95b, 6b or
30b acceptance threshold. If a better visible threat becomes clearly more
dangerous, the AI can switch. If the old contact becomes invisible, it cannot
be relabeled a fresh sighting. The pilot separately includes every genuinely
visible hostile in physical safety planning. The original no-fire input
contract remains `false,0`.

The **subsequent new local original-JAR 20-GameTest run** with this retention
and unchanged original five-aircraft starting geometry resulted in
**19 PASS / one still FAILED**. Original native Forge B-17 mission measured
**81/340** hostile intrusion ticks, closest **65.020050b**. Independent
strict synchronized CSV audit agrees **81/340**, **65.020052b**, with
minimum 10-pair aircraft separation **11.006527b** (thus zero under-6b
events). This is better than the immediately previous visible-CPA run
**105/340 at 52.680073b**, but still worse than an earlier policy's
**49/340 at 82.570680b**. The zero-intrusion strict criterion is not met.
All five original aircraft complete the full 340tick real physics horizon;
2v2 remains PASS, real IL-2/B-17 840tick strike/egress/RTB geometry PASS,
and newly measured independent 35-flight open-loop physics replay remains
PASS with maximum end error **0.001775711195b**. None of these imply
real weapon operation, bomber protection or landing.

The new `tools/forensic_b17_compare.py` produces a **read-only original
Forge vs externally autonomous SOURCE Twin** 341-step forensic timeline,
1,705 aircraft rows, numerical diagnostics, failure events, and self-contained
`forensic_b17.html`. Against the newest unmodified actual original pilot
records the tool explicitly marks an outdated summary sidecar as
`STALE_SIDE_CAR_QUARANTINED_NOT_ACCEPTED`, recomputes REAL geometry from
complete authenticated CSV, and separately reports real **81/340 / 65.020052b
FAILED** vs closed-loop SOURCE **204/340 / 30.355539b FAILED**. These
distinct policy trajectories are **not** a physics parity result. Only the
earlier recorded-control 35 flights establish scoped original aerodynamic
open-loop fidelity. Raw owner telemetry is ignored and never committed.

## Ownership and runtime contract

The adapter is under `runtime-probe/` and includes the **exact shared pure-Java** classes from `physics-ai/src/main/java` at compile time, including `TacticalAirAI`, `HistoricalDoctrineOrders`, `FlightGuidance`, `FlightSafetyPlanner`, `FlightControlLoop`, and `AircraftAtlasMain`. `stageRuntimeTacticalAtlas` embeds `../data/base-aircraft-anchor-v1.csv`; `RuntimeTacticalAtlas.load()` evaluates all 24 entries with the same code used by source-only tests. The driver does not hard-code A6M tuning or claim the ANCHOR JSON is the shipped historical WARFARE WINGS release.

The important observed control path comes from Immersive Aircraft source at immutable commit `550b38d3dfdbf5cb6ec3f78468e0e60725a47605` (tag `1.3.3+1.20.1`):

- [VehicleEntity.java](https://github.com/Luke100000/ImmersiveAircraft/blob/550b38d3dfdbf5cb6ec3f78468e0e60725a47605/common/src/main/java/immersive_aircraft/entity/VehicleEntity.java) lines 95–97: `public final InterpolatedFloat pressingInterpolatedX/Y/Z`; lines 181–182: 10 input interpolation steps; lines 380–435: `tickPilot()`, physics/controller, then `pressingInterpolated*.update(movement*)`; lines 505–522: a non-local/non-player pilot causes `setInputs(0,0,0)`; lines 821–825: public `setInputs(float,float,float)`.
- [InterpolatedFloat.java](https://github.com/Luke100000/ImmersiveAircraft/blob/550b38d3dfdbf5cb6ec3f78468e0e60725a47605/common/src/main/java/immersive_aircraft/util/InterpolatedFloat.java) lines 11–12, 19–28, 43–45: internal `steps=1/steps`, public `update(float)`, `decay(float,float)`, and `getSmooth()`.
- [AirplaneEntity.java](https://github.com/Luke100000/ImmersiveAircraft/blob/550b38d3dfdbf5cb6ec3f78468e0e60725a47605/common/src/main/java/immersive_aircraft/entity/AirplaneEntity.java) lines 33–58: controller gated by `isVehicle()`, `movementY` increments target engine but `setEngineTarget(float)` is available, then thrust. [AircraftEntity.java](https://github.com/Luke100000/ImmersiveAircraft/blob/550b38d3dfdbf5cb6ec3f78468e0e60725a47605/common/src/main/java/immersive_aircraft/entity/AircraftEntity.java) lines 122–129: `pressingInterpolatedX/Z.getSmooth()` controls yaw and pitch.

With an ArmorStand pilot, applying `setInputs` at `ServerTick.START` is ineffective because the plane resets it before physics. The present laboratory adapter therefore observes the airplane **after its entity tick**, at `ServerTick.END`, and calculates its next command through `FlightControlLoop.step()`. After IA's own `update(0)`, smooth is (0.9s_{N-1}). The adapter applies its raw steering control `u_N` by public `decay(0.9s_{N-1}+0.1u_N, 1)`, faithfully restoring the one-update-per-tick *source* interpolation recurrence. The AI command chosen at tick N thus affects IA yaw/pitch at **tick N+1**, not the just-completed physics tick. The adapter calls IA's `setEngineTarget(float)` and does not directly manipulate rotation, position, velocity, weapon callbacks or packets.

The runtime adapter checks that the resolved control surface still has the public/reflective `setInputs(float,float,float)`, `pressingInterpolatedX/Z`, `getSmooth()`, `decay(float,float)`, and private `steps == 0.1f`. A changed binary fails explicitly. These expectations come from the pinned source; binary identity is still checked separately.

## Exact artifact gates

The ForgeGradle task `verifyPinnedRuntimeJars` runs automatically before `prepareRuntimeTrace` / `runGameTestServer` and rejects absent or mismatched staged JARs:

| Runtime binary | Required digest |
|---|---|
| `flight-test-mods/warfare_wings-1.1.4-1.20.1-forge.jar` | SHA-256 `dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43` |
| `flight-test-mods/immersive_aircraft-1.3.3+1.20.1-forge.jar` | SHA-512 `7b74442e161bb74538e0d8da34a81616daeea56a0da62db86113a78b3bf3c2b3a6b0e12f12454fd7c96092762f6b212ba57cb87eb1af2b242a4d5df4eca03055` |

Build with Java 17 and Gradle 8.8:

```powershell
cd departments/minecraft/mods/warfare-wings/physics-ai/runtime-probe
gradle --no-daemon compileJava processResources verifyTacticalInputCorrection
gradle --no-daemon verifyPinnedRuntimeJars
gradle --no-daemon runGameTestServer
```

The first command can compile without the private JARs, using ForgeGradle's 1.20.1 mappings; it proves the **source adapter compiles**, not that the exact mod JAR can load. `verifyTacticalInputCorrection` runs six source-only synthetic ticks and asserts interpolated input recurrence and one-physics-tick control delay. The latter two commands require both pinned binaries. Do not replace the researched mod with the public version or with IA 1.3.2 to get a green check. Local runtime JARs and Gradle caches are excluded by `runtime-probe/.gitignore`.

## Spawn tests, observation and command bridge

Existing `ThrottleTraceGameTests.a6mThrottleStep` is preserved unchanged, including the 400-tick comparison recorder. Added five independent `TacticalRuntimeGameTests`, each at 180 aircraft entity ticks, using the **real Warfare Wings entity registry** and a mounted non-player pilot:

| Case | Real entity | Mission | Effect |
|---|---|---|---|
| `a6m-steered-interception` | `warfare_wings:a6m` | INTERCEPT | Turns toward an explicitly designated stationary observation target |
| `p47n-steered-interception` | `warfare_wings:p47n` | INTERCEPT | Same geometry; different Atlas-derived control envelope |
| `il2-ground-approach-no-fire` | `warfare_wings:il2` | STRAFE | Approaches ground-objective waypoint; weapon firing disabled |
| `b17-level-bomb-guidance-only` | `warfare_wings:b17` | LEVEL_BOMB | Remains on level route; no bomb release |
| `g4m-torpedo-guidance-only` | `warfare_wings:g4m` | TORPEDO | Approaches target geometry; no torpedo release |

Each GameTest asserts the actor remains a mounted IA aircraft through all ticks, produces nonzero steering, **moves at least 8 blocks**, and accumulates at least 2 degrees of yaw while responding to steering. Initial passive yaw may occur *before* the first server-END AI command, so the test does not infer an impossible causal clock from the first nonzero yaw alone. The strict receipt validator checks the source-derived 24-airframe smoothing recurrence and continued post-command movement separately. Each case writes a CSV in `run-gametest/ww-physics-traces/<scenario>-forge-controls.csv`. The trace separates real position/velocity/yaw and IA smoother state from AI commands, active maneuver and safety reason.

**GameTest isolation contract:** the five tactical scenarios each have their own single-test `@GameTest(batch="ww_tactical_<aircraft>")` batch. Their aircraft carry the `ww_tactical_game_test` tag. During each tick, if **any other** Warfare Wings aircraft enters the probe's 80-block nearby-aircraft sensor query, the isolated run fails with `cross-scenario aircraft within tactical sensor range`; it is never quietly interpreted as a new collision-avoidance maneuver. This catches accidental runner overlap even when tests are unexpectedly placed near each other. The existing 400-tick throttle trace stays in its separate original batch. After a successful restart with the same scenario name, the runtime pilot replaces its previous result and captures a fresh CSV; completed results are bounded to the latest 32 entries.

The owner-controlled Windows runtime workflow separately fails closed on each of the five tactical CSV receipts, checking 181 samples (initial tick 0 plus 180 executed ticks), the schema and aircraft identity, real nonzero lateral commands, yaw travel and displacement before the original A6M calibration. It also validates **all 24 independently generated 40-tick per-type aircraft receipts** with `tools/verify_all_aircraft_runtime_receipts.py` and its exact-model steering and motion thresholds. Uploading files alone is not evidence of successful flight validation.

If loaded manually with the pinned JARs, an operator (permission level 2) may issue `/wwai patrol` next to **exactly one empty, already-airborne** Warfare Wings aircraft within 20 blocks. It attaches a synthetic IA pilot, uses the same safety/guidance/recording loop for up to 900 ticks, and writes a uniquely named trace. `/wwai stop` detaches only that operator's synthetic pilot and leaves the aircraft intact. The command provides no combat, projectile, release, PvP or persistent world AI. It refuses ambiguous aircraft selection or a plane already occupied by a player.

The environment sensor uses actual world heightmap samples and other registered Warfare Wings aircraft as moving collision obstacles; **historical faction is not inferred to mean friend or enemy**. Only explicitly supplied enemy entities count as hostile; an optional doctrine order is an explicit scenario input. Collision envelopes and the temporary altitude margin remain gameplay hypotheses requiring live measurements.

## Known limits

The exact originally supplied WW SHA-256 JAR and pinned IA SHA-512 JAR are now both available for laboratory tests. A **local** Forge 1.20.1 exact-artifact GameTest run recorded `All 13 required tests passed :)`, including 24 sequential registered real-aircraft 40-tick smokes and the previous 12 named scenarios. Each type generated a physical movement/yaw/input-smoother trace; the independent model-aware validator confirmed all 24, and verified all five long 180-tick representatives. The pinned IA mixin initially failed SRG/official name resolution under UserDev; `gameTestServer` now explicitly remaps that original refmap through `createSrgToMcp/output.srg` **without modifying either JAR**. One earlier GameTest also exposed non-discarded aircraft contamination; test-owned entities are now cleaned up. These are **measured local GameTest results**, not full physical-parity calibration, runtime combat success or an owner GitHub Actions green run.

The driver has one-tick control lag, ArmorStand piloting, no ownership of real player controls, no weapon firing, no multiplayer player-input protocol, and no proof that the command will be acceptable in every game configuration. Only actual GameTest telemetry is promoted to `MEASURED`; model ranks remain `SOURCE_MICROKERNEL`.

## Live multi-aircraft autonomy (measured in bounded exact-JAR GameTests)

The `LiveSquadronCommands` operator interface is distinct from the original `/wwai patrol` research shortcut. A new live run registers an independently controlled, already-airborne and empty Warfare Wings entity; it mounts an owned ArmorStand pilot, retains an independent `TacticalAirAI.Memory`, and drives the **same** `FlightControlLoop` and IA next-tick input path. Up to 16 aircraft can be enrolled per command, subject to 64 active live-aircraft slots. Each controller expires automatically after 900 completed aircraft ticks and can be stopped sooner. Atomic preflight rejects an invalid or occupied selection; bulk enrollment rolls back any pilots successfully started before a later failure. Only explicitly selected entities are enrolled.

Use these permission-level-2 commands (individual aircraft selectors may use their exact entity UUID):

```mcfunction
/wwai enlist <aircraft> <team> <mission>
/wwai group <aircrafts> <team> <mission>
/wwai enemyteam <team> <enemyTeam>
/wwai target <aircraft> <targetEntity>
/wwai mission <aircraft> <mission>
/wwai waypoint <aircraft> <x> <y> <z>
/wwai leader <aircraft> <leaderAircraft>
/wwai squadstatus
/wwai stopcraft <aircraft>
/wwai stopteam <team>
```

Valid missions: `PATROL`, `INTERCEPT`, `ESCORT`, `LEVEL_BOMB`, `DIVE_BOMB`, `STRAFE`, `TORPEDO`. The project's existing Atlas validates compatible aircraft roles for strike missions before enrollment; **installed weapon loadout is not verified**, so all weapons, bombs, and torpedoes are **disabled**. Assign arbitrary lowercase team names of 1–24 characters starting with a letter; an aircraft's historical country, painted faction, name, or crew origin never defines its live team. `enemyteam` sets *explicit* hostile groups for all aircraft already enrolled under a chosen team in that dimension. `target` explicitly designates one entity UUID and replaces its selected enemy team. A same-team registered aircraft cannot be an explicit hostile target. `leader` requires a currently enrolled live aircraft on the same team in the same dimension. Each follower receives a stable per-leader slot (up to 16) at order assignment, with left/right and trailing spacing rotated into the leader's current yaw through `HistoricalDoctrineOrders.station`; slots are preserved when other followers are added, and released when detached. This is a **gameplay spacing candidate**, not verified real formation flight. `waypoint` sets a fixed target coordinate, including for patrol/strike routes. `squadstatus` reports each aircraft's mission/team/target/station slot and actual observed/rejected sensor counts. `stopcraft` and `stopteam` discard only their own synthetic crew, never the aircraft.

For example, after separately enrolling one A6M as team `blue` and one P-47N as team `red`, issue `/wwai enemyteam blue red` and `/wwai enemyteam red blue`. Each controller scans only enrolled aircraft in the assigned opponent team, **in the same level**, and only acquires a hostile when the actual entity lies within 240 blocks, inside a full 150-degree nose-relative cone, and has unobstructed Minecraft block ray visibility (`ClipContext.Block.COLLIDER`). A manually assigned individual target must pass exactly the same real visibility gate. No world-wide search for random hostile entities or fake universally known enemy coordinates exists. Unknown opponents remain unknown. All nearby registered aircraft are treated as moving obstacles independently of team.

A *confirmed* observation is remembered for at most **6 game ticks** after loss. During that time, the only extrapolated position comes from the **last observed position and velocity**, never from an unseen entity's current live position; the memory is then discarded. A change in live orders clears this memory immediately. Sightings and short-lived predictions are marked separately in the CSV reason field (`sighting=visible:<uuid>` or `sighting=last_seen_prediction:<uuid>`). The extrapolation is for steering only; it is **not a fresh sighting**. Runtime `Frame.lineOfFireClear=false` and `projectileSpeedBpt=0` for all live runs, so a stale track can never authorize firing. The pilot has no ammunition, mount, friendly-fire arbitration, target-leading ballistic solver, or proven exact-binary firing API; no shot is requested from IA or Warfare Wings.

The legacy `TacticalRuntimeGameTests` single-airplane experiments keep using an explicitly preset ArmorStand as test data. **That test-only contact is not the live sensing path.** The separate `LiveSquadronGameTests.twoIndependentPilotsAcquireAssignedEnemy` GameTest spawns a real A6M and P-47N, enrolls them into opposite explicit teams, and requires both independent real flight displacements and multiple *confirmed* live contacts. It explicitly rejects extraneous aircraft entering the paired controller's proximity sensor. `actualAirplaneFovAndBlockOcclusion` checks a real airplane target in front of the pilot, outside the rear field of view, hidden by a newly placed solid block, and visible after the obstruction is removed. `twoFriendlyAircraftNotImplicitlyHostile` enrolls two aircraft on the same team without an enemy-team or explicit-hostile order and requires zero acquired or extrapolated contacts. All three tests have unique batches and require pinned runtime JARs; source compilation cannot prove their results. The preexisting 400-tick throttle GameTest and five isolated single-aircraft GameTests remain unchanged.

## Verified weapon-entry API and why live firing remains disabled

The original Warfare Wings ANCHOR was independently SHA-256 verified (`dc302959...`) before being staged in the **gitignored** `runtime-probe/flight-test-mods/` directory. Separately the immutable IA `GsVmbbkj` binary passed the retained SHA-512. Public Warfare Wings binaries with different hashes are comparison material only. The following findings come from the exact ANCHOR's bytecode (`javap -c -p`) together with the pinned [Immersive Aircraft source commit](https://github.com/Luke100000/ImmersiveAircraft/tree/550b38d3dfdbf5cb6ec3f78468e0e60725a47605):

| API path | Direct evidence | Consequence for autonomous firing |
|---|---|---|
| IA `InventoryVehicleEntity.fireWeapon(int slot,int index,Vector3f direction)` | Calls `getWeapons().get(slot).get(index).fire(direction)` without independent checking of indexes, gunner authority, cooldown, safe muzzle alignment or friendly proximity | Calling it directly would bypass useful client/mission safety requirements |
| IA `FireMessage.receive(Player)` | Resolves the passenger's vehicle and calls `vehicle.fireWeapon(...)`; its input is a real `Player` | The server AI's synthetic ArmorStand cannot legitimately use the client packet without a player and must not impersonate one |
| IA `BulletWeapon.spentAmmo(...)` | Loads ammunition from an `InventoryVehicleEntity` and reduces inventory/count, then reports availability | The ammo check exists in some concrete weapons, but cannot by itself prove installed mount or server cooldown |
| WW `WarfareWingsMG.fire`, exact ANCHOR bytecode | Calls `spentAmmo(Config.gunpowderAmmunition,10)` followed by `BulletWeapon.fire`; `WWFBulletEntity` sets projectile owner to the vehicle entity | There is a server projectile implementation, but no verified operator/team kill attribution and no validated dynamic friendly fire check |
| WW `WarfareWingsBombBay.fire`, exact ANCHOR bytecode | Calls `spentAmmo(Config.bombBayAmmunition,20)` followed by `BulletWeapon.fire`; inspected bomber projectile creation does not explicitly assign owner | Cannot responsibly infer credit for kills or safe explosion/target ownership |
| IA `HeavyCrossbow` / `BombBay` examples | Cooldown is checked in client `clientFire`, while server `fire` checks ammo and spawns projectile; `HeavyCrossbow` owner is the controlling passenger | Synthetic ArmorStand ownership and server rate limit are not proven correct by invoking `fire` directly |

Therefore the bridge sets `Frame.lineOfFireClear=false` and `Frame.projectileSpeedBpt=0` and never calls `fireWeapon`, `FireMessage`, projectile constructors, or `Weapon.fire`. **This is a deliberate fail-closed implementation**, including during `DIVE_BOMB`, `STRAFE`, `LEVEL_BOMB`, and `TORPEDO`. Enabling shots would first require trustworthy installed weapon-mount/loadout and projectile-speed observation, a *server-owned* cooldown, real target LOS and aim lead, projected friendly-aircraft/ground fire corridor exclusion, correct owner attribution and damage/kill accounting, and tests against the exact loaded binary. The available source and ANCHOR bytecode do not jointly prove those safety contracts.

## Server-side mission phases (guidance only)

`LiveMissionPlanner` is deterministic and uses only the current aircraft position, operator-issued mission/waypoint/home, confirmed contact steering point, and observed engine fuel/health. It adds an explicit waypoint **strike ingress → strike egress** when the aircraft approaches within the uncalibrated 75-block gate; egress sends the aircraft toward its home route and disables contact pursuit, with *zero ordnance release*. `ESCORT` uses a heading-rotated follower station in quiet air; when a genuine contact threatens, it passes the actual leader position as the protectee to `TacticalAirAI` so the threat intercept is leader-relative. The source still applies `FlightSafetyPlanner.guard` each tick. A manual `/wwai rtb <aircraft>` or `/wwai rtbteam <team>`, low fuel, or severe damage latches **RETURNING** with threat pursuit off and home-directed guidance. It does not attempt landing or fuel replenishment. These are game-specific logic thresholds pending exact-flight calibration.

New GameTests `LiveMissionGameTests` use unique batches: B-17 with a separate P-47N escort that has to show its escort phase and physical displacement; an Il-2 with a late changed ground waypoint that has to enter and exit the strike phase; and a P-47N receiving RTB while in flight that must reduce the measured distance to home, shed its synthetic pilot, and leave its aircraft intact. `verifyLiveMissionPhases` is a Java17 source-only deterministic regression for ingress, egress, protective stations, fuel/damage return, and latched RTB.

**Observation safety boundary:** In live mode, the broad 80-block aircraft query is used to detect actual *same-team datalink* wingmen and guard against unrelated test aircraft. Other planes' true coordinates never enter the collision planner unless that contact has passed the current FOV/range/LOS sensor or is still a valid (maximum six-tick) last-observed prediction. Consequently hidden or unknown-team aircraft may remain outside the AI's avoidance model; this is an intentionally limited sensor model, not a claim of omniscience.

**ForgeGradle GameTest mapping boundary:** the immutable released IA JAR uses production SRG Mixin selectors (e.g. `Player.m_36342_()Z`), while ForgeGradle's userdev GameTest runs Minecraft in Mojang official mappings (`Player.wantsToStopRiding()Z`). The exact name mapping was found in `build/createSrgToMcp/output.srg`. The `gameTestServer` run now asks Mixin to remap the released JAR's refmap via `mixin.env.remapRefMap=true` and `mixin.env.refMapRemappingFile=build/createSrgToMcp/output.srg`; neither original binary is modified. This development-run adaptation requires independent live validation.

## Exact artifact real Forge test evidence — 2026-10-11

Local source build `Java 17 / Gradle 8.8 / Forge 47.4.20 / Minecraft 1.20.1` compiled, generated resources, passed `verifyPinnedRuntimeJars`, `verifyTacticalInputCorrection`, `verifyLiveAirSensorCone`, and `verifyLiveMissionPhases`. **The exact pinned original Warfare Wings SHA-256 and pinned IA SHA-512 were verified against bytes staged in gitignored `runtime-probe/flight-test-mods/`.** Actual `runGameTestServer` then returned **exit code 0** with the Forge server log:

```text
========= 13 GAME TESTS COMPLETE ======================
All 13 required tests passed :)
```

This comprises the unchanged 400-tick A6M throttle trace, five isolated 180-tick aircraft guidance/position/yaw tests, three existing live contact/team/obstruction checks, three live escort/strike-ingress-egress/RTB mission tests, and the new **24-base-airframe sequential real flight smoke**. The new `AllAircraftRosterGameTests` loads the same 24 source Atlas aircraft IDs, and individually validates actual registry spawn, an IA-mounted synthetic pilot, at least 40 physics ticks, 4 blocks observed position displacement, at least 3 nonzero lateral input ticks and at least 0.25 degrees accumulated yaw. Each aircraft and its synthetic pilot are removed before the next aircraft starts; no multi-plane collision is inferred from the sequential result. This is **source-vs-actual model support and bounded movement**, not validated dogfight success or aerodynamic parity. The entire set of 13 test methods passed without bypassing any assertion.

Example final-position displacement and yaw from the five actual 180-tick single-plane control CSVs (all blocks/degrees in this Minecraft world, **never** historical aircraft units):

| Aircraft | 180-tick final displacement | Start yaw → end yaw |
|---|---:|---:|
| A6M | 106.31 blocks | 0 → -31.06° |
| P-47N | 88.06 blocks | 0 → 144.86° |
| Il-2 | 100.82 blocks | 0 → -30.86° |
| B-17 | 57.94 blocks | 0 → -30.92° |
| G4M | 92.64 blocks | 0 → -30.87° |

The exact 1.3.3 source's `InventoryVehicleEntity.applyFriction()` first applies `rf=(1-friction)*VehicleStat.ROTATION_DECAY` to `pressingInterpolatedX/Z`; only then does `VehicleEntity.tick()` perform the 10-step `update(0)`, and the END-tick adapter adds `0.1*rawCommand`. With effective source friction `0.015` and rotation decay `0.97`, the correct **airborne recurrence** is `smooth[t] = 0.859905*smooth[t-1] + 0.1*command[t]`. The real same-artifact traces independently reproduce that retention across A6M/P-47N/Il-2/B-17/G4M; the source-only `IaNonPlayerInputBridgeMath` regression now asserts the correct six-tick series. A tiny passive A6M yaw change of +0.005° occurred **before the first command**; the runtime pilot's first-response test now requires a subsequent, causally directed yaw change consistent with IA's `yaw -= yawSpeed*smoothX`, while retaining accumulated physical steering thresholds. The earlier incorrect `first yaw movement > first command` failure is no longer conflated with an actual input timing bug.

Actual testing also exposed orphaned aircraft from prior GameTest batches: the 1×1×1 test structure does not clean up entities spawned 200+ blocks above it. Every test-created aircraft/pilot/contact is now explicitly discarded on terminal success/failure, with isolation guards remaining active. The initial post-refmap run **failed** from an orphan B-17, the next run **failed** from a passive-yaw false causal classification, and the final exact run passed all 13 after these root-cause fixes. Evidence was retained as measurements/failures; thresholds were not reduced.

Fuel semantics were also corrected from source: `EngineVehicle.getFuelUtilization()` denotes powered boiler utilization rather than fuel quantity. The runtime now reads the private pinned `EngineVehicle.fuel[]` counters via guarded reflection and returns a conservative fraction of `TARGET_FUEL=1000` for RTB decisions; when calibration disables fuel consumption, reserve is explicitly 1.0. `Ia133Microkernel.State.fuelUtilization` continues to receive actual engine utilization and the frame uses this separate fuel-reserve indicator. IA `VehicleEntity.getHealth()` is already normalized to 0..1 in pinned source.

**Remaining implementation limits:** No weapon fire, bomb or torpedo release is enabled; actual WW bullet/bomb bytecode ownership/cooldown/friendly checks do not yet meet the contract above. No exact-class `*Torpedo*` implementation was identified in the inspected WW JAR inventory. The 24-plane smoke measures only short controlled movement; combat kill outcomes, dogfight damage/avoidance under multiple actively engaging hostiles, longer-term fuel endurance, realistic landing, and all 24 aircraft's full 401-tick precision calibration remain further research. Archive the exact traces and unchanged artifact hashes with any new acceptance decisions.

## Extended real operational GameTests — 2026-10-11

`OperationalAirCombatGameTests` adds two independent longer acceptance scenarios using the exact pinned JARs and server-controlled aircraft. The scenario controller never creates projectiles, infers hostile positions outside FOV/range/LOS, or counts simulated combat hits. `GameTestFlightChunkLease` is test-only: it loads current and anticipated flight chunks, uses shared per-level reference-counted tickets, releases only chunks whose forced state it actually changed, and cleans up on normal completion/server stop. It does not alter regular `/wwai` pilot behavior. After the original CI detected B-17 tests stalling outside the GameTest structure, new tests preload each spawn's initial chunk before creating aircraft, require consecutive 20 Hz entity ticks, and fail explicitly if any enrolled plane stops ticking for more than 20 server ticks.

The operational scenarios are:

| GameTest | Aircraft and duration | Physical acceptance conditions |
|---|---|---|
| `twoVsTwoMustReallyEngageAndManeuver`, batch `ww_operational_2v2` | 2 A6M vs 2 P-47N, 280 actual ticks each | All four flights finish and move at least 30 blocks; any pair separation at least 6 blocks; at least one opposing contact comes within 120 blocks; each side records at least 8 confirmed visible-hostile ticks |
| `twoEscortsDefendB17AgainstTwoApproachingHostiles`, batch `ww_operational_b17_escort` | B-17 + 2 P-47N escorts vs 2 approaching A6M, 340 ticks each | All five finish and move at least 30 blocks; any pair separation at least 6 blocks; each escort has at least 150 assigned escort ticks; attackers approach the B-17 within 150 blocks; **zero** ticks with a raider inside the B-17's 95-block protection corridor |

Every plane generates its own `op-<name>-forge-controls.csv` trace; a separate `operational-2v2-geometry.csv` or `operational-b17-escort-geometry.csv` is recorded with one clock/sample per plane and the real coordinates, sighting counts, escort phases, opponent distances and B-17 distances. An operational failure is reported as a GameTest **FAILED** while preserving all geometry and allowing subsequent unrelated tests to execute; no acceptance threshold is silently lowered. Both real scenario results are further independently inspectable from their five- or four-plane control traces.

### Actual measured result

The final local run of the exact binaries reported **15 total GameTests: 14 PASS / 1 FAILED**, with `runGameTestServer` **exit code 1** (expected whenever a required GameTest fails). The existing 13 tests continued passing after the operational failure.

| Long-run measured result | Status | Actual observation |
|---|---|---|
| 2 vs 2, 280 ticks | **PASS** | Four source-guided aircraft flew with synchronized complete traces; minimum any-plane separation **11.198347 blocks**; minimum opposing-team separation **27.331806 blocks**; no pair came closer than 6 blocks |
| B-17 escort, 340 ticks | **FAILED** | Actual attackers penetrated the 95-block corridor for **101 ticks**, with closest B-17–raider separation **66.029297 blocks**; both guards were assigned to the escort phase but did not physically contain the attackers |

The B-17 failure is an actual **operational threat-containment failure**; it does not establish that a hypothetical machine-gun attack or kills would have occurred, because weapons are still disabled. The B-17 scenario correctly rejects a superficially successful result based on moving distances or assignment counts alone. The test still requires complete active ticks and confirmed threat approach: it cannot pass by preventing the attackers from loading, hiding targets, reducing attack range or omitting the hostile team. This work is a physical acceptance instrument for the tactical controller rather than a declaration that the controller now wins these engagements.

The initial runs failed from an un-ticking raider spawned in a distant chunk and from shared chunk leases being released too early. Source-level issues were corrected by synchronous preloading, shared ticket reference counting and one-time registration before physics-time measurement. The later reproducible B-17 run ran the required actual geometry and reached the explicit 95-block protection assertion. A future controller change must prove **zero real intrusion ticks** under the same or harder scenario before this GameTest can become PASS. The snapshot here may predate concurrent tactical Java improvements made by another worker; rerun against their final source before accepting integration.
### Final integration after standalone Twin END-bridge repair

After the external source Twin's smoothed-input actuation phase was repaired,
the owner **locally reran** Java17/Gradle8.8 `prepareRuntimeTrace
runGameTestServer` against the same **exact-hash original WW/IA Forge JARs**.
All **20 native GameTests completed: 19 PASS, one B-17 FAILED**, with
`B17_95_BLOCK_PROTECTION_BREACH intrusionTicks=81
minDistance=65.02005004882812`. The Gradle command exits **1** because the
GameTest's strict acceptance gate correctly fails, **not** because the
project failed to compile or because a Forge test was skipped.

Independent validators on the **newly re-recorded original real flight CSVs**
reported real 2v2 geometric **PASS**, real B-17 **FAILED** (`81/340`
intrusions), original 3-actor FOV/LOS contact-ranking **PASS**, original
840tick IL-2/B-17 no-ordnance return **PASS**, and the **35/35**
real-recorded-command free-air Twin replay **PASS** (24 airframes, 5,880 paired
ticks, maximum final position discrepancy **0.001775711195b**, distinct
0.01b physical replay gate). Raw original traces remain ignored; their
source-only analyses never replace actual GameTest geometry. The aborted
48tick B-17 bomber escape-side latch was **reverted after a worse SOURCE
190tick test**; the production tactical AI source remained unchanged.
