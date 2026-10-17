# Player replacement view and optional animation gates

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.13 declarations across replacement event, PlayerAnimator adapter and RealCamera wrapper/inner;89 integrity checks/10 negative controls. No independent semantic review, mapping promotion or external event/mod execution.

## Gates before custom player renderer

`O0oOOo00o0oooOo0OoO0OOo0` carries exact CLIENT EventBusSubscriber and SubscribeEvent RenderPlayerEvent.Pre annotations. It returns when YSM is unavailable, when renderedPlayer.equals(clientPlayer) and self-model disabling is true, when not equal and other-model disabling is true, or when rendered player is spectator. It uses equals calls here, not the identity comparison found in PersonView. There is no explicit client-player-null return in this entry.

The capability callback requires isInitializedAndEnabled. It replaces the player unless ALL of the following are true:

- PersonView.isFirstPersonView(cap)
- FirstPersonCompat.isRenderingPlayer is false
- RealCameraCompat.isActive is false
- DISABLE_EXTERNAL_FIRST_PERSON_ANIM is false
- PlayerAnimator reports THIRD_PERSON_MODEL for the captured local client player

Those conditions are short-circuited in that order. In particular the final PlayerAnimator argument is the local client player, not necessarily the event's rendered entity. Earlier [view evidence](VIEW-TEXTURE-INPUT-RECOVERY-2026-10-17.md) bounds the PersonView/Iris-shadow distinction; this event does not turn them into one universal first-person flag.

On replacement it sets the outer RenderPlayerEvent.Pre cancelled at50 BEFORE fetching/calling the custom player renderer at83. The subsequent [custom player entry](PLAYER-RENDER-ENTRY-RECOVERY-2026-10-17.md) can itself return for SW hide, capability absence or special-event cancellation. Those returns do not undo this earlier cancellation. No visible-output or fallback guarantee follows from reaching setCanceled.

## PlayerAnimator query is a zero-partial sample

`oO0OO00o0OoO0O0O000o0o0o` sets installed from ModList.isLoaded("playeranimator"). When installed, it requests the supplied player's external animation stack and calls getFirstPersonMode with literal0f, comparing by identity to THIRD_PERSON_MODEL. It does not pass current partial tick or add null-stack protection. When absent it returns false without calling the external library. The comment about hiding for the whole tick is an intent cue, not a measured temporal guarantee.

## RealCamera delegation

`O000000oO0O00OOOo0OooooO` starts false, initializes from ModList.isLoaded("realcamera"), then delegates isActive only when installed. Inner `O0O0oO0ooOOoOOOo00o0o00O` directly calls RealCameraCore.isActive. This does not prove camera operation, compatible version or successful runtime linking. There is no separate API-state cache in these two bodies.

## Combined route and remaining boundary

The player entry, inherited render selection, concrete attachment layers and first-person replacement paths are now separate connected dossiers. Keep outer player cancellation, special player event cancellation and ordinary arm event cancellation distinct; they occur at different stages and do not share a draw-success result.

No new frustum/distance culling implementation is established here. Actual Forge subscription order, external listener decisions and the renderer superclass bridge remain external or separately evidenced. Continue unresolved Java resource/render-state lifecycle rather than treating this checkpoint as whole-target completion. The fixed attachment-render checkpoint predates this cohort.
