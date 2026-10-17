# Maid render entry, capability ownership and inactive roaming listeners

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.31 declarations/six owners,187 integrity checks/12 negative controls, including exact class/method event annotations. No TLM/Forge runtime, native render, game tick or independent semantic review.

## Capability attachment and provider instance

SyncCapability `O00Ooo00ooOO0OOoo0oOO000` has an instance SubscribeEvent method. It attaches a new provider under yes_steve_model:ysm_maid only for EntityMaid whose level reports client-side. The class is OnlyIn(CLIENT); those attributes and the explicit body gate are distinct evidence. Outer registration and external event dispatch remain necessary.

Provider `OO0oo0O00O0Oo0O00000o0oO` plus its token anonymous class retains the maid. The direction overload ignores direction and delegates. Each no-direction lookup calls LazyOptional.of with this::createCapability and delegates CAP.orEmpty(cap,thatOptional). It does not retain a LazyOptional field. createCapability itself retains a CustomYsmMaidEntity, constructing one with async=true only while its instance field is null. Optional construction and entity construction are therefore different call sites; no external LazyOptional scheduling/resolve behavior was executed here. These bodies add no lock or invalidation method, which does not prove an actual leak or concurrent duplicate.

## Retrieval fallback is not the render-entry fallback

CustomYsmMaidRenderer `O00OOo0oo0O000OOooOOooOo` getAnimatableEntity maps an existing capability or supplies a newly constructed CustomYsmMaidEntity(maid,true) when absent. getGeoEntity delegates to that helper. In contrast geoRender uses capability.ifPresent directly and calls the inherited renderAnimatableEntity only from that callback. It does not use the helper's newly constructed fallback on the missing-capability branch.

Texture lookup likewise maps the capability's getTextureLocation or returns the missing-texture resource. This method adds no local initialized/enabled check; inherited animatable/renderer readiness remains the [shared render-selection contract](RENDER-SELECTION-RECOVERY-2026-10-17.md). Do not equate a retrievable fallback object, a resource location and an actual rendered model.

## Layers and placement

addGeoLayerRenderer appends the external layer reference without local deduplication or a null guard. The override iterates maidLayers and passes entity, limb swing/amount, partial tick, lerpedAge, netHeadYaw and headPitch. It does not call the ordinary superclass layer loop, and uses those latter two fields rather than the superclass loop's rawNetHeadYaw/rawHeadPitch. No per-layer push/pop, exception isolation or angle conversion is added in this override.

setupRotations first calls the superclass, then applies ordered corrections:
- Sitting maid: translate(0,-0.5,0), then return.
- Otherwise riding a Player: translate(-0.05,0.19,0.24), then return.
- Otherwise nonnull vehicle whose exact EntityType is in {MINECART, BOAT, registered BROOM}, with vehicle capability absent: translate(0,-0.5,0).

These are pose operations, not changes to entity world coordinates. Exact EntityType membership is not an instanceof test covering every boat/minecart variant. Capability presence suppresses the final correction without checking that capability's loaded model here. The class initializer resolves the broom registry value externally; no actual availability or initialization timing was tested.

## Registered listener does not imply implemented synchronization

YsmMaidTickEvent `O0oOO0oooooO0O0oooOO0OOO` has an instance SubscribeEvent method and CLIENT annotation. It returns without a local player, otherwise compares player UUID to maid owner UUID and performs a capability lookup only for the matching owner. The linked ifPresent callback's exact body is a single return. This path sends or updates no roaming variables in that callback.

UpdateRemoteStruct `oOOO00oO000oOo0O000OO0Oo` is an OnlyIn(CLIENT) class with ONLY its no-argument constructor. It declares no SubscribeEvent handler at all. The surrounding registration method still constructs/registers it, but the source's commented-out update method is not in the distributed class. Together with the entity's return-only setters/null getter, this narrows the actual inactive Java roaming path without asserting that all external maid synchronization is absent.

## Reuse

Preserve the distinctions between capability presence and readiness, optional wrappers and cached entities, fallback retrieval and rendering, supplied layer inputs and native output, registered objects and actual annotated handlers. [Maid control](MAID-ENTITY-CONTROL-RECOVERY-2026-10-17.md) and [registration](MAID-CONTROLLER-REGISTRATION-RECOVERY-2026-10-17.md) are the connected producers; this pass closes their concrete Java consumers without adding missing upstream features.
