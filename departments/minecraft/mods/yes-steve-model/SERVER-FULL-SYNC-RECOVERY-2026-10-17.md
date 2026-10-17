# Dirty/full synchronization orchestration — 2026-10-17

## Scope

Same exact JAR SHA-256 and pinned comparison source as
[producer evidence](SERVER-PROPERTY-PRODUCER-RECOVERY-2026-10-17.md).
Primary static review, independent semantic review NOT_RUN. No runtime, network
transmission, native extraction, whole-source equivalence or new mapping claim.
Full supporting snapshots contain 73 methods across CapabilityEvent (31),
ModelInfoCapability (35), SyncModelInfo (7). The conclusions below concern the
selected dirty/full builder and receiver path, not all event/NBT methods.

| Role | Exact owner suffix |
|---|---|
| CapabilityEvent | OoOoOOOOO0ooooo0O0ooo000 |
| ModelInfoCapability | oooooooOOoOOoO00OooOo00O |
| SyncModelInfo | O0oOOo0OO0000oooOO0ooo0O |

## Server tick and lambda linkage

The ServerTickEvent method first checks YesSteveModel.isAvailable, compares
phase to END at offsets 8–14, enumerates current players, and reads bandwidth
configuration. Its invokedynamic at 73 uses bootstrap 9, targeting the captured
(ServerPlayer, Boolean, ModelInfoCapability) callback.

That callback skips normal synchronization if the player channel is absent and
mandatory is false; only specific tick counts 200/600/1800 reach ServerInfo send.
This is a dispatch condition, not a claim about authorization or transport.

For normal processing, isDirty call 57 and branch 60 select:

1. Dirty: tracker.tick(player,false,lowBandwidth), with ICONST_0 at 68 and call
   at 73. The producer updates cached values without a delta broadcast.
2. Build a full packet with broadcast=true (ICONST_1 at 78, call 79).
3. Optional.ifPresent at 89 invokes bootstrap 16 callback only when a packet was
   produced. If model lookup is empty, no dirty-clear call occurs on this path.
4. The callback clears dirty at 1, then calls broadcast at 6. It optionally
   propagates the model to the player's vehicle only when firstPassenger is the
   same player (identity comparison 24). These are ordinary sequential calls;
   there is no transaction/finally or delivery acknowledgment in the body.
5. Not dirty: tracker.tick(player,true,lowBandwidth), ICONST_1 at 100, call 105.

ModelInfoCapability markDirty is its `oo0OoO00oOoo000O0000o0oo()V` method
(ICONST_1); clearDirty is `Oo00o0OooOOo0ooOoo0oO0o0()V` (ICONST_0).
Both write the same boolean field. No global atomic/thread-safe claim follows.

## Full builder and pending Molang consumers

`buildPacketForDispatch(ServerPlayer,Z)` gets the model by ID and uses Optional.map.
Bootstrap 0 points to its `(ServerPlayer,Z,ServerModel)SyncModelInfo` body.
That body looks up or creates the float map keyed by model info short hash,
using bootstrap 10 for the new empty-map factory. It polls queued Consumers at
28, checks null at 40 and executes each at 50 before constructing the snapshot.
The queue task is removed before execution; the method has no local exception
handler, rollback, or retry guarantee. This is an ordering boundary, not a
reported runtime failure or a claim that queued callbacks throw in practice.

It invokes tracker.full at 84, attaches model-hash Molang values at 96 and creates
SyncModelInfo at 99. Hence full snapshot creation depends on model lookup and
pending task normal completion. The source comment requiring the main thread is
not a runtime thread assertion. Rate limiting in the delta producer is not
called by this builder.

## Receiver order

SyncModelInfo's client path uses EntityLoadEvent deferral and capability lookup.
Its capability consumer is bootstrap 1. It calls updateModelAndTexture at 9,
setDisabled at 17, then DispatchServerDrivenProperty.handle at 25. Model selection
therefore precedes applying the snapshot's properties on this normal path.
`packetHandled` still does not prove entity availability, applied state or pixels.

## Next unresolved lifecycle seam

Pinned source plus previous model/frame evidence show that actual geometry load
resets the state tracker, while resource readiness may delay geometry load.
The new packet receiver ordering alone does not prove that full properties
survive a later readiness-triggered reset, or that every same-model full snapshot
resets the tracker. Trace the exact inherited update/load/reset bodies and all
relevant replay/application paths before diagnosing a bug or proposing a patch.
No behavior change is made by this research.

## Verification

`tools/server_full_sync_ysm_265.py` takes --jar, --source-root, --evidence, --out.
The matching receipt passed 384 integrity checks and rejected 13 mutated fixtures
including missing dirty clear, wrong optional dispatch, peek instead of poll,
invented finally and skipped receiver calls. Complete snapshot validation is
not independent semantic review. Central map remains 669 with unchanged bytes.
The earlier fixed17-cohort checkpoint is not modified to imply inclusion here.
