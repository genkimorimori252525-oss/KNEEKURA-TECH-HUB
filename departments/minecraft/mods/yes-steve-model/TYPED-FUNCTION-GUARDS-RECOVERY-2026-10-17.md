# Typed Molang function guards: complete direct abstract family

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Thirty declarations across ContextFunction and13 direct abstract subclasses, including one abstract declaration without Code. Existing captured common guards are retained as overlap anchors, not claimed as new mappings. The955-class declaration scan reconciles this bounded abstract subclass family, not all direct concrete functions or external subclasses.

## Context guard precedes the function body

ContextFunction counterpart `o0oOo0o000oOo00OO000OOoO` has final evaluate(ExecutionContext,ArgumentCollection). It reads the execution entity, tests IContext, dispatches validateContext, and only then invokes the typed eval body. Either failed gate returns null. It does not evaluate individual arguments on a rejected path. Argument creation and caller work before this method are separate; do not claim global suppression of all argument side effects.

The base validator always returns true. Each typed abstract subclass instead reads IContext.entity and performs exactly one instanceof test. Null underlying entities fail these typed guards, while a generic ContextFunction can accept an IContext with null underlying entity. There is no local exception handler around validation or eval. In particular an exception thrown by a context.entity implementation is not converted to a rejected type by this method.

## Exact targets

- O00OoOOOo0o0ooooo0OO0OOO: Mob
- O00o0Oo0O0oooOooOo0O0o00: LivingEntity
- O00oOoo00OOOO0Oo0oo00o0o: Arrow
- O0OO00o0OO000o00OOOoOO00: Item
- OO000oo0o000OooOoo00O0OO: Projectile
- OOOoo00ooO000oOOoO0OO000: AbstractClientPlayer
- o0000O00oo00oOOooO0oO0oO: ItemStack
- o000OOOo000O00o000O0ooo0: Block
- o0ooOO00oOoO000oooO00o0o: BlockBehaviour
- oOOooOO0O0OoOOoOO00ooO0o: AbstractArrow
- oo0000oOOoOo0OoOOOOoO0o0: TamableAnimal
- ooO00OOOOOo0oOoooO00oOoO: Entity
- ooO0oo0OOOoo0000O0OoooO0: LocalPlayer

The comparison source class named PlayerEntityFunction guards AbstractClientPlayer, not general server Player. BlockBehaviour is also distinct from BlockState. No tag, ownership, tame-state, alive-state, same-player identity or optional-mod availability test is implied by an instanceof class guard. Subclasses can supply additional checks in their own eval bodies, and a subclass can override the nonfinal validator; this family inventory is not a universal guarantee for every descendant.

## Relation to variable guards

[Typed query-variable guards](TYPED-QUERY-GUARDS-RECOVERY-2026-10-17.md) describe a different17-subclass family whose invalid context returns Integer0. Do not merge that failure value with these functions' null. In both cases successful validation does not force a particular numeric result or guarantee a nonnull callback result. Expression conversion, arity checks, emission permission and error handling belong to their specific callers/implementations.

## Verification

The companion auditor re-parses the exact artifact and compares declarations, instructions, handlers, bootstrap data and pinned source hashes. Its independent semantic-review status remains NOT_RUN. Target classes, Minecraft and optional integrations are not executed.
