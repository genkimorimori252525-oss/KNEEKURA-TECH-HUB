# Shield cooldown and effect events to synchronized query state

PRIMARY_STATIC_REVIEW_ONLY. Exact YSM2.6.5 SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, comparison source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Eleven declarations across LivingShieldBlockEvent counterpart `OOOOo00OoOo0000oo000OOO0` and MobEffectSyncEvent counterpart `OO00Oo0O00oOo0O00OoO0O00`. No game events or packets were generated; no confidence promotion.

## Shield cooldown is key presence, including stored zero

The ShieldBlockEvent body gets the LivingEntity's persistent CompoundTag and stores integer5 under ysm$shield_block_cooldown. It has no local YSM-availability, physical/logical-side, player-type, blocked-damage or cancellation check. These absences describe the body only; external event dispatch/cancellation behavior is not established.

The living-tick body first tests whether that key exists. If its integer value is positive, it writes value-1 and returns without removing the key. Otherwise it removes the key. The query helper only checks contains(key), not value>0.

For an ordinary integer5 just written, and six consecutive invocations of this body with no other writes, the stored sequence is4,3,2,1,0,absent. The presence predicate remains true at stored0 and becomes false on removal. This is a static branch consequence, not a measured six-tick duration: block/tick order, sampling time, event delivery and other writers affect a game's timeline. A repeated block assignment resets the value to5 rather than accumulating or taking max.

The two methods carry SubscribeEvent annotations with no encoded elements. The class EventBusSubscriber explicitly carries modid=yes_steve_model; no explicit dist or bus is encoded. Annotation defaults and actual registration are external facts, not silently supplied by the evidence parser.

## Shield sampling and query provenance

The already captured [server property producer](SERVER-PROPERTY-PRODUCER-RECOVERY-2026-10-17.md) samples this presence helper. Its local cached boolean is updated when changed, including sync=false; staging and rate-limited broadcast are separate operations. The full builder explicitly stages true only, and the [player-property receiver](PLAYER-PROPERTY-QUERY-RECOVERY-2026-10-17.md) updates shield state only when its presence bit is set. Full alone does not universally reset absent fields.

YSM's in_shield_block_cooldown query reads the player capability's tracker, including the local-player capability route; otherwise it returns false. It does not directly test the live entity NBT in that query. The six-invocation local sequence must not be advertised as six identically timed client-visible samples. No corrected timing or missing-bit patch is introduced.

## Effect event guards and supplied level

All three effect event methods return when YSM is unavailable or the entity level is client-side, then require a ServerPlayer and its model-info capability.

- Added requires the effect retrieved from getEffectInstance to be nonnull; the body does not separately check the instance before dereferencing. Its callback sends amplifier+1 to the property tracker using integer addition.
- Remove requires event.getEffect nonnull and stages removeEffect through the tracker.
- Expired explicitly checks both effect instance and effect before the analogous removal callback.

No local duration, visibility, category, cancellation or final effect-state confirmation is added. The removal event's occurrence is not itself proof that a game effect was successfully removed; engine semantics and other listeners are outside this exact Java inspection. The class EventBusSubscriber and three SubscribeEvent annotations have no encoded elements. Defaults and successful dispatch remain unverified.

## Staging is not direct delivery or map-key deletion

The existing tracker addEffect/removeEffect methods call setupPacket(player,true) and stage the change without immediately broadcasting from those methods. The ordinary tick and rate limiter control subsequent sending. Dirty/full processing can replace pending staging and construct its full snapshot; it is not correct to count one event as one delivered delta.

DispatchServerDrivenProperty.addEffect marks the effects field, narrows the supplied level to byte, and either constructs a singleton map, copies a size-one map before put, or puts into its current map. removeEffect delegates to addEffect(effect,0); it does not remove that key from the outgoing map. Multiple staged values for the same effect are keyed values rather than an ordered event history.

The client effects update uses putAll, clearing first only for a present effects field on a full packet. A zero entry can therefore represent removal without physically deleting a key in the delta route. The query's default zero and local/remote level rules are preserved in [equipment/effect queries](EQUIPMENT-EFFECT-QUERY-RECOVERY-2026-10-17.md) and [player properties](PLAYER-PROPERTY-QUERY-RECOVERY-2026-10-17.md). Byte narrowing, live amplifier+1 and cached levels are different representation boundaries; no unusual live input was tested.

## Connected reuse contract

Keep event occurrence, local NBT/map mutation, sampling, coalesced staging, rate permission, reception, presence-mask application and queried value separate. Event annotations and static integrity checks do not prove event order, cancellation policy, transport reliability or visible animation. Central map669 remains unchanged; independent semantic review is NOT_RUN.
