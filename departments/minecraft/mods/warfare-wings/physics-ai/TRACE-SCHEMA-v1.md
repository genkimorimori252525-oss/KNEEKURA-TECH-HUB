# Warfare Wings Physics AI — Trace Schema v1

Purpose: make real Forge runtime traces and pure-Java microkernel traces directly comparable.

CSV header, exact order:

```text
schema_version,source,scenario_id,aircraft_id,tick,game_time,pos_x,pos_y,pos_z,vel_x,vel_y,vel_z,speed_bps,horizontal_speed_bps,yaw_deg,pitch_deg,roll_deg,engine_target,engine_power,fuel_utilization,raw_x,raw_y,raw_z,smooth_x,smooth_y,smooth_z
```

Rules:

- `schema_version` = `ww.physics.trace.v1`.
- `source` is `microkernel` or `minecraft_runtime`.
- `tick` is scenario-relative and begins at 0.
- `game_time` may be blank for the microkernel and is informational only.
- positions and velocities are blocks and blocks/tick.
- speed fields are blocks/second.
- yaw/pitch/roll are degrees.
- control values are normalized to [-1,1]; engine values to [0,1].
- comparison joins by `scenario_id + aircraft_id + tick`.
- no acceptance threshold is implied by schema compatibility.

## Scenario A6M throttle step v1

ID: `a6m-throttle-step-v1`

Initial state:

- aircraft: `warfare_wings:a6m`
- position: `(0, 200, 0)`
- velocity: `(0, 0, 0.7)`
- yaw/pitch/roll: 0
- raw and smoothed X/Y/Z: 0
- engine target: 1
- engine power: 0
- fuel utilization: 1
- sample range: tick 0 through 400 inclusive

Environment:

- clear weather
- IA wind coefficients disabled for this calibration run
- IA fuel consumption disabled so utilization remains 1
- collision damage disabled
- no intentional terrain contact

Control:

- X = 0
- Y = 0
- Z = 0
- engine target = 1 for the whole trace

The runtime probe records tick 0 before the first scenario physics update and then records one row
after each subsequent aircraft tick. The first server END event after spawning is intentionally
skipped so the entity cannot produce a duplicate pre-physics sample merely because it was spawned
after the level entity-tick pass.
