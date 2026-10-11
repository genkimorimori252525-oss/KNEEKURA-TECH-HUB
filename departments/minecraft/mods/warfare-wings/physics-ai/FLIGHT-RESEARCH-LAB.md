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
