# Shader state, PBR providers and fixed-buffer adapter

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.30 declarations across Iris wrapper/two PBR loaders, Optifine wrapper, custom translucency and BufferSource mixin;182 integrity checks/12 negative controls. No independent semantic review, central-map promotion, YSM/provider/native/GPU execution. A separate seven-case JDK-only arithmetic model is explicitly not target execution.

## Oculus initialization and sampled state

Iris wrapper `OO0oooO0OO0o00oOOoOoOoOo` looks for mod ID"oculus". Its callback chooses current net.irisshaders vertex format/ID getter/PBR loader for version>=1.7.0, otherwise legacy net.coderbot variants. It registers the corresponding loader, calls the selected LongSupplier once and discards the result, calls its own isRenderingShadow helper and discards that result, THEN sets installed true.

The shadow helper short-circuits when installed is false. Therefore the first initialization's pre-installed shadow call does not necessarily probe IrisApi at all; do not call the entire sequence a successful shadow-API test. setupState later, when installed, updates the retained entity ID and then shadow flag through the current IrisApi path. No installed branch reset occurs when setupState is called while false. A failure after updating ID but before shadow assignment can leave a partially updated pair; there is no local finally/transaction.

Initialization catches Throwable from its protected setup sequence, logs and clears format/supplier/installed. It does not roll back an already registered PBR loader, reset the entity ID/shadow fields, or protect the logging operation itself with another handler. Absent mod Optional skips the callback; it is not an explicit reset of a previously initialized state. These are conditional lifecycle boundaries, not reported runtime failures.

## Signed ID composition must not be normalized silently

Both current and legacy getters narrow entity/block/item IDs to signed shorts (I2S), sign-extend to long, and OR a with b<<16 and c<<32. No unsigned0xffff mask occurs. Consequently this is not simply three independent unsigned16-bit lanes for all possible inputs.

The separate [JDK-only contract](tools/ShaderIdPackingContract.java) reproduces only those Java arithmetic operations. Seven cases pass in [receipt](SHADER-ID-PACKING-VERIFICATION-2026-10-17.json): positive(1,2,3) yields0x000300020001; first lane-1 yields-1 regardless of later lanes; negative second/third lanes sign-extend;65536 narrows to0;32768 narrows negative. This establishes Java arithmetic consequences for those supplied values, not the actual external ID domain, native consumer interpretation or a shader bug. No runtime/native patch was proposed.

## PBR provider forwarding

Both nested loaders read NORMAL then SPECULAR entries from NativeTexture.getPBRTextures. Each nonnull value is forwarded to its matching external consumer method; one may be present without the other. The ResourceManager parameter is unused by these load bodies. They register a singleton loader for NativeTexture.class in the corresponding current/legacy registry. These are provider handoffs, not texture decoding/upload or successful rendering receipts.

## Optifine probe and translucency wrapper

Optifine `oo0OO00OOOOo0ooOOoOOo0O0` uses Class.forName("net.optifine.Config") and sets installed true on success, false only when ClassNotFoundException is caught. Other linkage/initializer errors are not handled there. This probe was statically inspected, not executed.

Custom translucency `o0oOo0ooO00oOoooOOOoOOo0` memoizes constructor results through Minecraft Util, wraps entityTranslucent(texture), and forwards its format/mode/buffer-size/affects-crumbling plus bound setup/clear callbacks. The following boolean constructor argument is literalfalse rather than copied from the inner type. It snapshots inner isOutline and outline Optional into fields. No local cache-clear method is declared; actual Util cache behavior and GPU sorting remain external. The source-level name"entity_translucent_ysm" does not prove visual equivalence to every inner state.

## Fixed-buffer flush adapter

BufferSourceMixin's exact annotations target MultiBufferSource.BufferSource and shadow its final fixed-buffer map. endBatchFixedRenderType iterates the map's live keySet and calls endBatch(type) for each key, with no copied list, local order guarantee or finally. This is narrower than asserting a universal all-buffer flush; shared/non-fixed buffers are not explicitly enumerated by this body. The [hand layer](ATTACHMENT-RENDER-LAYERS-RECOVERY-2026-10-17.md) calls this adapter only under its renderLayersFirst/nonempty/item-buffer gates.

The [native wrapper](JAVA-RENDER-BOUNDARY-RECOVERY-2026-10-17.md) consumes the surrounding adapter state but native implementation remains out of scope. Next assess reusable lifecycle boundaries against existing texture/frame dossiers before adding any duplicate audit or runtime requirement.
