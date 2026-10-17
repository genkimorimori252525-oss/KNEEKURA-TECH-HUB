# Maid controller discovery and deferred renderer registration

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.55 declarations/three owners,294 integrity checks/eight negative controls. No optional-mod/game initialization or target execution.

## Factory layout is not a copy of every player stage

MaidControllerCollection `O0o0o0oo0O0O0o0O0o0ooOOo` initializes only when its static collection is empty, then delegates to the shared two-stage collection builder. There is no local synchronization or rollback of partially appended registrations. This is a conditional initialization contract, not an observed startup race.

The init body has22 registration sites:21 unconditional plus fire guarded by GunFirePredicate.available(). In order: pre_parallel, vehicle, pre_main, main, post_main, pre_hold, hold_offhand, hold_mainhand, post_hold, optional fire, pre_swing, swing, post_swing, pre_use, use, post_use, misc, passenger, cap, parallel, armor, statue. Discovery may expand or omit entries;22 sites does not mean22 instantiated controllers.

Most stages use the player category; misc and statue use maid single discovery with their named animation arrays and hybrid=true. There are two parallel discovery sites here, not the three stages of the separate player collection. Both parallel helpers pass true to ParallelControllerDiscovery. The final parallel factory also supplies its special final constructor flag true; do not collapse these different flags into one setting.

main/vehicle/hand/use/misc/passenger factories pass0.1f as the transition constructor argument; other shown factories pass0. cap uses CodedAnimationController with MaidRoulettePredicate; normal stages use HybridAnimationController. No implicit Bedrock override is added to that cap construction. Adapter inner `...$Oo0Oo0o00O00Oo0OOoOOoooo` returns the player model's animation/controller maps and armor condition, retaining existing ownership rules. It does not clone the maps or use a separate native maid geometry source.

## Event registration and renderer construction occur at different times

TlmClientCompatInner `OoOoo0ooooOo00OO0O0OoO0o` calls the Forge event bus's register with newly constructed screen, capability-sync, maid-tick and remote-struct listener objects, in that order. This method has no local idempotence gate; actual event dispatch requires the surrounding optional integration to initialize successfully. Listener annotations/behavior are separate work and are not inferred from the register calls alone.

Renderer registration assigns a Function to the external EntityMaidRenderer.YSM_ENTITY_MAID_RENDERER field. Only when that function is invoked does it construct CustomYsmMaidRenderer, assign the inner class's cached renderer field and return it. getRenderer merely reads the field and can be null before such an invocation. Assigning the factory is not evidence that a renderer has already been constructed or displayed.

The previously captured outer TlmClientCompat version/installation branch calls event registration, renderer-factory assignment and default animation-state registration in that sequence. It is still the external environment, not this static research, that determines availability.

## Narrow adapter predicates

isMaid/isChair/isSit/isGohei are class tests. hasMaidCap additionally requires the maid capability to be present and maid.isYsmModel true; it does not inspect the animatable's initialized/enabled/model-ready flags here. getChairId returns the chair model ID or empty string for other entities. maidIsFishing requires an EntityMaid with nonnull fishing field. markTacGunAnimationNeedReload obtains the capability on the supplied LivingEntity and sets its reload flag if present, without an additional EntityMaid instanceof gate in that body.

These are Java routing/registration observations. Do not generalize capability presence to readiness, make deferred registration immediate, or treat reference wrappers and source comments as runtime validation.
