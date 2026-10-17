# Server model synchronization: Java scheduling, publication and send completion

PRIMARY_STATIC_REVIEW_ONLY. Exact YSM2.6.5 SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Forty declarations across ServerModelManager `OoOoOoooO0O00oOoO00OOo00`, its $1 send listener and nested traffic context. Four native declarations have no Code and remain opaque. No native/model data, network send or target callback was executed.

## Scheduling and selected model order

syncModelsToPlayer obtains the current MinecraftServer and calls its execute with a Runnable capturing server, requested player and completion callback. The outer body has no null-server guard. In the task, online players are filtered by reference identity of their DimensionType objects, not a dimension-key/world equality check. Their distanceTo(requestedPlayer) floats are sorted with Float.compare.

The sorted players supply model priorities: getSelectedModelIds filters channel-present players, obtains model-info capabilities, keeps present IDs and applies distinct. It does not validate every resulting ID against the current model map in that helper. The native enqueue receives a one-element UUID array and name array for the requested recipient, plus those model IDs and the supplied state callback. This is a Java handoff, not proof of model-stream order/completion inside native code.

reloadAndSync passes a Java callback to native reloadBegin and returns its boolean. The source's nonblocking/busy comment does not prove the native boolean's complete contract. When the callback is invoked, it calls the supplied reload callback first, then obtains the current server and, if present, schedules capability checks and a synchronization enqueue. Recipient UUIDs and names are collected through separate channel-filtered streams; no atomic cross-stream snapshot guarantee is added locally.

## INIT and publication are different milestones

The native-access reloadCommit Java body casts its state to Consumer, obtains the server, and writes volatile INIT=true at10 before checking success or scheduling publication. This assignment cannot certify a successful model load or completed map replacement.

With a server, the scheduled task on success builds a new short-hash set from result model values, then assigns MODELS, MODEL_HASH_SET and AUTH_MODELS. A nonnull completion callback is submitted through ThreadTools afterward even when the result is unsuccessful. Without a server, success assigns MODELS and AUTH_MODELS but does not rebuild/assign MODEL_HASH_SET in that branch; the callback is invoked directly. No unconditional same-thread or all-fields-at-once completion contract follows.

The manager stores the result's map/set references, but the [result constructors](SERVER-MODEL-RESULT-CARRIERS-RECOVERY-2026-10-17.md) request immutable copies. Do not infer that mutating the original input Map changes the committed manager. getModels/getAuthModels return the manager's current reference, not a stable view that follows subsequent replacement; earlier retained references are not rewritten by a later assignment. This is ownership/order evidence, not a demonstrated race.

## Default selection and consistency checks

getDefaultModelAndTexture reads configured names, strips a trailing case-insensitive .png only when length>4, and returns that pair without model lookup while INIT is false. With INIT true, missing model falls back to default/default. A present model retains a valid selected texture, otherwise tries its declared default texture if contained, otherwise list.get(0). There is no local empty-texture-list guard around that final read; native/model validity may constrain inputs and was not executed.

checkCapability runs its nested capability logic only when MODELS is nonempty. Its Java path prunes owned-model names no longer in the relevant sets, may request a set update, validates selected model/ownership/texture with default fallback, and trims roaming storage using MODEL_HASH_SET. This is static observation of the existing validation path; no ownership data or access state was changed.

## Java send loop and completion status

Connection lookup returns null for missing server/player, nonaccepting messages or a listener whose concrete class is not exactly ServerGamePacketListenerImpl. This is exact-class equality, not an instanceof allowance for subclasses.

The send helper initializes traffic-context init=true before assigning highWaterMark=outboundBuffer.totalPendingWriteBytes()+65536. That context retains its threshold for later calls. Each send attempt compares outboundBuffer.size(), widened to long, against that threshold; if greater it calls safeSleep(10) and retries the connected-loop gate.

### External API unit comparison, not a loaded-runtime diagnosis

The [official Netty4.1.82.Final source](https://github.com/netty/netty/blob/netty-4.1.82.Final/transport/src/main/java/io/netty/channel/ChannelOutboundBuffer.java) defines size as a flushed-message count and totalPendingWriteBytes as byte accounting. Under that implementation, the captured comparison mixes message count and a byte-derived threshold; it is not a verified64KiB byte limit. The [reference receipt](NETTY-OUTBOUND-UNIT-COMPARISON-2026-10-17.json) pins the inspected source hash. The YSM JAR does not embed that class, and the actual loaded Netty version was not verified. No throughput/memory symptom or corrective patch is claimed; the YSM integrity auditor does not re-fetch this external source.

For each call the helper creates AtomicInteger status0. The listener sets1 on success before delegating to its interface default, or sets-1 on failure and returns null. The send call alone is inside a Throwable catch; errors there print and return false. The subsequent inner status0 loop sleeps5 and has no local timeout or renewed connection check. Status1 returns true; another status sleeps100, resets to0 and retries while the outer connection predicate holds. Sleep failure returns false. No asynchronous callback or packet was run, so the conditional waiting/retry limits are not a reproduced hang or delivery guarantee.

A true local listener status is not client decoding/application success. syncTaskComplete separately invokes a nonnull Consumer directly; its caller/thread is a native boundary. syncTaskAbort passes UUID and null to native syncReceiveData; the Java call is an abort request, not proof of completed cleanup.

## Reuse

Keep first handshake registration, channel agreement, native request acceptance, INIT, map publication, callback dispatch, local send status and remote model readiness separate. Native algorithms, protected model decoding, actual scheduler behavior and independent semantic review remain outside this primary Java evidence. Central669 mappings are unchanged.
