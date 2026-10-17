# CarryOn, SWEM and Create animation inputs

PRIMARY_STATIC_REVIEW_ONLY. Fixed SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source comparison `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Fifty-six declarations across twelve owners, including CarryOn enum/switch support and Create's exact mixin accessor annotations. No mapping promotion, independent semantic review, target runtime or external-provider execution.

## CarryOn

Wrapper `o0oO0OO0OoO0o00OOo0oOOo0` uses loaded carryon flag. Enabled factory returns a HybridAnimationController with 0.1f transition and CarryOnPredicate; disabled factory is absent. Both binding branches register livingEntityVar carryon_type and carryon_is_princess; absent-provider defaults empty String and false.

Inner `OOoO00oo0oO0O0ooOooo00oO` reads external carry data in BLOCK → ENTITY → PLAYER order, otherwise NONE. This test order differs from enum declaration order ENTITY/BLOCK/PLAYER/NONE, so do not derive priority from ordinal. Princess means current entity rides a Player whose carry type is PLAYER; it does not additionally require that current entity itself is a Player. The public wrapper accepts Player but the real binding calls the LivingEntity inner helper directly.

Binding `OoO00oO0oo00O0o0OOoo0oo0` returns empty type for non-Player or NONE, otherwise lowercase(Locale.ENGLISH) enum name. Predicate `oOOo00oo00O0OOOOoOOo0ooO` rejects null/preview, all SWIMMING pose (not only actual swimming), and FALL_FLYING pose when isFallFlying. It then chooses carryon:entity/block/player with LOOP, otherwise STOP. It does not locally check those clips exist. Raw carry query and animation predicate therefore have different pose gates.

## SWEM horse inputs

Wrapper `o0OOoOOO00O00Oo0oOo00Oo0` uses loaded swem flag. Disabled animation adapter returns null; disabled livingEntityVar swem_is_ride/state return false/empty String.

Inner animation naming `Oo000000000ooOO0oO0o0oO0` and query binding `O0o0OOO0o0OOoOoo00O0OOO0` both examine immediate vehicle instanceof SWEMHorseEntityBase. Neither inner routine adds a vehicle-alive check. JumpHeight>0 takes priority, using min(ceil(jumpHeight),5)-1 then +1 in name (finite positive heights select level1..5). Otherwise notMoving compares sqrt((x-xo)²+(z-zo)²)<=0, an exact horizontal no-displacement test with no positive epsilon, vertical term or partial-tick interpolation. Then gait name is cached per enum in an EnumMap and lowercased English.

Animation adapter returns swem:jump_lvN / swem:idle / swem:gait, or null without horse. Query returns unprefixed jump_lvN / idle / gait, or empty String. swem_is_ride is only type membership and does not imply a particular gait or selected clip. External gait/jump state and actual riding geometry are unexecuted.

## Create skyhook

Create wrapper `OoOoO00OooOoOOO0OO00o0Oo` requires loaded create version >=6.0.0 using DefaultArtifactVersion. Both branches register playerVar create_hanging_skyhook; absent provider returns false. Real inner `O00Oo0o0Oooo0000oO0O0Oo0` checks whether the player's UUID belongs to the set returned by PlayerSkyhookRendererAccessor. It does not infer hanging from position or riding entity.

Captured annotation targets com.simibubi.create.foundation.render.PlayerSkyhookRenderer and Accessor hangingPlayers with remap=false. The static accessor's untransformed body throws AssertionError; it must not be executed as a standalone implementation. This proves declared transformation intent and field spelling, not that Mixin applied successfully with an installed Create version. Main player predicate's earlier skyhook→parcool:ride_zipline selection uses this adapter, with no local clip-presence check.

## Reuse

Keep loaded-provider gates, query defaults, typed guards, pose exclusions, external-data priority and prefixed animation versus unprefixed query values distinct. Follow [humanoid rider precedence](RIDING-ARMOR-PREDICATES-RECOVERY-2026-10-17.md), [main selection](PLAYER-MAIN-SELECTION-RECOVERY-2026-10-17.md) and [hybrid behavior](HYBRID-PARCOOL-CONTROLLER-RECOVERY-2026-10-17.md). Scoped audit validates exact snapshots/source/annotations and negative mutations; later than the fixed nine-cohort checkpoint.
