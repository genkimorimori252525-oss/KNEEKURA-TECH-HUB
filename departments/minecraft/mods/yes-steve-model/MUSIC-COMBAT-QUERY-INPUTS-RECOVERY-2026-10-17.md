# Music cache and BetterCombat query inputs

PRIMARY_STATIC_REVIEW_ONLY. Fixed SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source comparison `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Forty-nine declarations across nine owners: ImmersiveMelodies wrapper/data/inner, HumanoidStateTracker, BetterCombat wrapper/inner, ReflectionUtil, PlayerAttackEvent and EmitSwingHand. No independent semantic review, mapping promotion, target/provider execution or packet transmission.

## Music values are cached, not fresh audio measurements

ImmersiveMelodies wrapper `oO000OOooo0Oo0OOO0Ooo00o` uses isLoaded(immersive_melodies). Both binding branches install livingEntityVar im_pitch, im_volume, im_current, im_delta, im_time. Defaults are Float0 for first three and Long0 for last two. Real callbacks read the animatable's HumanoidStateTracker, not necessarily the context entity; an incompatible tracker returns those same zeros. Child contexts sharing the parent animatable therefore do not automatically switch this cache to the child's music.

Inner updater `oO0OOo0Oo00ooO0O0o0O0OOO` calls external EntityModelAnimator.getInstrument. Only a non-null instrument updates: time passed to visualTick is entity.tickCount plus Minecraft frameTime, with only that fractional term forced0 when paused. It obtains provider progress, visualTicks it, and copies raw pitch, volume, current, delta and time. No clamping is present in the adapter; source comments about typical ranges/units are not enforced or runtime-verified here.

No instrument or disabled provider leaves previous cached values unchanged in these updater bodies. Data fields initialize to zeros; a later missing instrument is not an automatic reset. HumanoidStateTracker calls the updater from updateFrame after its superclass work. Existing frame scheduling determines whether that method runs; these queries do not themselves invoke it. Thus nonzero im_* alone is not a reliable proof an instrument is currently present.

## BetterCombat reflected input and conditional failure boundary

BetterCombat wrapper `oOoo00OO0oooO0oo0O00oO0O` checks loaded mod, calls innerInit, then sets INSTALLED=true after normal return. Inner `oo0OOOO0oOoo0o00OOOOOooO` asks ReflectionUtil for a VarHandle to AbstractClientPlayer.attackAnimation with AttackAnimationSubStack type. If no handle, innerInit returns before attack callback registration. The outer method still sets INSTALLED=true on that normal early-return path.

ReflectionUtil `OO00OoOo0O0OooO0oO0OO0oo` uses privateLookupIn/findVarHandle; it catches NoSuchFieldException and IllegalAccessException, prints them, returns Optional.empty. This is captured code, not a reflection operation performed by this research. Other failures are not universally swallowed by that helper.

Both binding branches register clientPlayerVar bcombat_attack_animation. Missing provider returns empty String. Real query calls FIELD_ATTACK_ANIM.get(player) without a local null-handle guard, then checks stack, base animation, active state, KeyframeAnimationPlayer type, and String-valued extraData['name']; failing those later checks returns empty. Missing field-handle is therefore a distinct conditional exception path, not safely represented by all later empty-string checks. No live mixin/provider failure or user-visible bug was reproduced.

## Attack animation → ordinary swing synchronization

PlayerAttackEvent `oo0oOoOOoOOOOo00000O0o0o` implements the provider's attack-start callback. It sets local swingingArm according to offhand flag, swingTime=-1, swinging=true, then calls NetworkHandler.sendToServer with EmitSwingHand. This callback body has no separate YSM availability/remote-channel gate; outer routing may impose behavior not proved here.

EmitSwingHand `oOO0O00OOoO00000OoOoOOo0` encodes/decodes InteractionHand through FriendlyByteBuf enum methods. Handler requires server reception side and a non-null sender before enqueueWork, and marks handled. Scheduled swing checks item empty OR item.onEntitySwing returns false. It starts/restarts only when not already swinging, swingTime>=currentDuration/2, or swingTime<0; it writes time=-1, swinging=true, arm, then broadcasts vanilla animate packet0(main) or3(offhand) from a ServerLevel chunk source.

Duration is6 minus1+dig-speed amplification when that effect exists; otherwise6 plus2*(1+dig-slowdown amplifier), else6. These are animation timing branches, not damage/attack processing. Actual queue scheduling, enum error handling, delivery and client application were not executed.

## Reuse

Keep cached music versus live provider existence, reflected-field readiness versus mod-loaded flag, and animation event versus network delivery separate. These joins connect to [child context](CHILD-CONTEXT-ARROW-RECOVERY-2026-10-17.md), [state tracker](STATE-TRACKER-INPUT-RECOVERY-2026-10-17.md) and [hand predicates](HUMANOID-HAND-PREDICATES-RECOVERY-2026-10-17.md). Scoped audit checks exact snapshots/source/negative mutations only; outside the fixed nine-cohort checkpoint.
