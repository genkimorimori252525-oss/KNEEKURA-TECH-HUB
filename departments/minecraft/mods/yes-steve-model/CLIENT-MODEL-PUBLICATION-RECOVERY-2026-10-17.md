# Client model publication, alteration and default initialization

PRIMARY_STATIC_REVIEW_ONLY. Fixed artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, comparison source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Twelve selected methods in ClientModelManager `o0OooO00ooo0OO000O0OoOoO`, complete owner declaration/bootstrap support, 71 checks and 10 rejecting corruption controls. No model, callback, texture registration or native code executed.

These Java producers are labeled Native Access by comparison-source comments. That provenance does not prove actual native caller identity, thread, order, multiplicity or input invariants. The remaining native implementation is not decoded by capturing these bodies.

## Pack catalog versus texture work

updateModelPackInfo builds a new fastutil map. Blank pack names construct a replacement carrier using the hierarchy's last-folder label while retaining description/icon/language references. Entries use hierarchy as key; duplicate hierarchies overwrite the map entry, while each nonnull icon still schedules a registration task. The loop does not locally validate array entries/null hierarchy.

For old packs, release is scheduled only when the new map does not contain that hierarchy AND the old icon is nonnull. A surviving hierarchy with a new null icon does not take this release branch; that observation alone is not proof of a resource leak because texture-manager replacement/external ownership behavior is outside this method. Registration/release helpers use Minecraft's texture manager; submitted futures are discarded. PACKS assignment at offset210 occurs after scheduling, without awaiting those futures. Catalog publication therefore is not a certificate that GPU/texture work finished. Native-side ordering and actual task execution are unresolved.

## Alteration is shallow, staged and nontransactional

The outer alterModel captures its four arrays by reference in a Runnable and calls Minecraft.execute; there is no local defensive copy. The task first copies MODELS into a new map, removes requested IDs and gathers found ClientModel objects, and schedules their texture-release task before later alteration/publication. It does not wait for that task.

For rename/authorization updates, it first removes all alterModelIds into a temporary ClientModel array, then iterates that array. Only nonnull models read needAuth[i] and dstModelIds[i], mutate the existing client-info authorization flag, and put the same model object under its destination key. There is no local array-length/null validation, duplicate/collision rejection, or rollback. A destination can overwrite an existing entry; the two-pass order preserves source objects during ordinary swaps. These are conditional Java contracts, not demonstrated native-invalid input or an observed race. A failure after object mutation can leave changes visible through shared objects even before assigning the new map; previously scheduled release is not rolled back.

At offset195 the map is published. onAlterModels is invoked when either supplied removal/alteration array is nonempty, regardless of whether any source ID existed. Nonnull empty arrays can still cause a new shallow map publication without listener notification. The listener receives that map reference, not a separately proven immutable snapshot. No all-resource disposal guarantee follows from removing a model ID.

## Default initializer and ordinary additions

addModel with isDefault=true stores a Runnable capturing data/path and returns. Its Runnable later calls addModelInternal(data,path,true,false): incoming needAuth is not forwarded for the default model. Nondefault additions call setupDefaultModel first, then addModelInternal(data,path,false,needAuth).

setupDefaultModel reads the current Runnable, synchronizes on that object, rereads the shared field, runs a nonnull initializer, and clears the field only after ordinary completion. The generated exception table releases the monitor; it does not clear the initializer on failure. This is not enough to prove once-only behavior under concurrent replacement of the Runnable; no concurrent schedule was exercised. Successful execution of a null-data initializer also reaches ordinary clearing without constructing a default model.

addModelInternal with nonnull data calls ClientModelBuilder within an Exception catch. Default build failure rethrows. Nondefault build failure logs and returns BEFORE scheduling the receive-progress task. A successful build enqueues Pair(model,path) in NEW_MODEL_QUEUE. Successful default build additionally assigns DEFAULT_MODEL, schedules first-texture registration, and returns before ordinary progress scheduling. The texture task obtains texture index0 without a local emptiness guard, registers it with the true flag and stores the holder; actual data invariants/texture completion remain untested.

Null model data bypasses building but reaches progress scheduling, including when isDefault=true. A successful nondefault model also reaches that scheduling. Thus a progress increment is not a universal count of successfully built models; an ordinary build exception follows a different branch than null data.

The existing CLIENT-MODEL-SYNC-STATE progress task increments only in SYNCING, sets IDLE on equality with total, then notifies through current state. Its setType resets counts, so completion notification can observe reset total while retaining the locally captured received count. Existing tick drains queued pairs into a copied MODELS map and then notifies onNewModelLoaded. Queue insertion, received progression, map publication and texture readiness are separate stages, not one success flag.

## Reuse

Use the fixed CLIENT-PUBLICATION checkpoint to connect input carriers, builder/containers, language metadata, texture ownership and state callbacks. Preserve asynchronous ordering and conditional limitations. Do not turn source comments or a successful integrity audit into runtime/native correctness claims. Independent semantic review NOT_RUN; central mappings unchanged.
