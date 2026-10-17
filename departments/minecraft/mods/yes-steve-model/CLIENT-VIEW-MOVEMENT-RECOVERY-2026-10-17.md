# First-person background and movement-driven animation stop

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.15 declarations/two owners,91 integrity checks/eight negative controls, plus exact CLIENT subscriber/method annotations. No Forge event delivery, native render, input injection, network send or game execution.

## Background deduplication is an early latch

RenderFirstPlayerBackground `O000O0O00ooo000O0oOOoo00` resets its single static already-rendered flag only on an available-mod RenderLevelStageEvent whose stage is AFTER_CUTOUT_BLOCKS. The hand handler first checks availability, self-model/self-hands disable settings, local player and the flag. It sets the flag true BEFORE capability lookup, initialized/enabled checks, model/background-feature checks or the cancellable SpecialPlayerRenderEvent.

A missing capability, ineligible model or later cancellation therefore still consumes this local latch until the observed reset path. It is not keyed by hand/player/frame number, and the method does not independently prove every external render cycle reaches that reset stage. No actual missing/double rendering is claimed. The handler does not call RenderHandEvent.setCanceled; ordinary arm replacement is a separate path.

## Direct background submission differs from animated arm rendering

The capability callback requires initialized/enabled, a nonnull model and armModel.hasFirstPersonBackground. It obtains the player renderer, then posts a newly constructed SpecialPlayerRenderEvent. It does not retain that event or read its textureOverride field afterward. It instead reads texture location/index from the capability after the post. Listeners might mutate other state, so this is narrower than claiming every possible texture change is ignored.

A CustomTranslucentRenderType buffer is acquired before the renderer-null branch. The renderer object is only a nonnull gate here; this handler submits directly to the static NativeRenderer wrapper instead of invoking the ordinary player-render method. It passes the arm geometry, that geometry's retained initialState array, null output state, capability texture index, literal mode3 (BACKGROUND), event light, NO_OVERLAY and RGBA1.

There is no local updateAnimation call or live-bone-state substitution in this handler. The initialState getter returns a shared array, not a newly copied immutable pose. Actual native interpretation remains opaque. [Animated first-person arm rendering](FIRST-PERSON-RENDER-REGISTRY-RECOVERY-2026-10-17.md) has different mode/state/update semantics and must not be substituted for this background branch.

## Pose operations

On the submission path it pushes pose, optionally applies its bob helper, translates(0,-1.5,0), calls the native wrapper and pops pose on normal completion. No local finally is present. The bob helper computes walkDelta=walkDist-walkDistO, phase=-(walkDist+walkDelta*partialTick), and bob=Mth.lerp(partialTick,oBob,bob). It applies:
- translationX=-sin(phase*pi)*bob*0.5; translationY=abs(cos(phase*pi)*bob); Z0
- negative-Z-axis rotation in degrees: sin(phase*pi)*bob*3
- negative-X-axis rotation in degrees: abs(cos(phase*pi-0.2)*bob)*5

These are inspected float calculations and external PoseStack/Axis calls, not measured camera motion. Pose-stack cleanup on an escaping exception is not established by the normal pop.

## Movement input and extra-animation lock

PlayerMoveEvent `oOoo0O0OO0OOOOo0O00OOooO` toggles one static lock when an available-mod key event has action1 (press) and matches the roulette-lock key/scancode. Release/repeat actions do not toggle through that branch. The public switchLock helper toggles without its own availability test; isLocked reads the field. This class has no session-specific reset method beyond static initialization.

Client-tick handling requires availability, END phase, unlocked state and a local player. Movement is input intent, not observed world displacement: nonnull Input and either abs(leftImpulse)>float1e-5, abs(forwardImpulse)>float1e-5, jumping or shiftKeyDown. Equality to the threshold is false. Null Input is false. The helper reads Input fields rather than only key events, so its event source differs from the lock toggle.

For movement it looks up the capability; only while extra animation is playing does the callback invoke stopExtraAnimation. It then checks remote-channel presence and, if present, constructs the stop message and calls sendToServer. Local stop precedes that send call, with no local rollback/finally. A channel-presence predicate is not proof a packet was delivered. The callback adds no separate initialized/enabled check of its own.

## Reuse boundaries

Keep early latches, actual draw completion, event overrides, shared initial state, input intent, local state changes and remote notification separate. This connects existing renderer/input semantics without replacing upstream behavior or asserting external event order.
