# Warfare Wings — Tactical Air AI v1 (source-laboratory implementation)

**Status:** Java 17 headless simulation implemented, 24/24 aircraft represented; **real Minecraft/Forge behavior NOT_RUN**. The ANCHOR data and physical-plant source models remain unchanged.

## 1. End-to-end relationship

```text
supplied Warfare Wings ANCHOR (verified derived raw properties)
    -> IA 1.3.3 effective aircraft properties
    -> AircraftAtlasMain v2 (source-microkernel response)
    -> TacticalAirAI.Profile (per-aircraft capabilities)
    -> Frame (observed position, mission, contacts, leader, friend, fuel/damage)
       + Memory (deterministic maneuver state)
       + optional HistoricalDoctrineOrders.Order (unit, year, formation slot)
    -> Decision (reason, maneuver, raw IA X/Z/throttle, aim waypoint)
    -> Ia133Microkernel.tick (20 Hz plant, including input/throttle lag)
    -> TacticalScenarioMain (96 deterministic 200-tick cases)

    FUTURE exact Forge GameTest:
    real flight dynamics, entity tracking, collision, weapon inventory/mount,
    projectile physics, damage, visibility/line of sight -> actual combat AI
```

The `atlasDoctrine` field in the ANCHOR is a descriptive label, not a historical
combat instruction. B-17 and G4M are labeled `escort` in that data despite
being bomber roles; the mission planner uses the actual `role` as a guard.
No behavior is selected merely because a plane has an IJN, RAF, USAAF,
Luftwaffe, VVS, IJA, USN or other faction label.

## 2. What the runnable Java code currently does

- **TacticalAirAI.java**: finite, validated, deterministic decision state and
  raw controller commands. Priorities are terrain clearance, actual nearby
  friendly separation, fuel/damage withdrawal, escort duty/acute threat,
  ground/ship mission, target encounter and patrol. It produces reason codes
  and an explicit `SOURCE_MICROKERNEL+TACTICAL_HEURISTIC` evidence label.
- Fighters can select intercept, high-side pass, close pursuit, energy-building
  extension, defensive break and escort screening. The branch uses the
  24-aircraft Atlas response axes, current speed/relative altitude,
  enemy bearing and proximity. For example, an under-speed P-47N can extend
  while an A6M with rapid source yaw response may turn toward a close target.
  **These are design hypotheses, not verified combat effectiveness.**
- Bombers/attackers/torpedo aircraft have mission-preserving route modes.
  Fighter pursuit is not assigned to a bomber. Rear approaching threat can
  interrupt non-fighter attack mission; dangerous altitude overrides it.
- HistoricalDoctrineOrders applies **only when a dated mission explicitly
  requests it**: a unit-specific RAF four-fighter station pattern (1940+),
  USN pair mutual-support/weave candidate (historical concept documented
  from 1942), USAAF bomber combat-box positions (1943+) and USAAF high
  fighter escort stations (1944+). Distances and weave timing are in Minecraft
  blocks/ticks for experiments, not historical dimensions. An F6F using the
  early-1942 USN pattern is rejected before 1943; the historical 1942
  demonstration involved earlier aircraft, not the F6F.
- The controller follows IA yaw/pitch signs and lets the physics microkernel
  apply its observed one-tick input lag; it never teleports or rotates an
  entity directly. The `firingWindowCandidate` flag computes a simple
  constant-velocity projectile interception feasibility with a line-of-fire
  gate. It is an advisory diagnostic, **not** a shot or a verified weapon
  solution.

The companion [historical source register](TACTICS-EVIDENCE-v1.md) separates
`HISTORY_FACT`, `PROJECT_FACT`, `DESIGN_INFERENCE`, `GAME_ADAPTATION`
and `TEST_REQUIRED`. Use it to audit unit, year and aircraft variant claims.

## 3. Reproducible evidence available today

The primary command is:

```powershell
node .\check-microkernel.mjs --java-home 'C:\Path\To\JDK17'
```

Run it from `departments/minecraft/mods/warfare-wings/physics-ai`. It compiles
the Java sources with `--release 17` and runs:

1. 18 pre-existing physics invariants, source trace and 24-aircraft Atlas
   golden/report comparison;
2. tactical decision branch/role/steering/fire-window tests and a repeatable
   80-tick flight for every aircraft;
3. historical formation slot, era and safety-priority checks;
4. two independent generations of **24 aircraft x 4 scenarios x 200 ticks =
   19,200 simulated aircraft ticks**, requiring byte-identical CSV output
   and equality to [the committed source-only scenario table](reports/tactical-source-scenarios-v1.csv).

The four scenario families are `AIR_CONTACT`, `ROLE_MISSION`,
`SAFETY_RECOVERY`, and `LOW_FUEL`. They are standardized test situations,
not historically recorded sorties. The CSV preserves per-aircraft maneuver
histograms, speed, minimum altitude, final objective distance and provenance.
No source-only trajectory is labeled a Minecraft result.

The same checks run with **OpenJDK 17 inside Docker**:
[Docker and runtime verification](DOCKER-AND-RUNTIME-VERIFICATION.md).

## 4. Behavioral contracts before promotion to the game

1. **Real sensor data**: current position/velocity, exact wingman and leader,
   nearby aircraft, terrain and waterline, current weapon slots, visibility,
   line of sight and damage/fuel are sampled through a server-side Forge
   adapter. Formation anchor denotes the leader/route reference; an actual
   neighbor has a separate `nearestFriendlyPosition` field for avoidance.
2. **Missions carry an actual loadout and release envelope**. The existing
   `TORPEDO`, `DIVE_BOMB`, `STRAFE`, `LEVEL_BOMB` modes currently
   navigate only. Never use `terrainHeight + 14` as a historically factual
   torpedo release height. A game adapter must discover waterline, actual
   ordnance and applicable speed/altitude restrictions before enabling drops.
3. **Safety and geometry**: validate collision lookahead, high-rate
   pull-out/egress, stall/ground margin, crossing pairs, heading wrap, cover
   leash and obstacle avoidance under true Forge entity movement. The
   simplified flat world cannot prove these.
4. **Weapons**: bind real hardpoint position, muzzle speed, ballistics,
   projectile gravity/spread, cooldown, ammunition, occlusion and friendly
   fire checks. A candidate firing window must not directly issue a game shot.
5. **Deterministic squadron scheduling**: provide formation leadership,
   unit/era-aware mission orders, target deconfliction and bounded
   reacquisition. Avoid a globally fixed nation personality.
6. **Real calibration**: run the exact supplied Warfare Wings JAR and pinned
   IA runtime in the GameTest environment. A6M and P-47N throttle/yaw/pitch
   first, followed by IL-2/B-17 turn response, 90-degree comparison,
   climb/egress, projectile/weapon tests and multi-aircraft trials. Report
   physics errors separately from decision-quality metrics.

The simulation kernel does not currently reproduce voxels, fluids,
multiplayer ownership, wind, real projectile callbacks or Minecraft damage.
No hit-rate, survival-rate, victory, historical tactical success or real-world
airspeed claim can be inferred from this v1 model.

## 5. Next gated milestones

| Gate | New capability | Acceptance evidence |
|---|---|---|
| A — Exact physical parity | Real A6M/P-47N, IL-2/B-17 throttle/yaw/pitch and equal-angle traces | Actual Forge source-vs-runtime samples, phase and error reports; calibrated tolerances |
| B — Forge observations | Entity pilot adapter, terrain/water/collision sensors and observed formation membership | GameTest trace proving every input maps to a concrete server entity state |
| C — Real attack systems | Loadouts, gun/ordnance API, lead and friendly-fire safeguards | Projectile/drop, avoidance and terrain recovery instrumentation |
| D — Multi-aircraft missions | Escort/attack/formation roles, coordinated section leaders, target handover | 2v2, fighter-vs-bomber, escort protection and multi-aircraft repeatable tests |
| E — Historically grounded policy | Unit/era-specific scripted missions and measured policy tuning | Scenario reports linked to historical evidence and exact game combat telemetry |

Treat milestone A as a gate for claims of **host-physics equivalence**, not a
prohibition on research prototyping in the faster source environment.
