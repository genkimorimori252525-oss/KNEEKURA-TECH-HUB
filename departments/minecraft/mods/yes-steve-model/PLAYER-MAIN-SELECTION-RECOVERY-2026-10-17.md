# Coded player-main selection versus ctrl state queries

PRIMARY_STATIC_REVIEW_ONLY; fixed SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, comparison source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Thirty-nine declarations across AnimationRegister, PlayerMainPredicate, AnimationState and IAnimationPredicate. Abstract test contract has no invented Code. No central mapping promotion, independent semantic review or game execution.

## State registration

AnimationRegister `OOoOOoOO00ooo0Ooo0o000O0` appends nineteen base states to PlayerMainPredicate `ooOoOOO00OO0OO0ooOOOo0Oo`. Names and priorities have the same ordering as the [ctrl priority groups](CONTROL-PRIORITY-ACTIONS-RECOVERY-2026-10-17.md), but use separate state objects and callbacks. Death and attacked explicitly use PLAY_ONCE; other registrations use LOOP via the default registration helper. No dedup/reset occurs in registerAnimationState; repeated calls would append, though actual repeated setup is not established.

AnimationState `oOoO0Oo0oO0o00O0oO0ooooo` retains name, loop type and BiPredicate, and delegates priority clamping to Mth.clamp with bounds0/4. PlayerMainPredicate stores lists in five priority slots. The base idle predicate is always true; other registrations/callers are not globally excluded by this cohort.

## Main predicate order and adapter precedence

Each coded main test obtains Player from the animatable, then returns STOP for null player, preview, nonblank ParCool selection, or a non-null vehicle that is alive. Next Create skyhook condition immediately selects `parcool:ride_zipline` using the no-loop-override helper. This occurs before base state scanning and does not locally check clip existence.

Otherwise scan priority0..4 and insertion order, selecting the first predicate match. For that state's name/loop:

1. Ask SlashBlade main-animation adapter; any non-null PlayState returns immediately (not only CONTINUE).
2. Ask TACZ; ask SWarfare only if TACZ returned null.
3. If the resulting gun adapter state is null, lazily invoke ordinary playAnimation(name, loop); otherwise return the non-null adapter state.

Exact call offsets: SlashBlade165, TACZ184, SWarfare200; null branching172/191; Objects.requireNonNullElseGet217. If no state matches, return STOP. This is one selected base state with adapter overrides, not blending all matching states or unconditional fallback after adapter STOP.

## Do not identify this with ctrl.walk/mainAnimationCache

The main predicate does not consult the ctrl selector's mainAnimationCache. Its movement tests use AnimationEvent.limbSwingAmount. Climb and sneak take abs(event amount)>0.05; walk uses event amount>0.05 without abs. Exact walk lambda is AnimationRegister `o0OOooo0o0OO00OoOOOo0o0O(Player,AnimationEvent)Z`, getter8/constant11/comparison13/branch14. Climb uses Math.abs14, sneak uses Math.abs21.

The ctrl selector instead samples entity.walkAnimation.speed at Minecraft partialTick and tests abs(value)>0.05, with an animatable-shared name cache. Those sources/sign tests/cache lifetimes can differ. Neither this static difference nor a negative synthetic input proves ordinary gameplay divergence; preserve the distinction rather than replacing one implementation with the other during reuse. Flying's remote capability versus local abilities branch and ladder vertical20*(position.y-yo) remain explicit in the registered callbacks.

The earlier ParCool missing-clip concern also reaches this coded main path: main suppression uses name availability, while ParCoolPredicate separately checks model clip existence. Hybrid/model controller choices and runtime schedule still determine visible behavior.

## Playback helper boundary

IAnimationPredicate `oOOO0Oo0O00oo0O0oO0OooO0` playAnimation helpers call event.getCodedController().setAnimation and return CONTINUE. They have no local null-controller or clip-existence check. playLoopAnimation supplies LOOP. The compatibility-hand helper asks ModelFormatVersion.shouldIgnoreCodedLoopTypeForHandAnim, then chooses setter with or without explicit loop; this cohort captures that branch/call but does not infer the external helper's version policy. CONTINUE is an instruction to controller processing, not proof a clip played or rendered successfully.

See [assembly](PLAYER-CONTROLLER-ASSEMBLY-RECOVERY-2026-10-17.md) for player.main installation, [hybrid handoff](HYBRID-PARCOOL-CONTROLLER-RECOVERY-2026-10-17.md), and [coded state handling](CODED-CONTROLLER-STATE-RECOVERY-2026-10-17.md). Integrity audit compares pinned bytes, descriptors, operands, bootstrap targets and source hashes; it is not an independent semantic test.
