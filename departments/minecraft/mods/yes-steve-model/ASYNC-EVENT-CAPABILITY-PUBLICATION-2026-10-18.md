# Async event result publication and renderer consumption

2026-10-18. BOUNDED_STATIC_JOIN; [independent review ACCEPT with consumer correction](ASYNC-EVENT-CAPABILITY-REVIEW-2026-10-18.md). This closes the event/capability join explicitly excluded from the fresh-event report. It reuses the existing async submission/wait evidence rather than claiming a complete scheduler or memory-safety analysis.

## Result

The ordinary successful Future-result path returns the worker's event only after its base update has returned normally. Renderers do not construct a new evaluator/context around that returned event or rerun its queue polling. Their shown uses are null gates, the humanoid renderer's EntityModelData read, and limb swing/amount reads in its layer helper. Thus ordinary async result reuse does not itself reactivate the four coded-control actions or create a mismatched renderer evaluator/event pair.

A predicate exception escaping the worker before base update returns cannot publish that partially processed event through this successful-result path. However, the event is already available to predicates/hooks during processing; callbacks could retain it. No whole-object escape proof or blanket claim that the event is inaccessible before task completion is made.

## Exact original paths

Owner prefix throughout: `com/elfmcys/yesstevemodel/`.

CustomEntity owner `oOo00OoOO00O000ooO0Oo00o` stores Future in `O0o00oO0O0ooOOOo0oo0Oo00:Ljava/util/concurrent/Future;`. Its existing submit bootstrap identifies worker `O00OOOooOoooOoo0o0o0oO0O(F)Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;`.

- Worker invokespecial base update at3 with boolean true at2. Returned event is stored locally6; storeFence10 precedes areturn14. The catch-all covers0..7 and executes storeFence19 then athrow23. An escaping base-update exception has no event return from this worker. A failure in the final fence also prevents normal return; it does not publish a partially processed success value.
- Base `o0000OoOooO0oo0o0oooo0Oo.o0OOooo0o0OO00OoOOOo0o0O(FZ)AnimationEvent` has the already-reviewed null-model early return. On the event-construction path it creates event411 and context459, supplies the same event to context469, invokes virtual tick488, and only then returns event493. A fresh original scan finds only one original declaration of the exact `(MolangContext,AnimationEvent)V` tick signature, on this base class. This does not rule out external overrides, called hooks or retained references.
- Wait `oOOOooO00oo0oOooooOO0Oo0()AnimationEvent` initializes local result=null7–8, Future.get13, casts18, stores result21, then loadFence25. The9..28 protected range catches InterruptedException and Throwable. After ordinary catch/normal completion, it clears stored Future42 and returns local result46. If get/cast throws before21, result remains null. If a fence/helper throws after21, the local event can still be returned after the catch, so 'every caught error produces null' would be incorrect. Such an event is nevertheless a value already obtained from get, not an early extraction from a still-running worker.
- CustomEntity override `o0OOooo0o0OO00OoOOOo0o0O(FZ)AnimationEvent` returns wait15→18 directly only for level-exclusive + stored Future. Otherwise it waits20, discards that result23, then calls base update27 and returns30. Nonexclusive rendering therefore uses the new base-update event/context when it reaches construction, not the discarded async event.

These are Java caller/order conclusions under the ordinary submitted Callable/Future completion contract, not an executed worker or an independently verified JDK implementation. An interrupted wait clearing the Future still does not prove job completion, cancellation or safe access to shared model arrays. That existing limitation is unchanged.

## Renderer join: no reused evaluator/context is built

The final base one-argument update method is `o0OOooo0o0OO00OoOOOo0o0O(F)AnimationEvent`; it obtains the rendering-scope flag and dispatches the two-argument override. Fresh scan of955 classfiles finds four direct callsites (full identities in compact receipt):

- GeoReplacedEntityRenderer `OOoo0o0oO000ooO0Oo00OoOo`, call38. Null-event gate59→573 skips the custom-model block but retains ordinary superclass/Post tails. The sole direct event member call in this entry body is extraData72. It also forwards the event at457/565 to its protected renderLayer helper. That helper reads limbSwing43 and limbSwingAmount48, then passes scalar floats to the layer call67, not the event reference. The original exact helper signature has two declarations: this base implementation and a synthetic bridge on maid renderer `O00OOo0oo0O000OOooOOooOo`. That bridge forwards at15 to its typed implementation, which reads limbSwing49/limbSwingAmount54 and passes scalar floats, not the event, to the external maid layer at73. Unknown external overrides remain excluded.
- Generic renderer owner `Oo00o0oOoo00O00ooooOo0OO`, call2; null-event gate14→275. No event member invocation.
- Generic renderer owner `oOoOOO0OOOoo000O0o0oo0OO`, call2; null-event gate14→232. No event member invocation.
- First-person arm renderer `o0oo00OoO00OO0Oo0oo00ooo`, call44; event nonnull51→55, otherwise return54. No event member invocation.

The two generic owners are kept exact rather than inferred solely from similar shapes. All four shown render bodies use the animatable's currently loaded model/arrays for rendering. The returned event is not a frozen pose-buffer snapshot.

Across this artifact, the only two direct MolangContext constructor callsites are base update469 and MolangContext.createChild6. No renderer direct context construction occurs. The only field declared with exact AnimationEvent descriptor is the context's protected-final event field. This typed-field inventory is not a no-escape proof: Object fields, collections, lambdas, external code or retained callback arguments may still carry references.

Consequently there is no renderer-created evaluator/event pairing to reconcile in these direct paths. The worker evaluated against its own fresh context/event pair; the caller receives its event for rendering metadata/gating after normal return. On the normal lifecycle the coded-controller pointer was cleared before player/queue evaluation, as established separately. No renderer event use shown here reads or sets that pointer.

## What remains conditional

Normal completion plus the existing no-external-mutation/reentry premises supports a null coded-control capability in the successful event. It is not a security boundary: the setter is public, the field protected, and callbacks can retain events. Neither original typed-field scarcity nor successful Future.get proves immutability.

A worker may mutate shared model state before throwing, while its returned event is absent. Interrupted waiting can allow unfinished work to coexist with subsequent activity; this report neither reproduces nor repairs that condition. Direct renderer null gates and lack of renderer-side MolangContext construction do not prove array coherence, image correctness, or successful native/GPU work. Unhandled exceptions in callbacks/reporting still retain the earlier documented cleanup limits.

## Provenance and verification

Fixed original JAR SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`. Seven candidate source files match pinned revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6` Git blobs. Whole source/artifact equivalence remains NOT_ESTABLISHED; prior divergence and central map669 are unchanged.

[async event evidence](ASYNC-EVENT-CAPABILITY-EVIDENCE-2026-10-18.json): four update callsite identities, two context-construction identities, typed-event-field inventory, renderer event uses/null branches, worker/wait method digests, layer-helper forwarding/read evidence,17 passing structural assertions and seven pinned source hashes. No full original methods in this compact receipt. Reproducer `scan_async_event.py`; full selected snapshots remain outside Git in `async-event-evidence.json`.

No original Java/native/assets execution, asset decoding, downloads, CI, runtime/403 retry, or Git edits occurred.
