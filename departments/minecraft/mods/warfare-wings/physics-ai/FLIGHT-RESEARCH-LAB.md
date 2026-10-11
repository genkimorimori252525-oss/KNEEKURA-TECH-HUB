# Warfare Wings — Offline Flight Research Lab

**Status: deterministic SOURCE_MICROKERNEL experiments, NOT Minecraft/Forge physics parity.**
The laboratory provides reproducible flight/AI research without launching a
Minecraft client. Exact-runtime movement, terrain, contact, wind and weapons
acceptance tests must remain separate.

The source entrypoint is **FlightResearchBatchMain.java** under
**physics-ai/src/main/java/org/kneekura/techhub/warfarewings/physics/**.
It loads all 24 current ANCHOR-derived aircraft via AircraftAtlasMain.load,
derives the actual SOURCE profiles via AircraftAtlasMain.evaluateReaction,
looks up the bytecode-verified aircraft engine reaction from
WarfareWingsEngineReaction.ticks, and calls **Ia133Microkernel.tickWithReaction
once each simulated tick, at 20 Hz**.
The default physical wind callback now uses the verified pinned IA 1.3.3
**PinnedIa133WindWorld.calmAirCalibration().windAfterFriction** on every
flight: zero configured weather wind still produces speed-dependent
aircraft yaw/pitch forcing through the original five-harmonic cosNoise.

Autonomous scenarios run FlightControlLoop.step, the existing
TacticalAirAI/FlightGuidance/FlightSafetyPlanner controllers and optional
HistoricalDoctrineOrders before the next physics tick. These produce raw
X/Z/throttle controls that the microkernel smooths. No direct position,
velocity or rotation override and no invented weapon, hit or kill simulation.

## One command in PowerShell

From the **physics-ai** folder, with Python 3 and JDK 17:

~~~powershell
$output = Join-Path $env:TEMP "ww-flight-research-lab"
py -3 .\tools\flight_lab_run.py --java-home "C:\Program Files\Java\jdk-17" --output $output --seed 20261011 --trials-per-aircraft 512 --ticks 180 --trace-stride 10
Start-Process (Join-Path $output "flight-lab.html")
~~~

Only Java 17 and Python standard libraries are used. The wrapper checks
that both the **compiler and runtime are JDK 17**, compiles only the pure
Java dependency graph into a temporary location, executes the SOURCE batch,
verifies counts/provenance, and builds the offline HTML. The JDK 17 path can
also come from JAVA17_HOME, JDK17_HOME or JAVA_HOME.

Default run: **24 aircraft × 512 trials = 12,288 distinct trials,
180 ticks each = 2,211,840 SOURCE ticks.** At least 11 trials per aircraft
are required to include all conditions. The seed is mixed with aircraft
ID and trial index, so the individual trial stays unchanged if the CSV
aircraft order changes. Use a durable --output path outside the repo for
experiments you want to keep.

Quick complete-coverage example:

~~~powershell
py -3 .\tools\flight_lab_run.py --output "$env:TEMP\ww-flight-lab-smoke" --trials-per-aircraft 11 --ticks 90
~~~

To rebuild only the HTML from existing Java outputs:

~~~powershell
py -3 .\tools\flight_lab_report.py "$output\summary.json" "$output\time_slices.csv" "$output\flight-lab.html"
~~~

## 11 experimental conditions × all 24 aircraft

Each model receives a balanced set of seeded trials (46–47 repetitions
per condition in the default run). Seeded initial altitude, velocity,
attitude, engine spool, ridge, wind phase and observed contact vary
between experiments. Aircraft models retain their individually
extracted stats and engine reactions.

| Scenario | Applied stimulus | Research question |
|---|---|---|
| CRUISE | No stick, full throttle | Speed response and path distance |
| THROTTLE_STEP | Throttle 0 then 1 | Engine-response transient |
| TURN_LEFT | Raw X = −1 after tick 15 | Yaw authority, 90° acquisition |
| TURN_RIGHT | Raw X = +1 after tick 15 | Opposite turn and symmetry |
| CLIMB | Raw Z = −1 after tick 10 | Pitch-up and climb trajectory |
| DIVE_RECOVERY | Raw Z = +0.9 then −0.9 | Dive/recovery behavior |
| SCRIPTED_WIND | Extra deterministic periodic wind perturbation atop pinned baseline | Declared external wind sensitivity |
| TERRAIN_RIDGE | Procedural height ridge, lower spawn, active safety AI | Height-based contact and recovery |
| AI_MISSION_ROUTE | Role-compatible patrol/bombing/attack route | Source-controller closed loop |
| AI_OBSERVED_CONTACT | Kinematic hostile observation | Intercept/survival/safety commands |
| AI_FORMATION | Moving leader and eligible historical orders | Formation station control |

**World limits:** every scenario receives the pinned IA 1.3.3
**speed-dependent calm-weather aerodynamic wind** through the
post-friction physics callback. SCRIPTED_WIND additionally superposes
a seeded wind stress pattern; the extra overlay is not part of IA's
native wind/weather calculation. The ridge uses analytic height(x,z)
and SOURCE point-height contact; it does
not model Minecraft voxel movement, collision boxes, fluids or chunks.
The observed hostile has a scripted linear position/velocity only;
it is not a second physically simulated airplane. Shooting remains
disabled because weapons/ownership/hits must be verified in real Forge.

## Output format and live visualization

| Output | Contents |
|---|---|
| **summary.json** | Provenance, seed, 24×11 grouped means/events, schema/counts |
| **outcomes.csv** | All trials, unique seed, per-trial speed, distance, turns, clearance, ground contact, AI safety events |
| **time_slices.csv** | One representative track per aircraft/scenario sampled from tick 0 to final: XYZ, velocity, yaw/pitch/roll, engine/control and AI reason |
| **flight-lab.html** | **Self-contained** interactive 3D-style rotated trajectory, X/Z overhead, Z/Y side, speed/altitude-clearance time series and 24-aircraft table |

The HTML embeds the summary and representative tracks directly. It
works as a local file:// without fetch, CDN, third-party JS, external
assets or a local web server. Summary groups incorporate **all** trials;
the flight trajectory illustrates **one** trial per aircraft/condition.

## Verification and full benchmark, Windows 2026-10-11

~~~powershell
py -3 -m unittest discover -s .\tools -p test_flight_lab.py -v
~~~

Five Python integration tests compile and run the **actual Java17 SOURCE
physics**, check 24 airframes × 11 conditions, yaw/pitch responses,
model reaction examples (A6M 100 ticks, B-17 150, G10N1 200),
nonzero calm-air yaw from the pinned speed-dependent wind,
non-simulated weapon effects, integrity of JSON/CSV/HTML, and
**byte-identical output for two independent runs with the same seed**.
They also check that changing the seed changes outcomes, corrupt
summary metadata is rejected, fewer than 11 conditions fail closed,
and a tampered ANCHOR provenance column cannot run.
The complete **12,288-trial production batch** was repeated with the
same seed and all four output artifacts had identical SHA-256 hashes
across the two independent executions.

Observed full default run:

- **12,288 trials / 2,211,840 simulated 20 Hz SOURCE ticks**;
- **264 trajectory samples / 5,016 sampled time-slice rows**;
- **809** trials contacted the laboratory terrain height clamp;
- Java batch internally measured **1.657 seconds** (about **1.33 million
  SOURCE ticks/s**); **3.275 seconds** end-to-end including JDK17
  compile, batch outputs and HTML conversion.

| Aircraft | TURN_LEFT mean speed (blocks/s) | TERRAIN_RIDGE contact trials |
|---|---:|---:|
| A6M | 18.72 | 11 / 46 |
| P-47N | 26.12 | 4 / 46 |
| B-17 | 12.56 | 18 / 46 |

These are results from the particular seeded trial distribution, not
measured Minecraft max speed, historical performance, verified tactical
success, or real-world ground-contact probabilities. Benchmark speeds
are observed on one machine and not guaranteed elsewhere.

## Provenance and parity boundary

Aircraft effective values are derived from pinned Warfare Wings 1.1.4
ANCHOR SHA-256:

dc3029597c88859744633b6f5e4a9f21d449294b1aaac90ea0c1749d7aa98a43

Associated Immersive Aircraft 1.3.3 source commit:

550b38d3dfdbf5cb6ec3f78468e0e60725a47605

The runner validates the expected ANCHOR provenance **column** in all 24
input Atlas rows; it does not inspect/re-hash the original JAR on each run.
Every result carries this explicit machine-readable evidence:

**SOURCE_MICROKERNEL_BYTECODE_REACTION__SYNTHETIC_WORLD__NO_FORGE_PARITY**

Before promoting any laboratory result to **MEASURED**, replay its exact
aircraft/input/initial state and environment assumptions in pinned
real Forge GameTests. Resolve discrepancies in entity movement,
collision, chunks, network/input scheduling, wind and armament. Preserve
failed real-world parity gates regardless of SOURCE test success.

## Flight Twin v1: simultaneous multi-aircraft closed-loop physics (2026-10-11)

The 24-airframe lab now has an **additional execution mode**. It advances all
aircraft in a mission against one frozen prior-tick state, including **actual
opponent aircraft updated by the same physical source kernel**. Every pilot
first detects enemies independently, then selects a target from its own
observations or limited track memory, applies FlightControlLoop (existing
TacticalAirAI / FlightSafetyPlanner / FlightGuidance), and finally advances one
actual **Ia133Microkernel.tickWithReaction** with **PinnedIa133WindWorld**
speed-dependent calm-air wind. A second aircraft's current position is
available only to the **observer's measurement predicate** or the
**post-integration statistical evaluator**, never directly as hidden
information in a pilot decision.

The Twin implementation lives in new, same-package Java files:

- **FlightTwinSensor.java** — default finite detection range **240 blocks**,
  3D forward FOV **150° FULL (75° half-angle)**, matching the actual
  LiveAirSensor.java constants. Height-based LOS still uses 24 synthetic
  terrain samples, 1.5-block margin and a 6-tick stale contact memory;
  those three values remain unverified laboratory assumptions. Hidden
  contacts are extrapolated only from the last *actually seen* motion.
- **FlightTwinScenario.java** — strict original geometry, 95-block bomber
  protection and 6-block body-centre minimums; synthetic LOS fixture;
  an additional arbitrary 24-airframe scenario.
- **FlightTwinResearchMain.java** — synchronization, target load balancing,
  each pilot's track and maneuver memory, shared *friendly-only* telemetry,
  team formation/escort commands, 20Hz physical integration, continuous
  within-tick centre-pair diagnostic, strict original safety gates, stable
  machine-readable output.
- **FlightTwinSensorSelfTestMain.java** — executable Java17 assertions on
  front/rear/range/FOV/LOS, stale/expired enemy memory, and reacquisition
  without hidden true-position leaks.

**Enemy observations are synthetic sensor assumptions** based on the
scenario world height function. They are not Minecraft's block raycast,
rendering distance, hitbox occlusion or perception API. Teammate positions
are provided through an explicitly idealized separate ally-channel,
independent of hostile FOV or LOS. Weapon effects, kills and ammo consumption
remain disabled.

### Running the integrated 12k batch + multiplayer Twin

From the physics-ai directory:

~~~powershell
py -3 .\tools\flight_lab_run.py --mode both --java-home "C:\Program Files\Java\jdk-17" --output "$env:TEMP\ww-flight-lab-both" --seed 20261011 --trials-per-aircraft 512 --ticks 180 --twin-24-ticks 240 --trace-stride 10
Start-Process (Join-Path $env:TEMP "ww-flight-lab-both\flight-twin.html")
~~~

The **default --mode is now both**, and can be changed to **--mode twin**
for only the new experiment, or **--mode batch** for the original 12,288
single-plane SOURCE trials. Twin runs are deterministic with a signed
64-bit seed, independently of the aircraft specification input order.
Choose **--twin-scenario original_b17_aft**, **original_b17_forward**,
**original_2v2**, **all_24_unique** or **synthetic_los_occluded** to
restrict to a specific case. Running the complete Twin requires no network
or Minecraft client.

### Original starting geometry and experiment boundaries

The original combat cases preserve the unchanged coordinates, headings,
initial speeds and time horizons in CombatSimulationSelfTest:

| Case | Setup | Strict criterion |
|---|---|---|
| original_2v2 | A6M/F4U at X ±35, Y170, Z0 heading0, BF109/P47N at X ±35, Y170, Z105 heading180; all start at 1.2 blocks/tick, 160 ticks | All six aircraft pairs: swept and sampled minimum >=6 blocks |
| original_b17_aft | B-17 (0,170,0, heading0, speed0.8), F4U (-65,190,-20, speed1), P47N (65,190,-20, speed1), attacking A6M (0,170,170, heading180, speed1.3), 190 ticks | 6b pair separation and hostile distance from flying B-17 strictly >95b |
| original_b17_forward | Same B-17 and intruder; F4U (-27,190,115), P47N (27,190,115), 190 ticks | Same strict 6b and 95b criteria |
| all_24_unique | 24 **distinct** source airframe types, simultaneously piloted for 240 ticks by two artificial 12-aircraft teams | All 276 centre pairs >=6b; same 95b condition for actual B-17 |
| synthetic_los_occluded | A6M (0,170,0) and BF109 (0,170,90) with an artificial terrain wall rising to Y220 between Z37–58, 90 ticks | Detect blocked LOS; any terrain contact is reported as an explicit FAILED gate |

The **all_24_unique** blue/red assignments are an explicit arbitrary
**operator scenario configuration**. These teams do not imply nationality,
historical alliances or inferred hostility by aircraft type. All aircraft
keep individual source models, engine reaction and actual movement. F4U
and P47N are assigned to physically escort a moving B-17.

Pair safety now reports **both tick-end separation and closest distance
under a *piecewise-linear one-tick sweep***. This catches possible
between-frame proximity missed by endpoint sampling. A sweep over
centre positions still does not approximate the entire physical aircraft
hitboxes or an authoritative Minecraft collision event. The checks use
the **original 6.0-block and 95.0-block thresholds, unchanged**.

### Measured SOURCE results (seed 20261011, Windows JDK17, corrected 240b/FOV150° live-sensor contract)

| Case | 6-block centre-pair gate | B-17 minimum attacker distance | 95-block protection gate | Source result |
|---|---:|---:|---|---|
| Original 2v2 (160t) | min swept **30.030977b**, 0 breaches | n/a | n/a | **PASS_SOURCE_SAFETY** |
| Original aft B-17 (190t) | min swept **31.263143b**, 0 breaches | **79.552707b** | **68 swept intrusion ticks**, fails | **FAILED_SOURCE_SAFETY** |
| Original forward B-17 (190t) | min swept **23.880247b**, 0 breaches | **130.936936b** | 0 intrusion ticks | **PASS_SOURCE_SAFETY** |
| Synthetic LOS fixture (90t) | min swept **38.977284b**, 0 breaches | n/a | n/a | **FAILED_SOURCE_SAFETY** due to terrain contact |
| All 24 (240t) | min swept **1.237758b**, **5 <6b swept ticks**, fails | **47.280238b** | **68 swept intrusion ticks**, fails | **FAILED_SOURCE_SAFETY** |

The LOS experiment recorded **118 terrain-occluded observations and zero
acquired hostile-contact ticks**. The remaining cases include positive
visual acquisitions, finite-FOV denials and remembered tracks that expire
without receiving hidden enemy truth. The failure counts are first-class
results; the laboratory does not treat a completed computation as a
successful combat/escort mission.

The full **5-case Twin advanced 38 aircraft instances, 8,100 genuine
per-airframe SOURCE physics ticks** in synchronized 20Hz steps. The
combined pipeline also produced the original **12,288 single-plane
trials / 2,211,840 ticks**. One observed combined run, including Java17
compilation, both simulations, CSV/JSON and two HTML reports, took
**5.061 seconds**; this is only a local benchmark.

### Twin outputs and verification

The Twin writes **twin_summary.json** (source provenance, 6b/95b gates,
per-case PASS/FAILED and reason codes), **twin_units.csv** (24 individual
aircraft types, role, engine reaction, AI, sensing and speed), **twin_pairs.csv**
(all pairwise minimum sampled/swept centre distances and <6b ticks),
**twin_assets.csv** (actual B-17/attacker 95b proximity with intrusion
timing and escort assignments), **twin_time_slices.csv** (XYZ/attitude/speed,
memory age, observed target and policy command), **twin_sensor_events.csv**
(each observer's visibility transitions and memory expiration), and a
self-contained interactive **flight-twin.html** (top/side/3D-style plots,
all simultaneous trajectories, moving 95b perimeter, per-plane AI
decisions, and exact failed gates).

~~~powershell
py -3 -m unittest discover -s .\tools -p "test_flight*.py" -v
~~~

**Java17-backed integration coverage** includes five original batch
cases, seven Twin cases, and the new real-Forge forensic comparator.
The initial Twin tests require exact original 2v2
and aft/forward bomber coordinates, unchanged 6/95 gates, physically
moving 24 unique source models and engine reactions, **17 standalone**
observation assertions, real LOS occlusion, stale target memory,
no weapon candidates and honest failed operational gates. They independently
run a full reversed-roster Twin with the **same seed and compare all seven
JSON/CSV/HTML output files byte-for-byte**; another seed changes the
24-aircraft outcome. Node syntax checking of the offline HTML is also
performed when Node is already present; Node is not needed to run the lab.

**Remaining uncertainty:** the Twin does not reproduce the real Forge
airframe's voxel movement/hitboxes, true block raycast, network timing,
weather configuration, live chunk lifecycle or verified ammunition/weapon
behavior. Its successful source-only 2v2 or forward B-17 case cannot be
substituted for the original GameTest acceptance criteria. Failed Forge
tests must not be reclassified based on this offline Twin.

## Original REAL Forge B-17 vs autonomous Twin: 340-tick forensic experiment

The prior 190-tick four-plane B-17 laboratory task is a separate training
exercise. The **original operational REAL Forge GameTest** flew one
B-17, **two P-47N escorts**, and **two A6M raiders**, for **340 ticks**.
The new **forge_original_b17_340** source scenario restores this exact
five-airframe starting geometry, and the optional forensic tool compares
it against saved authentic REAL runtime receipts.

From the physics-ai directory, after verifying that the original ignored
real receipt directory is available, run this completely optional command:

~~~powershell
py -3 .\tools\forensic_b17_compare.py --real-dir .\runtime-probe\run-gametest\original-root-receipts-20261011-preserved --output "$env:TEMP\ww-b17-forensic" --java-home "C:\Program Files\Java\jdk-17" --seed 20261011
Start-Process (Join-Path $env:TEMP "ww-b17-forensic\forensic_b17.html")
~~~

**This does not run in the default SOURCE-only batch/Twin workflow.**
Hosted/CI research can run without owner-private real Forge receipts.
The optional command refuses missing, incomplete, altered or
synthetically labelled REAL evidence. In particular, the ignored
**pre-margin2-root** directory has only 235 pilot records per plane and
is invalid for the 340-tick comparison. The original preserved root
contains **five × 341 control rows** (ticks 0..340) and independent
GameTest geometry sampled for the same five planes, including an
extra geometry snapshot after the final controller update.

Original world coordinate B-17 at initial tick 0 is (55.5,165,0.5).
For the comparison we subtract X=55.5 and Z=0.5 from all REAL
positions while retaining their Y coordinate. This coordinate
translation never mutates the REAL CSV. The source scenario starts:

| Aircraft | Initial relative XYZ | Yaw | Starting Z velocity | Mission |
|---|---|---:|---:|---|
| B-17 | (0,165,0) | 0° | +0.65 b/tick | PATROL |
| Escort left / P-47N | (-48,172,18) | 0° | +0.80 | ESCORT |
| Escort right / P-47N | (48,172,18) | 0° | +0.80 | ESCORT |
| Raider 1 / A6M | (-40,168,148) | 180° | -0.78 | INTERCEPT |
| Raider 2 / A6M | (40,168,153) | 180° | -0.78 | INTERCEPT |

The source world is **synthetic flat ground**, with calm-weather
speed-dependent pinned IA1.3.3 wind; real Minecraft ground, chunk
liveness, bounding box LOS and entity collision behavior remain
unmodeled. Source sensor distance now matches LiveAirSensor
**240-block maximum range** and **150° FULL field of view** (75° half
angle). The synthetic 24-sample height ray, 1.5b margin and 6-tick
remembered-track lifetime are separate experimental assumptions.

**Critical causal timing correction:** The actual runtime computes
TacticalAirAI commands at **ServerTick.END**, after the aircraft
entity's physical movement. The Twin now first advances ALL aircraft
with their previously queued raw inputs (initial physical tick 1:
neutral X/Z stick, engine target 1), observes that completed snapshot
and computes a new policy command at tick 1 END for physical tick 2.
Both the queued command and previously applied input, with exact
origin tick, are logged in twin_time_slices.csv. Java17 tests prove
that no newly issued command can retroactively affect its own
completed physics tick. All five initial physics positions at t1
agreed with REAL Forge within 0.00000004 blocks, but that one-step
agreement cannot certify later closed-loop parity.

### Recorded REAL versus predicted SOURCE outcomes (seed 20261011)

| Measurement | REAL Forge, independently verified | Autonomous SOURCE Twin |
|---|---:|---:|
| First crossing into or touching B-17 95b zone | **tick 88** | **tick 102** |
| Minimum moving B-17 to raider distance | **66.029299b**, tick 140 | **30.355539b** |
| Strict inside 95b, 341 positions | **101 ticks** | **204 ticks** |
| Within-tick centre interpolation intrusion (SOURCE only) | NOT MEASURED | **206 ticks** |
| Minimum sampled pair separation | **10.807900b** | **27.107954b** |
| Under 6b sampled aircraft-pair ticks | 0 | 0 |
| B-17's own opponent sighting ticks | **0** | **124** |
| B-17 protection gate | **FAILED** | **FAILED_SOURCE_SAFETY** |

The REAL GameTest's original strict gate is **distance less than 95b**,
and it failed for 101 ticks. The source asset gate uses
**distance less than or equal to 95b**; both event rules are documented
and separately counted. Neither the source result nor its earlier
entry/longer exposure can override the REAL GameTest acceptance.
The real B-17 observer seeing zero hostiles while SOURCE sees them
for 124 ticks is a concrete controller input difference. Because the
closed-loop pilots are **not teacher-forced to use the same commands**,
their position deviations combine observation, policy, world and
physics effects; this report cannot isolate physics parity by itself.

### Generated forensic files, with strict provenance

| File | Contents |
|---|---|
| forensic_b17_summary.json | Namespaced REAL and SOURCE provenance, input SHA-256, original acceptance sidecar, gates, all five motion/control/sighting metrics |
| forensic_b17_ticks.csv | All **341** synchronized positions, 95b and 6b diagnostics, nearest opponent and human-readable tick interpretation |
| forensic_b17_controls.csv | All **1,705** aircraft-by-tick lines: aligned position/velocity, yaw/pitch, real and Twin signed controls, sightings, phases, maneuvers and combined divergence explanation |
| forensic_b17_events.csv | Source-labeled sighting/maneuver/phase/safety/boundary transitions (event count changes with sensor/policy) |
| forensic_b17_units.csv | Per-aircraft path, RMSE, final position error, control differences and sighting totals |
| forensic_b17_pairs.csv | All ten physical pair distance minima and under-6b counts, REAL separate from SOURCE |
| forensic_b17_findings.md | Plain-English result narrative with the first real 95b entry and five-plane explanation |
| forensic_b17.html | Fully self-contained file:// interactive time slider, twin trajectory overlays, 95b threshold chart and clickable event explanations |

The comparator independently invokes the existing
verify_live_aircombat_receipts.py proof verifier, checks all five
REAL pilot identity/source/continuous game clocks, independently
validates the GameTest operational-b17-final.json result, and
crosschecks the separate 341-sample REAL geometry against controller
tick t=1..340. It hashes each real input under
**real_evidence** while listing all generated source hashes separately
under **source_twin_evidence**. No original REAL CSV or original JAR
is edited, repackaged, committed or promoted from synthetic physics.
UUID-based real sightings are never guessed into named aircraft IDs.

To re-analyze full-resolution already-generated SOURCE data, use
the same command with **--reuse-twin**. The source-only 340tick case
also works without local REAL receipts:

~~~powershell
py -3 .\tools\flight_lab_run.py --mode twin --twin-scenario forge_original_b17_340 --trace-stride 1 --output "$env:TEMP\ww-b17-source-only"
~~~

### Forensic regression tests

~~~powershell
py -3 -m unittest discover -s .\tools -p "test_flight_twin_forensic.py" -v
py -3 -m unittest discover -s .\tools -p "test_flight*.py" -v
~~~

The forensic suite checks original REAL 341-row clock synchronization,
unchanged 6/95b gates, exact Forge sensor constants, independent
geometry matching and 5-plane initial conditions, readable event
timelines, deterministic byte-equal source/forensic outputs under
reversed roster, changed-source-label rejection, broken REAL source
marker rejection, partial old 235-row receipt rejection, and real
geometry tamper rejection. Missing original private receipts are
**explicitly skipped in general CI**; that is not a pass of the REAL
acceptance gate. No report implies verified weapon behavior, actual
Forge physics parity, kill counts, or B-17 mission victory.

### Newer owner REAL policy receipts: explicit stale-sidecar quarantine

The two additional ignored REAL directories **pre-cpa-original-root**
and **ww-physics-traces** each have five 341-row GameTest flight
control traces and independent geometry. Both retained an **obsolete
operational-b17-final.json from the earlier 101-tick / 66.029299b
GameTest**. Normal forensic comparison rejects this disagreement
between the saved sidecar and the newly recomputed REAL telemetry.

An explicitly requested forensic audit can accept those original
REAL flight CSV files **only after independent full verification**,
while marking their stale saved sidecars
**STALE_SIDE_CAR_QUARANTINED_NOT_ACCEPTED**. The preserved stale JSON
is never promoted into an accepted REAL result. Original file hashes
and the actual independently recomputed results are recorded
separately.

The newest ww-physics-traces archive additionally contains an
*extra* post-controller geometry sample 341 where **raider-1 is still
at entityTick 340** while the others advanced to 341. Only the
consistent control/geometry comparisons through tick 340 are used.
The extra non-synchronized sample is named under
**excluded_post_control_stale_units** and is excluded from any
claims of complete five-plane physics parity.

~~~powershell
py -3 .\tools\forensic_b17_compare.py --real-dir .\runtime-probe\run-gametest\ww-physics-traces --quarantine-stale-sidecar --output "$env:TEMP\ww-b17-latest-real-vs-source" --java-home "C:\Program Files\Java\jdk-17"
~~~

For direct BEFORE versus AFTER **two verified REAL GameTests**,
an additional standard-library comparator provides the independent
tick-by-tick account of what changed. It contains no simulated
aircraft evidence:

~~~powershell
py -3 .\tools\forensic_b17_policy_delta.py --before-real-dir .\runtime-probe\run-gametest\pre-cpa-original-root --after-real-dir .\runtime-probe\run-gametest\ww-physics-traces --quarantine-stale-sidecars --output "$env:TEMP\ww-b17-policy-real-before-after"
~~~

The latest owner-local run observed during this audit had **49
strictly-inside-95b ticks, 82.570680b closest approach** before
the policy change, versus **81 ticks, 65.020052b closest approach**
after it: **32 more exposure ticks**, and a threat **17.550628b
closer**. Both original REAL results are FAILED. As owner REAL
receipts can be regenerated, these numbers apply to that particular
read-only dataset and are identified by per-file SHA-256. The
**forensic_b17_real_policy_delta.json** records separate REAL
before/after provenance; its two CSV outputs provide 341 frame
records and 1,705 per-plane records, each with sighting,
phase, signed control, maneuver, distance and human-readable
explanation. The Markdown report describes the earliest changes
without claiming which code change caused a particular outcome.

Another now-exposed SOURCE failure involves **P-47N and Ki-84**
in the independent 24-unique-aircraft, 240tick stress case:
**five swept ticks below 6b**, with closest swept centre separation
**1.237758b at tick 192**. Four tick-end snapshots also violated
6b. Both pilots were already reporting
**COLLISION_AVOID / WORLD_SAFETY_MOVING_COLLISION_RISK** around
ticks 186–194, yet the queued inputs and actual motion still
carried them into proximity. Source operational gates remain FAILED;
no initial position, safety radius or speed was artificially
adjusted to manufacture a pass.

Validation commands for optional owner-only original-real
and two-REAL-comparison proof:

~~~powershell
py -3 -m unittest discover -s .\tools -p "test_flight_twin_forensic.py" -v
py -3 -m unittest discover -s .\tools -p "test_flight_twin_policy_delta.py" -v
~~~

These owner REAL tests **skip when ignored input receipts are
absent**. Hosted CI can still run source-only experiments with no
owner CSV/JAR access. Real receipts remain read-only and excluded
from commits. A 95b boundary claim for either run must be derived
from actual, validated REAL five-aircraft positions, never a Twin
prediction or an archived stale sidecar.
