# Java client-model synchronization state and listener boundary

PRIMARY_STATIC_REVIEW_ONLY. Exact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.48 selected/support declarations across manager, state, enum and listener;263 integrity checks/12 negative controls. Thirty manager declarations were selected for state/listener/default-init/queue-publication and their same-owner Java/bootstrap dependencies. Native receive remains a declaration with no Code. Packet sending, model decoding/authentication and native implementation are not analyzed or executed here. No map promotion/independent semantic review.

## State access is not a progress-completion guarantee

getSyncState asserts game-thread access then returns the retained mutable state object. Its fields are ordinary state fields, not a separately immutable snapshot. Initial type is WAITING, total/received are-1. setType(any supplied type) resets both counts to-1. setSyncing(total) writes SYNCING, supplied total and received0 without its own positive-total validation.

receiveServerInfo directly chooses LOADING for local server, IDLE otherwise, then invokes listeners. Unlike several other callbacks it contains no Minecraft.execute wrapper in that body. The listener interface's all-client-thread comment does not independently establish every caller's thread.

syncPreparation(-1) submits a Runnable setting PREPARING and notifying preparation. Other totals submit a Runnable choosing SYNCING only for total>0, else IDLE, then notify progression with the supplied total and0. The callback accepts values below-1 into the latter branch; no global range contract is proven here.

## Terminal progression callback reads reset total

The selected progression Runnable only acts while state.type==SYNCING. It increments received, retains that new value in a local, compares equality to current total, and on equality calls setType(IDLE), which resets the state counts. The listener callback then reads state.getTotal and passes the retained received value. Therefore on the ordinary equality transition it can report(-1,completedCount), not(originalTotal,completedCount). Listener mutation can further affect later listeners because total is read from shared state per callback. This follows exact bytecode/order; no UI symptom or protocol defect is claimed.

The callback's Java-body semantics are captured without executing the native/data producer or claiming that every model reaches it. A progression notification and model publication are separate events.

## Queue publication and returned maps

Manager tick returns for empty NEW_MODEL_QUEUE. Otherwise it shallow-copies the current model map, polls pairs until null, puts each model under its path (later same-key pair wins), assigns the new map to the volatile field, then notifies onNewModelLoaded with that same mutable map object. Map getters return retained map references, not defensive copies or immutable wrappers. Concurrent producers and external listener mutation need their own contract; volatile publication of the reference does not make its contents immutable or establish full native upload completion.

No local per-tick maximum bounds the drain loop. The queue-size getter is a size observation, not a generation or completion receipt. The [client tick ordering](RENDER-SELECTION-RECOVERY-2026-10-17.md) places this service among other updates; do not equate a received/progression count with fully visible assets.

## Weak listeners and exception handling

Listeners are WeakHashMap keys with null values. Registration returns the listener reference, removal uses remove(key,null), and invocation iterates the live keySet rather than a snapshot. Each consumer.accept is inside a Throwable catch that prints its stack trace and continues on the normal path. Iterator operations are outside that catch; mutation during callbacks is not uniformly protected. The map has no local synchronization, order guarantee or strong ownership promise. Interface default callbacks are empty.

syncFailed's scheduled body sets IDLE then invokes a callback casting a nonnull supplied Object to Component. A wrong-type object can therefore throw inside the per-listener caught region; a later instanceof guard only controls player-message/log output, not the earlier cast. Do not silently describe the entire method as type-safe because of that later guard.

## Abort and default initialization

syncAbort first passes null to the declared native receive method, then submits a Runnable setting WAITING. Native behavior is unknown; if that call fails, scheduling is not reached. The separate syncAborted callback submits IDLE+listener notification. Requesting abort is not evidence the completion callback ran, and order between external/native callbacks is unproven.

setupDefaultModel loads the volatile Runnable, synchronizes on that initially read object, rereads the current field inside the monitor, runs it if nonnull, then clears the field. Monitor exit is protected on exceptions, but field clearing occurs only after successful run. This is not a fixed global lock, nor proof of once-only execution under arbitrary concurrent replacement of the Runnable. The producer/body of deferred model construction is a separate boundary.

## Reuse

Use explicit states/generations and listener lifetime when reusing these concepts; do not infer transactional state, listener ownership, complete assets or successful native abort from method names. This closes the Java state/listener seam from login/logout and retains the protected implementation boundary. Future continuation should inspect relevant Java consumers of these state events, not run or replace native synchronization.
