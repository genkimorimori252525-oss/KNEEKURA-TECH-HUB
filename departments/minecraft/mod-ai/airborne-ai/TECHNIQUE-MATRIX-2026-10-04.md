# Airborne AI technique matrix — 2026-10-04

## Common vocabulary

- **Tactical intent**: why to move — cruise, chase, orbit, dive, flee, land, return, perch.
- **Destination policy**: where the current objective point should be.
- **Route**: safe sequence or corridor toward that point.
- **Steering**: continuous velocity/orientation changes.
- **Transition**: ground ↔ takeoff ↔ flight ↔ landing.
- **Local flock**: neighbor-based motion influence.
- **Tactical formation**: group-assigned slots/attack reservations.
- **Presentation**: animation/body pose derived from flight state; not navigation authority.

## Layer comparison

| Capability | Strong reference | Technique |
| --- | --- | --- |
| Goal/route/steering separation | Olympus | Goal chooses objective, Navigation resolves direct/path route, MoveControl executes inertia-aware steering |
| Full large-flyer flight stack | Saint's Dragons | request → async resolver → look-ahead path following → steering executor → stuck recovery |
| Cheap hostile flight shell | HMaG | Goal writes wanted point; MoveControl direct-accelerates only while a reachability probe is clear |
| Ecology schedule | Fowl Play | game time selects Activity; Brain behavior chooses target/intent |
| Ambient mass flock | Cosy | client-only BirdParticle with Boids and tiny FSM |

## Takeoff and landing

### Saint's Dragons
- Searches bounded rings around an anchor rather than assuming the point below the target is safe.
- Validates the creature's full footprint.
- Prefers dry land and treats water as species-gated fallback.
- Separates route-to-approach from the short final descent corridor.
- Revalidates touchdown near contact and periodically during approach.
- Completes landing only after real ground/water contact.
- Cancels or fails the landing transition explicitly when a new flight command or invalid site appears.

### Fowl Play
- Flight state and ground state use different movement logic.
- Perch selection writes a normal Brain movement target.
- Landing decelerates near the destination.
- Rest behavior composes "find perch" and "sleep if perched".

### Cosy
- Minimal FSM: `FLYING → LANDING → PERCHED ↔ CHECKING`.
- Samples candidate high points, rejects fluid landing, and stores the supporting block.
- Invalid support or disturbance returns the particle to flight.

### Alex's Mobs
- Crimson Mosquito can impulsively take off from ground.
- A long non-combat flight eventually attempts ground rest.
- Negative flight ticks act as a cheap post-landing rest/cooldown.

### Ice and Fire
- Explicit ground / AI-flight / controlled-flight navigator modes.
- Roost/escort logic can trigger hover/flight based on distance and height.
- Hippogryph source itself warns that hover/flying state interaction can break landing, making it useful as an anti-pattern.

## Destination and altitude policy

### Olympus
- Idle altitude is terrain-relative.
- Combat altitude is target-relative.
- Orbit destination uses tangent motion plus radial correction.

### Saint's Dragons
- Predicted target motion feeds chase/dive destination.
- Dive destination is floor-clamped when clearance is known.
- Landing target is a validated physical touchdown point rather than just a combat focus.

### Ice and Fire
- `TACKLE`: direct target intercept.
- `HOVER_BLAST`: random horizontal standoff at stage-dependent height.
- `SCORCH_STREAM`: preserves the attack-start/prey-start vector and flies through to the opposite side.
- Global `maxDragonFlight` clamps target altitude.

### Cosy
- Terrain heightmap + configured relative height limit applies a soft downward correction.

## Route and obstacle handling

### Olympus
1. Try a cheap clear direct segment.
2. Fall back to 3D flying path navigation.
3. Shortcut only bounded safe path nodes.
4. Recover when embedded in collision.

### Saint's Dragons
1. Path requests are asynchronous/budget-aware.
2. Movement follows look-ahead points rather than raw node centers.
3. Stuck detection/backoff prevents endless immediate retries.
4. Landing uses stricter final-approach rules than normal cruise.

### Alex / HMaG
- Cheap direct-vector movement is gated by collision/reachability probes.
- This is appropriate for common hostile flyers when full 3D planning would be excessive.

### Cosy
- Forward raycast supplies a tiny obstacle-avoidance response suitable for visual ambience.

### Ice and Fire
- Legacy dragon flight turns away, reduces speed and clears the current flight target on horizontal collision.

## Continuous steering

Useful combined rules:
- preserve velocity continuity instead of teleporting heading each tick;
- limit yaw/pitch change;
- slow for hard turns;
- slow near final arrival;
- separate movement direction from look/attack facing when needed;
- retain a vertical deadzone to prevent jitter around target altitude;
- validate every produced vector as finite before applying it.

Fowl Play is a clear small-bird reference for pitch-to-forward-motion and landing deceleration. Ice and Fire demonstrates turn-dependent speed. Olympus/Saint's provide the richer inertia/look-ahead form.

## Combat patterns

### Olympus
- tangent orbit;
- lateral strafe;
- time-to-impact projectile dodge;
- quadratic Bezier dash;
- swept-AABB hit testing for scripted dash.

### Saint's Dragons
- scored air-versus-ground tactics;
- predicted chase and dive;
- landing as a tactical option rather than a timer only;
- Nulljaw pack attack:
  `ORBIT → STAGE → DIVE → EGRESS`;
- deterministic formation slots;
- attack reservation;
- staggered pincer runs for sufficiently large packs;
- cooldown before next wave.

### Alex's Mobs / Crimson Mosquito
Resource-driven combat cycle:

`APPROACH → ATTACH → FEED → DETACH → STAND-OFF → RANGED FIRE → repeat`

This is useful because movement tactics are driven by combat resource state (blood level), not only distance.

### HMaG
- reusable shared charge-attack shell;
- cheap random flight;
- specialized ranged/beam/summon phases replace the attack Goal while retaining common flight movement.

### Ice and Fire
- attack mode maps directly to different target geometry: direct tackle, overhead blast, through-target scorch pass.

## Group movement: do not confuse two different systems

### Local flock steering
Fowl Play and Cosy implement versions of:
- alignment;
- cohesion;
- separation;
- noise/randomness.

Fowl Play gates flocking with Brain memory, allowing avoidance or food behavior to override it.

### Tactical formation
Saint's Dragons assigns:
- deterministic orbit slots;
- group membership;
- attack reservations;
- attack wave timing;
- staging and egress waypoints.

**Recommendation:** tactical formation owns the group objective. Local Boids may add only bounded separation/alignment underneath it. Cohesion must not pull a committed attacker out of a tactical lane.

## Ecology

Fowl Play supplies the strongest non-combat reference:
- `IDLE`, `FORAGE`, `HUNT`, `SOAR`, `REST` by day schedule;
- perch/rest target selection;
- sleep while perched;
- hunting as an activity rather than a permanent target loop.

The reusable idea is not SmartBrainLib itself; it is the separation:
`Schedule → Activity → Behavior → Movement Intent`.

## Performance tiers

### Tier A — Hero / boss / large combat flyer
Use:
- predictive destination;
- direct fast path + async/budgeted 3D fallback;
- validated landing;
- tactical state;
- sophisticated recovery;
- optional pack coordinator.

References: Saint's Dragons + Olympus.

### Tier B — Common hostile flyer
Use:
- direct wanted-point steering;
- collision/reachability probe;
- limited state machine;
- cheap bounded recovery;
- simple attack Goals.

References: HMaG + Alex's Mobs.

### Tier C — Ambient flock
Use:
- client-only particle entities where authority is unnecessary;
- local Boids;
- simple altitude/raycast/perch FSM.

Reference: Cosy.

This tiering is a design requirement: do not make every visual bird pay Tier-A server cost.
