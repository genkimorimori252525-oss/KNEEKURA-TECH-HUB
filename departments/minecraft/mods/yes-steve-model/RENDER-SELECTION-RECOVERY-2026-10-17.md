# Client tick to humanoid model/texture render selection

Primary static review; independent review NOT_RUN. Same fixed YSM2.6.5 artifact
SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f` and
source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. No target execution,
GPU outcome or global source equivalence. Mapping669 remains unchanged.

54 captured methods across ClientTickEvent `o0O0000ooOOO0O0oo0OOOoOo`,
GeoReplacedEntityRenderer `OOoo0o0oO000ooO0Oo00OoOo` and CustomHumanoidEntity
`o0O0oOooOo0OoOo0oOo00O00`. Complete owner snapshots provide context, not a claim
that every unrelated method is semantically recovered. Reviewed paths follow.

## Registration/release service order

The client tick handler returns when YesSteveModel is unavailable or phase==END.
On the remaining path it increments tickCount, calls CustomTextureManager.tick
at26, ClientModelManager.tick at29, DecoderManager.tick at32, then queries/stores
the window refresh rate and optionally handles player roaming-variable changes.
There is no handler/finally around this sequence. A failure in texture processing
can prevent the later calls for this invocation; no occurrence is claimed.
The earlier texture delay counts these accepted handler visits, not render frames.
Actual Forge subscription/invocation timing is not a runtime receipt here.

## Pre-event can stop animation work; null result does not skip every tail

The texture-override render overload constructs/posts RenderLivingEvent.Pre at26.
If post returns true, it returns before updateAnimation. Otherwise the animation
update occurs at38, before event-null and local-player-null gates at59/67.
Only the custom model rendering block requires both nonnull. Both null branches
jump to573, where the superclass-render bridge and RenderLivingEvent.Post tail
still execute on the ordinary path. This differs from the canceled-Pre path.
The early event contains the entity/pose/buffer context, so external listeners are
an unclosed dependency; this report does not infer their behavior.

## Model, texture index and texture override are selected separately

Inside the custom block, transforms and preRenderCallback run before
getLoadedGeoModel at250. A null textureOverride selects the animatable's texture
index and getTextureLocation; a nonnull override selects index0 and that supplied
resource location. Model translucency is queried using the selected index.
Body-visible/glowing decisions feed render-type selection. preRender still runs
before the renderType-null branch; a null type skips the main body render only.
Layers may render before or after it according to renderLayersFirst, and are
suppressed for spectators. The actual low-level render implementation/GPU call
path is still separate; this method's name is not proof of visible output.

The CustomHumanoidEntity texture getter first calls isModelPresent. True selects
its holder.id Optional.get; false selects ClientModelManager's default texture.
Its texture-index getter similarly returns configured index or0. Joined with the
readiness dossier, this uses the non-fallback/ready predicate rather than simply
whether a model object exists. These calls do not themselves recheck completed
native uploads or establish a lock around the full selection sequence.

The body dereferences the loaded model after the event gate without a separate
model-null guard at that point. Normal base updateAnimation returns null without
a model, but virtual callbacks/overrides and mutations must be considered before
claiming this is universally safe or a demonstrated crash.

## Exception and scope limits

The render overload has no exception handlers/finally. pose pop, superclass bridge
and Post event are ordinary-tail operations; a preceding exception can bypass
some or all. No automatic repair or claim of an observed rendering bug is made.
The explicit source/bytecode join confirms ordering and selection, not concurrent
stability, complete Forge event behavior or correctness of external shaders.

## Verification and next seam

289 fixed-artifact/source/declaration/body checks pass;16 evidence-negative
controls reject changed Pre cancellation, null-event tail, texture override,
layer order, client phase, fallback selection and invented finally. No independent
semantic approval is claimed. Continue low-level Java render-cycle/buffer handoff
and model-manager readiness only as needed to close this path; keep native
implementation boundaries explicit.
