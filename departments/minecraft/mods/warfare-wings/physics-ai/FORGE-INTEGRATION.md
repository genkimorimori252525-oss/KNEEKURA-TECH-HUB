# Warfare Wings Tactical AI → Real Forge 1.20.1 Aircraft Bridge

Status: **source compiled; pinned real aircraft GameTest execution NOT_RUN until both exact runtime binaries are locally staged**. This is an experimental Forge integration with no weapon firing and no claim of source/microkernel to actual Minecraft parity.

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

Each GameTest asserts the actor remains a mounted IA aircraft through all ticks, produces nonzero steering, **moves at least 8 blocks**, turns at least 2 degrees overall, observes the first yaw response **after** first nonzero lateral command, and writes a CSV in `run-gametest/ww-physics-traces/<scenario>-forge-controls.csv`. The trace separates real position/velocity/yaw and IA smoother state from AI commands, active maneuver and safety reason. A passing test proves only those properties of that exact staged runtime.

**GameTest isolation contract:** the five tactical scenarios each have their own single-test `@GameTest(batch="ww_tactical_<aircraft>")` batch. Their aircraft carry the `ww_tactical_game_test` tag. During each tick, if **any other** Warfare Wings aircraft enters the probe's 80-block nearby-aircraft sensor query, the isolated run fails with `cross-scenario aircraft within tactical sensor range`; it is never quietly interpreted as a new collision-avoidance maneuver. This catches accidental runner overlap even when tests are unexpectedly placed near each other. The existing 400-tick throttle trace stays in its separate original batch. After a successful restart with the same scenario name, the runtime pilot replaces its previous result and captures a fresh CSV; completed results are bounded to the latest 32 entries.

The owner-controlled Windows runtime workflow separately fails closed on each of the five tactical CSV receipts, checking 181 samples (initial tick 0 plus 180 executed ticks), the schema and aircraft identity, real nonzero lateral commands, yaw travel and displacement before the original A6M calibration. Uploading files alone is not evidence of successful flight validation.

If loaded manually with the pinned JARs, an operator (permission level 2) may issue `/wwai patrol` next to **exactly one empty, already-airborne** Warfare Wings aircraft within 20 blocks. It attaches a synthetic IA pilot, uses the same safety/guidance/recording loop for up to 900 ticks, and writes a uniquely named trace. `/wwai stop` detaches only that operator's synthetic pilot and leaves the aircraft intact. The command provides no combat, projectile, release, PvP or persistent world AI. It refuses ambiguous aircraft selection or a plane already occupied by a player.

The environment sensor uses actual world heightmap samples and other registered Warfare Wings aircraft as moving collision obstacles; **historical faction is not inferred to mean friend or enemy**. Only explicitly supplied enemy entities count as hostile; an optional doctrine order is an explicit scenario input. Collision envelopes and the temporary altitude margin remain gameplay hypotheses requiring live measurements.

## Known limits

The mod binary may differ from the checked public-source tag or contain transformed class names. Reflection is source grounded and guarded but **not yet proven against the exact loaded binary**. The source-only lab's 20Hz recurrence test cannot stand in for running this Forge GameTest. The driver has one-tick control lag, ArmorStand piloting, no ownership of real player controls, no weapon firing, no multiplayer player-input protocol, and no proof that the command will be acceptable in every game configuration. Runtime traces must be captured before promoting any behavioral or performance result to `MEASURED`.

## Live multi-aircraft autonomy (new, not yet exact-JAR measured)

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
