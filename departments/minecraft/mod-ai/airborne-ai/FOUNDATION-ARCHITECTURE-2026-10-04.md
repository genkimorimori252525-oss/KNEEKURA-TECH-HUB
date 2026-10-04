# KNEEKURA Airborne AI Foundation — research-derived architecture

Status: **design synthesis only; no implementation in this task**.

## Design principle

A flying creature is not one algorithm. Separate:
- intent;
- state transition;
- destination;
- route;
- steering;
- collision/recovery;
- combat;
- group behavior;
- ecology;
- presentation.

This lets a boss, a mosquito and an ambient bird share contracts without paying the same runtime cost.

## 1. Tactical / Brain layer

Produces a `FlightIntent`, for example:

- `CRUISE`
- `CHASE`
- `ORBIT`
- `STRAFE`
- `DIVE`
- `FLEE`
- `RETURN_HOME`
- `LAND`
- `PERCH`
- `TAKEOFF`

The tactical layer may consider target state, combat resource, schedule, pack reservation and cooldown. It must not directly write velocity.

References:
- Saint's scored tactics and pack attack phases;
- Olympus combat Goals;
- Alex resource-driven feed/egress loop;
- Fowl Play Activities.

## 2. Exclusive air/ground state machine

Recommended states:

`GROUNDED → TAKEOFF → AIRBORNE → LANDING_APPROACH → TOUCHDOWN → GROUNDED`

Exceptional state:

`RECOVERY`

Rules:
- exactly one state owner;
- request/cancel/complete are explicit;
- tactical code requests a transition rather than flipping multiple booleans;
- landing completes only on physical contact;
- invalid landing transitions back to AIRBORNE/RECOVERY.

This layer is the direct response to Saint's landing repair history and Ice and Fire Hippogryph state conflict.

## 3. Destination policy

Transforms intent into a desired spatial objective.

Profiles may define:
- terrain-relative cruise band;
- target-relative combat band;
- maximum altitude;
- desired orbit radius;
- attack approach/egress distance;
- landing search radius;
- perch preference.

Target prediction is bounded by short prediction horizons. A desired point is sanitized before use:
- finite coordinates;
- world height bounds;
- species altitude policy;
- target not self.

## 4. Route planner

Recommended order:

1. clear direct corridor fast path;
2. if blocked and profile permits, budgeted/async 3D route;
3. bounded shortcut/look-ahead;
4. partial-path extension if useful;
5. fail to recovery/backoff instead of per-tick retry storm.

Every route request carries:
- objective/generation ID;
- purpose;
- target point;
- arrival policy;
- profile/bounding-box identity.

A stale async result is discarded.

References:
- Olympus direct + 3D fallback;
- Saint's async request/resolver/look-ahead/stuck controller.

## 5. Steering executor

Consumes route/look-ahead point and produces continuous movement.

Required properties:
- velocity continuity;
- bounded yaw/pitch rate;
- turn-dependent speed reduction;
- final-arrival braking;
- vertical deadzone;
- optional dive/takeoff envelope;
- movement heading may differ from attack/look heading;
- final finite-vector validation.

References:
- Olympus inertia-aware MoveControl;
- Saint's steering/motion policy;
- Fowl Play pitch/landing deceleration;
- Ice and Fire turn-speed behavior.

## 6. Clearance and recovery

Use the creature's volume, not only a center ray, where authority matters.

Mechanisms:
- swept/stepped bounding-box corridor test;
- short look-ahead ray for cheap profiles;
- floor/ceiling clearance observation;
- stuck progress detector;
- exponential/bounded backoff;
- embedded-free-space recovery;
- bounded retry budget.

No infinite "recompute every tick until it works" loop.

## 7. Landing subsystem

Candidate pipeline:

1. generate bounded candidates near anchor;
2. apply surface/fluid/species policy;
3. validate full footprint/support;
4. score distance/separation/height;
5. reserve selected site with TTL if needed;
6. route to approach region;
7. validate strict short final descent;
8. periodically revalidate candidate;
9. complete only on contact;
10. cancel/recover if invalidated.

Dry land vs water is a policy, not a hard-coded universal rule.

## 8. Combat modules

Plug-in patterns:

### Orbit / strafe
Olympus-style tangent/radial orbit and lateral attack positioning.

### Predictive chase / dive
Saint-style short target prediction and floor-aware dive intercept.

### Resource combat cycle
Alex-style:
`approach → attach/feed → detach → egress/standoff → ranged attack`.

### Charge shell
HMaG-style cheap direct charge for common enemies.

### Pass-through attack
Ice and Fire scorch geometry: preserve approach vector, cross the target, then reposition.

### Scripted dash
Olympus Bezier dash allowed only as bounded scripted combat motion with swept hit/collision checks.

## 9. Group layer

Two independent concepts:

### A. Local flock vector
`alignment + cohesion + separation + noise`.

Can be memory/behavior-gated as in Fowl Play.

### B. Tactical formation coordinator
Assigns:
- formation slot;
- stage point;
- attack reservation;
- launch time;
- egress lane;
- cooldown/wave.

Saint's Nulljaw is the strongest reference.

Composition rule:
- tactical waypoint is authoritative;
- separation remains active;
- cohesion/alignment are bounded and may be reduced during committed attack phases.

## 10. Ecology schedule

Recommended chain:

`Time / world context → Activity → Behavior → FlightIntent`

Examples:
- REST → find perch → land → sleep;
- HUNT → acquire valid prey → take off → pursue;
- SOAR → cruise band + flock;
- FORAGE → ground/perch target.

Do not make the schedule manipulate MoveControl directly.

## 11. Target perception and memory

Separate fields/concepts:
- current target identity;
- target validity;
- direct LOS now;
- last known position;
- last seen time;
- bounded search/reacquire deadline.

This avoids both permanent omniscience and instant target loss on a blocked ray.

## 12. Observability

Every authoritative flyer should expose a bounded debug snapshot:

- airborne state;
- tactical intent;
- activity;
- target ID and LOS state;
- destination;
- route mode: DIRECT / PATH / RECOVERY;
- path generation ID;
- altitude band/error;
- landing candidate and validation reason;
- stuck ticks/retry count;
- pack slot/reservation;
- last transition reason.

Reason codes are part of the design, not optional logging. They are how high-impact eligibility predicates become testable.

## 13. Performance profiles

### Tier A — Hero
- full 3D fallback;
- predictive combat;
- validated landing;
- rich recovery;
- formation coordinator when needed.

### Tier B — Common hostile
- direct steering;
- cheap collision probe;
- simple attack Goal;
- bounded fallback only when necessary.

### Tier C — Ambient
- non-authoritative client particles;
- Boids;
- simple raycast/perch FSM.

The profile is selected by gameplay authority and entity importance, not visual size alone.

## 14. Forge 1.20.1 boundary

- Minecraft 1.20.1 / Forge 47.x is the KNEEKURA anchor.
- The foundation should rely on its own small interfaces/contracts rather than requiring SmartBrainLib solely because Fowl Play uses it.
- Vanilla Goal/Brain concepts may implement the same separation.
- Upstream code reuse must obey each source license.
- Saint's source code is MIT, but its art/audio assets are ARR.
- Book of Dragons is ARR and supplies only observed design hints here.
- No upstream textures/models/audio are part of this research output.

## 15. Minimum test invariants

A foundation implementation is not accepted unless tests cover:

- finite movement vectors;
- target != self;
- altitude bounds;
- landing support validation/revalidation;
- one transition owner;
- stale async route rejection;
- bounded retries/backoff;
- contact-based landing completion;
- expiring group attack reservations;
- bounded LOS memory/search;
- embedded recovery;
- clear separation of normal navigation and scripted dash.

## 16. Suggested first prototype

Build only one Tier-A flyer and one Tier-B flyer before adding species-specific combat.

Tier A:
- cruise;
- chase;
- direct/path fallback;
- landing;
- recovery;
- instrumentation.

Tier B:
- random flight;
- chase/charge;
- collision probe;
- cheap recovery.

Only after those contracts survive LAB scenarios should flocking, pack combat and advanced attack modules be layered on.
