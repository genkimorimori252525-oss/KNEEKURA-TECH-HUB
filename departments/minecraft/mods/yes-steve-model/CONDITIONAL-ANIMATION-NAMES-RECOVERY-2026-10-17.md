# Conditional animation names and model ingestion

PRIMARY_STATIC_REVIEW_ONLY. Fixed artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison source `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Fifty-eight declarations in six owners: ConditionalUse, ConditionalSwing, ConditionManager, ConditionArmor, EnumUtil and ClientModelBuilder. Other builder methods are supporting snapshots, not a new complete loader/authentication review. No mapping promotion, independent semantic review or target execution.

## Actual producer: merged animation keys

ClientModelBuilder `OOOOOO00o0Oo000O0OO0OOO0` separates the animation file named exactly `fp_arm` from other player animation files, merging each destination with putAll. For nondefault models it fills missing main/first-person-arm keys from DEFAULT_MODEL using computeIfAbsent. The returned values are existing Animation references, not cloned animations. It then creates fresh ConditionManager and sends every merged main animation key through manager::addTest (invokedynamic311, forEach316). First-person arm keys go to a separate FPArmConditionManager (342/347).

A fixed-JAR scan of all955 classes found zero direct invoke instructions to this ConditionManager.addTest signature, but one bootstrap method handle used at that exact builder call site. Thus a direct-invoke-only graph would incorrectly miss the producer. [Caller/handle evidence](CONDITION-REGISTRATION-CALLERS-EVIDENCE-2026-10-17.json) records the target, bootstrap and instruction. This is not native/reflection/external closure.

Tag conditions preserve registration order internally, but builder registration traverses an Object2ReferenceOpenHashMap keySet. Therefore “first registered matching tag” does not prove original file order or alphabetical priority. No sorting is applied before the forEach. Default main player animations are marked isCopiedFromDefaultModel on default build, and fallback references preserve that flag; this connects to the hand loop-policy helper. Default first-person-arm/projectile/vehicle marking is not implied by that selected main-animation flagging loop. Nondefault construction expects DEFAULT_MODEL to exist; actual initialization history is outside this cohort.

## Manager dispatch

ConditionManager `oO0OoOoo00ooooO00OoOO00O` constructs eleven condition objects and sends each added name to all of them, in this order: swing main/off, use main/off, hold main/off, armor, TAC, vehicle, passenger, chair. It is not a mutually exclusive prefix router. No clear/dedup method is present in this captured class; each condition's own collection controls duplicates. Getter methods return the retained condition instances.

## Swing/use matching contracts

ConditionalSwing `oOo0oOOOO0ooOOO0oOoOO0oo` uses main prefixes swing$/swing#/swing: with size6, offhand swing_offhand prefixes with size14. ConditionalUse `o0oOOoOooOoOOO0oOoOOoo00` uses use_mainhand prefixes size13 and use_offhand prefixes size12. Names must be longer than the prefix size. Valid resource suffixes register item IDs or tag keys; unavailable tag manager aborts that registration. Extra branches skip exact lowercase `none`, record a recognized UseAnim if available and also record the full name as an inner-classification candidate.

At evaluation: empty item returns empty string (unlike ConditionalHold's explicit hold_*:empty). Otherwise ID match → first matching registered tag → recognized inner category → allowed UseAnim → empty. No new model animation lookup occurs in these evaluators; names were learned at construction. Slot/hand-specific active-action gating happens in the consuming [hand predicates](HUMANOID-HAND-PREDICATES-RECOVERY-2026-10-17.md), not here. ID sets deduplicate; tag lists can retain duplicates.

EnumUtil `ooOOoO0OOO000o0oo00o0ooO` uppercases supplied UseAnim names with Locale.US for EnumUtils.getEnum, then Optional.ofNullable. Its equipment-slot map is built from lowercase slot names, but getEquipmentSlot performs a raw exact lookup without lowercasing the input. This differs from the Molang slot parser documented elsewhere. Input null/format handling should not be generalized beyond the captured calls.

## Armor matching is cosmetic-aware

ConditionArmor `oO000ooO00OO000oOOoo0OoO` recognizes `^(.+?)\$(.*?)$` and `^(.+?)#(.*?)$`, resolves the leading slot through EnumUtil, validates resource text, and stores IDs or ordered tags per slot. It does not itself require that resolved slot is Type.ARMOR. This is consistent with explicit hand-slot controller discovery being possible.

Evaluation uses EquipmentUtil.getEquippedItem (including existing cosmetic provider precedence), checks empty first, then exact ID before first matching tag. Separate helper calls reread equipped item; this is not one immutable item snapshot. hasTest returns whether either map contains the slot, not whether a current item matches. The direct ctrl.armor query instead reads raw entity equipment and rejects non-armor slots; do not merge these contracts.

## Verification and limits

The selected snapshot auditor and the separate direct-reference inventory algorithm both match the fixed JAR; neither is an independent semantic reviewer. The inventory checks955 classes and rejects invented calls/handles/global closure. Raw model decoding/native construction, optional registries, external class behavior and rendered results remain unexecuted. This cohort was added after the fixed nine-cohort checkpoint and is not silently included in it.
