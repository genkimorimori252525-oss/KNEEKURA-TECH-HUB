# First-person arm assembly and shared resources

PRIMARY_STATIC_REVIEW_ONLY. Fixed YSM 2.6.5 Forge 1.20.1 SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source comparison `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Forty-three declarations across FPArmControllerCollection plus adapter, CustomFirstPersonArmEntity, FPArmConditionManager and FPArmArmorPredicate. No central promotion or independent semantic review. No YSM/Minecraft target runtime was executed; an isolated JDK regex test is explicitly distinguished below.

## Separate first-person animation map

CustomFirstPersonArmEntity `oo0000o0OO0OooOo00oO0O0o` wraps LocalPlayer and retains its main PlayerAnimatableCapability. Constructor passes false to CustomEntity, stores main reference and adopts the main model ID. Setup invokes playerModel.fpArmControllerFactory. Geometry comes from armModel; animation lookups use fpArmAnimations. Controller-data lookups use the shared player animationControllers map. Width/height use model properties.

Texture delegates to main entity. createResourceHolder returns mainModelEntity.getResourceHolder without allocating a new holder in this method. checkModelUpdate compares model-container references and updates the arm model ID when they differ. This is not a proven disposal/refcount policy; see earlier [holder lifetime](TEXTURE-HOLDER-LIFETIME-RECOVERY-2026-10-17.md). preAnimationSetup places main model roaming struct into the animation processor; it does not clone a private roaming map here. isImmutableRender returns true, but this flag alone does not mean a frozen pose or no animation processing.

## Three discovery families

FPArmControllerCollection `oOOOOOo0OoOOO0OO0OoooO00` lazily installs category `fp.arm` in order:

1. single misc, hybrid=true, no animation-name list, EmptyPredicate. It is discovered via controller or event presence, not automatically emitted from a misc clip.
2. parallel, multi=true, HybridAnimationController with legacy blendRotation=true; ParallelPredicate only when discovered animation name is non-null, otherwise EmptyPredicate.
3. armor, using ordinary ArmorControllerDiscovery but an FPArmArmorPredicate factory.

Adapter reads the shared controller map, separate fpArmAnimations map and separate fpArmConditionManager armor tests. FPArmConditionManager `ooOoooooO0OoOOOO0oO0OooO` only forwards names to one ConditionArmor. It does not reuse all eleven main condition groups. ClientModelBuilder feeds only fp_arm animation keys to it, as documented in [conditional ingestion](CONDITIONAL-ANIMATION-NAMES-RECOVERY-2026-10-17.md).

FPArmArmorPredicate `o0oOO00OO00oOOooooOo0oo0` requires a non-null LocalPlayer, non-preview, and nonempty EquipmentUtil-resolved item. It tries the first-person armor condition, then slotName:default only if the first-person clip lookup is non-null, else STOP. Playback uses ordinary explicit LOOP. Shared discovery means explicit controller/event entries can select hand slots while fallback armor tests require armor type; preview instances are suppressed by both discovery and predicate gates.

## Captured regex category nuance, tested without target classes

ParallelControllerDiscovery formats `^%s\.%s_.+` and `^%s_ctrl_%s_.+` without escaping category. The fp.arm category's internal dot therefore remains a regex wildcard; only the separator after category in the controller pattern is escaped.

`tools/DiscoveryRegexContract.java` ran eight isolated JDK Pattern.asMatchPredicate cases after checking those format literals and fp.arm against the captured artifact snapshots. Both controller and event forms accept fp.arm, fpXarm and fp/arm category text; fpXYarm is rejected. [Receipt](FIRST-PERSON-REGEX-VERIFICATION-2026-10-17.json) records code hash, Java version, cases and exit0. No YSM classes, model files or optional mods are loaded by this test.

This demonstrates the library-level pattern behavior, not that a real model contains such names or that the behavior causes a rendering defect. Do not silently escape the category while reconstructing current behavior. The normal canonical names remain fp.arm.*. Other dynamically formatted patterns should be reviewed on their own evidence rather than assuming universal exact category matching.

## Verification boundary

The scoped snapshot auditor checks descriptors, bytes/operands, bootstrap/constants and source anchors. The regex contract checks only JDK matching, not Minecraft rendering. This cohort is after the fixed nine-cohort checkpoint. Native geometry processing and actual first-person renderer behavior remain separate from these recovered Java factory/input contracts.
