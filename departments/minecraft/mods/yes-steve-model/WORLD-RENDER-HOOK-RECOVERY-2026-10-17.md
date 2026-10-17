# Exact world-render Mixin annotation and refmap evidence

Primary static inspection only. Same fixed YSM2.6.5 artifact as the preceding
ASYNC-ANIMATION dossier. Independent semantic review NOT_RUN; no game execution
or successful runtime injection claim. This follow-on resolves that dossier's
specific annotation-decoding gap, not its broader runtime/thread-safety limits.

The class RuntimeInvisibleAnnotations Mixin.value targets
net/minecraft/client/renderer/LevelRenderer. Both private hook methods carry
RuntimeVisibleAnnotations Inject.method targeting the full renderLevel descriptor.
Their nested At annotations specify INVOKE with:

- First hook: FogRenderer.setupColor(Camera,float,ClientLevel,int,float)V
- Second hook: RenderType.entitySolid(ResourceLocation)RenderType

Neither encoded annotation supplies a shift, ordinal, require or cancellable
value. The absence is recorded rather than inventing explicit values; annotation
defaults and actual Mixin engine behavior are external dependencies.

Packaged yes_steve_model.mixins.json lists client.WorldRendererMixin, requires
Mixin0.8/JAVA_17, sets defaultRequire1, and names MixinTweaker as plugin plus
yes_steve_model.refmap.json as refmap. The refmap's owner-specific mappings encode
setupColor→m_109018_, entitySolid→m_110446_ and renderLevel→m_109599_, preserving
the full descriptors. These are declared mappings, not verification that the
plugin permits this mixin or that external Minecraft bytecode has matching sites.

Combined with the previously captured hook bodies: first available hook sets the
render-level flag true and submits scheduling; second available hook waits then
clears the flag. Source annotation labels are now corroborated by the distributed
class and packaged remapping entry. Exception handling and runtime placement
remain as bounded in ASYNC-ANIMATION-RECOVERY.

The new parser decodes nested annotation elements directly, consumes annotation
and class byte streams fully, and retains exact class SHA-256 plus decoded
config/refmap subset. One exact comparison passes; five corrupted/missing-evidence
controls reject. These are focused evidence checks, not independent parser
validation or a live Mixin application test. Next follow MixinTweaker eligibility
and rendering-state helpers before claiming which branches are reachable.
