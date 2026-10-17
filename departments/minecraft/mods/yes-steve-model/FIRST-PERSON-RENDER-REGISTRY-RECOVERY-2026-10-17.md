# First-person arm render handoff and renderer registry

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Twenty declarations across first-person renderer, registry and previously captured backpack adapter;120 integrity checks/9 negative controls. No mapping promotion, independent semantic review or target/native/GPU execution. The adapter snapshot overlaps the earlier backpack cohort, not twenty newly discovered semantic methods.

## Cached first-person animatable

Renderer `o0oo00OoO00OO0Oo0oo00ooo` constructs an arm animatable when its retained field is null or the retained entity is not the supplied LocalPlayer. It does not compare capability identity in this reuse condition. The ClientModel parameter is not read by the render body. The arm entity retains the capability provided at construction; the current cap argument separately supplies the special render event and texture choice. A same-player/different-cap mismatch is therefore a conditional input concern, not an observed game state or reason to invent a patch.

checkModelUpdate and updateAnimation occur before the null-event and null-model returns. After those gates, the special player event is posted. Its cancellation happens AFTER animation work on this path, unlike the [third-person entry](PLAYER-RENDER-ENTRY-RECOVERY-2026-10-17.md) where the special event precedes the inherited animation update. Cancellation does not undo completed animation work.

## Arm-specific native-wrapper arguments

On normal continuation, null event texture override uses current cap texture and index; nonnull override uses that resource and index0. The renderer always requests its custom translucent render type here. This body does not query model translucency to choose cutout/outline, run the ordinary attachment-layer list, call IGeoRenderer.countRender or set its render-cycle state.

HumanoidArm.LEFT selects mode1 and translation(+0.25,1.8,0); every other reference comparison outcome selects mode2 and(-0.25,1.8,0). Then scale(-1,-1,1), pass the loaded arm model plus retained input/output arrays, selected texture index/mode, packed light, NO_OVERLAY and RGBA1 to the Java NativeRenderer wrapper. The exact wrapper call is at253 and ordinary pose pop at258; no finally protects pop. These values identify Java requests only; native mask semantics and visible arm geometry remain outside this review.

The [earlier arm assembly](FIRST-PERSON-ARM-ASSEMBLY-RECOVERY-2026-10-17.md) and [native boundary](JAVA-RENDER-BOUNDARY-RECOVERY-2026-10-17.md) describe the adjacent model/controller and implementation limits.

## Registry replacement and optional layer timing

Registry `OOoO00ooO00OOO00O0o0000O` has the exact CLIENT EventBusSubscriber annotation and a SubscribeEvent AddReloadListenerEvent handler. The handler checks YesSteveModel.isAvailable before registering a ResourceManagerReloadListener callback. No explicit bus element appears in that annotation; external Forge dispatch/timing was not executed.

Its init builds one context, then assigns new player, projectile, first-person-arm and vehicle renderers, in that order, and finally calls SophisticatedCompat.addLayer at108. Each getter independently checks its own field for null and calls init if null, replacing ALL four renderer fields. Getters do not repeat the handler's availability gate. This is not an atomic transaction or synchronized lazy initialization: fields are assigned sequentially and there is no local rollback/finally. Actual concurrent calls are not established.

The backpack adapter's addLayer only acts when its retained installed flag is true, calls getPlayerRenderer and appends a new backpack layer. During ordinary init the player field has already been set, so that getter does not itself recurse. Repeated addLayer calls have no local deduplication, while repeated successful init replaces the renderer/list before adding once. If initialization occurs before the installed flag becomes true, that invocation skips the backpack layer; later installation alone does not prove this list is retroactively updated. Actual startup/reload ordering needs separate evidence.

## Continuation

This closes Java entry-to-arm handoff and the optional backpack registration link. Next trace the caller that chooses arm replacement and default vanilla cancellation, not the already reviewed native wrapper. Added after the fixed14 optional-integration checkpoint.
