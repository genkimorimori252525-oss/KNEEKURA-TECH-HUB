# Warfare Wings combat and strike simulation v1

## Evidence and purpose

This experiment runs autonomous source-microkernel aircraft at **20 physical ticks per simulated second** using the exact derived 24-type Atlas and existing `TacticalAirAI`, `HistoricalDoctrineOrders`, `FlightControlLoop`, `FlightSafetyPlanner` and `SquadronCommand` policies.

**Evidence level: `SOURCE_MICROKERNEL+SCRIPTED_SCENARIO`. Real Minecraft parity: `NOT_RUN`.** It exercises source-side aircraft and controller behavior without Forge, private game binaries, network, actual projectile entities, ballistic weapon layouts or payload effects. Do not infer damage, successful ordnance release, fighter victories, historically measured turn envelopes or mission completion from an attack window.

Two independent, deterministic heads are supplied:

- `CombatSimulation.run(atlasCsv, scenario)` delegates aircraft movement and individual sensor/track/target behavior to `SquadronCommand.advance` on immutable, synchronous snapshots. It aggregates the resulting flight and encounter telemetry. Combat participants and bomber assets share the same actual source-world positions.
- `StrikeSimulation.run(atlasCsv, plan)` loads the relevant `AircraftAtlasMain.load/evaluate` model, calls `FlightControlLoop.step` and `Ia133Microkernel.tick` exactly once per physical tick, and advances a scripted mission-phase controller. It supports level bombing, torpedo runs and dive pull-out, plus strafing as a source-only mission type.

These layers can be evaluated side-by-side to establish airframe-relative interception and strike trajectories, but a `StrikeSimulation` strike trajectory does **not** overwrite aircraft inside a `SquadronCommand` formation. Genuine simultaneous escorts reacting to a *dynamically rephased* strike aircraft will require a new shared multi-aircraft phase adapter; the existing `CombatSimulation` mixed flight already runs bombers/escorts/enemies simultaneously using current fixed-role tactical instructions.

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
| `AssetMetric.threatWithinCorridorTicks`, `corridorBreached` | Whether a hostile approached the protected asset within an explicitly supplied protection radius |
| `AssetMetric.escortThreatAssignedTicks` | Aggregate escort response assignments (counts can exceed scenario ticks because multiple escorts independently respond) |

The `escortAssets` map must identify actual same-team `ESCORT` pilots pointing at the specified escorted asset. All aircraft are physically integrated in the same `SquadronCommand` step. All pair IDs use structured `PairKey` records, so arbitrary aircraft instance names cannot alias through a text delimiter.

The collision guard now uses both allied aircraft and **currently observed** hostile aircraft from each individual pilot's own sensor tracks. Stale/expired enemy information cannot masquerade as a new sighting or control an imminent-aircraft safety decision. For observed enemies, the source-only predictive check looks ahead up to **55 ticks**, with opposing pilots attempting right-side separation; these engineering margins are not measured Minecraft collision dimensions or historical reaction constants. Low-fuel withdrawal retains only the closest imminent aircraft safety override and can otherwise continue its return-home order.

A fixed horizon returns `timedOut=true` meaning **measurement budget exhausted**; it does not represent combat defeat. `corridorBreached=true` identifies a concrete failure of the stipulated proximity defense criterion even if escorts were issuing tactical orders.

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

## Measured source-only scenario baselines (HEAD 351754f, before Forge parity)

These illustrative outputs are observed source simulation telemetry; assertions test physical relationships and safety limits instead of requiring one specific floating-point trace.

| Scenario | Measured source behavior | Regression interpretation |
|---|---|---|
| A6M vs P-47N, 150 ticks | Closest approach ~**39.80 blocks**, from 90-block initial separation | Both pilots detect and avoid the closing aircraft; no touchdown |
| 2v2, 160 ticks | Blue wing pair closest ~**69.76 blocks**; opposing A6M/Bf 109 closest ~**51.17 blocks**, **zero ticks under 6 blocks across all six aircraft pairs** | **PASS** for the selected 2v2 source-body-separation gate. Other starting geometries are not guaranteed |
| Mixed B-17 + 2 escorts vs A6M, 190 ticks | Escort assignments **355 pilot-ticks**; enemy inside 95-block corridor for **136 ticks**, minimum ~**14.46 blocks** | **FAILED: ESCORT_PROTECTION_BREACHED**. Closest intrusion improved from initial ~1 block, but exposure duration worsened from 102 ticks. Target assignment is insufficient to contain a hostile without an independently modeled engagement effect |
| B-17 level-bomb geometric pass | Window around tick **176**, target plane around **248**; return phase entered; min terrain clearance ~**164.78 blocks** | Strike geometry achieved, **return incomplete at scenario timeout** |
| G4M sea run | Window around tick **144**, minimum sea clearance ~**21.94 blocks**; egress and return phase entered | Safe source-only sea-surface corridor, **no torpedo release** |
| Ju 87 dive recovery | Pull-out commanded around tick **92**, altitude recovery around tick **410**, min clearance ~**49.48 blocks** | Physical climb recovery observed, no ground contact; **early abort earns no weapon window** |
| Forced short horizon | No target crossing / window | Explicit `TIMEOUT`, not a fictional mission victory |

A further all-Atlas regression stages all **24** types at widely separated locations, integrates actual control ticks and asserts movement, ground clearance and finite distances for all **276** unique aircraft pairs.

The low-fuel regression physically advances 50 ticks with **42 RETURN_HOME** decisions and **8 immediate collision-avoidance** decisions, without touchdown. An independent sensor test checks that an out-of-range fighter is not provided as a hostile collision obstacle, while a detected head-on target is; tests also verify correct risk selection in the presence of both allies and an observed enemy.

## Limits and next integration gate

Source-only policies currently treat each aircraft as an approximate flight body on a height-field. Prediction avoids dangerous contact in the chosen 2v2 scenario, but cannot guarantee hard-body collision avoidance in every world. **The B-17 defense is still a blocking operational failure**, regardless of positive escort target assignments. The regression intentionally expects `ESCORT_PROTECTION_BREACHED` rather than silently passing it; successful code tests must not be confused with practical escort containment. Faction metadata never grants a combat win; team and mission come from scenario facts.

The fixed-role `SquadronCommand` and dedicated `StrikeSimulation` share the microkernel but do not yet exchange live mission phases; that is a **future integration task**, separate from source evaluator correctness. Fuel/integrity fractions in squadron scenarios are supplied configuration values, not simulated consumption, damage or ammunition. The next evidence gate is the user's exact Warfare Wings / Immersive Aircraft binary on Forge 1.20.1, verifying real server-side controllability, per-tick power/steering phase, collision, and attack equipment semantics. No weapon-release control is added without direct primary-source/API evidence and real runtime checks.
