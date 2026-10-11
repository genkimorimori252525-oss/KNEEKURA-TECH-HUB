# Warfare Wings combat and strike simulation v1

## Evidence and purpose

This experiment runs autonomous source-microkernel aircraft at **20 physical ticks per simulated second** using the exact derived 24-type Atlas and existing `TacticalAirAI`, `HistoricalDoctrineOrders`, `FlightControlLoop`, `FlightSafetyPlanner` and `SquadronCommand` policies.

**Evidence level: `SOURCE_MICROKERNEL+SCRIPTED_SCENARIO`. Exact Minecraft parity: `NOT_ESTABLISHED` by these source tests.** It exercises source-side aircraft and controller behavior without Forge, private game binaries, network, actual projectile entities, ballistic weapon layouts or payload effects. Do not infer damage, successful ordnance release, fighter victories, historically measured turn envelopes or mission completion from an attack window.

Two independent, deterministic heads are supplied:

- `CombatSimulation.run(atlasCsv, scenario)` delegates aircraft movement and individual sensor/track/target behavior to `SquadronCommand.advance` on immutable, synchronous snapshots. It aggregates the resulting flight and encounter telemetry. Combat participants and bomber assets share the same actual source-world positions.
- `StrikeSimulation.run(atlasCsv, plan)` loads the relevant `AircraftAtlasMain.load/evaluate` model, calls `FlightControlLoop.step` and `Ia133Microkernel.tick` exactly once per physical tick, and advances a scripted mission-phase controller. It supports level bombing, torpedo runs and dive pull-out, plus strafing as a source-only mission type.

**Integrated source mission phase path is now implemented:** `CombatSimulation.runWithStrikePlans(...)` uses the immutable `StrikeSimulation.SquadronPhase` controller to supply validated `SquadronCommand.MissionOrder` directives to an aircraft on the **same physical 20 Hz snapshot** as its escorts (and any adversaries). The mission may move from its original aircraft-role attack type to navigation-only `PATROL` for pull-out, egress and return, with no instantaneous position, orientation, speed or health modification. Plan binding requires the exact same starting aircraft type/mission, position/velocity/heading, objective/home, world object and sufficient tick horizon. The legacy `StrikeSimulation.run` remains a separately benchmarked single-aircraft scenario.

## Exact-WW engine-response SOURCE V3 operational contrast

The existing `CombatSimulation.run` remains the legacy 20tick-reaction
source benchmark. New `CombatSimulation.runWithExactReaction` runs the same
20Hz 24-type simulator with `SquadronCommand.loadWithExactReaction` and
the real original JAR's per-airframe `getEngineReactionSpeed()` values.
The **95-block** bomber-defence corridor, **6-block** aircraft body-safety
limit, starting geometries and observation constraints are UNCHANGED.

| Scenario | Legacy source engine20 | Original WW bytecode engine response | Result |
|---|---:|---:|---|
| 2v2 opposing A6M/Bf109 closest | 47.557 blocks | 36.923 blocks | Both satisfy strict all-six-pair ≥6-block clearance |
| B-17 original aft guard, enemy within 95 blocks | Legacy engine20: **47 / 190 ticks** | **54 / 190 ticks** (7dcda5e baseline 55; previous 59, original V3: 92) | **FAILED** protection; actual breach remains |
| B-17 original aft guard, closest threat | Legacy: **69.378 blocks** | **81.923 blocks** (7dcda5e baseline 81.231, original V3: 40.913) | Still **FAILED** |
| B-17 original forward-prepared guard, intrusion | Current legacy: **0 / 190 ticks** | **0 / 190 ticks** (V3 original: 30) | **PASS only for this exact prepared-start 95-block source geometry** |
| B-17 original forward-prepared guard, closest threat | Legacy: **122.165 blocks** | **112.379 blocks** (7dcda5e baseline 98.570, original V3: 77.643) | **PASS**; margin **17.379 blocks** above unchanged 95b |

The V3 source engine-response model is a nontrivial operational constraint:
the exact per-airframe source reaction delays effective thrust during the first
part of the encounter. In the frozen old-code timing diagnosis, fighters
initially at 1.00 blocks/tick fell to roughly **0.42 blocks/tick by tick 20**,
then slowly accelerated. With the original aft deployment, fighter assignment
begins at tick **8** yet the attacker enters the 95-block protection corridor
near tick **100**; assignments alone cannot produce physical interception.
No model silently changes starting speed, entity health, aircraft size, roster,
the 190-tick window, the 95-block corridor, or the 6-block body safety gate.

Current improvements are a role-appropriate higher escort throttle and a
protectee-relative predictive screen with independent lateral guard stations.
New decisions use the fighter's personally observed hostile position/velocity
and the actual allied asset's observed velocity; the source controller
extrapolates both future trajectories without reading global unseen hostile
state. The lead horizon derives from range, measured relative-closing rate,
and estimated achievable fighter travel time, **not** the 95-block test gate.
The fighter normally aims **20 blocks below** this projected moving screen,
but while its *measured* engine power is below **0.12** the source policy
temporarily commands **70 blocks below** it to obtain a descending early
intercept during delayed engine response. These are guidance requests, not
instantaneous altitude/speed modifications; terrain and aircraft separation
safety can overrule them. When its individually sensor-known hostile is
within **48 blocks and closing by more than 0.10 blocks/tick relative to
the fighter**, the escort requests a bounded **155-block tangential escape**
from the hostile's observed position, including a **0.35 outward component**
relative to the actual protected aircraft. This is intended to avoid dragging
the attacker straight back through its bomber. An unseen, distant, or
receding hostile cannot trigger that escape. These action distances are
uncalibrated navigation parameters; they do **not** replace or redefine
the original 95-block protection, 30-block Forge escort-hostile, or 6-block
physical separation acceptance gates.

Across the two unmodified 190-tick source geometries, this policy changes
exact V3 aft penetration duration from the earlier **55 to 54 ticks** and
minimum separation from **81.231 to 81.923 blocks**: **STILL FAILED**.
In forward-prepared cover, intrusion stays **zero** and the minimum hostile
separation grows from **98.570 to 112.379 blocks**: **PASS in source V3**.
No Forge behavior can be inferred from these source-only observations.
In source V3, an escort assigned at tick 8 still initially flies behind
its protectee, and no amount of assigning targets itself stops a live fighter:
the same aft-deployed starting geometry remains a stringent known failure.
The updated bomber evasive maneuver uses the personally observed hostile's
own course to choose a stable lateral escape lane and a physically controlled
**65-block upward steering waypoint request**. The actual aircraft climbs
only through filtered pilot inputs, source physics, gravity and speed, never
instantaneous position changes. The bomber's observed-inbound defense supports
both LEVEL_BOMB and the real Forge planner's PATROL mission. No unseen target
can trigger it; inert hostiles do not satisfy its approaching-contact rule,
and low-fuel withdrawal remains higher priority.
Other fighter attack phases now solve the constant-velocity interception
quadratic for a **personally observed** hostile using the fighter's own state,
the track's last-known position and velocity, and the estimated current airspeed.
Only positive future interception roots are allowed; unreachable tracks fall
back to a finite pursuit prediction. Prediction stays capped at **30 ticks**;
this is an advisory steering waypoint, not knowledge of an enemy's real future
course or a weapon firing command. A crossing-contact test distinguishes the
quadratic prediction from the previous range/summed-speeds heuristic.
Under exact-WW source response the unchanged forward-prepared V3 flight
reaches 0/190 intrusion ticks, but the unchanged aft flight STILL FAILS with
54/190 ticks. There is no fake kill, fired weapon, or proven real-Forge
combat parity; the real GameTest must establish that separately.
The aft-deployed aircraft still records `ESCORT_PROTECTION_BREACHED`
under those same 95-block operational gates.

## Combat diagnostics

`CombatSimulation.Report` records:

| Signal | Operational interpretation |
|---|---|
| `PairMetric.closestApproachBlocks`, `closestTick` | Closest 3D encounter of a pair across all physically integrated ticks |
| `PairMetric.dangerouslyCloseTicks` | Ticks with center-to-center distance below experimental **6 blocks**; this is a **hazard flag**, not a confirmed collision |
| `UnitMetric.pathBlocks`, `finalSpeedBps` | Physical movement and end-of-window speed, measured in the microkernel |
| `UnitMetric.minTerrainClearance`, `groundedTicks` | Terrain approach and touchdown exposure; collision handling uses the source height-field approximation |
| `UnitMetric.minObjectiveDistance`, `objectiveWindowTicks` | Distance to assigned objective; an objective window is geometric and does not imply a payload or successful mission |
| `UnitMetric.hostileContactTicks`, `assignedTicks` | Sensor-known contact and assigned target durations, per pilot |
| `UnitMetric.firingCandidateTicks` | Advisory aiming condition only; no projectile fired |
| `UnitMetric.withdrawalTicks`, `terrainOverrides`, `collisionOverrides` | Actual requested return-home and world-safety maneuvers |
| `UnitMetric.defensiveAbortTicks` | Physical ticks in which a bomber/other aircraft aborts mission navigation to avoid a real observed threat |
| `AssetMetric.threatWithinCorridorTicks`, `corridorBreached` | Whether a hostile approached the protected asset within an explicitly supplied protection radius |
| `AssetMetric.escortThreatAssignedTicks` | Aggregate escort response assignments (counts can exceed scenario ticks because multiple escorts independently respond) |
| `AssetMetric.firstEscortAssignmentTick`, `firstThreatEntryTick`, `lastThreatEntryTick` | Physical-tick sequencing of threat acquisition and perimeter penetration |
| `AssetMetric.nearestEscortHostileBlocks`, `escortInterpositionTicks` | Experimental geometry-only cover observation; interposition requires an escort between attacker and asset, within 18 blocks of their connecting segment |

The `escortAssets` map must identify actual same-team `ESCORT` pilots pointing at the specified escorted asset. All aircraft are physically integrated in the same `SquadronCommand` step. All pair IDs use structured `PairKey` records, so arbitrary aircraft instance names cannot alias through a text delimiter.

`TacticalAirAI.Frame` retains its original source/API constructor and adds
an optional, explicitly observed `observedFormationVelocity` vector for
updating an escort's future protectee reference. The default is
`Vec3.ZERO` for integrations that have no allied velocity. It must be
finite; the tactical policy does not fabricate an unobserved hostile track.
V3 regression verifies that advancing allied protectee data really moves the
screen waypoint, while unchanged FOV/TTL constraints are preserved.

The collision guard now uses both allied aircraft and **currently observed** hostile aircraft from each individual pilot's own sensor tracks. Stale/expired enemy information cannot masquerade as a new sighting or control an imminent-aircraft safety decision. For observed enemies, the source-only predictive check looks ahead up to **55 ticks**, with opposing pilots attempting right-side separation; these engineering margins are not measured Minecraft collision dimensions or historical reaction constants. Low-fuel withdrawal retains only the closest imminent aircraft safety override and can otherwise continue its return-home order.

A fixed horizon returns `timedOut=true` meaning **measurement budget exhausted**; it does not represent combat defeat. `corridorBreached=true` identifies a concrete failure of the stipulated proximity defense criterion even if escorts were issuing tactical orders.

An arriving threat to a **bomber** now produces an early navigation abort only when that bomber personally has a sensor contact whose *own observed velocity* is approaching and whose relative trajectory is closing. A merely static hostile target in front of a moving bomber does not cause a false incoming-threat alarm. The current avoidance command uses actual IA-filtered steering and a lateral direction away from the observed threat; it cannot teleport the bomber or guarantee recovery of its bombing route. The `Memory` maneuver supplies bounded continuation against a temporarily turning threat while preserving fuel withdrawal, terrain priority and other original role checks. This emergency maneuver can protect the asset geometrically while significantly delaying the strike objective.

The explicit `failedOperationalGates` codes report `BODY_SEPARATION_LT6:unitA:unitB`, `ESCORT_PROTECTION_BREACHED:asset:intrusion_ticks=N`, and `GROUND_CONTACT:unit`. A scenario's `passesSafetyGates()` tests these geometric conditions only; it is never a simulated combat victory. The V3 2v2 **PASSES** all six pair separation gates; the unchanged aft-deployed B-17 flight remains **FAILED**, while the forward-prepared V3 scenario geometrically **PASSES** the identical 95-block gate.

## Strike phases and geometry

State machine:

```text
APPROACH -> WINDOW -> EGRESS -> RETURN_HOME -> COMPLETE
    |                    ^
    +----(dive)----> PULL_OUT
    |                  |
    +----(miss)--------+
Any unfinished phase after budget -> TIMEOUT
```

The recorded `Phase` durations and event timestamps come from actual integrated positions and velocity. `WINDOW` is an observed geometric approach with plausible altitude and forward alignment; a missed or aborted approach may produce **zero** windows. For level bombing the assumed engineering altitude band is **45–260 blocks above terrain**. For torpedo practice the assumed sea-surface clearance band is **12–35 blocks**. These are **LAB configuration values, not historical release conditions**. The sea surface is a configured horizontal reference; the model does not simulate water hydrodynamics, torpedo stabilization, weapon cooldowns, sighting equipment or exact Minecraft projectile behavior.

The target-plane crossing timestamp is the tick where horizontal signed progress first passes the target's normal plane. `lateralAtCrossing` is the cross-track distance at that tick. This defines a **waypoint crossing**, not a bomb/torpedo collision. `closestHorizontalToStrike`, `closest3dToStrike`, min/max sea clearance and ground-contact counts remain independently available.

Dive pull-out is commanded when forward distance to the dive objective reaches the configured near-target threshold or height crosses the **90-block LAB trigger**. A recovery is recorded only after **actual altitude gain of at least 18 blocks from the lowest point during pull-out**, upward vertical speed, and regained 90-block ground clearance. A `PULL_OUT` directive without these observations is *not* a passed recovery. While aborting, no attack window is credited.

After any geometric target-plane crossing the `WINDOW` phase expires after a fixed 12 tick observation dwell (or earlier on lateral departure). `EGRESS` then commands an independent outbound waypoint before `RETURN_HOME`. `COMPLETE` requires the aircraft physically entering its configured home radius. A long-running `RETURN_HOME` state without reaching home is reported as `TIMEOUT`.

## Reproducing the source-only checks (Windows PowerShell)

From the repository root, compile all existing and new source files with Java 17-compatible bytecode. The `-d` destination is outside the repository; no tracked sources or golden reports are modified.

```powershell
$src = 'departments/minecraft/mods/warfare-wings/physics-ai/src/main/java/org/kneekura/techhub/warfarewings/physics'
$tests = 'departments/minecraft/mods/warfare-wings/physics-ai/src/test/java/org/kneekura/techhub/warfarewings/physics'
$classes = Join-Path $env:TEMP 'ww-combat-lab-351754f'
$anchor = 'departments/minecraft/mods/warfare-wings/physics-ai/data/base-aircraft-anchor-v1.csv'
New-Item -ItemType Directory -Force $classes | Out-Null
$sources = @(Get-ChildItem -LiteralPath $src -Filter '*.java' | ForEach-Object { $_.FullName })
$sources += @(Get-ChildItem -LiteralPath $tests -Filter 'Combat*.java' | ForEach-Object { $_.FullName })
$sources += @(Get-ChildItem -LiteralPath $tests -Filter 'Strike*.java' | ForEach-Object { $_.FullName })
javac --release 17 -d $classes $sources
if ($LASTEXITCODE -ne 0) { throw 'Combat/Strike compilation failed' }
java -cp $classes org.kneekura.techhub.warfarewings.physics.CombatSimulationSelfTest $anchor
if ($LASTEXITCODE -ne 0) { throw 'Combat test failed' }
java -cp $classes org.kneekura.techhub.warfarewings.physics.StrikeSimulationSelfTest $anchor
if ($LASTEXITCODE -ne 0) { throw 'Strike test failed' }
```

## Measured source-only regressions (2026-10-11 working tree, unchanged scenarios)

These illustrative outputs are observed source simulation telemetry; assertions test physical relationships and safety limits instead of requiring one specific floating-point trace.

| Scenario | Measured source behavior | Regression interpretation |
|---|---|---|
| A6M vs P-47N, 150 ticks | Closest approach ~**39.80 blocks**, from 90-block initial separation | Both pilots detect and avoid the closing aircraft; no touchdown |
| 2v2, 160 ticks | Blue wing pair closest ~**69.76 blocks**; opposing A6M/Bf 109 closest ~**47.56 blocks**, **zero ticks under 6 blocks across all six aircraft pairs** | **PASS** for the selected 2v2 source-body-separation gate. Other starting geometries are not guaranteed |
| B-17 + F4U/P47N **aft-deployed cover** vs A6M, 190 ticks | Legacy reaction: **47 intrusion ticks**, min hostile distance **69.378 blocks**; original-WW reaction: **54 intrusion ticks**, min **81.923 blocks**. Starts x±65/z−20, first V3 assignment tick8, V3 intrusion tick105–158, final bomber objective distance **267.835 blocks** | **FAILED: ESCORT_PROTECTION_BREACHED** despite 366 escort-assignment pilot-ticks. 7dcda5e baseline was 55 ticks and 81.231b; source maneuver still cannot defend unchanged perimeter |
| B-17 + F4U/P47N **forward-prepared cover** vs same A6M, 190 ticks | Same x±27/z+115 original forward starts, 95-block gate, aircraft and source V3 reaction: **0 intrusion ticks**, closest hostile **112.379 blocks** (7dcda5e baseline 98.570b), first assignment tick1; B-17 final objective distance **226.082 blocks** | **PASS for this exact physically flown V3 prepared-start scenario**, margin 17.379b above unchanged 95b. Aft start remains FAILED. No simulated projectile/hit/kill |
| B-17 level-bomb geometric pass | Window around tick **176**, target plane around **248**; return phase entered; min terrain clearance ~**164.78 blocks** | Strike geometry achieved, **return incomplete at scenario timeout** |
| G4M sea run | Window around tick **144**, minimum sea clearance ~**21.94 blocks**; egress and return phase entered | Safe source-only sea-surface corridor, **no torpedo release** |
| Ju 87 dive recovery | Pull-out commanded around tick **92**, altitude recovery around tick **410**, min clearance ~**49.48 blocks** | Physical climb recovery observed, no ground contact; **early abort earns no weapon window** |
| Extended no-threat B-17/G4M return-to-base | B-17 actually enters unchanged 45-block home radius at **tick 1067**; G4M at **tick 717**, zero touchdown | **COMPLETE in the source flight model**, while shorter 680-tick runs properly report TIMEOUT. The recorded home tick equals actual `State.tick` |
| Integrated B-17 + two escort airplanes, 1600 ticks (no hostile) | ONE shared `SquadronCommand` physical snapshot; B-17 attack window tick176, target-plane crossing tick248, actual home arrival tick1068, no 6-block pair collisions | **Source mission phase integration PASS**. Escort and strike aircraft are physically co-simulated. No evidence that a hostile will be defeated or protected target will survive |
| Forced short horizon | No target crossing / window | Explicit `TIMEOUT`, not a fictional mission victory |

With V3 original engine-response the designated 2v2's minimum separation across all **six pairs** remains **36.923 blocks**, with zero under-six-block samples. The unchanged forward-prepared B-17 passes geometric defense only through **ordinary integrated source yaw/pitch/thrust**, including a lateral and upward escape waypoint for a genuinely observed inbound enemy. The B-17 still progresses toward the source mission objective (final 226.082b distance versus initial 280b). The source cannot claim a weapon hit or victory. The gate margin is modest and should be checked against Forge-calibrated drift, not assumed universally valid.

A further all-Atlas regression stages all **24** individually identified types at widely separated locations, explicitly retains A6M, P-47N, Spitfire, IL-2 and B-17, integrates actual control ticks and asserts movement, ground clearance and finite distances for all **276** unique aircraft pairs. Running the installed **JDK 17** with `javac --release 17` yielded **14/14 Java source SelfTest classes PASS**, including **261 passing Combat assertions** (249 before), **40 passing Strike assertions**, and checks for closing observed-only diversion, a receding contact, a missing contact, fuel override, bounded steering, and actual engine-power-dependent screen altitude. The unchanged `check-microkernel.mjs --java-home <JDK17_PATH>` also **PASSED its immutable generated report comparisons**, including the versioned v2 tactical golden, without overwriting any golden. Fighter interception tests cover constant-velocity crossing roots, an unreachable faster departing track, the 30-tick cap, coincident positions, and no enemy knowledge without a valid observed contact.

The low-fuel regression physically advances 50 ticks with **42 RETURN_HOME** decisions and **8 immediate collision-avoidance** decisions, without touchdown. An independent sensor test checks that an out-of-range fighter is not provided as a hostile collision obstacle, while a detected head-on target is; tests also verify correct risk selection in the presence of both allies and an observed enemy. Separate tests distinguish a stationary hostile from a truly inbound observed bomber threat and ensure a fuel emergency retains priority. The prepared escort test enforces **no penetration of the same 95-block corridor and no pair distance below six blocks**; the aft-deployed case keeps the same operational gate and must remain flagged FAILED.

## Limits and next integration gate

Source-only policies currently treat each aircraft as an approximate flight body on a height-field. Prediction avoids dangerous contact in the chosen 2v2 scenario, but cannot guarantee hard-body collision avoidance in every world. **The aft-deployed B-17 defense is still a blocking operational failure**, regardless of positive escort target assignments. The regression intentionally expects `ESCORT_PROTECTION_BREACHED` rather than silently passing it; successful code tests must not be confused with practical escort containment. Starting the guards ahead of the bomber produces physically measured protection in the alternate prepared-start geometry and demonstrates how inadequate prepositioning undermines interception. This does not authorize changing the original test's initial positions to hide its failure. Faction metadata never grants a combat win; team and mission come from scenario facts.

The new `runWithStrikePlans` shared-snapshot pathway now exchanges source-level mission phases, but remains a **source-only laboratory implementation**; it has not been promoted to Forge aircraft control, exact weapon behavior, or live mission success. Fuel/integrity fractions in squadron scenarios are supplied configuration values, not simulated consumption, damage or ammunition. The next evidence gate is the user's exact Warfare Wings / Immersive Aircraft binary on Forge 1.20.1, verifying real server-side controllability, per-tick power/steering phase, collision, and attack equipment semantics. No weapon-release control is added without direct primary-source/API evidence and real runtime checks.

The independent **original 340-tick, five-aircraft real Forge B-17 GameTest
still FAILED after this tactical change and the runtime's CPA contact-retention
update**. The final local original-entity run completed **19/20 Forge
GameTests PASS**, with this strict B-17 defense as the one **FAILED** case:
**81/340 hostile-intrusion ticks inside the unchanged 95-block perimeter**,
minimum bomber–hostile separation **65.020052 blocks**. All ten aircraft
pairs stayed outside the original **6-block** body-separation gate (minimum
observed pair was raider-1/raider-2 at **11.006527 blocks**). However the
closest escort–hostile pair, escort-left/raider-1, reached **11.719345
blocks**; escort-right/raider-2 reached **18.568841 blocks**. Both are below
30 blocks of separation, but **no original 30-block escort–hostile separation
requirement exists**: the actual GameTest's 30-block condition is each
aircraft's **initial-to-final net displacement**, not its proximity to an
enemy. In this latest real run, escort-left travelled **85.869852 blocks**
net and escort-right **39.183028 blocks** net, so both satisfy that separate
minimum net-displacement requirement. The B-17 remains FAILED solely because
the 95-block protection gate was breached. Source: the local
actual synchronized Minecraft entity-position receipt
`runtime-probe/run-gametest/ww-physics-traces/operational-b17-hysteresis-independent.json`.

For chronology, an older immutable Forge receipt measured **101/340** and
minimum **66.029 blocks**; a subsequent pre-edit Forge run on **HEAD
7dcda5e** improved that to **49/340** and minimum **82.570680 blocks**,
although escort-left's **net displacement** was only **29.594142 blocks**,
below the original 30-block movement gate. The latest
**81/340 / 65.020052** receipt is from the final tactical code plus the
prime's new CPA retention, so it **regressed versus 49/340**, and cannot be
credited as a real Forge improvement. The completed real 2v2 and 840-tick
return-to-base GameTests PASS, as do 35 original open-loop physics-fidelity
checks, but these independent achievements do not waive the B-17 failure.
An operational B-17 PASS still requires **zero** 95-block intrusion ticks,
at least **30 blocks** escort–hostile clearance and all **6-block** airframe
pair limits in the unchanged original scenario.

For a *diagnostic only*, a headless 340-tick five-plane setup with the same
aircraft roles, starts, headings, speeds, experimental 150-degree sensor
cone, exact bytecode engine reactions and pinned IA wind produced before:
**197/340 intrusion ticks**, minimum bomber-to-hostile **34.229 blocks**,
minimum escort-to-hostile **24.230 blocks**; after the tactical edit:
**192/340 intrusion ticks**, minimum bomber-to-hostile **34.798 blocks**,
minimum escort-to-hostile **26.044 blocks**, minimum any pair **22.323
blocks**. Both synthetic runs **FAIL** the 95-block condition, and the
new synthetic escort separation still falls below the real Forge's 30-block
criterion. Microkernel behavior differs materially from the real Minecraft
entity trajectory, so these numbers are *not* actual-Forge estimates or
substitutes for GameTest evidence. No source-only pass implies a weapon hit,
live aircraft victory, or physical 340-tick protection.
