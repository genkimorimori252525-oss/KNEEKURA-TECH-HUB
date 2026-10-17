# Player provider construction versus projectile/vehicle activation

PRIMARY_STATIC_REVIEW_ONLY. Exact YSM2.6.5 SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Fourteen declarations across PlayerAnimatableCapabilityProvider `O0OooOo0oOOoOoOoOooO000o` and ModelInfoCapabilityProvider `Oo00o0OooOOo0ooOoo0oO0o0`. No target execution, Forge fixture, native loading or independent semantic review.

## Different ways to offer a capability

The player rendering provider constructor stores AbstractClientPlayer, leaving its animatable instance null. The two-argument getCapability ignores Direction by delegating to the one-argument overload. That overload passes LazyOptional.of(this::createCapability) to CAP.orEmpty. The bootstrap points to the provider's private factory.

When that factory is invoked, it constructs PlayerAnimatableCapability only if its field is null, stores the result, clears its original player reference and returns the stored instance. Later factory invocations reuse it. Thus the supplier offered by a query can construct the capability; the constructor did not eagerly construct it. The timing/number of supplier invocations and invalidation rules belong to the external LazyOptional/Capability implementation, not these YSM instructions alone.

This differs from the already captured [projectile](PROJECTILE-CAPABILITY-TRANSPORT-RECOVERY-2026-10-17.md) and [vehicle](VEHICLE-CAPABILITY-TRANSPORT-RECOVERY-2026-10-17.md) rendering providers. They return empty while their instance field is null and require their explicit initialize path before a query supplies the stored instance. Do not impose that explicit-initialize requirement on the player provider, or assume a player-like lazy factory exists for every entity.

This refines the [debug target selection](CLIENT-COMMAND-DEBUG-TARGET-RECOVERY-2026-10-17.md) connection: selection uses capability lookup and does not itself invoke initialize, but the player Optional's supplied factory differs from the projectile/vehicle empty-before-initialize contract. Actual capability resolution and attachment success are still not game-tested.

## Server model-info provider and NBT bridges

ModelInfoCapabilityProvider starts with a null backing field. Its direction-bearing getCapability supplies a private create factory through LazyOptional.of; its one-argument overload delegates with null Direction. The factory constructs the already studied ModelInfoCapability when absent and reuses the field afterward.

Both NBT entry points call that factory before delegating, so serialization/deserialization can request construction without a preceding successful getCapability result. The class retains interface bridge methods for Tag and obfuscated CompoundTag implementations. The bridge cast/delegation is recorded; no arbitrary NBT was supplied.

Neither inspected provider caches a LazyOptional in its own fields, declares an invalidate/reset method, or adds local synchronization around its instance test/store. These are local declaration facts, not proof that Forge's entity-level invalidation is absent, that a leak occurs, or that concurrent construction occurs in practice.

## Attachment guards must be read as branches, not type labels

The existing [CapabilityEvent snapshot](SERVER-FULL-SYNC-EVIDENCE-2026-10-17.json) first checks YSM availability. Player model-info attachment is server-side and tests both current capability presence and the pending event resource key. Projectile model-info and remaining-entity vehicle model-info follow their own server-side branches. Other player capabilities in that method are outside this dossier's semantic scope.

On physical CLIENT plus client-side level, an AbstractClientPlayer receives the player rendering provider only when its capability and pending animatable resource key are absent. The method returns immediately only after that addCapability call returns on the ordinary path. The return is not unconditional for every AbstractClientPlayer: a failed guard falls through to the generic client-lazy branch.

That generic branch tests only client-lazy capability/key absence before adding a vehicle rendering provider, adding a projectile provider if the entity is Projectile, and attaching their ClientLazyCapability wrapper. It has no corresponding per-provider duplicate tests inside that guarded block. This describes the captured control flow, not a claim of duplicate attachment under actual Forge event sequencing or other mods.

## Clone paths and ownership remain separate

The earlier [client session bridge](CLIENT-SESSION-SKIN-EVENTS-RECOVERY-2026-10-17.md) records local respawn's availability/channel gates, old capability revival, nested old/new lookups, copyFrom and later invalidation. The provider's factory explains how a newly supplied player instance can be constructed; it does not change copyFrom's shallow reference-transfer semantics or make model/texture readiness immediate.

Likewise the common server Clone callback's capability retrieval and copying must retain its actual ordering; these provider declarations do not prove externally managed Optional lifetime. No new invalidation patch, thread-safety claim or successful respawn was introduced.

## Reuse contract

Separate provider attachment, query construction, supplier resolution, retained backing instance, clone transfer, NBT entry points and resource readiness. Preserve the player versus projectile/vehicle difference instead of treating all LazyOptional wrappers as interchangeable. Central669 mapping remains byte-identical; external Forge lifecycle and runtime remain explicit limits.
