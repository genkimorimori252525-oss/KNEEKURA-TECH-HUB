# Child context, projectile owner and arrow evaluation — 2026-10-17

## Scope

Primary static review of exact JAR SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, pinned source
YesSteveModel/YesSteveModel `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.
40 captured methods across MolangContext, selected evaluator methods and YSMBinding
include supporting context methods/registration constructor. No new central map
promotion; 669 unchanged. Independent semantic review NOT_RUN. No target/runtime,
network traffic or native implementation executed.

## Two different kinds of child creation

MolangContext.createChild wraps a new entity in a new MolangContext using its
private `(Object,MolangContext)` constructor. ExpressionEvaluatorImpl.createChild
instead creates a fresh evaluator with the supplied value as its entity. These
are different operations; the arrow evaluator does not automatically wrap every
raw entity value into an IContext or copy the parent's execution control state.

## MolangContext copy is selective, not live delegation

Exact owner `O0O00Oo0o0oO0oo0oO00OOoO`'s child constructor writes:

- new child entity at offset 6
- parent's animatable entity reference at 14
- parent's AnimationEvent at 22 and EntityModelData at 30
- parent's AnimationContext reference at 38
- parent's RandomSource at 46, MolangMemory at 54, global sound manager at 62

It does not copy controllerContext, debugSource or allowEmitting; absent later
writes their new-instance defaults are null/null/false. Nor does it directly
copy parent foreignStorage. Instead it tries the child's player, projectile or
vehicle capability and assigns that capability's public-variable storage in an
ifPresent callback. Missing capabilities and non-Entity children leave it null.
The child constructor does not require a nonnull child entity.

Copied references remain shared objects, but replacing a parent context field
later is not live delegation to the child's already copied field. temp/scoped
storage uses shared memory; contextStorage uses the copied animation context.
Public/foreign storage selection is distinct. Do not promise useful public
values merely because a storage reference exists: previous initialization
inventory found only null public-name initialization on its direct Java path.

## Query consequences under this exact constructor

A child context is not a complete switch to the child's animation/render state:
entity-specific queries see the new entity, while animatable/event/data and
animation context initially still originate from the parent. getUserFunction
also delegates through that retained animatable entity.

The copied animation context can keep anim_time available; the non-copied
controller context makes all/any completion queries use their absent-context
false default unless something subsequently sets it. Emission is initially
false and debug printing is disabled through null debugSource. This is a Java
field-copy consequence, not proof of every expression's final visible output.

## projectile_owner returns a wrapper, including a null owner

YSMBinding's registered callback invokes Projectile.getOwner at offset 10 and
IContext.createChild at 13. There is no owner-null test before wrapping. With the
captured MolangContext implementation, an absent projectile owner produces a
nonnull context whose entity is null, rather than returning Java null directly.
A later EntityVariable/EntityFunction guard may reject that entity; generic
context queries may still observe the retained parent state. This differs from
assuming the arrow operator always skips its RHS when a projectile lacks an owner.

## Arrow operator and control state

Evaluator owner `oo00Oo00o0ooooOooo0Oo0OO`, arrow evaluator method
`Ooooo0oooO0oooOOOoO0000O(ExpressionEvaluatorImpl,Expression,Expression)`:

1. Visit left once. Only a Java-null result skips right and returns null.
2. Create a fresh evaluator carrying the nonnull left value (call offset 16).
3. Visit right directly in that evaluator (24).
4. Copy the child's returnValue field to the parent (34→37), then return the
   right result. This assignment can also overwrite the parent with null.

It does not copy the child's control field, loop-depth or returnThrough counter
back; the new evaluator constructor starts its own counters. There is no local
exception handler/finally around the RHS visit and copy tail. Outer evaluation
error handling is a separate boundary. Raw non-IContext left values are not
silently converted by this createChild method.

## Verification and continuation

`tools/child_context_arrow_ysm_265.py` accepts --jar, --source-root, --evidence,
--out. 219 integrity checks passed; 9 corrupted fixtures rejected. The snapshot
includes complete supporting declarations/bootstrap records. These checks do
not execute the above conditional examples or independently review semantics.

Continue context variable/public binding reachability and typed query guard
coverage. Keep entity identity, animatable identity, shared storage and control
state separate in any reusable reconstruction; no fix is made to the upstream
copy policy based on its source FIXME comment.
