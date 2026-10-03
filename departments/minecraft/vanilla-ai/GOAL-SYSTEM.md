# Goal system — Minecraft 1.20.1 ANCHOR

Evidence: `Goal`, `WrappedGoal`, `GoalSelector`, and `Mob` in [the exact bytecode ledger](ANCHOR-BYTECODE-LEDGER-2026-10-03.json).

## Scheduler flow

The inspected `GoalSelector.tick()` performs:

1. Cleanup: stop a running wrapped goal when its flags intersect disabled flags, or its continuation test fails.
2. Remove flag-owner map entries whose wrapped goal is no longer running.
3. In registered iteration order, examine inactive goals whose flags are enabled, whose existing flag owners can be replaced, and whose `canUse()` succeeds.
4. Stop displaced owners, assign each flag to the accepted wrapper, then start it.
5. Tick running goals with `tickRunningGoals(true)`.

`WrappedGoal.canBeReplacedBy(other)` requires the current goal to be interruptible and the other's numeric priority to be **strictly lower**. Equal priorities do not replace an owner through this test. Priority alone does not prove a goal is eligible.

The independent `targetSelector` uses the same scheduler machinery; it is not interchangeable with the main goal selector. Preserve selector identity when two instances register the same goal class.

The `newGoalRate` field/setter exists, but the inspected class references that field only from its constructor and setter. It is not an eligibility throttle in this `tick()` body. The actual reduced/full tick split is at `Mob.serverAiStep()`; see [AI-ARCHITECTURE.md](AI-ARCHITECTURE.md).

## Snapshot surface

The exact development class exposes `getAvailableGoals()`. A `WrappedGoal` exposes its goal object, priority, flags and running state. These support bounded registered/running snapshots with reference-instance tokens. Names alone cannot distinguish duplicate instances.

`lockedFlags` and `disabledFlags` are private fields in the inspected GoalSelector. They require an explicitly validated accessor/reflection capability to observe; lack of access must remain `NOT_EXPOSED`. A list of registered/running goals is not a record of all eligibility decisions or rejected candidates.

The actual development `Mob.goalSelector` and `Mob.targetSelector` fields are public final. This is verified for the captured Forge/userdev/access-transformed artifact, not a promise about other class stages or versions.

## Safe observation and timing

Do not invoke `canUse()`, `canContinueToUse()`, `start()`, `stop()`, or `tick()` from a snapshot adapter. Even an eligibility check can execute arbitrary MOD logic or consult random/stateful input.

Comparing running sets at two retained samples establishes a sampled transition interval. It cannot establish every intervening start/stop, interruption reason, exact transition tick or causal relation to a path. Exact lifecycle/eligibility events need an explicitly armed hook that observes the original invocation without replaying it.

Goal snapshots can expose state and execution. Candidate/evaluation availability, disabled/owner state, replacement evidence and eligibility trace must be declared independently.
