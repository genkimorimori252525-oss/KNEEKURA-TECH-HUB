# Warfare Wings — 20 Hz source-to-flight control integration v1

Status: **pure-Java flight guidance and world-safety pipeline implemented**.
Exact Minecraft 1.20.1 / Forge / Warfare Wings runtime flight remains a
**separate acceptance gate**; do not label simulated traces MEASURED.

## Architecture and execution order

```text
Forge server aircraft Entity tick snapshot (the future live adapter)
    vehicle UUID/type -> 24-Atlas Model + role/provenance
    observed pos, velocity, yaw/pitch, current smoothed raw X/Z
    fuel, damage, objective, visible enemy, true nearby allied positions
    terrain sampling, moving obstacles, mission, leader, optional historical order
    |
    v
TacticalAirAI.Frame + per-aircraft Memory
    |
    +-- TacticalAirAI.decide() [mission/target/bearing/energy]
    +-- HistoricalDoctrineOrders.decide() [explicit unit + period + slot]
    |
    v
FlightControlLoop.step()
    +-- FlightSafetyPlanner.guard()
    |     4/8/15/25-tick sampled terrain and future obstacle closest-approach
    |     priorities: terrain, collision, low-speed reserve
    +-- FlightGuidance.plan()
          desired yaw/pitch from real 3D waypoint
          IA sign contract: positive raw X -> decreasing yaw;
                            negative raw Z -> nose-up pitch
          anticipates smoothed yaw/pitch momentum from IA input filter
          clamps X/Z [-1,1], engine [0,1]
    |
    v
Adapter applies raw inputs to exact IA 1.3.3 vehicle
    |
    v
IA's 20 Hz update: smoothed input, engine power, yaw/pitch and movement
    |
    v
Next server tick reads actual vehicle state; repeat
```

The Java API for a single aircraft is:

```java
FlightControlLoop.Output output = FlightControlLoop.step(
    new FlightControlLoop.Input(frame, previousMemory, optionalOrder,
        new FlightSafetyPlanner.Environment(terrainSampler, movingObstacles,
            aircraftCollisionRadius)));
Ia133Microkernel.Control raw = output.decision().controls();
previousMemory = output.decision().nextMemory();
```

The same schema deliberately works in deterministic source simulations and
can be consumed by an exact-runtime Forge adapter once its API is verified.
Calling the function alone does **not** move a Minecraft entity; the real IA
pilot update needs a runtime bridge that survives its passenger/controller
overrides. See [DOCKER-AND-RUNTIME-VERIFICATION.md](DOCKER-AND-RUNTIME-VERIFICATION.md).

## Forge 1.20.1 experimental bridge (source compiled; game validation pending)

The `runtime-probe` mod now compiles the **same** source policy package via
Gradle source sets and embeds the derived exact-ANCHOR 24-aircraft CSV. The
`RuntimeTacticalAtlas` loader resolves per-airframe model and profile from
that resource. `RuntimeTacticalPilot` samples live Forge aircraft state,
uses `FlightControlLoop.step` once after each aircraft tick, and writes
actual attitude, position, engine and command telemetry when a GameTest or
operator-managed aircraft is available.

The integration addresses a specific discovered Immersive Aircraft 1.3.3
behavior: a nonplayer ArmorStand pilot has its raw inputs zeroed by
`VehicleEntity.tickPilot`. At the END server phase the adapter compensates
the IA `InterpolatedFloat` state with `0.1 * command` after the 0.9 decay,
so the **next** vehicle controller update consumes the intended delayed
input. This correction is pinned to the exact IA source semantics and checked
by `IaNonPlayerInputBridgeMath`; source compilation and the six-step math
contract do not prove the binary follows it. Real GameTests verify input
commands, yaw response after input, and physical displacement before calling
the bridge operational.

Operator research entrypoint after the exact mod binaries are installed:

```text
/wwai patrol
/wwai stop
```

Both commands require permission level 2. The research patrol only accepts
one uncrewed, already-airborne Warfare Wings aircraft near the operator;
it attaches a temporary nonplayer rider, uses the operator's look direction
to define a patrol waypoint, runs for at most 900 ticks, logs the control
series and supports explicit detach. It never grants automatic weapon or
ordnance use. **Command operation has not been demonstrated in Minecraft
yet.** It is a pilot trial, not a finished production enemy-AI spawner.

## Guidance and safety evidence

`FlightGuidanceSelfTest` directly verifies:
wrapped yaw at the 180-degree seam; east/west steering; climb/descent pitch
signs; damping of leftover filtered pilot input; throttle near a station;
non-finite rejection; and 100 real source-microkernel ticks approaching a
requested heading.

`FlightGuidanceAtlasSelfTest` validates **all 24 derived aircraft**: for each
aircraft, it applies 200 consecutive computed raw controls through the actual
source microkernel (4,800 aircraft-ticks), requiring finite states, bounded
controls, substantial reduction in yaw error, real yaw movement, and
eastbound displacement. This is a dynamic acceptance test rather than
merely a switch/case tactic check. It does not imply real Minecraft parity.

`FlightControlLoopSelfTest` verifies clear-air mission retention, a sampled
hill ahead causing climb command, closing obstacle prediction and collision
avoidance, non-closing obstacle rejection, low-speed reserve, terrain priority
over reserve, refusal to trust nonfinite terrain, and identical action replay.

`FlightTerrainChallengeSelfTest` runs **all 24 source-Atlas aircraft for
180 actual source-microkernel ticks** (4,320 aircraft-ticks) against a
synthetic raised ridge. It requires warning/avoidance to occur, continued
forward movement, no `onGround` transition and finite position throughout
the scenario. This is a real closed-loop success assertion **within the
source heightfield**, not a Minecraft voxel-collision or universal obstacle
clearance guarantee.

These tests intentionally do **not** claim that a commanded climb always
escapes a wall or that passing an 8-block clearance check means every plane's
actual hitbox is safe. The collision dimensions, forward height samples,
projectile line-of-fire and waypoint speed margins require exact-runtime
measurement under both the target JAR and actual Minecraft collision code.

## Scenarios and aircraft compatibility

The common input format already carries per-plane `Model` and
`AircraftAtlasMain.Metrics`; it does not compress the performance axes into
a universal score. The source says:

| Aircraft | 90° yaw source estimate | Equal-angle source speed retention | Intended test focus |
|---|---:|---:|---|
| A6M | 42 ticks | 0.9256 | close nose tracking, energy bleed, defensive break |
| P-47N | 60 ticks | 0.9646 | speed-preserving extension/re-entry |
| Spitfire | 44 ticks | 0.9350 | tracking and unit-specific section formation |
| IL-2 | 41 ticks | 0.9520 | low-level ground attack and pull-out margin |
| B-17 | 118 ticks | 0.9946 | slow heading response, stable route, combat box |

All numbers in this table are `SOURCE_MICROKERNEL`, not historical aircraft
measurements or a same-artifact runtime trace.

## Unresolved acceptance gates

- The IA `setInputs` path has to be injected at an actual tick position
  that the normal nonplayer `tickPilot` handling does not erase. Confirm
  effective smoothed X/Z and engineTarget from **actual GameTest telemetry**.
- Terrain and obstacle sampling must come from live world blocks and entity
  bounding boxes, with explicit chunk/load and no-ground handling.
- Loadout, weapon type, ammunition, projectile speed/gravity, torpedo
  waterline/drop range and friendly fire need authentic Forge/IA/WW APIs.
- Flight control must handle multiple aircraft *simultaneously* with a
  stable tick clock; use independently stored `Memory` and contact tracks.
- Run actual A6M/P-47N/IL-2/B-17 control-envelope and 90° traces before
  accepting physical parity, then flight/escort/bombing scenarios under
  the exact game versions. Keep source simulation and runtime results in
  separately tagged reports.

Historically sourced tactical hypotheses and service/year distinctions live
in [TACTICS-EVIDENCE-v1.md](TACTICS-EVIDENCE-v1.md).

## Coordinated multi-aircraft source simulation

`SquadronCommand` connects real per-unit source state with command and
sensing. It uses distinct **aircraft instance IDs** and exact Atlas type IDs,
retains independent local tracking memories and controller state, and advances
all units simultaneously from one frozen tick snapshot. The team commander
assigns locally observed targets with deterministic saturation penalties,
prioritizing contacts close to an escorted asset. It computes generic or
explicit historical formation stations, actual nearest friendly positions
and a geometric friendly-fire corridor; the source simulator never fires a
real projectile or invents damage.

`MissionScenarioSelfTest` tests real synchronized 20 Hz source motion and
target selection in 1v1 and 2v2 contacts, insertion-order determinism, B-17
escort against an A6M interceptor, Spitfire RAF formation with nonzero
leader heading, IL-2/Ju87/G4M/B-17 attack roles, friendly-fire inhibition,
nearby allied collision avoidance, track-expiration/no omniscience, mission
and roster validation and all 24 aircraft advancing as separate entities.
These are **source flight/decision outcomes**, not combat kills or
exact-game multiplayer behavior. Flight status is preserved per unit.
