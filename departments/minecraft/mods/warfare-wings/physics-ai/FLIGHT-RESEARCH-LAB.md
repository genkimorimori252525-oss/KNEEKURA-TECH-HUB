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

- **FlightTwinSensor.java** — finite detection range (190 blocks), 3D forward
  FOV (150-degree half-angle), 24-sample analytic terrain LOS, 1.5-block
  terrain clearance margin, 6-tick stale contact lifetime. Hidden contacts
  are extrapolated only from the last *actually seen* position/velocity.
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

### Measured SOURCE results (seed 20261011, Windows JDK17)

| Case | 6-block centre-pair gate | B-17 minimum attacker distance | 95-block protection gate | Source result |
|---|---:|---:|---|---|
| Original 2v2 (160t) | min swept **36.913694b**, 0 breaches | n/a | n/a | **PASS_SOURCE_SAFETY** |
| Original aft B-17 (190t) | min swept **32.084309b**, 0 breaches | **78.880041b** | **62 swept intrusion ticks**, fails | **FAILED_SOURCE_SAFETY** |
| Original forward B-17 (190t) | min swept **20.154772b**, 0 breaches | **95.687836b** | 0 intrusion ticks | **PASS_SOURCE_SAFETY** |
| Synthetic LOS fixture (90t) | min swept **39.658547b**, 0 breaches | n/a | n/a | **FAILED_SOURCE_SAFETY** due to 1 terrain contact |
| All 24 (240t) | min swept **16.268176b**, 0 breaches | **32.168267b** | **52 swept intrusion ticks**, fails | **FAILED_SOURCE_SAFETY** |

The LOS experiment recorded **167 terrain-occluded observations and zero
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

**11/11 Java17-backed Python integration tests PASS** (five original batch
cases plus six new Twin cases). The Twin tests require exact original 2v2
and aft/forward bomber coordinates, unchanged 6/95 gates, physically
moving 24 unique source models and engine reactions, 13 standalone
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
