# Flying AI — legacy research prototype and modern objective adapters

Status: **legacy flight physics mapped with explicit WIP boundary; modern 1.20.1 integration mapped. Runtime NOT_RUN.**

## Legacy architecture

The 1.7.10 tree contains an ambitious general flight stack: `EntityIMFlying`, `IMMoveHelperFlying`, `NavigatorFlying`, plus circle/swoop/strike/tackle/pickup/stabilise goals.

### Flight-state physics

`EntityIMFlying` distinguishes:

```text
GROUNDED -> TAKEOFF -> FLYING -> LANDING -> TOUCHDOWN
```

The move helper converts desired heading/speed into thrust, lift, bank and climb behavior instead of treating the mob as a ground walker in the air.

### Aerial attack commitment

The legacy combat flow is approximately:

```text
circle / hold range
 -> find opportunity
 -> swoop alignment
 -> commit final run
 -> strike (fly-by / tackle / pickup)
 -> stabilise / climb away
```

The reusable idea is the **commit phase**: once a high-speed attack run begins, retargeting every tick would destabilize the maneuver.

## The obstacle retina is WIP

`NavigatorFlying` allocates a 30×20 `retina` and 28×18 `headingAppeal` grid. The intended design ray-traces possible headings and biases the field toward a target/circle/landing direction.

In the pinned source, however, the statements that write measured ray-trace distance into the retina are commented out. The uploaded 1.1.2 bytecode confirms the same boundary: ray traces occur, but measured hit distance is not written into the retina before heading selection.

Therefore the obstacle field is **not promoted as a working Invasion technique**.

## Legacy gameplay boundary

Bird/GiantBird/Vulture are not established normal 1.1.2 invasion content:

- Bird/GiantBird registration is guarded by `debugMode`;
- the Vulture egg is debug-only;
- default debug mode is false;
- `IMWaveBuilder` has no bird/vulture pattern.

`EntityIMGiantBird` also contains obvious test behavior. Treat this stack as a research prototype.

## Modern 1.20.1 direction

The modern port does **not** make the legacy aerodynamic navigator the common flight foundation.

Instead it tends to preserve each mob's native movement:

- Phantom-like units retain Phantom movement semantics;
- Ghast-like units retain Ghast movement semantics;
- configured flying/jumping mobs are driven through their native `MoveControl` / navigation when possible.

The invasion layer supplies strategic Nexus intent and small obstacle adapters.

## FlyingWallPath

A reusable modern helper is `FlyingWallPath`:

1. ray toward the Nexus to locate a blocking wall;
2. scan vertically for enough clearance;
3. select a waypoint above it;
4. put the crossing target several blocks beyond the wall;
5. keep that commitment until the mob has actually crossed.

Wall/clearance results are cached for a short interval (20 ticks in the inspected repair), avoiding a vertical scan every movement tick.

This is often a better tradeoff than a full 3D global flight pathfinder when the dominant problem is “fly to the objective but climb over a fortified wall.”

## Modern recovery

`IMPhantomEntity` includes progress-aware attack handling: a swoop that fails to approach can abandon and temporarily blacklist the target; after a hit it deliberately retreats upward before another approach.

## Bounded repair history

| Commit | Observed repair |
|---|---|
| `946ec1a8` | wall ascent detection |
| `4ba7e71c` | persistent/smoothed wall crossing |
| `47926902` | cache/throttle wall scans |
| `05a23ad9` | temporary revert |
| `5f209558` | restoration by reverting that revert |
| `c8b19f63` | native movement controls for configured jumping/flying mobs |

The reason for the temporary revert/restoration pair is **UNKNOWN** in this bounded review.

## KNEEKURA guidance

Promote explicit attack commitment/recovery, native movement-controller adapters, small obstacle-specific waypoint planners, progress/unreachable timers and cached spatial queries.

Do **not** promote the legacy retina, debug-only Bird/Vulture gameplay, or wholesale legacy aerodynamics as production-ready systems.
