# Projectile owner state, lazy initialization and client application

PRIMARY_STATIC_REVIEW_ONLY. Exact YSM2.6.5 Forge1.20.1 SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. No target execution, packet generation, native analysis, confidence promotion or original-name claim. The new snapshot captures44 declarations across eight owners, including bridges and constructors; that is not44 independently recovered semantics.

## Grounded comparison roles

| Comparison role | Exact owner suffix |
|---|---|
| ProjectileAnimatableCapability | OOOo0OOOoOO0O00Oo00ooOOO |
| ProjectileAnimatableCapabilityProvider | oOo0o0000OOOO0OooooO00oo |
| ProjectileModelInfoCapability | O0ooooOO0oOo000O0Oo00OOO |
| ProjectileModelInfoCapabilityProvider | OO0ooO00OoO00o0OO0OOooO0 |
| ClientLazyCapability | Ooooo0oooO0oooOOOoO0000O |
| ClientLazyCapabilityProvider | oo0OoO00oOoo000O0000o0oo |
| SyncProjectileModelInfo | OOOOoO00oo0000OO0ooo0OOo |
| Named ProjectileEntityMixin | mixin/ProjectileEntityMixin |

These roles are connected by constructors, capability fields, callback descriptors, NBT keys and the captured packet's actual consumer chain. The old descriptor-only lead for the projectile capability is not being promoted automatically. Earlier [server/full evidence](SERVER-FULL-SYNC-RECOVERY-2026-10-17.md) already contains CapabilityEvent and ModelInfoCapability; those bodies are reused rather than recaptured.

## Owner assignment is not an immutable launch snapshot

The packaged Mixin annotation names Projectile and injects at RETURN of setOwner(Entity)V. Its refmap entry maps that descriptor to Projectile.m_5602_. The configured mixin and encoded metadata are checked, not its successful runtime application. The body first requires YSM availability and a nonnull server-side level. ServerPlayer owners route to CapabilityEvent; other owners route to the maid helper only when its type predicate succeeds. No new owner-type branch is invented.

The existing CapabilityEvent projectile callback skips if the owner's channel is absent AND mandatory=false. For a present projectile model-info capability it calls the owner's executeWithMolangVars Consumer route. ModelInfoCapability resolves the current model and either supplies the retained per-model-hash map immediately or queues the Consumer until a later full builder drains it. That full builder polls before executing and has no transactional retry.

The projectile callback reads the owner's model ID when the callback runs, calls the projectile capability's init(String,map), constructs SyncProjectileModelInfo and requests a visibility broadcast. The callback captures the owner capability/projectile, not a copied model ID or copied variable map. The initializer stores the supplied map reference directly (PUTFIELD12), and copyFrom likewise shares the source map reference (GETFIELD18, PUTFIELD21). Therefore these instructions do not establish a frozen launch-time snapshot. Whether values change before serialization or a deferred callback runs is a separate runtime question; no observed stale-model bug is claimed.

The maid branch remains different: its [common-side helper](MAID-COMMON-MODEL-COPY-RECOVERY-2026-10-17.md) supplies a new empty map rather than this player's retained map. Tracking-entry synchronization separately checks initialized before sending; this does not make every packet receiver validate that flag.

## Persistence and wire representation

ProjectileModelInfoCapability starts with model ID "default", initialized=false and a new empty map. Init sets initialized=true and retains the supplied map without a local null check. Its NBT serializer writes owner_model_id, initialized, and a nested molang_vars_server_bound compound. Deserialization reads the two scalar fields, clears the existing map at24, then repopulates it. It does not replace that map with a fresh copy. Thus another object that already shares this map through copyFrom would observe the same mutation if that path is exercised; this is aliasing semantics, not proof such a copy is invoked in a live game.

The serializable provider creates its backing capability lazily; both serialization and deserialization call that factory. The artifact retains public serializeNBT()/deserializeNBT(Tag) bridges that delegate to obfuscated CompoundTag methods. Generic interface entry points and internal method names must not be conflated.

The message constructors retain the capability and supplied client map. The short constructor supplies an empty client map, but encode writes only entity ID and capability NBT, not that int-keyed map. Decode constructs a NEW model-info capability, optionally reads nonnull NBT, then converts its string variable names through StringPool.computeIfAbsent into a NEW Int2FloatOpenHashMap. It does not send process-local pool IDs on this route. A null NBT leaves the constructor defaults. This is distinct from the separately documented delta codec.

## Lazy rendering capability versus capability presence

The existing attach-event body creates the projectile rendering provider only for a Projectile on the client-side path, and stores it alongside a vehicle provider in ClientLazyCapability. The carrier permits a null projectile provider for other entities. These are declared branch conditions, not a successful Forge attachment receipt.

The projectile rendering provider's getCapability returns LazyOptional.empty while its instance field is null; it does not initialize on query. initialize performs the null guard at4, constructs/stores a ProjectileAnimatableCapability and then clears its original projectile field at24. Subsequent calls reuse the stored instance. Its lazy supplier returns that field. No synchronization or external LazyOptional lifetime guarantee is inferred.

The client wrapper provider instead retains its carrier from construction and returns a LazyOptional supplier for it. Presence of that wrapper is therefore not equivalent to an initialized projectile renderer. This explains why the packet walks through ClientLazyCapability before explicitly calling the projectile provider's initialize.

## Receiver ordering and Molang installation

The handler checks client reception side and delegates entity ID plus Consumer to [EntityLoadEvent](ENTITY-LOAD-APPLICATION-RECOVERY-2026-10-17.md); its ordinary tail sets packetHandled=true. Null world, missing-entity deferral and callback failure remain that helper's distinct paths. Handled does not mean applied.

For a present client wrapper, the callback gets the projectile provider, calls initialize, then calls init(model ID) at13 and initRoamingVars at18. It does not locally test the payload capability's initialized flag, recheck entity type, or check the nullable provider before invoking it. Normal attachment/sender routing supplies the intended projectile relation; no malformed payload was generated and no exploitability claim follows from this local assumption.

The animatable init first calls updateModelId and then setInitialized; neither means that resource readiness or drawing succeeded. initRoamingVars replaces its field with a new RemoteRoamingStruct for nonnull input, or sets it null. Its preAnimationSetup calls the superclass first, then passes the field to AnimationProcessor.putRemoteStruct. The earlier [roaming merge contract](ROAMING-STATE-MERGE-RECOVERY-2026-10-17.md) records that putRemoteStruct ignores null. Clearing this field alone must not be described as an explicit processor-struct removal. The later scope/frame reset rules remain separate.

## Reuse and remaining evidence limits

Preserve five different stages: server model/variable availability, retained references or deferred callback, wire serialization, lazy client initialization, and subsequent model/processor readiness. A successful constructor or handled flag is not visible animation. No native decoder, game launch, packet transmission, actual injection, external capability implementation or independent semantic review was performed. The central669 mapping remains byte-identical.
