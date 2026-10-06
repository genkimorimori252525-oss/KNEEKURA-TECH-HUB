# Foundation Map

## 1. Bootstrap and registry

The mod uses an MCreator-generated Forge skeleton with a substantial custom client-rendering layer.

Key surfaces:
- JujutsuKaisenMod
- init registries
- network/JujutsuKaisenModVariables
- generated key/UI message classes
- JujutsuNetwork for the dedicated ripple channel
- mixins.jujutsu_kaisen.json

## 2. Authoritative combat/state layer

Most gameplay behavior lives in 1,196 Procedure classes plus MobEffect/entity state.

Domain lifecycle:
DomainexpantionMobEffect
-> Domain_expansion_startProcedure
-> DomainexpansiontickupdateProcedure
-> Domain_effect_releaseProcedure

Normal hit integration:
Attackhit1Procedure
-> DomainbattleProcedure

Sure-hit:
DomainexpansiontickupdateProcedure
-> DomainexpansionhitProcedure
-> scheduled shell scan
-> DomainexpansionhitattackProcedure

Domain Expansion is therefore a combat subsystem, not a renderer-owned feature.

## 3. Compact synchronized actor state

Several effects use entities as authoritative state carriers and reconstruct expensive visuals client-side.

Examples:
- LaserEntity: RGBA, fire/charge, curve, lock and max-length synchronized data
- FireEntityEntity: beam/VFX mode and size/explosion state
- PureloveentityEntity: fire/explode/size
- OpenEntity2Entity: explosion type/scale/max tick
- BlueentityEntity: synchronized radius/yaw
- PiercingbloodentityEntity: synchronized UUID reference

The reusable split is: synchronize semantic parameters, not every visual primitive.

## 4. Client presentation layer

### World geometry
- BlackFlashRenderer
- BeamRenderer
- VFXRenderer

### Render-layer augmentation
- DomainAmplificationRender
- AuraBufferSource
- AuraRenderType
- AuraRenderUtils
- UniversalAuraMixin
- GeckolibAuraMixin

### Full-screen post process
- RippleEffectManager
- RipplePacket
- entity_ripple shader chain

### GUI cinematic
- DomainCutinOverlay

### Off-screen target / domain surfaces
- CustomPortalBlockEntityRenderer
- CustomPortal2BlockEntityRenderer
- CustomPortal3BlockEntityRenderer
- DomainRenderDispatcher
- custom portal shaders

## 5. Animation

- 121 GeckoLib animation JSONs
- 122 Geo model JSONs
- 2 PlayerAnimator JSONs

The mod uses both animated Geo entities and player animation resources.

## 6. Particles

There are 50 particle definition files.

ParticlePacketMixin forces ClientboundLevelParticlesPacket.isOverrideLimiter() to return true. This improves effect persistence but is a client-performance risk and should not be copied blindly.

## 7. Networking

Generated network classes handle keybind/UI/action messages and variable sync.

JujutsuNetwork defines ripple_sync_channel and registers one explicit RipplePacket carrying entity ID plus cancel-mode boolean. It is sent to tracking clients and self, then resolved to a target entity client-side.

## 8. Mixins

16 mixins include:
- ProjectionFreezeMixin
- ProjectionVanillaRenderMixin
- ProjectionGeckoRenderMixin
- ProjectionCullingMixin
- MonsterDaylightSpawnMixin
- WorldBorderCancelMixin
- QuestCameraModeMixin
- ItemInHandLayerMixin
- ItemInHandRendererMixin
- LookGeckolibAnimationMixin
- CameraONMixin
- CancelEXPOabMixin
- ServerLevelMixin
- ParticlePacketMixin
- UniversalAuraMixin
- GeckolibAuraMixin

## 9. Data/world layer

The artifact includes:
- dimensions: black, questdimension
- 36 damage type files
- 33 worldgen files
- 26 structures
- 130 advancements

This pass maps them for context but focuses on combat/effect engineering.
