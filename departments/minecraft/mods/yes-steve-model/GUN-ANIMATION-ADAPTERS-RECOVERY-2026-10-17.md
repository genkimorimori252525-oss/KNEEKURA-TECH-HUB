# Optional gun-animation entry points and ID/query contracts

PRIMARY_STATIC_REVIEW_ONLY. Fixed SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source comparison `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Fifty declarations in GunFirePredicate, ConditionTAC, TACZCompat, SWarfareCompat and TacCtrlBinding. No target runtime, external provider execution, independent semantic review or central mapping promotion. This is visual-animation integration, not weapon simulation.

## Fire-controller admission and priority

GunFirePredicate `oOO0oOoOooO0Oo00OoO0O0OO` is available if either TACZ or SWarfare adapter is installed. Player collection evaluates that during collection initialization. Its test rejects null/preview. It only asks adapters when entity is neither swinging nor using an item; otherwise STOP. It passes raw mainhand ItemStack to TACZ once-animation first, SWarfare only on null, then defaults null to STOP. A non-null adapter STOP does not cause fallback to the second provider.

TACZCompat `OOO0O0O0oo0ooooo00oOOOO0` initializes from ModList.isLoaded(tacz), then registers inner events when present. SWarfareCompat `O0O0O000oOo00ooooO0O0o0o` requires superbwarfare version >=0.8.7.1 using DefaultArtifactVersion, then registers its arm-render replacement. These are captured gates, not proof those mods are present in a live session.

Both main/once wrappers require installed and inner isGun. TACZ hold also checks isGun; SWarfare hold only checks installed before delegating, so the inner implementation must decide item eligibility there. Do not assert identical wrapper guards. Offhand render wrappers push pose, delegate, pop pose on normal return; no local finally proves stack restoration after an exception. Other native/render/provider internals remain outside this cohort.

## Gun IDs are not one universal registry

ConditionTAC `OOOoOOo0oO00O0OoOO0oO00O` only learns names starting tac: and containing $, uses StringUtils.split with max2, validates the suffix as a ResourceLocation and stores both full raw animation name and parsed ID. doTest rejects empty item, asks TACZ getGunId first, then SWarfare on null. When the ID is registered it removes exactly the final character of the supplied prefix, appends $ plus the ID, and requires that constructed full name in nameTest. It does not validate that prefix ends with a colon or is nonempty in this body.

TACZ getGunId delegates to its inner provider. SWarfare getGunId, when installed, returns ForgeRegistries.ITEMS.getKey(stack.getItem()) directly, with no isGun check (registry call13). Thus name alone must not be treated as proof of gun eligibility. Full raw name storage versus parsed ResourceLocation normalization also matters: matching IDs alone does not ensure reconstructed canonical name equals the originally registered text. Preserve both membership gates.

## Nine ctrl.tac_* names

TACZ's real and missing-provider branches register the same livingEntityVar names. Missing provider returns false for hold_gun/is_fire/is_aim/is_reload/is_melee/is_draw, empty string for gun_type/gun_id/fire_mode.

TacCtrlBinding `O0OoOo00OoOOoOo0oo0O00oo` real callbacks:

- hold_gun: external IGun.mainhandHoldGun.
- gun_type: raw mainhand→IGun or empty; TimelessAPI common gun index or empty; then index type.
- gun_id: raw mainhand→IGun or empty; provider gun ID.toString.
- is_fire: synced shoot cooldown>0, not proof of a shot this frame.
- is_aim: synced aiming progress>0, not only fully aimed.
- is_reload: synced reload state's countdown>0.
- is_melee/is_draw: corresponding synced cooldown>0.
- fire_mode: external mainhand FireMode.name unchanged (no lowercase) unless UNKNOWN, then empty string.

These callbacks do not all pre-check hold_gun. For example, operator getters are called directly once the LivingEntity guard accepts context. Provider absence and wrong context remain distinct from external operator behavior. Inner animation selection/cooldown mutation and event timing are not established here; the next seam is those inner adapters.

See [main selection](PLAYER-MAIN-SELECTION-RECOVERY-2026-10-17.md), [hand hold precedence](HUMANOID-HAND-PREDICATES-RECOVERY-2026-10-17.md) and [model name ingestion](CONDITIONAL-ANIMATION-NAMES-RECOVERY-2026-10-17.md). Scoped verification checks exact evidence/source and negative integrity mutations; later than the fixed nine-cohort checkpoint.
