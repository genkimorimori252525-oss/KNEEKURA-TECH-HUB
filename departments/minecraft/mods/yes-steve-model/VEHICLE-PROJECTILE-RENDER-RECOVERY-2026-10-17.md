# Vehicle and projectile render entries

PRIMARY_STATIC_REVIEW_ONLY. Exact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source comparison `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.26 captured declarations across concrete vehicle/projectile renderers and their two Java bases;153 integrity checks/9 negative controls. No independent semantic review, central-map promotion, runtime or GPU execution.

## Outer visibility gates precede model work

CustomVehicleRenderer `oo00OO0OO0o000oo0oOOoo0O` and CustomProjectileRenderer `O0Oo000OO0O00oooO00Oo0OO` both return when the client player is null or entity.isInvisibleTo(player) is true. These gates precede capability lookup and checkModelUpdate. A missing capability also means no callback/render call. Their callbacks checkModelUpdate then invoke the base animatable render overload. Their texture getters independently use capability texture or the missing-texture location.

The base can choose glowing outlines, but that does not bypass the concrete entry's earlier invisibility return. A direct call to the animatable base overload is a different path. No replacement registration or upstream caller decision is proven merely by having these classes.

## Different boolean render guards

GeoEntityRenderer `oOoOOO0OOOoo000O0o0oo0OO` and GeoProjectilesRenderer `Oo00o0oOoo00O00ooooOo0OO` first updateAnimation, then require nonnull event/local player for the custom body. They read loaded model without a separate local null guard, choose body visibility and glowing, and query model translucency at index0. Their render calls also pass texture index0.

The vehicle base's bytecode89..101 implements renderType!=null OR bodyVisible OR glowing. The projectile base's92..104 implements renderType!=null AND(bodyVisible OR glowing). Keep these distinct. The previously reviewed default render-type factory normally correlates visibility/glowing and nonnull type; a differing override could expose the guard difference. This is not evidence of an observed null-type failure or justification for a patch.

The base tails still call EntityRenderer.render after a null animation event/local player or skipped body on ordinary return. Concrete outer early returns do not reach that base tail. No SpecialPlayerRenderEvent, ordinary attachment-layer list or RenderLivingEvent posting appears in these captured base methods.

## Transform and handoff differences

Both bases copy the incoming pose matrix into dispatchedMat, reset render cycle to INITIAL, push pose, and call the shared Java render path with normalized color channels/255. The vehicle applies positive-Y rotation180 minus the supplied yaw. The projectile instead applies positive-Y rotation lerp(oldYaw,currentYaw,partial)-90 followed by positive-Z rotation lerp(oldPitch,currentPitch,partial); it does not use the supplied yaw for those body rotations, though it passes it to the superclass tail. These are ordinary lerps rather than an explicitly wrapped-angle interpolation in these calls.

They pass null VertexConsumer and texture index0 to the shared renderer. The overlay helper ignores its entity parameter and packs u(input) with v(false), not living hurt-state logic. Pose pop and superclass render follow normal paths with no local finally.

Their renderEarly override copies the current matrix and delegates to the interface default. However these render entry bodies directly call render and contain no preRender invocation; recording a renderEarly override does not prove it is invoked on this path. The [Java render boundary](JAVA-RENDER-BOUNDARY-RECOVERY-2026-10-17.md) describes the separate preRender/default call structure. No native implementation was executed or inferred from method names.

## Culling boundary and next seam

The captured four owners declare no custom frustum/distance shouldRender implementation. This bounds only these declarations; upstream dispatcher/entity culling and mixins are outside them. Continue the replacement hook/dispatcher route to establish when these entries replace vanilla rendering, and distinguish render selection from animation/controller state. Added after the fixed attachment-render checkpoint; do not relabel that earlier receipt as covering this cohort.
