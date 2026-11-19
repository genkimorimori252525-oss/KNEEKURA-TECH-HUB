# BWR-0010 — canceled Forge death committed the custom death state

Date: 2026-10-03
Origin: OWN_DEVELOPMENT
State: VERIFIED_FIXED (bounded local Forge revival contract)

## Symptom and scope

A synchronous Forge `LivingDeathEvent` listener restored positive health and canceled death. The entity remained alive, but its custom death sequence had already started: pending death ticks and death state remained, AirAttack had changed, and an active dash lost its charging state.

This was reproduced separately during phase-1 aerial combat and active phase-2 dash execution. It implements the existing adopted Java/Forge semantic-death compatibility boundary, not a new Bedrock mechanic.

## Root cause

Basis: DIRECT_OBSERVATION + official Forge source + mapped 1.20.1-47.2.0 bytecode.

`BedrockWitherEntity.die` called `deathController.begin()` before `super.die()`. The superclass first posts the cancellable Forge event, returning before its protected `dead` flag is set if the event is canceled. The product had already committed visual/combat side effects before learning that decision.

Source artifacts and exact changed-file hashes are retained in [the compact receipt](../../evidence/gametest-cancellation-2026-10-03.json). Upstream bodies or JARs are not copied into Git.

## Repair

Call `super.die(source)` first. Start the custom sequence only after the inherited `dead` flag confirms accepted semantic death, retaining the existing removed/state/countdown guards. Health-based `isAlive`/`isDeadOrDying` is not the event-acceptance signal.

No spawn/death duration, explosion, reward amount/timing, or other unresolved Bedrock value changes.

## RED → GREEN

- Baseline: published `1d067f087222a1a7efffe55cb3fc459f1b581b30` with the two new tests and unchanged production code
- RED: 23 required GameTests ran; the original 21 passed; both new revival cases failed with the intended custom-state assertion
- GREEN: `gradle build runGameTestServer` succeeded; **23/23 required tests passed**
- Each listener is entity-identity scoped and removed in `finally`. The tests then kill the same boss normally and verify the existing full death countdown and final removal
- Independent review found no blocking issue

## Verification boundary and rejected hypothesis

The verified contract is synchronous cancellation with **positive-health revival**. Cancellation leaving health at zero, delayed revival, arbitrary third-party integrations and real client/Tank parity are not established. Existing health-driven ticking is not redesigned by this repair.

A separate concern that custom `tickDeath` suppressed XP was disproved: this Forge version's accepted `die` path invokes `dropAllDeathLoot` and `dropExperience` before removal. Adding XP again at the final visual tick would risk duplication, so no reward change was made. Exact Bedrock XP timing remains unresolved.

## Lesson

A lifecycle request is not an accepted lifecycle transition. Commit custom visuals/combat state after the framework's cancellable semantic decision, and test both cancellation recovery and a later genuine death.
