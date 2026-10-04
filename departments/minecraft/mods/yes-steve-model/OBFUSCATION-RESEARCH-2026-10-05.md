# YSM 2.6.5 Java obfuscation map — 2026-10-05

## 1. Scope and result

This report maps **publicly observable Java-level obfuscated symbols** from the official YSM
2.6.5 Forge / Minecraft 1.20.1 distribution back to semantic roles.

It does not decrypt YSM models, defeat VMProtect, devirtualize the native library or publish a
private YSM JAR.

The useful result is that a meaningful part of the Java shell can already be recovered without any
of those actions.

Current status:

- native-library bootstrap: mapped;
- capability registration/provider: mapped;
- final native-render bridge: mapped;
- player / first-person render event interception: mapped;
- vehicle / projectile / fishing-hook replacement helpers: mapped;
- paperdoll / preview renderer: mapped at the distributed-artifact semantic level;
- several player-runtime members: semantic hints recovered, owner still unresolved;
- protected native implementation: **UNKNOWN / OUT OF SCOPE**.

Machine-readable companion:

[OBFUSCATION-MAP-2026-10-05.json](OBFUSCATION-MAP-2026-10-05.json)

## 2. Non-negotiable identity rule

YSM's obfuscator reuses the same textual member name heavily.

For example:

`Oo0Oo0o00O00Oo0OOoOOoooo`

appears as:

- a no-argument native-library loader;
- a Path -> Path extraction-directory helper;
- a Forge player-render event subscriber;
- a Forge arm-render event subscriber;
- a RenderHandEvent subscriber;
- a vehicle replacement helper;
- a projectile replacement helper;
- a fishing-hook replacement helper;
- a model-preview vehicle helper;
- a paperdoll renderer;
- a capability field in another class.

Therefore:

> **owner + member + JVM descriptor is the minimum mapping key.**

The member text alone has almost no semantic value.

This is consistent with the public YSM Mapping API design, which normalizes unstable YSM names and
uses descriptor shape, opcodes, constants, calls and field graph instead.

## 3. Confidence policy

### CONFIRMED

Actual-2.6.5-facing public evidence gives an exact target/descriptor and one semantic implementation
fits it.

### HIGH

The actual artifact is identified by event type, stack context, call graph or verified compatibility
probe, but one exact source-identity detail is missing.

### MEDIUM

More than one meaningful semantic candidate remains.

### LOW

Only another YSM/Minecraft version or lineage evidence supports it.

### UNKNOWN

No defensible semantic identity.

A future exact JAR scan that produces more than one structural candidate **downgrades** the item to
AMBIGUOUS. We do not use popularity or repeated guesses to break ties.

## 4. High-value recovered classes

| Obfuscated owner | Recovered role | Confidence |
|---|---|---|
| `oOoOO0o0ooO0oO000o0oOOoO` | `util.NativeLibUtil` | HIGH |
| `OoOoOOOOO0ooooo0O0ooo000` | `event.CapabilityEvent` | HIGH |
| `O0OooOo0oOOoOoOoOooO000o` | `capability.PlayerAnimatableCapabilityProvider` | CONFIRMED |
| `ooOOo000OOO0ooO0oo0ooooO` | `geckolib3.geo.NativeRenderer` | CONFIRMED |
| `OOoOoooOOooO0o0000o0O0o0` | `GeoModel` argument type used by NativeRenderer | CONFIRMED |
| `O0oOOo00o0oooOo0OoO0OOo0` | `client.event.ReplacePlayerRenderEvent` | CONFIRMED |
| `ooOOOoOO000oo0o00o00o000` | `client.event.ReplacePlayerHandRenderEvent` | CONFIRMED |
| `O000O0O00ooo000O0oOOoo00` | `client.event.RenderFirstPlayerBackground` | CONFIRMED |
| `OOoO0O0OooOO0o00oOoOOoO0` | `client.renderer.replace.EntityRendererReplace` | CONFIRMED |
| `O0oOooooo00Ooooo0OoOOOO0` | `client.renderer.replace.ProjectileRendererReplace` | CONFIRMED |
| `oO0Ooooooo0O0OOOO00OoOo0` | `client.renderer.replace.FishingHookRendererReplace` | CONFIRMED |
| `OoO00Oo00Ooo0OoOoo00o000` | distributed 2.6.5 preview / paperdoll utility, readable-layout name `ModelPreviewRenderer` | HIGH |
| `O0O00oOoOoooOOooo0OOOoO0` | paperdoll HUD entry / `ExtraPlayerScreen` semantic role | HIGH |

## 5. Native library bootstrap

### 5.1 Class

`com.elfmcys.yesstevemodel.oOoOO0o0ooO0oO000o0oOOoO`

maps to the `NativeLibUtil` role.

Three public lines of evidence agree:

1. official 2.6.5 issue #444 reaches this class when `Files.createDirectories` fails and YSM prints
   `Failed to create preferred directory, using fallback`;
2. the official release-line source candidate has exactly that error path inside
   `NativeLibUtil.prepareExtractPath(Path)`;
3. public TheFastLaunch code reflectively invokes this same obfuscated class's no-arg
   `Oo0Oo0o00O00Oo0OOoOOoooo` as the YSM native-core preload.

### 5.2 No-arg member

~~~text
oOoOO0o0ooO0oO000o0oOOoO
  # Oo0Oo0o00O00Oo0OOoOOoooo()V
~~~

maps with **HIGH** confidence to:

~~~text
NativeLibUtil.loadCoreLibrary()V
~~~

### 5.3 Path member

The same textual member name with:

~~~text
(Ljava/nio/file/Path;)Ljava/nio/file/Path;
~~~

maps with **HIGH** confidence to:

~~~text
NativeLibUtil.prepareExtractPath(Path): Path
~~~

This is the clearest direct proof that member text alone is useless.

## 6. Capability registration

The exact 2.6.5 crash path exposed:

~~~text
OoOoOOOOO0ooooo0O0ooo000
  # Oo0Oo0o00O00Oo0OOoOOoooo(AttachCapabilitiesEvent)V
~~~

Forge's generated event-subscriber name and the failing `Entity.getCapability` call identify the
role as the official source candidate's:

~~~text
CapabilityEvent.onAttachCapabilityEvent(...)
~~~

Confidence: **HIGH**.

The player capability provider is even stronger.

Public EpicFight compatibility code pins and tests:

~~~text
O0OooOo0oOOoOoOoOooO000o
  # Oo0Oo0o00O00Oo0OOoOOoooo : Capability
~~~

as the legacy/original YSM provider and capability field.

This maps to:

~~~text
PlayerAnimatableCapabilityProvider.CAP
~~~

Confidence: **CONFIRMED**.

## 7. Final mesh / native renderer bridge

The public YSMRagdoll 2.6.5 compatibility Mixin contains the exact target:

~~~text
owner:
  ooOOo000OOO0ooO0oo0ooooO

member:
  Oo0Oo0o00O00Oo0OOoOOoooo

descriptor:
  (VertexConsumer,
   PoseStack$Pose,
   OOoOoooOOooO0o0000o0O0o0,
   float[],
   float[],
   int,int,int,int,
   float,float,float,float)void
~~~

The official source candidate has exactly one Java semantic boundary with this shape:

~~~text
NativeRenderer.renderModel(
    VertexConsumer,
    PoseStack.Pose,
    GeoModel,
    float[] inputState,
    float[] outputState,
    int textureIndex,
    int renderMode,
    int packedLight,
    int packedOverlay,
    float red,
    float green,
    float blue,
    float alpha)
~~~

Therefore:

- `ooOOo000OOO0ooO0oo0ooooO` -> `NativeRenderer`
- `OOoOoooOOooO0o0000o0O0o0` -> `GeoModel`
- the full method signature -> `NativeRenderer.renderModel`

Confidence: **CONFIRMED**.

This is especially valuable because it recovers the exact Java-side seam where semantic bone state
enters the accelerated/protected render backend.

## 8. Player and first-person rendering events

### Third-person player replacement

~~~text
O0oOOo00o0oooOo0OoO0OOo0
  # Oo0Oo0o00O00Oo0OOoOOoooo(RenderPlayerEvent$Pre)V
~~~

maps to:

~~~text
ReplacePlayerRenderEvent.onRender(RenderPlayerEvent.Pre)
~~~

Confidence: **CONFIRMED**.

### First-person arm

~~~text
ooOOOoOO000oo0o00o00o000
  # Oo0Oo0o00O00Oo0OOoOOoooo(RenderArmEvent)V
~~~

maps to:

~~~text
ReplacePlayerHandRenderEvent.onRenderHand(RenderArmEvent)
~~~

Confidence: **CONFIRMED**.

### First-person background/full-body helper

~~~text
O000O0O00ooo000O0oOOoo00
  # Oo0Oo0o00O00Oo0OOoOOoooo(RenderHandEvent)V
~~~

maps to:

~~~text
RenderFirstPlayerBackground.onRenderHand(RenderHandEvent)
~~~

Confidence: **CONFIRMED**.

Official history shows these readable semantic classes were long-lived before the 2.6.5 release-line
candidate. This is stronger than matching only a current reconstructed source tree.

## 9. Vehicle / projectile / fishing-hook replacement helpers

These mappings exposed one useful correction.

The public compatibility Mixin comment calls the vehicle target
`CustomVehicleRenderer#renderVehicle`.

But its actual target descriptor is:

~~~text
(Entity, float, float, PoseStack, MultiBufferSource, int)boolean
~~~

The official release-line source candidate's `CustomVehicleRenderer.render` returns **void**.

The unique source-side boolean method with the same complete descriptor is:

~~~text
EntityRendererReplace.renderInMixin(...)
~~~

Therefore the descriptor-backed map is:

~~~text
OOoO0O0OooOO0o00oOoOOoO0
  # Oo0...(Entity,FF,PoseStack,MultiBufferSource,I)Z
      -> EntityRendererReplace.renderInMixin
~~~

Confidence: **CONFIRMED**.

Likewise:

~~~text
O0oOooooo00Ooooo0OoOOOO0
  # Oo0...(Projectile,FF,PoseStack,MultiBufferSource,I)Z
      -> ProjectileRendererReplace.renderInMixin

oO0Ooooooo0O0OOOO00OoOo0
  # Oo0...(FishingHook,FF,PoseStack,MultiBufferSource,I)Z
      -> FishingHookRendererReplace.renderInMixin
~~~

Both: **CONFIRMED**.

This is why comments and class names are discovery aids; exact JVM shape is stronger evidence.

## 10. Paperdoll / preview renderer and source-artifact divergence

The actual-2.6.5-derived compatibility layer targets:

~~~text
OoO00Oo00Ooo0OoOoo00o000
~~~

as the preview/paperdoll renderer utility.

It gives two strong descriptor mappings.

### Vehicle preview

~~~text
# Oo0...(Entity, PoseStack, float)V
    -> ModelPreviewRenderer.renderVehicleModel
~~~

### Paperdoll

~~~text
# Oo0...(GuiGraphics, LocalPlayer, double, double,
         float, float, int, float)V
    -> ModelPreviewRenderer.renderPlayerOverlay
~~~

OpenYSM exposes a readable `ModelPreviewRenderer` with those same method shapes.

However the official f184eda source candidate has **no**
`client/renderer/ModelPreviewRenderer.java` path in its history. Its equivalent paperdoll operation
is in:

~~~text
RenderUtil.renderExtraPlayerEntity(...)
~~~

This is not a reason to force one track to match the other.

It is evidence that:

> **the public version-matched source candidate is not a byte-for-byte source identity for the
> distributed obfuscated 2.6.5 artifact.**

The obfuscated-artifact mapping remains **HIGH**, while the release-line counterpart is recorded
separately.

## 11. Paperdoll HUD entry

Public actual-jar call-chain work identifies:

~~~text
O0O00oOoOoooOOooo0OOOoO0
~~~

as the HUD overlay entry that reads its config and then calls the paperdoll helper.

The official release-line source candidate's corresponding class is:

~~~text
client.gui.overlay.ExtraPlayerScreen
~~~

which is an `IGuiOverlay`, reads the same screen-position/scale/yaw configuration, and calls the
paperdoll render utility.

Confidence: **HIGH**.

## 12. Player-runtime member hints

A public compatibility layer reads two obfuscated no-arg methods on the runtime player animatable.

### String getter

~~~text
OOOoOOo0oO00O0OoOO0oO00O()Ljava/lang/String;
~~~

is probed alongside readable names:

~~~text
getSelectedModelId
getModelId
~~~

Semantic result: **selected/current model ID getter**.

Release-line counterpart: `CustomEntity.getModelId()`.

Confidence: **HIGH semantic**, exact owner unresolved.

### Boolean getter

~~~text
O0OooOo0oOOoOoOoOooO000o()Z
~~~

is probed as:

~~~text
isModelSwitching
~~~

Confidence: **HIGH semantic**, exact owner unresolved.

There is no obvious corresponding method in f184eda. That is retained as another
SOURCE_ARTIFACT_DIVERGENCE instead of inventing a counterpart.

## 13. What YSM Mapping API contributes

YSM Mapping API's 1.20.1 branch provides a better long-term method than growing a handwritten
obfuscation dictionary.

Its whole-JAR structural fingerprint normalizes:

- YSM-internal types -> `@ysm`
- Minecraft types -> `@minecraft`
- loader types -> `@loader`
- internal member names -> wildcard-like normalized form

while preserving meaningful shape through:

- access flags;
- normalized descriptors;
- opcode digest;
- constant digest;
- call graph;
- field graph.

Its resolver also preserves NOT_FOUND and AMBIGUOUS instead of forcing a winner. The default
consumer policy is safe-only: a structural target becomes resolved only when a single candidate
survives.

That should be the TECH HUB rule too.

## 14. Public-source history cross-check

Relevant official history supports the semantic roles:

- `NativeLibUtil`: multiple platform/runtime fixes through the 2.6.x line, including
  2025-09 Linux unwritable-user-directory fallback;
- `ReplacePlayerRenderEvent`: long-lived third-person interception path;
- `ReplacePlayerHandRenderEvent`: long-lived arm interception path;
- `RenderFirstPlayerBackground`: long-lived RenderHandEvent background/full-body path;
- `EntityRendererReplace`, `ProjectileRendererReplace`,
  `FishingHookRendererReplace`: introduced in the same 2025-09 custom vehicle/projectile design
  family and retained through the 2.6.5 candidate.

The public repository also has a 2024 history entry named “remove class encryption”. Later public
compatibility projects still observe a heavily obfuscated distributed 2.6.5 root package.

That means repository readability and distribution obfuscation must be treated as separate build
surfaces.

No claim about how the native protection itself works is inferred from this.

## 15. What remains unknown

Still unresolved:

1. exact SHA-256 of the distributed 2.6.5 JAR in TECH HUB evidence;
2. a complete class/member map for all ~root-package obfuscated classes;
3. exact obfuscated owners for the selected-model and model-switching getters;
4. the native model-sync protocol body;
5. the protected renderer/native library implementation;
6. encrypted model/container internals;
7. exact source-to-distributed build transformation chain.

The next safe route for deeper coverage is an **authorized local structural scan of the user's own
installed 2.6.5 JAR**, recording only hashes, normalized fingerprints and minimized mappings. The JAR
itself and raw private analysis output should stay outside Git.

## 16. Engineering takeaway

The Java obfuscation is not opaque enough to erase architecture.

Even without breaking protection, stable external types and behavior leak enough structure to
recover:

~~~text
Forge event
  -> obfuscated subscriber
  -> presentation capability
  -> renderer replacement helper
  -> model/pose state
  -> NativeRenderer.renderModel
  -> protected native geometry backend
~~~

For KNEEKURA, the more durable asset is not the current literal `Oo0o...` dictionary.

It is the **descriptor/structure-first resolver** that can regenerate the semantic map when those
names change.


## 17. Chinese-speaking community expansion

A second public-evidence pass expanded the machine-readable map from **26** to **55** owner/member
mappings.

Current audited distribution:

- **22 CONFIRMED**
- **33 HIGH**
- **0 duplicate owner + member + descriptor keys**
- **20 explicit SOURCE_ARTIFACT_DIVERGENCE mappings**
- **0 diverged mapping promoted to CONFIRMED**

New high-value areas include:

- Carry On compatibility;
- YSM Jade plugin;
- ConfigScreen;
- CustomPlayerRenderer;
- TaCZ binding, transform and animation handlers;
- GeoEntityRenderer / GeoReplacedEntityRenderer;
- CustomPlayerItemInHandLayer;
- actual-artifact AnimatableEntity / LivingAnimatable / AnimatedGeoModel semantic roles.

A separate unresolved-owner alias surface records **23** public animated-bone accessors. These are not
inflated into owner mappings until the concrete runtime bone class is independently identified.

The strongest maintenance lesson from the Chinese-speaking compatibility projects is to use two
verification layers:

~~~text
exact supported JAR
    -> ASM name + full descriptor contract

then

relevant runtime context
    -> expected hook entered / not entered diagnostic
~~~

This catches both stale descriptors and "method exists but the intended runtime path never fires".

See:

- [CHINESE-COMMUNITY-OBFUSCATION-RECON-2026-10-05.md](CHINESE-COMMUNITY-OBFUSCATION-RECON-2026-10-05.md)
- [OBFUSCATION-MAP-2026-10-05.json](OBFUSCATION-MAP-2026-10-05.json)
