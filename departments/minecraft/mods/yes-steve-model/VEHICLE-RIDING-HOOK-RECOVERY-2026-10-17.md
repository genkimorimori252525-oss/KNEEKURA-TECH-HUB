# Riding hook as a second player-to-vehicle transfer entry

PRIMARY_STATIC_REVIEW_ONLY. Exact YSM2.6.5 SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Two declarations in named mixin/ServerPlayerMixin plus an exact helper-caller inventory. No riding action, packet, Mixin execution or confidence promotion.

The earlier [vehicle transfer dossier](VEHICLE-CAPABILITY-TRANSPORT-RECOVERY-2026-10-17.md) identified the helper's Optional-only state acquisition and the dirty/full caller's first-passenger guard. This extension establishes another declared entry instead of assuming dirty/full is the only trigger.

## Exact hook declaration

The class Mixin annotation targets ServerPlayer. Inject names startRiding(Entity,boolean)boolean and an INVOKE target Entity.positionRider(Entity)void, with explicit shift AFTER. The packaged config includes ServerPlayerMixin; its refmap maps those methods to ServerPlayer.m_7998_ and Entity.m_7332_ with full descriptors.

This is an after-invocation injection point, not an injection at the return of startRiding. The callback body does not inspect CallbackInfoReturnable's result, the force boolean argument, or set/cancel the returned value. Therefore the hook metadata alone must not be labeled "after successful riding returned true." Matching/applying the injection to actual Minecraft bytecode remains unverified.

## Body and exact callers

The body returns when YSM is unavailable, casts this to ServerPlayer, obtains the supplied vehicle's first passenger and compares reference identity with that player. Only equality reaches CapabilityEvent.onVehicleSetModel(vehicle,player). No new transfer algorithm is added here; it uses the same previously studied helper.

The declaration-validated [955-class caller inventory](PLAYER-VEHICLE-TRANSFER-CALLERS-EVIDENCE-2026-10-17.json) finds two direct invokes and zero matching bootstrap handles: this mixin callback and the already captured server dirty/full callback. The latter has its own vehicle/non-null and first-passenger checks. These two captured callers support those local guards; they are not a whole-program guarantee about future external/reflection/native callers.

The helper itself separately requires player model-info, channel-or-mandatory acceptance and a vehicle model-info capability. It then uses getMolangVars Optional rather than the projectile path's deferred Consumer queue. A missing model lookup can leave this invocation without transfer. The mixin does not add a retry or wait until the lookup succeeds.

## Why the connection matters

Model changes propagated through dirty/full processing and riding-triggered transfer can reach the same helper at different times. Both retain the helper's map ownership, serialization, client lazy initialization and readiness limits; neither hook occurrence nor a queued/broadcast packet proves a visible vehicle animation.

The separate maid vehicle helper remains a different method with its own earlier zero exact-caller result. This player hook does not establish that the maid helper is active. Central669 mappings remain unchanged; independent semantic review and actual event ordering remain open.
