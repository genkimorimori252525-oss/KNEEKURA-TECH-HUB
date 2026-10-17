# Vehicle model transfer: optional state versus deferred projectile state

PRIMARY_STATIC_REVIEW_ONLY. Exact artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Four new owner snapshots contain31 declarations, not31 independently recovered behaviors. No target execution or central mapping promotion.

| Comparison role | Exact owner suffix |
|---|---|
| VehicleModelInfoCapability | oOOOooO00oo0oOooooOO0Oo0 |
| VehicleModelInfoCapabilityProvider | OO0O00oO0OOO00oOO0OoO0OO |
| VehicleAnimatableCapabilityProvider | O0o00oO0O0ooOOOo0oo0Oo00 |
| SyncVehicleModelInfo | o00o00Oo0oooo00o0oo000o0 |

Existing [server/full](SERVER-FULL-SYNC-RECOVERY-2026-10-17.md), [roaming merge](ROAMING-STATE-MERGE-RECOVERY-2026-10-17.md) and the new [projectile transport](PROJECTILE-CAPABILITY-TRANSPORT-RECOVERY-2026-10-17.md) provide the joined caller, animatable and client-wrapper bodies. They are reused rather than counted as newly recovered owners.

## Important producer difference

Both CapabilityEvent transfer helpers require the player's model-info capability and skip when player channel is absent AND mandatory=false. The vehicle path then calls ModelInfoCapability.getMolangVars followed by Optional.ifPresent. Missing model lookup does not queue this vehicle callback. The projectile path instead calls executeWithMolangVars, which may enqueue its callback. A shared-looking transfer name therefore does not imply a shared waiting policy.

When the vehicle optional contains a map, its callback reads the player's model ID, stores that ID plus the existing map reference in VehicleModelInfoCapability.update, constructs SyncVehicleModelInfo, and requests a visibility broadcast. The helper itself does not assert that the player is the vehicle's first passenger. The previously captured dirty/full caller applies that identity condition before invoking it; another caller cannot inherit that check merely by calling the same helper.

The separate maid vehicle helper has its own first-passenger check and supplies a new empty map, but the earlier exact inventory found no Java invocation of that helper. Do not substitute the existence of this player route for evidence that the maid helper is active.

## Retained state, persistence and codec

The vehicle capability starts with "default", initialized=false and a new empty map. Update and copyFrom retain map references. Deserialization clears and repopulates the current map after reading owner_model_id and initialized; serialization writes those values plus molang_vars_server_bound. This matches the bounded aliasing contract of the projectile carrier, not deep copying or immutable launch/riding snapshots. Its serializable provider lazily creates state for query suppliers and NBT entry points, preserving the actual interface bridge methods.

The packet's short constructor creates Int2FloatOpenHashMap(0), whereas the projectile short constructor uses the no-argument overload. Both encoders serialize entity ID and capability NBT; neither serializes its client-bound int map. Vehicle decoding constructs fresh capability/map objects and interns string keys into local StringPool IDs. Nullable NBT preserves constructor defaults; the receiver does not use initialized as an application guard.

## Client provider and animation installation

The rendering provider stores Entity until initialize constructs the already studied VehicleAnimatableCapability, then clears the stored Entity reference. getCapability returns empty before initialization and a supplier afterward; querying alone does not initialize. The client-wrapper path explicitly initializes it.

The packet reception-side guard delegates to EntityLoadEvent; its application callback gets the wrapper's vehicle provider, initializes, calls init(model ID), then initRoamingVars(map). There is no local transactional rollback or readiness/draw acknowledgement. Entity-load deferral, missing-world behavior and handled=true retain the limits of the existing dossier.

VehicleAnimatableCapability itself was already captured in ROAMING-STATE-MERGE. Its initRoamingVars constructs RemoteRoamingStruct without the projectile capability's explicit null-to-null branch. Its separate updateRoamingVars creates an empty struct only when absent, then merges the supplied values. Full packet initialization/replacement and later incremental updates are different operations; they must not be treated as the same merge.

The pre-animation hook passes the current struct after the superclass hook. Processor installation, model/texture readiness and visible rendering remain later boundaries. No thread-safety, Forge attachment success, native behavior or packet delivery was tested. Independent semantic review is NOT_RUN; the central669 map is unchanged.
