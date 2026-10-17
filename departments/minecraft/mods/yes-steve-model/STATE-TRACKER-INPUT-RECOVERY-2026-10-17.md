# Entity-state tracker and Molang position-delta input

Primary static review; independent review NOT_RUN. Fixed artifact SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, source
candidate `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. 22 complete methods across
EntityStateTracker `oOooOOo00oOO0oO0O00O0O0o`, HumanoidStateTracker
`oo00oOO00o0OOo0oO0OOOO00`, and PositionDelta candidate
`ooO0O0ooo0O0OoooOOOOOoOO`. No runtime execution or central mapping promotion.

## Entity ticks and render ticks invalidate different caches

The final update(IFF) first compares lastEntityTickCount<entityTickCount. On true
it invokes updateEntityTickData, then stores the supplied count. Independently,
it compares lastRenderTick<renderTick; on true it invokes updateRenderTickData,
then stores renderTick. Both comparisons are strict. Equality/backward inputs
leave those paths untouched, and NaN fails the render comparison. No loop replays
missed ticks. Callback exceptions can prevent the corresponding last-marker write;
there is no finally and subclasses may have already mutated state.

Base entity-tick update clears the integer state set. Render-tick update computes
current-minus-last delta, updates interpolated position, then clears the main
animation-name cache. Thus the integer marks can survive multiple render updates
within an entity tick, while main-animation cache is render-update scoped. These
are tracker updates gated by AnimatableEntity.shouldTick, not a promise that every
displayed frame advances these caches.

Position sampling lerps entity previous/current xyz using the supplied partial
fraction. With a prior sample, positionDelta becomes current minus lastPosition;
without one it only stores lastPosition. Constructor/reset initialize delta to
Vec3.ZERO. This is displacement between accepted interpolated samples, not direct
velocity, network packet displacement or keyboard input. setEntity merely replaces
the entity reference without resetting previous position/markers/caches; callers
must decide whether reset is needed. No cross-entity artifact is demonstrated.

Reset clears the state set, markers, lastPosition, positionDelta and main cache.
setEntityTickState returns IntOpenHashSet.add, so duplicate marks produce the set's
boolean result rather than unconditional success. getPositionDelta and cache
getters directly return the stored references/values.

## Humanoid extension

Humanoid reset clears both hand-item references then calls base reset. Its render
update calls the base method before ImmersiveMelodiesCompat.updateMelodyProgress.
The melody-data object is created in construction and is not replaced by this
reset body. Hand access chooses main hand for equality with MAIN_HAND and offhand
otherwise; the setter stores supplied references without copying. External melody
integration and actual inventory mutation semantics are not validated here.

## Axis query

The PositionDelta evaluator converts argument0 to int, obtains the animatable's
tracker displacement, and uses tableswitch0..2 to return boxed Double xyz. Its
default branch returns null. The argument-size validator requires exactly1.
The evaluator itself does not divide by elapsed time or normalize displacement;
argument conversion, surrounding evaluator error handling and query registration
are distinct boundaries. Candidate identity was also located from the
QueryBinding position_delta construction reference; this dossier's complete
snapshot is the evaluator/tracker path, not a full binding-registration audit.

## Checks and continuation

129 static checks pass;15 missing/corrupt-evidence controls reject strict-boundary
changes, displacement sign/call changes, axis switch/default and arity changes.
Source identity is pinned but whole-artifact equivalence remains unproven.
Mapping669 is unchanged. Continue the speed/delta-time and directional movement
query consumers, especially unit conversions, zero-delta handling and distinction
between displacement-derived direction and physical/input state.
