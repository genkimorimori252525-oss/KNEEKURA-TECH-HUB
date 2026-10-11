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
| 2v2 opposing A6M/Bf109 closest | 51.167 blocks | 36.922 blocks | Both satisfy strict all-six-pair ≥6-block clearance |
| B-17 original aft guard, enemy within 95 blocks | 50 / 190 ticks | **92 / 190 ticks** | Both **FAILED** escort protection |
| B-17 original aft guard, closest threat | 64.623 blocks | 40.913 blocks | Both **FAILED** |
| B-17 forward-prepared guard, intrusion | 0 / 190 ticks | **30 / 190 ticks** | V2-only prepared success **DOES NOT GENERALIZE** |
| B-17 forward-prepared guard, closest threat | 120.518 blocks | 77.643 blocks | V3 **FAILED** |

This is a nontrivial SOURCE operational-regression finding: slower correct
engine spool-up reduces early acceleration and compromises interception.
No kill, successful air defence, fired projectile or real Minecraft
multiplayer battle is implied. Even the prepared forward fighter placement
**fails** the unchanged gate with original response timing; the earlier V2
success remains a separate reproducible source experiment, not a promise.

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

The collision guard now uses both allied aircraft and **currently observed** hostile aircraft from each individual pilot's own sensor tracks. Stale/expired enemy information cannot masquerade as a new sighting or control an imminent-aircraft safety decision. For observed enemies, the source-only predictive check looks ahead up to **55 ticks**, with opposing pilots attempting right-side separation; these engineering margins are not measured Minecraft collision dimensions or historical reaction constants. Low-fuel withdrawal retains only the closest imminent aircraft safety override and can otherwise continue its return-home order.

A fixed horizon returns `timedOut=true` meaning **measurement budget exhausted**; it does not represent combat defeat. `corridorBreached=true` identifies a concrete failure of the stipulated proximity defense criterion even if escorts were issuing tactical orders.

An arriving threat to a **bomber** now produces an early navigation abort only when that bomber personally has a sensor contact whose *own observed velocity* is approaching and whose relative trajectory is closing. A merely static hostile target in front of a moving bomber does not cause a false incoming-threat alarm. The current avoidance command uses actual IA-filtered steering and a lateral direction away from the observed threat; it cannot teleport the bomber or guarantee recovery of its bombing route. The `Memory` maneuver supplies bounded continuation against a temporarily turning threat while preserving fuel withdrawal, terrain priority and other original role checks. This emergency maneuver can protect the asset geometrically while significantly delaying the strike objective.

The explicit `failedOperationalGates` codes report `BODY_SEPARATION_LT6:unitA:unitB`, `ESCORT_PROTECTION_BREACHED:asset:intrusion_ticks=N`, and `GROUND_CONTACT:unit`. A scenario's `passesSafetyGates()` tests these geometric conditions only: it is never a simulated combat victory. The selected 2v2 geometry now **PASSES** all six pair separation gates; the mixed B-17 escort case still **FAILS** its protection gate despite aircraft issuing defensive orders.

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

## Measured source-only regressions (HEAD ca711a2, independent of real Forge parity)

These illustrative outputs are observed source simulation telemetry; assertions test physical relationships and safety limits instead of requiring one specific floating-point trace.

| Scenario | Measured source behavior | Regression interpretation |
|---|---|---|
| A6M vs P-47N, 150 ticks | Closest approach ~**39.80 blocks**, from 90-block initial separation | Both pilots detect and avoid the closing aircraft; no touchdown |
| 2v2, 160 ticks | Blue wing pair closest ~**69.76 blocks**; opposing A6M/Bf 109 closest ~**51.17 blocks**, **zero ticks under 6 blocks across all six aircraft pairs** | **PASS** for the selected 2v2 source-body-separation gate. Other starting geometries are not guaranteed |
| B-17 + F4U/P47N **aft-deployed cover** vs A6M, 190 ticks | Fighters start x±65/z−20 behind bomber. First assignment **tick 8**, enemy crosses unchanged 95-block corridor at **tick 54**, exits at **103**. **50 intrusion ticks**, minimum enemy-to-B-17 **64.62 blocks**. **141 bomber defensive-abort ticks** and final target distance **249.69 blocks** | **FAILED: ESCORT_PROTECTION_BREACHED** despite **355 pilot-assignment ticks**. Prior code: 136 intrusion ticks and closest14.46; emergency evasive diversion shortens exposure but severely delays objective progress. Escort separation and threat contact alone never count as a kill |
| B-17 + F4U/P47N **forward-prepared cover** vs same A6M, 190 ticks | Identical aircraft, 95-block safety gate, opponent, pilot inputs and source physics; only starting fighter stations changed to x±27/z+115. **0 intrusion ticks**, hostile closest **120.52 blocks**, all pairs ≥6 blocks, first assignment tick1; final bomber objective distance **182.06 blocks** | **SOURCE GEOMETRIC PROTECTION PASS for this prepared-start scenario only.** Forward deployment is a planning precondition; the rear-deployed mission remains explicitly FAILED. Neither result is a simulated weapon hit or broad historical escort effectiveness claim |
| B-17 level-bomb geometric pass | Window around tick **176**, target plane around **248**; return phase entered; min terrain clearance ~**164.78 blocks** | Strike geometry achieved, **return incomplete at scenario timeout** |
| G4M sea run | Window around tick **144**, minimum sea clearance ~**21.94 blocks**; egress and return phase entered | Safe source-only sea-surface corridor, **no torpedo release** |
| Ju 87 dive recovery | Pull-out commanded around tick **92**, altitude recovery around tick **410**, min clearance ~**49.48 blocks** | Physical climb recovery observed, no ground contact; **early abort earns no weapon window** |
| Extended no-threat B-17/G4M return-to-base | B-17 actually enters unchanged 45-block home radius at **tick 1067**; G4M at **tick 717**, zero touchdown | **COMPLETE in the source flight model**, while shorter 680-tick runs properly report TIMEOUT. The recorded home tick equals actual `State.tick` |
| Integrated B-17 + two escort airplanes, 1600 ticks (no hostile) | ONE shared `SquadronCommand` physical snapshot; B-17 attack window tick176, target-plane crossing tick248, actual home arrival tick1068, no 6-block pair collisions | **Source mission phase integration PASS**. Escort and strike aircraft are physically co-simulated. No evidence that a hostile will be defeated or protected target will survive |
| Forced short horizon | No target crossing / window | Explicit `TIMEOUT`, not a fictional mission victory |

For the two escort deployments, final `SOURCE_MICROKERNEL` speeds (only a speed/energy-retention **proxy**, not measured historical kinetic energy) were: aft F4U **31.973 b/s**, P-47N **35.999 b/s**, versus prepositioned F4U **26.879 b/s**, P-47N **37.599 b/s**. Closest F4U-to-P-47N distance remained **25.625** / **21.898 blocks** respectively. Both flights retain valid 6-block safety separation, so the contrast cannot be dismissed as one scenario exploiting unmodeled body overlap. The prepositioned screen's closest guard–hostile approach was about **13.676 blocks**; none of these source observations represents a weapon hit.

A further all-Atlas regression stages all **24** types at widely separated locations, integrates actual control ticks and asserts movement, ground clearance and finite distances for all **276** unique aircraft pairs.

The low-fuel regression physically advances 50 ticks with **42 RETURN_HOME** decisions and **8 immediate collision-avoidance** decisions, without touchdown. An independent sensor test checks that an out-of-range fighter is not provided as a hostile collision obstacle, while a detected head-on target is; tests also verify correct risk selection in the presence of both allies and an observed enemy. Separate tests distinguish a stationary hostile from a truly inbound observed bomber threat and ensure a fuel emergency retains priority. The prepared escort test enforces **no penetration of the same 95-block corridor and no pair distance below six blocks**; the aft-deployed case keeps the same operational gate and must remain flagged FAILED.

## Limits and next integration gate

Source-only policies currently treat each aircraft as an approximate flight body on a height-field. Prediction avoids dangerous contact in the chosen 2v2 scenario, but cannot guarantee hard-body collision avoidance in every world. **The aft-deployed B-17 defense is still a blocking operational failure**, regardless of positive escort target assignments. The regression intentionally expects `ESCORT_PROTECTION_BREACHED` rather than silently passing it; successful code tests must not be confused with practical escort containment. Starting the guards ahead of the bomber produces physically measured protection in the alternate prepared-start geometry and demonstrates how inadequate prepositioning undermines interception. This does not authorize changing the original test's initial positions to hide its failure. Faction metadata never grants a combat win; team and mission come from scenario facts.

The new `runWithStrikePlans` shared-snapshot pathway now exchanges source-level mission phases, but remains a **source-only laboratory implementation**; it has not been promoted to Forge aircraft control, exact weapon behavior, or live mission success. Fuel/integrity fractions in squadron scenarios are supplied configuration values, not simulated consumption, damage or ammunition. The next evidence gate is the user's exact Warfare Wings / Immersive Aircraft binary on Forge 1.20.1, verifying real server-side controllability, per-tick power/steering phase, collision, and attack equipment semantics. No weapon-release control is added without direct primary-source/API evidence and real runtime checks.
