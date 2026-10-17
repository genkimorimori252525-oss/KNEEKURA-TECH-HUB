# Living-renderer bridge and paper-doll entry contract

PRIMARY_STATIC_REVIEW_ONLY. Fixed YSM2.6.5 SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Seven declarations across four owners, including an abstract interface member with no Code. No game, graphics, Mixin application or original-name proof.

| Comparison role | Exact owner suffix |
|---|---|
| ILivingRenderer | O00OOOooOoooOoo0o0o0oO0O |
| LivingRendererMixin | mixin/client/LivingRendererMixin |
| ExtraPlayerScreen | O0O00oOoOoooOOooo0OOOoO0 |
| ExtraPlayerScreenConfig | o0Oo00ooo0o0o0ooO0ooo0oo |

## The previously captured interface cast has a declared provider

The [replacement render selection snapshot](RENDER-SELECTION-EVIDENCE-2026-10-17.json) reaches an interface checkcast at574 and invokeinterface at588 on its ordinary tail, after pose pop and before RenderLivingEvent.Post. That interface's one method takes LivingEntity, two floats, PoseStack, MultiBufferSource and packed-light int, and is abstract in the original class file.

The named mixin declares that interface, targets LivingEntityRenderer in its encoded Mixin annotation and marks its implementation Unique. The method forwards all arguments with INVOKESPECIAL at10 to EntityRenderer.m_7392_, whose entity parameter type is Entity. It is not another invocation of the living renderer's main body and not a call to YSM's native renderer. The exact external base-render implementation remains outside this cohort; do not label its visual effects merely from a source comment/name.

The packaged config includes client.LivingRendererMixin. There is no owner-specific entry for this class in the inspected refmap; this absence is retained, not called an injection failure. The interface cast's runtime validity depends on actual Mixin transformation and external classes. Config inclusion, annotation presence and a body forwarding to a superclass are necessary static connections, not a game-start/injection receipt.

The existing render dossier's exception limits remain: a preceding exception may bypass the pose pop, bridge or Post event. This bridge adds no finally or replacement-draw success acknowledgement.

## Actual paper-doll overlay entry

The earlier [client initialization evidence](CLIENT-COMPAT-INITIALIZATION-EVIDENCE-2026-10-17.json) constructs ExtraPlayerScreen and registers it above DEBUG_TEXT under ysm_extra_player. The new overlay body tests its disable BooleanValue first, returns for no local player, and returns when the current screen is the ExtraPlayerConfigScreen comparison class. It does not itself require that a YSM replacement model be loaded before handing the local player to RenderUtil.

It reads configured X/Y integers and widens them to doubles, reads scale/yaw doubles and narrows them to floats, then calls the existing renderExtraPlayerEntity helper with z=-500. Although the overlay callback receives partialTick as a parameter, this body loads Minecraft.getFrameTime at120 for the helper instead. No screen width/height normalization or separate local clamp appears here. Actual frame timing and pixel placement were not measured.

This connects the real LocalPlayer overlay route to the [preview state dossier](GUI-PREVIEW-STATE-RECOVERY-2026-10-17.md), whose RenderUtil paper-doll path sets its flag, adjusts model-view/pose/camera/lighting/shadow state, dispatches rendering and performs normal-tail cleanup. This is separate from the GUI-model overload whose observed equipment-suppression callers use FakePlayer; do not transfer that overload's inventory-clear finding to this overlay path.

## Declared configuration values, not effective runtime settings

The config initializer pushes extra_player_render and passes these values to ForgeConfigSpec.Builder:

- DisablePlayerRender: default false
- PlayerPosX and PlayerPosY: default10, lower0, upper2147483647
- PlayerScale: default40.0, lower8.0, upper360.0
- PlayerYawOffset: default5.0, lower4.9E-324 (Double.MIN_VALUE), upper1.7976931348623157E308 (Double.MAX_VALUE)

The yaw lower bound is the smallest positive double, not a large negative bound. These are exact constant/API-call arguments. They do not prove the current config file's values, external validation/persistence behavior, UI slider domain or a reproduced inability to select a negative angle. The render entry's float narrowing is distinct from this double-valued declaration; no replacement range or corrective patch was applied.

## Reuse

Preserve the transformed-interface prerequisite, superclass-versus-living-body distinction, real overlay actor versus fake preview actor, actual frame-time source and configuration representation. Central map669 remains unchanged, all findings stay primary-only, and native/GPU output and independent semantic review remain open.
