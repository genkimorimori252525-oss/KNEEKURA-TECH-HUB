# Client login, respawn and vanilla-skin event bridges

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.15 declarations across three event owners with their exact CLIENT subscription/method annotations and bootstrap callbacks;95 integrity checks/9 negative controls. No game, network sending, skin lookup, thread start or provider execution occurred. No mapping promotion or independent semantic review.

## Login initialization and delayed notice

ClientLoggedEvent `oO0O0O0O0Oo000ooOoOo00OO` skips repeated login events while its static logged-in flag is true. Otherwise setupDefaultModel is called BEFORE setting that flag true and BEFORE checking YSM availability. Setup failure prevents the flag assignment. Unavailability sends the existing unavailable-message call and returns; local-server mode returns without starting the notice thread.

The remote branch creates a daemon thread, sets daemon true then starts it. Its Runnable sleeps60000ms; InterruptedException returns. Otherwise it submits a second Runnable through Minecraft.execute. That second body reads the THEN-current client player and connection, requires nonnull player/accepting messages/channel absent, and issues the server-not-found translated system message. It does not retain the login connection/player, recheck the logged-in flag, or compare a session generation. A delayed notice could therefore evaluate a different current connection after a session change; occurrence/timing are not established here.

Logout only acts while logged-in true: clear flag first, then availability gate, then ClientModelManager.syncAbort. The thread handle was local to login and is not stored/cancelled here. syncAbort invocation is not a receipt of completed native synchronization shutdown or a blanket clearing of all preview/entity/texture caches. Native implementation remains outside scope.

## Respawn bridge transfers retained storage through existing copyFrom

LocalPlayerRespawnEvent `O00oo0OOoO0Ooo0O0oO00oO0` requires YSM availability AND remote-channel presence before touching capabilities. Then oldPlayer.reviveCaps, nested old/new capability lookups, newCap.copyFrom(oldCap), and oldPlayer.invalidateCaps on the normal tail. Missing either capability skips copy but still reaches tail invalidation. There is no local finally, so a throwing lookup/copy can bypass invalidateCaps.

The [roaming-state dossier](ROAMING-STATE-MERGE-RECOVERY-2026-10-17.md) already bounds copyFrom: putAll with retained nested storage, model/texture/disabled changes, then source map/reference clearing. This bridge does not convert it to a deep clone or transactional rollback. It uses event old/new players, not the GUI fake-player cache or arbitrary client entity-arrival recovery. Existing [entity-load deferral](ENTITY-LOAD-APPLICATION-RECOVERY-2026-10-17.md) remains a separate ID-keyed path and was not redundantly recaptured.

## Concrete writer of the special-event texture override

VanillaPlayerRenderEvent `ooO00OO0OooOOo00O0O0O0O0` handles SpecialPlayerRenderEvent. After availability it tests model ID against exact"misc/2_steve" or"misc/1_alex" and requires AbstractClientPlayer. It asks SkinManager for insecure skin information for that player's GameProfile. If the map contains SKIN, it registers that texture and uses the returned ResourceLocation; otherwise it selects the wide Steve or slim Alex resource based on model ID. It finally writes the event's texture override.

The check invokes modelId.equals; no null-ID guard precedes it. The special event's no-argument constructor can contain null, but this does not prove such an event is dispatched to this handler. There is no local skin-upload completion check or fallback catch around external SkinManager calls. No profile data was transmitted by this analysis.

This is an actual Java writer adjacent to the [player entry's pre/post-event texture reads](PLAYER-RENDER-ENTRY-RECOVERY-2026-10-17.md). Its override reaches the explicit argument read after post on normal listener execution; it does not retroactively mutate the renderer field read before post. First-person rendering also posts this event and uses post-event texture/index selection. Listener priority/order against other mods is not established by these default annotations.

## Continuation

Keep setup requested versus completed, login flag versus connection identity, shallow capability transfer versus new entity, and texture reference versus loaded pixels distinct. Next follow the Java client-model synchronization state/listener wrapper only as needed to close logout/readiness, leaving native data parsing/authentication/decryption and provider execution outside scope. Added after the fixed8 render-lifecycle checkpoint.
