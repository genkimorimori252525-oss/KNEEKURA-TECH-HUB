# NativeTexture: Java scheduling and ownership boundary only

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Owner `O0O00000Ooooo00oooo0ooo0`, seven declarations including two native methods with NO Code. Native implementation, image contents, decoding, GPU operations and target classes were not executed. The snapshot does not invent native method bodies or promote central mappings.

## Load is a dispatch, not a completion receipt

The constructor initializes an empty PBR map, stores the supplied long nativeId and registers CleanerUtil.ref(this,boxedId,free callback). It does not locally validate that ID. The existing cleaner dossier covers the Java ObjectCleaner delegation; registration does not prove cleanup ran or that native free is thread-safe.

load(ResourceManager) ignores the resource-manager parameter. It tests RenderSystem.isOnRenderThreadOrInit. If false it records a RenderCall capturing this and targeting doLoad; if true it calls doLoad immediately. No ready flag, one-shot guard, cancellation token or completion future is added in this class. Multiple calls are not locally coalesced by this body. The queue's actual processing and superclass/external behavior remain separate.

doLoad calls inherited getId, binds that integer through GlStateManager._bindTexture and invokes native upload. There is no local try/finally restoring a previous binding or rollback on failure. This describes the Java sequence, not an observed GL-state leak or upload failure. A return from the scheduling branch is not evidence of a completed upload.

## PBR references are shallow-copied on the setter path

The private setPBRTextures method constructs a new Reference2ReferenceOpenHashMap from the supplied Map and wraps it unmodifiable before replacing the field. Its texture values remain the original object references. The getter returns the current map. The field is not volatile and these methods add no locking; this does not independently establish an actual concurrent caller.

load/doLoad do not recursively upload PBR child textures in their own bodies. The separate [texture manager](TEXTURE-HOLDER-LIFETIME-RECOVERY-2026-10-17.md) recursively obtains and retains child holders during registration. [Shader/PBR adapters](SHADER-BUFFER-ADAPTERS-RECOVERY-2026-10-17.md) expose another consumer boundary. Keep those operations separate from the private setter, whose Native Access comment does not prove which native path invokes it or when.

## Cleanup layers remain distinct

This declared class has no close/release override; inherited AbstractTexture behavior is not rederived here. CustomTextureManager.release's Java cache removal, Minecraft texture-ID release, cleaner scheduling and native free are different boundaries. Do not label one as a synchronous substitute for all others or assume a native-ID lifecycle solely from final-field ownership.
