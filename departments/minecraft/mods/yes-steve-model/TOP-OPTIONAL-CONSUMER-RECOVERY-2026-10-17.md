# Optional The One Probe consumer: registration and guarded lookup

Status: PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source comparison revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. No target execution, installed-plugin assertion, independent semantic review or central mapping promotion.

## Evidence scope

TOP-OPTIONAL-CONSUMER-EVIDENCE records all 15 declarations of three owners, bootstrap targets, full operands, source hashes and annotations. TOP-OPTIONAL-CONSUMER-VERIFICATION checks artifact correspondence: 95 checks and 11 rejecting corruption controls. These are integrity checks, not executed behavioral tests. Source names below are comparison labels, not recovered original symbols.

- InterModMsg: `o0oO0OO0oo00o0O00oOO000o`
- TopPlugin: `oooO000OOOOOOo000OOooo0o`
- YSMProvider: nested `$Oo0Oo0o00O00Oo0OOoOOoooo`

## Registration is an offer, not evidence of activation

The event owner carries EventBusSubscriber(bus=MOD); its InterModEnqueueEvent method carries SubscribeEvent. Its body supplies the strings `theoneprobe` and `getTheOneProbe`, a bootstrap-linked factory constructing TopPlugin, then invokes InterModComms.sendTo at offset 9. The boolean result is discarded at 12. There is no local mod-loaded check, availability check, result check or retry. Annotation presence does not prove an event actually fired or a recipient accepted the message.

TopPlugin's typed function checks probe != null, constructs a fresh YSMProvider and calls registerEntityProvider at 12; otherwise it returns null without registering. The bridge apply(Object) casts to ITheOneProbe before calling this function. There is no local once-only latch. Repeated calls could register additional providers, but external invocation frequency and deduplication are not established. No The One Probe installation or runtime was used.

## Entity branch gates

addProbeEntityInfo tests the inspected entity (argument 5), not the inspecting player. ServerPlayer takes the player capability branch and never falls through to vehicle handling merely because its capability/model is absent. The player callback requires mandatory mode OR the inspected player's YSM channel, then looks up its model ID in ServerModelManager. Model absence omits output.

All non-ServerPlayer entities take the vehicle-info capability branch. The callback requires initialized=true, resolves the owner model ID, then applies a predicate calling ServerModel.vehicleModels() at offset 1 and Set.contains(entity type registry location) at 17. There is no additional channel, availability, world-side or authorization check in this branch. This is a display lookup, not a permission grant; external caller and capability attachment constrain actual reachability.

Both display callbacks create a centered horizontal probe layout and translated model-info label, appending metadata name if nonblank or the model-ID filename fallback. ProbeMode, sourcePlayer, world and hit data have no observed uses in these method bodies. No display cadence or GUI rendering was tested.

## Connection to the conditional lazy-set finding

SERVER-ENTITY-SET-CALLERS already records this predicate as the sole exact Java vehicleModels invocation within the 955-class scan. SERVER-MODEL-RESULT-CARRIERS captures the getter that reads raw-array length without a null guard, and clears the raw field inside the nonempty loop.

This cohort establishes a conditional Java route to that getter, not an actual crash: external TOP acceptance and invocation, a non-player inspected entity, present initialized vehicle capability, present server model, and a relevant raw-array state are all required. Repeated predicate invocations on the same model instance without outside reinitialization are not demonstrated. Native initialization/reinitialization, plugin lifecycle and external exception handling remain unknown. Do not describe this as a reproduced defect or patch upstream from this evidence alone.

## Reuse boundary

Keep optional integration registration separate from readiness. Keep inspected player gates separate from vehicle gates. Do not model the vehicle set getter as an independently proven repeatable pure cache accessor. Preserve existing conditional limitation and do not infer native behavior or whole-source equivalence.
