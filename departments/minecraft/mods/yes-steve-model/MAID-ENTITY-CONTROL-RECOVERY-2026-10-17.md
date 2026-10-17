# Maid entity animation control and remote-struct limit

PRIMARY_STATIC_REVIEW_ONLY. Artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.49 declarations/five owners,272 integrity checks/10 negative controls. No TLM/game execution, independent review or mapping promotion. Source-path presence in an older broad role inventory is not evidence that these full behaviors were previously recovered.

## Entity bridge

CustomYsmMaidEntity `Ooo0OOOOOoooo0oo00OoO0oO` extends the humanoid adapter. Controller setup retrieves the player-model maid factory, casts to Consumer and accepts this entity. The body adds no null/availability guard of its own. Its resource-holder override passes the incoming fallback flag, true,true and600 to HumanoidResourceHolder; inherited readiness/lifetime behavior remains the earlier contract.

MaidStateTracker `O0O0ooOOO00oO0OOO0o00oO0` adds only constructor delegation and a reset that calls the superclass. It is not a separate maid-motion simulation. Compiler bridge methods in the entity are retained without counting each as a distinct feature.

The entity reads roulette-playing/dirty/name directly from EntityMaid and clears dirty by writing false. It retains/replaces MaidModelInfo by reference identity, forwards model/texture changes to inherited updateModelAndTexture, and exposes the loaded model's cached TLM location adapter. A source comment saying the class was copied from a player is not proof of identical player behavior.

## Remote roaming methods are actual no-ops here

The exact setRemoteStruct(Object2FloatOpenHashMap) and updateRoamingVars(Object2FloatOpenHashMap) bodies consist only of return. getRemoteStruct returns null. preAnimationSetup calls its superclass first and then passes that null-returning accessor to AnimationProcessor.putRemoteStruct. These are binary observations, not reliance on source TODO comments.

Do not advertise this maid adapter as implementing the player's remote roaming-variable behavior merely because it exposes similarly named methods. This does not prove every maid capability or external TLM networking feature is absent; it bounds these specific override paths. No implementation was added to change upstream behavior.

## Main-animation priority

YsmMaidMainPredicate `ooOOOo0OooOoooO0OoOOOO0o` stops for a null maid, preview entity, non-ENTITY render state or a living vehicle being ridden. Otherwise it scans five priority lists from0 through4, preserving insertion order within each. On the first matching predicate it tries SlashBlade, then TACZ, then ordinary playAnimation if TACZ returns null. It returns that selected result rather than continuing to a later state when playback is STOP. This body does not invoke the player's Parcool/SW main-selection branches.

GeoMaidAnimatedRegister `oOoooOoO0Ooo0oo00oOOOooo` appends13 default states:
- priority0: death (PLAY_ONCE), sleep, swim, ladder_up, ladder_stillness, ladder_down
- priority1: sit
- priority2: swim_stand, attacked (PLAY_ONCE), jump
- priority3: run, walk
- priority4: idle

Other defaults use LOOP. Ladder speed is20f times a float-narrowed double positionY-minus-oldY difference, checked >0/==0/<0 with climbable. Jump tests airborne and not in water, not upward velocity. Run tests on-ground plus sprinting; walk tests on-ground plus event limb amount strictly >0.05, without abs. Idle always matches. Registration indexes directly by supplied priority and appends; no local deduplication, reset or bounds validation is added.

## Roulette selection

MaidRoulettePredicate `o0OOOO0O0000OoOo0OOOOoo0` handles previews first: an available preview loops that name; otherwise STOP. Ordinary entities play only when roulette-playing is true. Within that branch, dirty is cleared before coded-controller.indicateReload, then the current roulette name is played. When playing is false the dirty flag remains untouched. The body supplies no local controller-null guard, rollback or exception handler; this is not evidence that the normal caller provides an invalid controller.

## Related seams

[Controller registration](MAID-CONTROLLER-REGISTRATION-RECOVERY-2026-10-17.md) supplies the factory layout; [TLM location adaptation](TLM-LOCATION-ADAPTER-RECOVERY-2026-10-17.md) supplies live locator wrappers. The real/fallback query bindings and version checks remain [a separate adapter dossier](MAID-QUERY-ADAPTER-RECOVERY-2026-10-17.md). None alone proves optional dependency availability or rendered behavior.
