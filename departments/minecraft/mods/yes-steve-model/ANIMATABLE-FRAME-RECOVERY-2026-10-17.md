# Animatable frame gates, seek clock and model lifecycle

Primary static review only; independent review NOT_RUN. Artifact SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, official
source candidate `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Whole-source
identity is NOT_ESTABLISHED; historical divergence retained. No runtime execution,
central mapping additions, renderer-thread safety assertion or frame-rate benchmark.

## Scope

Complete snapshots: AnimatableEntity `o0000OoOooO0oo0o0oooo0Oo` (47 methods),
RateLimiter `ooo000oO0ooo0oo0o00OOOoO` (5), AnimationEvent
`OO00O0o0OooOOOo00OO00o00` (13), AnimationData `Oo0OO00OooO0o0OOOo0oO0Oo`
(7). Abstract declarations are retained without fabricated Code bodies. Four
pinned source files supply candidate semantic labels; complete operands, class
interfaces/fields/methods, handlers and bootstrap records are retained.

## Two time domains and monotonic frame handling

AnimationEvent initially constructs renderTicks from entity tick count plus the
actual partial tick. Animatable updateAnimation(FZ) keeps requested partial tick
separate: exactly 1 selects Minecraft's frame time (53→60); other values are
passed through. Preview instances use the client tick supplier. Entity pose
interpolation still uses the requested partial tick. Do not conflate these clocks.

Animatable tick reads event.renderTicks, computes mutableRender as the inverse of
isImmutableRender, then compares frameTime > lastFrameTime (`fcmpl`, `ifle`,25–26).
Only a strictly newer frame clears currentFrameTicked/currentFrameShouldTick,
updates lastFrameTime and rate limit, transfers currentFrameRendered to
lastFrameRendered, then clears currentFrameRendered. Equal/backwards inputs use
lastFrameTime (71–75). For ordinary finite timestamps this prevents backwards
seek progression; malformed infinities/NaN are not validated here.

AnimationData startTick=-1 is initialized on first use. Otherwise positive
currentTick-lastTick advances lastTick and seekTime (127–147); nonpositive deltas
do not. event.renderTicks is then overwritten with seekTime at155. Controllers
therefore receive the accumulated animation timeline, not the initial world tick
sum. This time update occurs before the processor-empty gate at162–165.

## Rate request, state tick and pose update are separate decisions

When the processor is nonempty:

    currentFrameShouldTick |= limiter.request(seekTime / 20)
    shouldUpdate = (currentFrameShouldTick && !currentFrameTicked)
                   || lastMutableRender || mutableRender
    shouldTick = (!mutableRender || (seekTime == 0 && !currentFrameTicked))
                 && currentFrameShouldTick && !currentFrameTicked

The OR assignment is bytecode `ior`188: rateLimiter.request is evaluated on every
entry to this block, not short-circuited when the flag is already true.
recoverLastCodedAnimation runs before the shouldUpdate gate. If shouldUpdate,
shouldTick first sets currentFrameTicked=true (286–287), then updates stateTracker.
Physics update follows even when shouldTick is false, then preAnimationSetup,
processor.tickAnimation, postAnimationSetup, lastMutableRender assignment.
codeAnimation runs after this gate on every nonempty-model invocation, receiving
shouldUpdate; lastFrameUpdated is stored last. No finally protects these steps:
a throwing downstream call may leave currentFrameTicked already set, and skip
later bookkeeping. This is static ordering, not a demonstrated runtime exception.

Joined with the earlier processor dossier, shouldTick=false does not mean every
operation is skipped: processor task queues and snapshot commits have their own
ordering outside its controller-process gate. Mutable-render pose restoration is
also distinct from a new controller state tick. No asynchronous task creation or
wait is visible in this base tick body; external callers/overrides remain open.

## Rate policy and limiter arithmetic

Frame-rate policy applies distance/offscreen limits only when local player is
nonnull, differs from this entity, and its position is not exactly the origin.
Within that path, lastFrameRendered=false returns10; otherwise distance>64
returns30, else distance>40 returns60. Equality64 falls into the >40 case; equality
40 falls back to the client refresh-rate supplier. These are requested update
limits, not measured FPS, and the supplier's/configuration range is not proven.
The new-frame call sets the limit before transferring currentFrameRendered into
lastFrameRendered; this ordering uses the previous stored flag for that call.

RateLimiter uses float interval=1/limit. It does not validate zero/negative limits
or normalize time. request adds time-lastRequestTime, records time, rejects only
aggregate<interval, otherwise keeps aggregate%interval and returns true. Equality
passes, and a long gap produces one true result rather than a catch-up loop.
Constructor aggregate=1 differs from reset aggregate=interval; reset clears last
request time to0. Division/remainder retain Java float exceptional-value behavior;
no actual bad-input runtime behavior is claimed here.

## Model reset/reload is ordered, not transactional

resetGeoModel clears current model/events, processor model, physics, limiter,
manager and state tracker, then frame flags/timeline and coded state map. The
base initialize flag is not reset by that body. loadGeoModel invokes reset first,
constructs GeoModelState, installs handlers, calls setup-controller hook, loads
processor model, then onLoadGeoModel. reload saves the model and handler references,
resets, then calls loadGeoModel which resets again. This double virtual reset is
present on the base ordinary path (reload21, load1); subclasses may override and
must be investigated before interpreting side effects. No rollback or finally.

## Evidence checks and continuation

383 fixed-artifact/source/declaration/method checks passed;19 malformed-evidence
controls rejected. See ANIMATABLE-FRAME-VERIFICATION and
`tools/animatable_frame_ysm_265.py`. These are evidence-integrity regressions,
not model behavior tests or independent semantic approval. The mapping remains669.

Next: find actual updateAnimation callers and subclass overrides, especially
mutable renders, model reload and possible Java task scheduling. Keep any thread
ownership conclusions bounded by those call sites rather than this base class.
