# Dispatcher replacement routing and yaw adapters

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.18 declarations across dispatcher mixin and three helpers;114 integrity checks/10 negative controls. Fishing-line helper bodies are captured as support; their full numeric/visual semantics are not claimed here. No independent semantic review, central promotion or target/mixin/GPU execution.

## Conditional invocation, not dispatcher-wide cancellation

EntityRenderDispatcherMixin records a WrapWithCondition on method"render" at the EntityRenderer.render(Entity,float,float,PoseStack,MultiBufferSource,int) invocation. This describes the intended wrapped call; annotation presence alone is not a successful injection receipt. The helper's boolean controls that original invocation, not every other dispatcher operation or upstream frustum/distance culling.

When YSM unavailable it returns true. Otherwise a Projectile with projectile-model disabling false immediately routes to FishingHook-specific or ordinary projectile helper and returns that result. Even when the helper returns true, this branch does not continue into vehicle/passenger handling. If that projectile branch is not taken, vehicle-model disabling false runs passenger pose adjustment BEFORE generic entity replacement; otherwise returns true. Therefore disabling projectile models can still allow the generic vehicle path for the same entity if its own configuration/capability qualifies. Passenger pose adjustment may remain even when generic replacement later returns true and the original renderer is allowed.

## Direct animatable overload bypasses concrete outer gate

Generic `OOoO0O0OooOO0o00oOoOOoO0` and projectile `O0oOooooo00Ooooo0OoOOOO0` query their respective capability. Missing capability, uninitialized state or absent model yields true. On accepted state they call the registry renderer's overload whose first parameter is AnimatableEntity, then return false after normal return.

This is the direct base-overload path distinguished in [vehicle/projectile render entries](VEHICLE-PROJECTILE-RENDER-RECOVERY-2026-10-17.md): it bypasses the concrete Entity/Projectile overload's early invisibility gate and checkModelUpdate callback. The base updateAnimation and visibility/glowing choice still apply. Thus the outer-gate finding must not be generalized to this dispatcher route. Readiness and model refresh contracts are separate; no unconditional refreshed-model claim is made.

A normal return with no body drawn still yields false, suppressing the wrapped original renderer. No success boolean from the void renderer is available. Exceptions do not produce that normal false return and are not locally converted into a fallback.

## Yaw selection

Generic helper starts with supplied yaw. LivingEntity takes precedence and uses rotLerp of body/head angles; when it is a passenger, the vehicle exists/shouldRiderSit and is itself living, vehicle body yaw is used, wrapped head difference clamped to[-85,85], then yaw=head-minus-difference and an extra0.2*difference when difference squared>2500.

For AbstractMinecart it interpolates old/current position, requests rail center and offsets±0.3f (promoted double constants±0.30000001192092896), substitutes center for missing front/back, and when back-minus-front has nonzero length uses atan2(z,x)*180/pi. Without usable rail data it keeps incoming yaw. Other entities keep incoming yaw. This helper also supplies the passenger locator frame described in [passenger attachment](PASSENGER-HAT-ATTACHMENT-RECOVERY-2026-10-17.md); external rail methods and actual orientation were not executed.

## Fishing hook special path has a retained entity mutation

`oO0Ooooooo0O0OOOO00OoOo0` uses the projectile capability readiness/model gates. On acceptance it sets the hook's current X rotation to0 and old X rotation field to0 before the custom renderer call. There is no local restoration. Unlike pose-only passenger adjustment, these are writes to the entity object, not solely a temporary matrix. No claim is made about server state/physics consequences.

After normal custom rendering it obtains the player owner. A nonnull owner adds a push→fishing-line helper→pop sequence; null owner skips that sequence but still returns false. Pose cleanup lacks a local finally. Full line geometry/degenerate-vector and Iris tail semantics are the next bounded question; this entry analysis does not substitute a screenshot or native result.

## Limits

Upstream visibility/frustum checks, actual MixinExtras application, external provider listeners and native drawing remain separate. Source names are comparison labels, not proof of original unobfuscated names. Added after the attachment-render checkpoint; no previous frozen receipt was expanded implicitly.
