# Riding, passenger and armor predicate routes

PRIMARY_STATIC_REVIEW_ONLY. Exact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Twenty-five declarations across VehiclePredicate, PassengerPredicate, ArmorPredicate, ConditionalVehicle, ConditionalPassenger and ConditionalChair. No central promotion, independent semantic review or target runtime.

## Rider animation precedence

VehiclePredicate `OOOo0oO00oOooooooOO00OOo`'s public test converts a null helper result to STOP. Its helper returns null for missing entity, preview, missing vehicle or non-alive vehicle. For a live riding relationship it tries, in order:

1. SWEM nonblank animation name → LOOP.
2. With TLM enabled, nonblank conditional chair name → LOOP.
3. Nonblank ordinary conditional vehicle name → LOOP.
4. Legacy type fallbacks: Pig→ride_pig; any Saddleable→ride; Boat→boat.
5. Player CarryOn-princess condition OR maid riding a Player → carryon:princess.
6. Any non-null TLM vehicle-adapter PlayState.
7. Final sit → LOOP.

Key bytecode calls: SWEM49, chair112, vehicle157, legacy setters200/217/234, CarryOn253, maid predicate267, TLM adapter313, final sit setter332. The Saddleable branch tests interface membership, not whether a saddle is equipped. Early branches skip later checks. Name selection generally does not locally verify a clip exists. Provider internals and actual clip playback remain outside this cohort.

## Passenger and armor

PassengerPredicate `oOooO00oOO00OOO000oo00OO` rejects null/preview and examines only getFirstPassenger, requiring alive. A nonblank conditional passenger name plays LOOP; otherwise STOP. It does not fall back to a universal passenger animation or scan all riders.

ArmorPredicate `OOo0ooo0oOOO0O0OoOOoO0OO` stores one EquipmentSlot; rejects null/preview and empty EquipmentUtil-resolved item. It tries ConditionArmor first. Otherwise slotName:default is played only if getAnimation returns non-null; no local isEmpty test. All playback here uses ordinary explicit LOOP helper, not the hand format-aware helper. Cosmetic present-empty behavior and repeated condition reads follow [equipment](EQUIPMENT-EFFECT-QUERY-RECOVERY-2026-10-17.md) and [conditional-name](CONDITIONAL-ANIMATION-NAMES-RECOVERY-2026-10-17.md) contracts.

## Registered riding names

ConditionalVehicle `OOoo0OOooooOoo0OoO0oo00o` and ConditionalPassenger `o0oOoOOo0ooo00Oo0oo0o00O` register respective vehicle$/vehicle# and passenger$/passenger# names with validated ResourceLocation suffixes. They match immediate live vehicle/first passenger, first exact entity TYPE ID, then first matching registered entity-type tag. ID sets deduplicate; tag lists preserve registration order. Missing registry key/tag manager returns empty. Registration-order provenance comes from the [merged animation map](CONDITIONAL-ANIMATION-NAMES-RECOVERY-2026-10-17.md), not guaranteed file ordering.

ConditionalChair `oo00O0OoO0o00000O0o000oo` only recognizes chair$ names. Although it validates suffix as a ResourceLocation string, it stores the raw substring String, not a normalized ResourceLocation object. Evaluation asks the TLM chair adapter, then compares its chair-model ID string exactly. Consequently omitted namespaces/case should not be silently normalized during reuse. Chair model ID is not the entity TYPE registry ID. This helper itself does not repeat the outer live-vehicle check; its other callers must be considered separately.

## Boundary

These are animations of the humanoid rider/passenger/armor, not physics or movement control for a vehicle entity. They are installed through [player controller assembly](PLAYER-CONTROLLER-ASSEMBLY-RECOVERY-2026-10-17.md). Native output, external SWEM/CarryOn/TLM behavior and actual animation presence were not exercised. The scoped auditor validates exact snapshots and mutation controls; this cohort is later than the fixed nine-cohort checkpoint.
