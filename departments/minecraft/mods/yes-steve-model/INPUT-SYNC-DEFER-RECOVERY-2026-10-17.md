# Input observation, sync and defer boundaries — 2026-10-17

## Scope

Exact JAR SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`;
comparison source YesSteveModel/YesSteveModel
`f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.
35 methods across 11 owners cover input functions/event storage, sync function and
ordinary message handlers, defer recorder/reset and CustomPlayer sync enqueue.
Primary static review; independent semantic review NOT_RUN; map 669 unchanged.
No user keys/mouse state were polled, no messages sent, and no target code/game
was executed. This is behavior reconstruction, not a network security test.

## Input is gated cached event state

Keyboard/Mouse implement Function directly, not ContextFunction. They first call
InputCheckUtil.isInGame and return false before reading arguments when it fails.
The predicate rejects a client overlay, an open screen, an ungrabbed mouse, or an
inactive window. It is not merely a world/player-nonnull check.

Keyboard accepts >=1 arguments and evaluates integer key codes in order, returning
true at the first cached pressed key in range 32..348. Later expressions are not
evaluated after success. Mouse requires one argument and reads a cached button
in 0..7. Neither callback polls GLFW's live device state or requires allowEmitting.

ModInputEvent initializes arrays of length349 and8. Its handlers also require YSM
availability and isInGame before changing elements. PRESS sets true, RELEASE false;
other actions leave the cached value unchanged. Rejected-event returns do not
clear the arrays in these methods. Therefore a release occurring only during a
rejected state is not recorded by that handler; persistence until another update
is a conditional observation, not a reproduced stuck-key bug. Volatile array
references do not make every element a separately volatile field or prove all
cross-thread behavior.

## Sync routing and argument evaluation

Sync derives from PlayerEntityFunction, whose actual type predicate requires
AbstractClientPlayer, not arbitrary Player. With allowEmitting=false it returns
null before packing arguments. Normal branches:

- PlayerAnimatableCapability with a remote channel and LocalPlayer entity:
  pack arguments and submit EmitMolangSync.
- Same capability/channel but non-LocalPlayer: return null without packing,
  waiting for a later ordinary server-originated sync event.
- Without that channel path, a CustomPlayerEntity animatable triggers its local
  molangSync with packed arguments; other animatables do nothing here.

packArguments evaluates every argument as float in order. The function's arity
contract is size<=16 (zero is accepted); the pack loop does not independently
truncate to16. Do not mistake a parser-level count contract for a verified
transport authorization or universal input-validation guarantee.

## Ordinary message and event handoff

EmitMolangSync serializes count byte then floats. Its server-side handler requires
server reception and a nonnull sender, then enqueueWork broadcasts MolangSync
using that sender's entity ID and the argument list. MolangSync serializes entity
VarInt, count byte, then floats. This records ordinary shape/order; no traffic
was constructed, transmitted or exercised against a server.

The client handler enqueues a direct Minecraft.level.getEntity lookup followed by
capability access. Unlike DispatchServerDrivenProperty's earlier path, it does
not call EntityLoadEvent.executeOnEntity or cache for later availability in this
body. It has no local level/entity-null guard. Runtime dispatch failure handling
and actual entity timing are unverified; packetHandled is not successful execution.

CustomPlayerEntity.molangSync, when syncHandler exists, wraps handlers/args and
calls executeMolangExp with allowEmitting=true and pre=false. That API enqueues a
processor task; it is not an immediate invocation of every handler or a rendering
receipt. Keep message handling, task enqueue, task execution and visible effects
as different stages.

## Defer gate, name and replay order

Defer requires allowEmitting and a nonnull AnimationContext before reading the
first pooled-string argument. EMPTY names are ignored. Otherwise it calls
AnimationContext.defer(ctx,name,args,1) and returns null. It supplies no custom
arity validator, retaining Function's default acceptance; that does not add a
bounds check before raw argument0 access on the enabled path.

The exact recorder does NOT load or store its name parameter (local slot2): no
ILOAD_2 or indexed load of slot2 occurs. The first argument is a nonempty-key gate,
not a named handler selector in this implementation. The recorder increments a
defer counter, obtains/reuses a list sized to args.size()-1 and evaluates the
remaining argument values into it. It is not storing unevaluated expressions or
including the name in the recorded values. No rollback handler surrounds partial
argument capture.

AnimationContext.reset uses the animatable model's DEFER handler list. It visits
recorded groups in reverse order and handlers in forward order, temporarily sets
allowEmitting true, invokes the user functions, then clears emission/count/context
variables on its normal tail. There is no finally guarantee for that entire
sequence. The existing runtime-storage dossier covers call-frame cleanup; do not
extend a successful inner frame pop into whole-reset transactional semantics.

## Verification and continuation

`tools/input_sync_defer_ysm_265.py` accepts --jar, --source-root, --evidence, --out.
226 integrity checks passed; 16 corrupted fixtures rejected. Abstract/function
contracts and complete handlers are captured, but runtime behavior is not tested.

Continue remaining utility/noise/math/control functions, using the query catalog
to avoid assuming every registered name has equivalent arity, purity or emission
rules. Do not modify upstream behavior based on conditional static concerns.
