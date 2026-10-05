# Goal system — Minecraft 1.20.1 ANCHOR

Evidence: `Goal`, `WrappedGoal`, `GoalSelector`, and `Mob` in [the exact bytecode ledger](ANCHOR-BYTECODE-LEDGER-2026-10-03.json).

The additive [Goal / Brain member ledger](GOAL-BRAIN-BYTECODE-LEDGER-2026-10-04.json) verifies the same JAR, Foundation Map, class identities and JDK provider. It adds method/field descriptors, private disassembly line locators and slice hashes. These are exact Forge 47.2.0 resolved-userdev bytes, not loaded post-Mixin bytes or proof of every MOD subclass. The [coverage record](GOAL-BRAIN-RESEARCH-2026-10-04.md) maps the original B2/B3 requirements to these explanations.

## Base Goal and wrapper contracts

| Member | Inspected body |
| --- | --- |
| `Goal.canUse()Z` | Abstract; the concrete goal supplies eligibility. |
| `Goal.canContinueToUse()Z` | Calls the same object's virtual `canUse()` and returns it. A continuation callback can therefore execute eligibility logic again in normal gameplay. |
| `Goal.isInterruptable()Z` | Returns true by default. A subclass can override it. |
| `Goal.start/stop/tick()V` | Base bodies do nothing. Concrete goal bodies determine effects. |
| `Goal.requiresUpdateEveryTick()Z` | Returns false by default. |
| `Goal.adjustedTickDelay(I)I` | Returns the argument when every-tick updates are required; otherwise delegates to `reducedTickDelay`. That helper calls `Mth.positiveCeilDiv(argument, 2)`; for positive delays this rounds half the delay upward. It does not schedule eligibility by itself. |
| `Goal.setFlags(EnumSet)V` / `getFlags()EnumSet` | The constructor creates an empty EnumSet. The setter clears that owned set and adds the input elements; the getter returns the owned mutable set. It is not an immutable snapshot. |

`WrappedGoal` retains a goal reference and numeric priority. Eligibility, continuation, interruptibility, every-tick requirement, adjusted delay, flags and ticks delegate to that reference. `start()` returns immediately if already running; otherwise it sets its running field true **before** calling the goal's start. `stop()` returns immediately if already stopped; otherwise it sets the field false **before** calling the goal's stop. Repeated wrapper calls therefore do not repeat the delegated lifecycle body on the normal path. Neither body rolls the field back if the delegated call throws. A wrapper's running flag alone does not prove that the delegated call returned successfully.

## Flags and ownership

The inspected `Goal.Flag` values are `MOVE`, `LOOK`, `JUMP`, and `TARGET`. The selector owns one `lockedFlags` map and one disabled EnumSet per selector instance. It stores available goals in a LinkedHashSet; the update loop uses that iteration order rather than globally sorting by priority.

`goalContainsAnyFlags` is an intersection test. `goalCanBeReplacedForAllFlags` requires every requested flag's current owner to accept replacement. An unowned flag uses the `NO_GOAL` sentinel, whose priority is `Integer.MAX_VALUE`, wrapped base goal cannot start through `canUse()`, and overridden `isRunning()` always returns false. This is a scheduler placeholder, not an observed active goal. Empty requested flags make the all-flags test true; they do not automatically make `canUse()` true.

`disableControlFlag(flag)` adds to the disabled set; `enableControlFlag(flag)` removes from it. `setControlFlag(flag, true)` enables it. These methods do not immediately call a running goal's stop. Cleanup in a subsequent full selector tick applies the disabled check. The running-only tick does not perform cleanup, eligibility or flag replacement.

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

At that caller, sensing precedes both selectors, and `targetSelector` precedes `goalSelector` on both branches. When entity `tickCount > 1` and `(server tick count + entity ID) % 2 != 0`, each receives `tickRunningGoals(false)`. Otherwise each receives a full `tick()`. The running-only helper ticks a running wrapper only when its boolean argument is true **or** the delegated goal requires every-tick updates. Navigation follows the selectors, then custom server AI, move/look/jump controls and debug packets. This is a source-established call order; it is not a causal explanation of a retained movement sample.

## Snapshot surface

The exact development class exposes `getAvailableGoals()`. A `WrappedGoal` exposes its goal object, priority, flags and running state. These support bounded registered/running snapshots with reference-instance tokens. Names alone cannot distinguish duplicate instances.

`lockedFlags` and `disabledFlags` are private fields in the inspected GoalSelector. They require an explicitly validated accessor/reflection capability to observe; lack of access must remain `NOT_EXPOSED`. A list of registered/running goals is not a record of all eligibility decisions or rejected candidates.

The actual development `Mob.goalSelector` and `Mob.targetSelector` fields are public final. This is verified for the captured Forge/userdev/access-transformed artifact, not a promise about other class stages or versions.

## Safe observation and timing

Do not invoke `canUse()`, `canContinueToUse()`, `start()`, `stop()`, or `tick()` from a snapshot adapter. Even an eligibility check can execute arbitrary MOD logic or consult random/stateful input.

Comparing running sets at two retained samples establishes a sampled transition interval. It cannot establish every intervening start/stop, interruption reason, exact transition tick or causal relation to a path. Exact lifecycle/eligibility events need an explicitly armed hook that observes the original invocation without replaying it.

Goal snapshots can expose state and execution. Candidate/evaluation availability, disabled/owner state, replacement evidence and eligibility trace must be declared independently.
