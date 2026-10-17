# Vanilla and SWarfare arm replacement gates

PRIMARY_STATIC_REVIEW_ONLY. Exact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison source `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Nineteen declarations across two handlers and previously captured SWarfare wrapper;115 integrity checks/9 negative controls. Exact handler annotations and bootstrap callbacks retained. No runtime/event dispatch/native execution, independent semantic review or map promotion.

## Ordinary Forge RenderArmEvent

`ooOOOoOO000oo0o00o00o000` carries CLIENT EventBusSubscriber and a static SubscribeEvent handler. It returns if YSM unavailable, self-model disabled, self-hands disabled, or event player is not LocalPlayer. Capability absence leaves the event untouched by this handler. The callback additionally requires isInitializedAndEnabled, a nonnull model container, and the selected arm-model feature flag. The helper selects the left flag for LEFT, otherwise right; it does not dynamically search a bone by name.

On passing those gates it takes event pose/buffer/light, samples Minecraft.getPartialTick, calls the [first-person renderer](FIRST-PERSON-RENDER-REGISTRY-RECOVERY-2026-10-17.md) at82, and only after normal return calls event.setCanceled(true) at87. The renderer is void and may return early for absent animation/model or cancelled special event; that still counts as normal return and the outer Forge arm event is cancelled. Thus cancellation is not a receipt that any vertices or pixels were emitted. If the renderer throws, the subsequent cancellation call is not reached by this local path.

## SWarfare event cancels earlier

`oOo0Oo0ooo000OOOOOOO0oOO` has an instance SubscribeEvent handler. The version-gated SWarfare wrapper registers a new instance on the event bus during its successful init path (minimum0.8.7.1); this is distinct from automatic class-level subscription of the ordinary handler. No listener invocation was performed.

It shares the availability/two-config gates and rejects null local player. Then setCanceled(true) occurs at51, BEFORE capability lookup/ifPresent. Its callback checks model container and the arm feature but has no isInitializedAndEnabled call corresponding to the ordinary handler. Missing capability, missing model or absent arm feature can therefore leave the SW event cancelled without calling the custom renderer. Preserve this asymmetry rather than silently normalizing the two paths. Other listeners or the external event publisher can affect observed behavior, so this is not an asserted runtime defect.

## Provider pose adjustment and scope

Before invoking the shared arm renderer, the SW callback mutates the supplied pose:

- LEFT: translate(-0.0625,0.125,0), then(-0.275,0.0625,0). Otherwise use positive x values.
- Old-hand mode: translate((pivotX-1)/16,(pivotY-2)/16,pivotZ/16).
- New-hand mode: translate(pivotX/16,(pivotY+7)/16,pivotZ/16), then Y180 and Z180 rotations.

These initial constants are embedded in the exact bytecode; this is not a dynamic query of the provider's scale constant. The callback does not push/pop around these transforms or guard a null provider bone. The shared renderer's own push occurs later and its normal pop restores only that later scope; it does not reverse the provider adjustments already made here. Outer publisher pose ownership remains an external dependency, not proof of a leaked transform.

## Reuse

Separate gate failure before cancellation, failure after cancellation, normal renderer return without drawing, and exceptions. This closes the two exact Java caller paths found for the first-person renderer. It does not establish exhaustive reflective/native callers or provider event ordering. Added after the fixed14 checkpoint; later render-batch verification can compare shared evidence without rerunning unrelated repository tests.
