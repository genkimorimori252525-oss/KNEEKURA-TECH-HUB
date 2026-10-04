# Brain system — Minecraft 1.20.1 ANCHOR

Evidence: `Brain`, `Sensor`, `Behavior`, `BehaviorControl`, and `ExpirableValue` in [the exact bytecode ledger](ANCHOR-BYTECODE-LEDGER-2026-10-03.json).

The additive [Goal / Brain member ledger](GOAL-BRAIN-BYTECODE-LEDGER-2026-10-04.json) retains exact same-artifact method/field descriptors, class/disassembly hashes and private line locators for the required types and helpers. The [coverage record](GOAL-BRAIN-RESEARCH-2026-10-04.md) distinguishes method-body research, current adapter capabilities and remaining integrated runtime evidence. Claims here refer to Forge 47.2.0 resolved-userdev bytes, not all loaded MOD implementations.

## Registered memories and expiry

Brain stores registered `MemoryModuleType` keys with optional `ExpirableValue` values. Registered-but-empty and unregistered are different states.

`getMemory(type)` throws `IllegalStateException` for an unregistered key. A generic adapter must inspect the registered map or use a verified registration-aware read; it must not issue an arbitrary list of memory getters against every Mob.

`getMemories()` returns the underlying map in the captured development class. Treat it as read-only and snapshot bounded entries. Each present `ExpirableValue` exposes `getValue()`, `getTimeToLive()` and `canExpire()`; reading must not call its `tick()`.

`forgetOutdatedMemories()` checks whether the retained TTL has expired and erases that memory, then ticks the expirable object. `ExpirableValue.hasExpired()` checks TTL <= 0. The observer records the actual retained TTL and whether it can expire; it does not recompute a guessed expiry from wall time.

Unknown/custom memory values must use a declared bounded representation. Do not call arbitrary object `toString()`, traverse arbitrary object graphs, or describe an unsupported custom value as empty. Entity references, block positions, known Walk/Look targets and known Path values need typed encoders with exact identity.

`MemoryModuleType` is a registry-backed key, not a decision or value. Its constructor maps an optional value codec through `ExpirableValue.codec`; `getCodec()` returns that optional wrapped codec. A key without a codec can still be registered in a Brain and used at runtime. Codec availability does not establish a current value, its cause, or complete persistence of arbitrary custom objects.

| Registered map state | `REGISTERED` | `VALUE_PRESENT` | `VALUE_ABSENT` |
| --- | --- | --- | --- |
| No key | false | false | false |
| Key with empty Optional | true | false | true |
| Key with present Optional | true | true | false |

This is the exact `Brain.checkMemory(MemoryModuleType, MemoryStatus)Z` test. `setMemoryInternal` ignores unregistered keys. For a registered key, a present value whose payload is an empty Collection is erased; other values replace its Optional. `eraseMemory` and `clearMemories` retain registration and store empty Optionals. `getMemoryInternal` returns null for an unregistered key in this artifact, whereas `getMemory` throws; neither result may be silently normalized to registered-but-empty.

`ExpirableValue.of(value)` uses `Long.MAX_VALUE` for non-expiring storage. `canExpire()` is a comparison with that sentinel; `tick()` decrements only expiring TTLs. Expiry is checked before the decrement in each Brain tick: a TTL of one becomes zero in that pass and is erased at a subsequent expiry pass if nothing else removes/replaces it. This is Brain-call cadence, not elapsed wall-clock time.

## Sensor and activity cadence

`Sensor.tick()` decrements its counter, resets it to the configured scan rate when due, and calls the original sensor's `doTick()`. Counter/readable-memory state is not the sensor's full candidate population. Never call the sensor again to produce an observation.

`Brain.tick()` orders memory expiry, sensors, behavior starts and running behavior ticks. Activity requirements use registered memory status and configured behavior/activity structures.

`updateActivityFromSchedule(dayTime, gameTime)` returns while `gameTime - lastScheduleUpdate <= 20`; when due, it records the update time, queries the schedule at `dayTime % 24000`, and attempts an activity change if needed. This method's cadence is distinct from every Brain tick.

Public snapshot surfaces include active activities, active non-core activity and running behaviors. Core/default activity and Sensor instances are private in the captured class and need separately declared access capability. No adapter infers an unexposed core/default activity from its absence in the non-core getter.

`SensorType.create()` calls its stored supplier. The Brain constructor creates the configured sensors, then registers their `requires()` memory keys as empty, in addition to explicitly supplied keys; it finally applies supplied initial memories. Sensor construction, factories and `requires()` can be MOD code and must not be repeated by an observer. The base Sensor's default scan rate is 20; its initial counter comes from `RANDOM.nextInt(scanRate)`. A `Sensor.tick` invocation can return without a scan. The scan hook and tick count are different facts.

`Activity` stores a name and cached name hash, is registered in the Activity registry, and compares equality by exact class and name. `Schedule` stores Activity-to-Timeline entries in a HashMap. `getActivityAt(time)` chooses the entry with greatest `Timeline.getValueAt(time)`, or IDLE for an empty map. Equal scores have no explicit activity-priority tie rule in this body; do not invent one from names or registry order.

Timeline keyframes are sorted by timestamp; a later insertion at the same timestamp replaces the earlier entry. `getValueAt` returns a step value, not an interpolation. If time moves before the cached keyframe it restarts scanning from zero with the last keyframe's value as the initial fallback. Empty timelines return zero. The getter writes `previousIndex` while scanning. Calling Schedule/Timeline getters merely to reconstruct a decision would execute this stateful query again; record an original result or bounded retained state instead.

## Priority buckets and activity transitions

The Brain constructor creates a TreeMap for numeric priority buckets. Registration places each `(priority, BehaviorControl)` in a per-priority HashMap keyed by Activity, with a LinkedHashSet for that activity's behaviors. Start attempts traverse ascending numeric priority, then the inner activity map, then that registered set. This is not the GoalSelector flag-lock/replacement protocol; no exclusive winner or flag ownership follows from a priority bucket. Ordering between different activities in the same bucket is not a stable sorted order supplied by this implementation.

The overload `addActivity(activity, startingPriority, behaviors)` creates incrementing priorities for successive entries via `createPriorityPairs`; it does not put all entries into the same bucket. Activity registration also stores its required `(memory key, status)` pairs and optional keys to erase when stopped. `activityRequirementsAreMet` returns false for an activity with no requirements entry, otherwise requires every pair to pass `checkMemory` (an empty registered requirements set passes).

`setActiveActivityIfPossible` selects the requested activity if its requirements pass, otherwise calls `useDefaultActivity`. That fallback directly selects the configured default; it does not perform another requirements test. `setActiveActivityToFirstValid(list)` selects the first passing entry; if none passes it leaves the active set unchanged.

On `setActiveActivity`, an already active requested activity causes no change. Otherwise it erases configured memories of previously active activities other than the requested activity, clears the active set, adds core activities and then the requested activity. This operation does **not** invoke `stopAll` or each behavior's `doStop`. `setCoreActivities` and `setDefaultActivity` assign their fields; the core setter alone does not rebuild the current active set. Keep configured core/default, active set, memory erasure and Behavior status separate.

`Brain.tick` tries to start STOPPED behaviors only from currently active activities. Afterwards `getRunningBehaviors()` collects RUNNING controls across **all** registered buckets/activities, without an active-activity filter, and `tickEachRunningBehavior` calls their `tickOrStop` using server game time. A just-started behavior can therefore be ticked or stopped later in the same Brain tick. Switching activity alone does not prove that all former behaviors have stopped. `stopAll` explicitly calls `doStop` on the collected running controls; `removeAllBehaviors` only clears the registration map in the inspected body.

## Behavior state

BehaviorControl is the scheduler interface; Behavior implements a status/start/end-time lifecycle and memory requirements. A snapshot may record running class/reference identity. A sampled set difference is a derived transition interval, not an exact lifecycle callback or explanation of why a behavior ran.

`BehaviorControl` declares `getStatus`, `tryStart`, `tickOrStop`, `doStop` and `debugString`; it supplies no default lifecycle bodies. An implementation need not extend Behavior. [R49](ORIGINAL-INDEPENDENT-CONTROL-RETURN-2026-10-04.md) now records original normal lifecycle returns for OneShot and GateBehavior (including inherited Gate bodies such as RunOne), in addition to the existing base Behavior hooks. Arbitrary implementations or overridden bodies that bypass these bases remain outside that coverage. Generic BehaviorBuilder$1 class identity does not identify a concrete trigger, and Gate parent success is not a child-success result.

| Base Behavior member | Inspected body |
| --- | --- |
| Constructors | Initial STOPPED status, retained entry-condition map and duration bounds. The one-map constructor uses 60 for both duration bounds. |
| `tryStart(ServerLevel, LivingEntity, J)Z` | Checks required memories first, then extra start conditions. On success sets RUNNING, draws `min + random.nextInt(max + 1 - min)`, sets `endTimestamp = supplied time + duration`, calls start and returns true. The scheduler tests STOPPED before calling; this method itself has no status guard. |
| `hasRequiredMemories` | Tests each entry condition through the entity's Brain `checkMemory`. It does not search sensor candidates. |
| `tickOrStop` | If not timed out and `canStillUse` passes, calls tick; otherwise calls doStop. Timeout short-circuits the continuation call. |
| `timedOut(J)Z` | Strict `time > endTimestamp`, not equality. |
| `doStop` | Sets STOPPED before stop, with no idempotence guard; differs from WrappedGoal.stop. |
| Base defaults | start/tick/stop do nothing; extra start conditions return true; `canStillUse` returns false. Subclasses determine actual work and continuation. |

These normal-path facts do not prove a successful callback if original MOD code throws, a rejected condition's exact reason, or that a result was achieved. In particular a base/default continuation can stop an accepted start during the same Brain tick, which a coarser running-state snapshot can miss.

Vanilla Villager's inspected `customServerAiStep()` explicitly calls Brain.tick. Other entities require their own call-site evidence; inherited Brain existence alone does not establish a Brain-driven Mob.

Keep key memories, active/running state, navigation and resulting motion as separate facts. WalkTarget, LookTarget, AttackTarget and PATH can be linked spatially where typed values are exposed; temporal proximity is not automatically causal.

## Target representation and present observation limits

| Memory key | Declared value and exact representation boundary |
| --- | --- |
| `WALK_TARGET` | WalkTarget retains a PositionTracker, speed modifier and close-enough distance. The BlockPos constructor uses BlockPosTracker; its Vec3 constructor first converts to BlockPos (fractional location is lost); its Entity constructor uses EntityTracker with eye-height tracking false. A custom tracker can be supplied directly. |
| `LOOK_TARGET` | PositionTracker interface, which declares currentPosition, currentBlockPosition and isVisibleBy. It is not always a fixed block, an entity, or a Vanilla implementation. |
| `ATTACK_TARGET` | LivingEntity reference; preserve identity and observation time rather than just a class name. It is separate from Mob's target field. |
| `PATH` | Path reference; its retained data and Navigation's currently adopted path need independent identity/provenance. A stored Path is not proof of Navigation adoption or movement success. |

Exact BlockPosTracker copies the immutable block and its center when constructed from BlockPos; when constructed directly from Vec3 it retains that exact vector plus its containing block. EntityTracker retains an entity reference and reads its current position, optionally adding eye height; its currentBlockPosition reads the entity's block position. These are query-time positions, not an immutable historical target. `EntityTracker.isVisibleBy` additionally consults a Brain memory/visible-entity container and is not a visibility probe to replay from a snapshot.

[R48 cached typed-memory observation](TYPED-BRAIN-MEMORY-2026-10-04.md) now encodes exact WalkTarget, BlockPosTracker, EntityTracker and Path cached fields, plus base Entity cached identity/position fields, under `TYPED_CACHED_MEMORY_V1`. Arbitrary tracker/WalkTarget/Path subclasses and unsupported memory containers remain `NOT_EXPOSED`; no tracker, visibility, Schedule, eligibility or AI getter is replayed. Cached entity coordinates are sampled fields rather than a second query of tracker position. PATH/Navigation reference equality is scoped to one snapshot and does not prove adoption or movement success. The separate TLM-specific public-memory getter path cannot establish safe arbitrary-tracker coverage for the generic adapter.
