# Airborne AI failure / repair lessons — bounded cross-source synthesis

This is not a substitute for each MOD's full `FAILURE-REPAIR-HISTORY.md`. It records only the bounded failure evidence encountered while building the cross-MOD airborne synthesis.

## F01 — Landing transition can deadlock

**Evidence:** Saint's Dragons release history reports simplifying landing logic so flying dragons behave deterministically and do not remain stuck in a landing queue. Current source has one explicit ground-transition state with cancel/fail/contact-complete behavior.

**Lesson:** one subsystem owns the air/ground transition. A second Goal must not independently toggle landing flags.

**Foundation invariant:** every transition has a state owner, timeout/backoff, explicit cancellation and completion predicate.

## F02 — Tactical phase and flight state can disagree

**Evidence:** Saint's Dragons history includes an airborne phase case where the dragon did not land after the phase change.

**Lesson:** combat phase exit must reconcile the movement medium. "Attack phase ended" is not equivalent to "landing completed".

**Invariant:** tactical state requests a transition; the transition machine reports completion back.

## F03 — Naive vertical correction can drive a large flyer into a ceiling

**Evidence:** Saint's Dragons history includes flying dragons spawned in large caves shooting upward into ceilings and becoming stuck.

**Lesson:** preferred altitude is a request, not permission to move vertically through occupied space.

**Invariant:** altitude correction is clearance-constrained; large bounding boxes use volume/corridor checks.

## F04 — A candidate block is not automatically a valid landing surface

**Evidence:** Cosy 1.20.1 history reports a crash when birds attempted to land on blocks without collision.

**Lesson:** block existence and collision/support validity are separate.

**Invariant:** touchdown/perch requires a non-empty valid support surface for the full footprint.

## F05 — A perch can disappear after selection

**Evidence:** Cosy history later reports birds continuing to perch on blocks that no longer exist and getting stuck.

**Lesson:** environmental reservations expire.

**Invariant:** revalidate support while perched; invalid support causes a safe transition to flight.

## F06 — Activity registries can collide

**Evidence:** Fowl Play history reports duplicate activity names causing a crash.

**Lesson:** ecology scheduling needs the same identifier discipline as movement/control registries.

**Invariant:** unique registry-safe Activity IDs; schedule selects activity only and does not directly mutate velocity.

## F07 — Legacy hover/fly flags can conflict

**Evidence:** Ice and Fire's Hippogryph source contains a FIXME stating that hover/flying logic can result in not landing and animation issues.

**Lesson:** multiple booleans encode illegal combinations too easily.

**Invariant:** replace independent booleans with an exclusive state machine or enforce one transition owner with explicit legal combinations.

## F08 — One broken predicate can suppress an entire behavior family

**Evidence:** Ice and Fire: Dragon Fix reports repairing an `isChained` condition that could remain true and break dragon behavior.

**Lesson:** eligibility predicates are high-impact control gates.

**Invariant:** expose gate reason codes in debug telemetry and test each gate independently.

## F09 — Altitude can escape intended limits

**Evidence:** Dragon Fix reports correcting dragons flying above configured maximum height.

**Invariant:** clamp final destination and final movement command, not only an early intermediate target.

## F10 — Steering math can become non-finite

**Evidence:** Dragon Fix release history includes additional NaN checks.

**Typical causes:** normalization of near-zero vectors, invalid angle math, stale/uninitialized targets.

**Invariant:** no movement command applies unless position, velocity, direction, yaw/pitch and target values are finite.

## F11 — Self-target is a valid software state unless explicitly rejected

**Evidence:** Dragon Fix reports preventing dragons from trying to attack themselves.

**Invariant:** target acquisition and every retained target memory enforce `target != self`.

## F12 — Shared flight shell defects can affect many mobs at once

**Evidence:** HMaG 9.0.33 release notes report AI crashes involving Banshee, Dyssomnia, Ghastly Seeker, Ghost, Hornet and Wither Ghost.

The inspected release version-bump commit only changes metadata, so this study does **not** invent the underlying cause.

**Lesson:** shared MoveControl/Goal code needs a small cross-entity regression suite.

## F13 — LOS is not the same as target validity

**Evidence:** Book of Dragons public history first fixes dragons that effectively never lost a target regardless of distance, then describes LOS-aware behavior that attempts to find a target after direct sight is lost.

**Lesson:** both extremes are bad:
- omniscient permanent lock;
- immediate forget on one blocked ray.

**Invariant:** track separately:
- target valid;
- target currently visible;
- last known position;
- memory/search deadline;
- reacquire result.

Book of Dragons is ARR; this is behavior-history evidence only.

## F14 — Stale asynchronous path results must not win

**Derived from:** Saint's current request-generation/state design and the general async route architecture.

**Invariant:** every async route request carries a generation/objective identity. A result for an old objective is discarded.

## F15 — Scripted dash is not normal navigation

**Derived from:** Olympus research.

**Lesson:** a `noPhysics`/scripted Bezier dash can be valid for a bounded attack but must not become the ordinary flight controller.

**Invariant:** scripted movement has its own collision/hit sweep, bounded duration and explicit handoff back to normal steering.

## Required regression cases for a future LAB prototype

1. Spawn under a low ceiling and request climb.
2. Landing support removed during approach.
3. Landing support removed after perch.
4. New chase objective during landing approach.
5. Path result arrives after target moved and objective generation changed.
6. Zero-length target vector.
7. Forced non-finite input rejected without moving.
8. Flight at configured maximum altitude.
9. Self-target injection rejected.
10. LOS lost behind wall, then reacquired before search timeout.
11. Pack attacker reservation expires after entity removal.
12. Flyer starts embedded in collision and recovers or fails boundedly.
13. Common-flyer controller cannot loop unlimited full-path recalculation.
