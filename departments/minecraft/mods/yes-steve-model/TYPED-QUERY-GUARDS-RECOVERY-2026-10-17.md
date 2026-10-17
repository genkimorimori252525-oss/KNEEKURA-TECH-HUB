# Typed query variable guards — 2026-10-17

## Fixed family and scope

The exact artifact contains 17 direct LambdaVariable subclasses with entity/item/
block type guards. This cohort captures their complete methods plus ContextVariable,
LambdaVariable and ContextBinding: 63 methods across 20 owners. A fresh class scan
reconciles the direct-subclass set; it does not claim to cover external subclasses
or dynamically generated code.

Artifact SHA-256: `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`.
Comparison source: YesSteveModel/YesSteveModel
`f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.
Primary static review only; independent semantic review NOT_RUN. No target/game
execution or new mapping promotion. Central mapping remains 669.

| Required Java instanceof target | Exact owner suffix |
|---|---|
| net/minecraft/world/entity/TamableAnimal | O0OooO0o0000O0OOoO000O0O |
| net/minecraft/world/entity/player/Player | O0o0OO0oO0o0o00oOoOOO0O0 |
| net/minecraft/world/level/block/state/BlockBehaviour | OOO00ooO0O000o0ooOoooO0o |
| net/minecraft/world/entity/projectile/AbstractArrow | OOO0O00OO000OOO0000OOoOO |
| net/minecraft/world/entity/Entity | OOOO00o000o00OoOOo0o0oOO |
| net/minecraft/world/entity/projectile/FishingHook | Oo00oo000oO00o000OOoO0oO |
| net/minecraft/client/player/AbstractClientPlayer | Oo00ooOO0O0o00OOO00oOO00 |
| net/minecraft/world/entity/projectile/Arrow | Oo0oO0oo000oOo0Oo00oOOOO |
| net/minecraft/world/entity/LivingEntity | OooOOo00Oo0OOo0oO0OO0OOO |
| net/minecraft/world/level/block/state/BlockState | o0OO000oOOO00O0OoOo0OOo0 |
| net/minecraft/world/item/ItemStack | o0OOooOo00oOo00oO0oooOoO |
| net/minecraft/client/player/LocalPlayer | o0Oo0ooOoOo0ooOOo0Ooo0O0 |
| net/minecraft/world/entity/projectile/ThrowableItemProjectile | oo00OO0oO0oOoo00o0OoOoOo |
| net/minecraft/world/entity/projectile/Projectile | oo0ooOO00ooO0ooOO0OOoOoO |
| net/minecraft/world/entity/Mob | ooOO0oo0o0OOoOoOO0oOo00O |
| net/minecraft/world/item/Item | ooo0oo00O0o00Oo0OO0o0oo0 |
| net/minecraft/world/level/block/Block | oooo0Ooo00oO0oOoo00ooO0o |

## Guard, callback and conversion are different stages

ContextVariable.evaluate(ExecutionContext) checks that evaluator.entity is an
IContext, then calls validateContext. If either fails it returns boxed Integer 0.
For a valid context it calls evaluate(IContext) and returns that raw Object.
There is no exception handler added around this path. Each typed subclass tests
context.entity against the exact class in the table; null fails these instanceof
checks. This is class-based validation, not a duck-type or registry-tag predicate.

LambdaVariable stores an IValueEvaluator and passes the IContext directly to its
eval method. It does not convert the callback result to float/boolean/string.
Generic LambdaVariable inherits ContextVariable's always-true context validator,
so it accepts an IContext whose underlying entity is null; that is distinct from
all 17 typed subclasses. Downstream typed numeric conversions happen separately.

Do not merge this invalid-variable result with ContextFunction's invalid-context
result: the former is Integer 0, while the latter is null. Nor does a passed type
guard guarantee a nonnull callback result or suppress exceptions thrown there.

## Registration and names

ContextBinding maps each typed registration method to construction of the matching
wrapper. function registers the supplied Function itself. Generic var constructs
LambdaVariable. getProperty performs a direct map lookup; getAllName exposes the
map's key set, not a defensive copied set. Re-registering a key uses map.put.
Name normalization in parser identifiers is a separate layer, not an operation
performed by this binding's direct getProperty body.

constValue treats String as a new StringExpression, Number as floatValue, Boolean
as 1f/0f, and other objects as themselves. This conversion of registered constants
does not mean variable callback results are narrowed the same way. Large numeric
constant precision and raw callback boxing must therefore remain distinct.

## Child-context implications

The guards inspect IContext.entity, not IContext.animatableEntity. A wrapped child
may pass a child entity type check while callbacks that explicitly inspect the
retained parent animatable still use that parent's capability or model. The
[child-context dossier](CHILD-CONTEXT-ARROW-RECOVERY-2026-10-17.md) records that
selective copy policy; this cohort does not add automatic retargeting.

LocalPlayerVariable means Java LocalPlayer instanceof. It does not itself check
a custom capability's isLocalPlayer flag. Item and ItemStack, and Block and
BlockState/BlockBehaviour, remain distinct target classes; the wrapper does not
implicitly unwrap stacks or convert state into a block.

## Verification and next seam

`tools/typed_query_guards_ysm_265.py` takes --jar, --source-root, --evidence, --out.
403 integrity checks passed; 23 mutated evidence fixtures were rejected, including
all 17 altered predicate types and a missing family entry. Complete direct-family
reconciliation is also checked against the JAR before auditing.

The counts describe snapshots/guards, not runtime test cases or completion percent.
The earlier fixed ten-cohort checkpoint is unchanged and does not include this
later cohort. Continue remaining YSM entity-specific callback sources and compare
actual predicate classes, state sources and units before reusing their names.
