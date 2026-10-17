# Extra animation and preview controller lifetimes

PRIMARY_STATIC_REVIEW_ONLY. Fixed artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source comparison `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Fifty-nine declarations across ten owners: five small predicates, GUI entity/fake player, preview info/interface and CustomPlayerEntity support. No central promotion, independent semantic review or target runtime.

## Extra animation cap controller

CapPredicate `O0oOO000oo0o0O0OOoOO0ooo` handles preview and normal entities differently. For IPreviewEntity, nonblank preview info plays the selected preview with explicit LOOP; missing preview returns STOP and does not fall through to ordinary extra-animation state. For ordinary entities, playing-extra flag is required. Dirty flag is cleared before indicateReload, then the extra name is selected without an explicit loop override. No local rollback reinstates dirty after an exception.

CustomPlayerEntity playExtraAnimation requires a non-null animation lookup; success stores name, playing=true and dirty=true even when the same name is requested again. Failure only sets playing=false. stopExtraAnimation likewise only clears playing; name/dirty persist until other transitions. Geometry reset clears playing, restores name idle and clears dirty. postAnimationSetup automatically stops only for localPlayer AND shouldTick AND currently playing with cap coded state IDLE; it then conditionally sends the existing stop message when remote channel is present. No packet was sent in this analysis. Remote/preview lifetime is not automatically identical to this local path.

## Preview GUI predicates

- Hover `O000000OOoOo00oooOOO0oOO`: directly casts animatable to IPreviewEntity. Nonblank hover string sets the GUI entity's allowEmitting flag true, then plays LOOP. Blank hover sets it false, calls current coded controller.stopPlayingSounds, then STOP.
- Focus `OOO000o0OoOo0o0o000OO0o0`: same direct preview cast; nonblank focus plays LOOP, otherwise STOP. It does not itself toggle emission.
- Parallel `oO0O0O00OOO00oOooO000OOO`: unconditionally asks playLoopAnimation for its constructor-supplied name; no local null/blank/clip check.
- Empty `ooO0OooOO0oOO0oo000OOOo0`: always STOP. This does not imply an attached hybrid can never animate, because model Bedrock logic can remain active.

The player collection's preview-only factory conditions justify hover/focus casts on that construction path; the predicate classes are not independently safe for arbitrary non-preview invocations. Their ordering is cap, gui_hover, gui_focus, then parallel/armor families in the existing player collection.

## GUI entity and emission sampling

CustomGuiPlayerEntity `O00000oOo0o0o00OOoo0O0oo` wraps a local fake player and retains PreviewAnimationInfo `oO0Ooo00oOOO00O0OO00o0o0`. Info setters store strings directly; hasPreview uses nonblank checking. reset clears focus/preview/hover and GUI emission flag before super.reset. isActive and isFakePlayer return true; isImmutableRender true is not proof of a static pose. updateAnimation returns null when the fake player cannot obtain current client level; otherwise delegates to parent. Frame-limit input uses refresh rate. Its resource-holder constructor uses the captured flags and literal300 lifetime parameter; this cohort does not measure disposal timing.

GUI allowEmitting is an entity field, distinct from MolangContext.allowEmitting. Existing [frame evidence](ANIMATABLE-FRAME-RECOVERY-2026-10-17.md) samples entity.allowEmitting when calling processor.tickAnimation; the processor passes that boolean to controller.process. A hover predicate's field write does not retroactively mutate the already passed boolean. This is a Java parameter-lifetime distinction, not a measured one-frame audiovisual delay: instruction/event/task paths have their own context gates. The [particle/sound dossier](PARTICLE-SOUND-DISPATCH-RECOVERY-2026-10-17.md) additionally distinguishes fake-player particle suppression from sound handling.

Hover's stopPlayingSounds call is on its current coded controller; it is not proof that all global or other-controller sounds were stopped. No actual UI, audio, fake-player tick or render loop was exercised.

## Reuse

Keep extra-animation flags, preview selection strings, controller PlayState and context emission permission separate. Preserve direct-cast assumptions, dirty-clear-before-reload order and local-only IDLE cleanup. The scoped auditor checks all snapshot/source anchors and negative mutations, not runtime UI behavior. Later than the fixed nine-cohort checkpoint.
