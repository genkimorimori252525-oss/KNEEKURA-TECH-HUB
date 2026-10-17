# AnimationPlayer clock and transition decisions — 2026-10-17

Status: primary static review; independent semantic review pending. No central map
additions. The existing AnimationControllerInstance role/source-divergence record
for owner OOOO0o0oo0o000oOOooOoOo0 is retained; AnimationPlayer is the pinned official
candidate counterpart, not a silently substituted original name.

Exact artifact: Zqooxsd2, SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`.
The dossier retains 50 complete method records across player, linear-transition
implementation/interface and two enums, plus six source records at f184eda.
The reviewed boundary is clock/state/load/reset/ending capture and transition units,
not every event executor or all point-generation semantics.

## PAUSE does not install a local frozen clock

The player has no pause argument: its process receives renderTicks, evaluator and
allowEmitting. getAnimTicks subtracts animTickOffset from renderTicks and calls
Math.max with zero. There is no pause-clock compensation using allowEmitting.
That boolean is forwarded to event-related helpers, not used as a local branch
around time computation or normal pose production.

Combined with the already-inspected coded controller, PAUSE calls this process with
emission false, then clears its point queues and suppresses queue enumeration.
It is therefore not correct to describe that Java path as simply not updating the
player. The actual time depends on renderTicks, offsets and state transitions;
this finding is not a runtime measurement or a guarantee about all external calls.

## State tests and boundary ordering

The process first installs its animation context and calculates the relative tick.

1. ENDING_TRANSITION at relative tick >=3 resets to idle before subsequent tests.
   The fixed 3.0F is visible in the exact instructions and pinned source constant.
2. RUNNING + PLAY_ONCE at tick >= animation length resets event keyframes, sets up
   ending transition, resets animation context and recalculates the tick.
3. IDLE resets context and tries to load next animation. Failure returns immediately;
   success sets offset=renderTicks and local tick=0, then selects beginning transition
   only when transition.length()>0, otherwise RUNNING.
4. Point queues reset before the following state-specific generation.
5. BEGINNING_TRANSITION generates and returns while tick<transition.length(). At
   equality or above, it subtracts transition length, adjusts offset and enters RUNNING.
6. RUNNING marks finished only when tick>animation length. LOOP then wraps by float
   remainder for positive length, otherwise sets tick zero, resets event keyframes
   and updates offset. HOLD_ON_LAST_FRAME clamps to length. Event execution then
   precedes runAnimation. PLAY_ONCE's >= guard is earlier, so the strict comparison
   here must not be substituted for it.
7. ENDING_TRANSITION passes a tick capped above at3 into ending-point generation,
   while animation context time uses the captured ending source tick divided by 20.

These are ordered float/JVM branches, not a simplified universal duration test.
NaN, malformed timing and arbitrary transition implementations are not made safe
by this pass. No method-local catch/finally makes the whole operation atomic.

## Loading, repeated selection and reset boundaries

setAnimation(null) calls reset. Otherwise an equal cached name plus identical loop
override returns early. For a new selection, resetToIdle precedes storing the new
lastSetAnim pair and looking up the animation. A missing lookup returns after that
pair is stored: repeating the same name/override can hit the early-return path until
that selection state is cleared, rather than necessarily retrying a newly available
asset. Caller reload behavior and actual missing-asset scenarios remain untested.

loadNextAnim consumes the pending pair, installs animation/loop state and marks
finished false. It activates only queues found by pooled bone name. Its
`disableEndingTransition` argument is true when that animation's **scale keyframe
list is nonempty**; it is a queue-wide flag supplied to later axis-ending-point
construction, not a separately stored rotation/position flag. No runtime visual
impact is inferred without joining the point/processor paths.

resetToIdle's body runs only when state is not already IDLE. It resets sound execution,
nulls executors, deactivates and clears active queues, clears current animation and
marks finished. reset additionally clears cached/next selection before calling it;
clear also clears the model queue map. indicateReload only clears cached selection.
Do not substitute one of these operations for another based on their names.

## Ending transition captures previously evaluated point samples

setupEndingTransition acts only from RUNNING or BEGINNING_TRANSITION. For each axis,
it copies a new Vector3f only when both the stored point and that point's
lastLerpResult are nonnull. It does not freshly evaluate missing samples or copy the
current IBone transform as a fallback. It updates tick offset, saves a running source tick capped above at animation length (or zero from beginning), marks finished and enters ENDING.

This connects the earlier AnimationPoint observation cache to an actual consumer.
The transition-destination accessor deliberately bypasses cache/interpolation, so
not every point-query path populates that cache. Missing player-level capture is
not proof of a visual defect: the separately reviewed AnimationProcessor also has
its own snapshot tail-reset path, and timing/caller order still matters.

## Transition units must not be silently normalized

LinearBlendTransition stores constructor input multiplied by 20. Its length getter
returns that stored float; get(tick) divides by it except that either signed zero
length returns 1. The player's getBeginningTransitionLength then multiplies the
interface length by 20 again. Its exact instruction is fmul, not fdiv.

For the specific linear implementation constructed with 1.0F, the local arithmetic
chain therefore gives 20.0F from transition.length and 400.0F from the player getter.
Do not assume the player getter returns the original constructor input. The coded
setter compares that getter to its requested value before replacing the transition.
This observed round-trip/unit discrepancy is retained for caller review; it is not
an authorized fix, a runtime performance conclusion or proof of intended units.
Other transition implementations can have different length/startNew behavior.
The interface's default startNew simply returns this, not a guaranteed fresh copy.

## Context cleanup and event limits

process installs animation context and has ordinary early returns. finalizeAnimationContext
separately installs context, calls reset and clears context; it too has no local
finally. resetEventKeyframes sets context time to the animation endpoint, executes
remaining instruction frames if present, resets that executor, and resets sound
execution. executeEventKeyframes orders sound before instruction execution when
present. Whether flags suppress all effects and whether callbacks mutate state
require their own executor/caller evidence.

## Verification and continuation

278 strict checks and 18 corruption controls passed. They enforce all 50 method identities,
five declarations/bootstrap records, six pinned source records and actual source
bytes/revision. Mutations cover boundary strictness, loop remainder, clock max/subtract,
transition-unit factors, zero-duration behavior, enum names, invented cleanup and
missing evidence. Target Java/JNI/game execution did not run. Independent semantic
review remains pending, so no new central map rows are added here.

```bash
python tools/animation_player_clock_ysm_265.py --jar /absolute/path/ysm.jar \
  --source-root /absolute/path/to/pinned/source \
  --evidence ANIMATION-PLAYER-CLOCK-EVIDENCE-2026-10-17.json \
  --out /tmp/ysm-player-clock-audit.json
```

Continue the exact point producers and Bedrock controller's activation/transition
aggregation to test the beginning-point homogeneity assumption. Then trace Java
schedule/wait/commit ownership. Preserve the native/runtime boundary and do not
stop the overall research at this checkpoint.
