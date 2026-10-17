# Model administration and startup reload: Java producer boundaries

PRIMARY_STATIC_REVIEW_ONLY. Exact YSM artifact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; comparison source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. No command, game, native loader, permission change or external feedback was executed. All source names are comparison labels. Independent semantic review NOT_RUN; central mappings unchanged.

Evidence captures 28 declarations across ModelCommand (`oOo0ooooOO0OOoo0Ooo0oOO0`) and ServerStartingEvent (`oO0000ooOOOo0OOoOo0o0O00`), all operands, bootstrap targets and annotations. Audit: 156 integrity checks, 10 rejecting corruption controls. Counts are not behavior coverage or completion percentages.

## Administrative set differs from client selection

The command tree attaches CommandUtil.hasPermission(source,2) to `model`, then reload, disable and set children. Existing MOLANG-COMMAND-PRODUCER evidence resolves this helper's source permission OR local-player predicate. The optional ignore_auth argument is part of this permission-gated administrative command; it is not an unprivileged client request bypass.

The set handler resolves players, model ID and texture ID, checks initial catalog lookup for null, and emits missing-model feedback then returns 1. Texture `-` selects declared default; blank or absent default selects textures.get(0) at offset 118. The later second catalog lookup and textures.isEmpty test occur at 128–155, AFTER get(0). Thus that later empty check does not guard the earlier fallback access. For a non-`-` explicit texture, this method does not perform a list-membership check. These are conditional Java input contracts, not demonstrations of invalid models accepted by the native loader or observed failures.

The method retrieves the catalog twice rather than retaining one snapshot for all validation. Concurrent replacement and actual thread scheduling are not demonstrated; do not claim an observed race. A present nonempty second texture list permits per-player callbacks. The ordinary ownership branch requires BOTH model-info and owned-model capability, even for unrestricted models; it writes only when the model is unrestricted or owned. The explicitly privileged ignore_auth branch requires model-info capability only. Both writing branches set model/texture then mandatory=true, then report per-player success. No stopAnimation call occurs in these callbacks, unlike the client selection packet's ordinary validation tail. Dirty flags and later transport follow existing SERVER-PROPERTY-PRODUCER/SERVER-FULL-SYNC contracts; feedback does not certify rendering.

Disable stages setDisabled(value) only for present model-info capabilities and reports there. Set/disable/reload ordinary returns are 1, not affected-player counts or end-to-end success. Capability absence can omit work without changing that return.

## Reload has separate immediate, load and synchronization feedback

reload starts one StopWatch and supplies two consumers to ServerModelManager.reloadAndSync at offset 18. Its immediate boolean controls `reload.in_progress` versus `reload.start` feedback, then returns 1 in both cases. These message choices reveal the Java interpretation; they do not independently prove native enqueue/rejection reasons.

The reload-result consumer reports a nonnull message, then on success reports elapsed microseconds divided by 1000.0 and resets/restarts the same stopwatch. The synchronization-result consumer first stops it, then reports overall failure or, on success, calls playerErrors().isEmpty without a local null guard. The previously captured result constructor permits a null playerErrors map; the producer's actual native success/error shape remains unknown.

The sync consumer branches at offset 41 directly to return for an empty per-player error map. Only the NONEMPTY error-map branch reports each error and, on physical DEDICATED_SERVER, emits `model.sync.complete`. Therefore absence of that text is not evidence of incomplete synchronization, and its presence is not proof that all recipients succeeded. This is the actual branch direction, not a correction inferred from message wording. Stopwatch callback order and multiplicity are controlled by unresolved native behavior; do not infer a safe reusable timing protocol merely from source comments.

CommandUtil.sendAsyncFeedback is already captured in MOLANG-COMMAND-PRODUCER: absent current server drops feedback; otherwise server.execute resolves an online sender by UUID when possible, falling back to server command source. This is separate from direct immediate command feedback and from model publication.

## Startup producer

The startup owner and method carry EventBusSubscriber and SubscribeEvent metadata. ServerAboutToStartEvent handler checks YSM availability, then calls reloadAndSync with a reload consumer and null sync consumer, discarding its boolean. It does not locally wait for loading or inspect enqueue success.

On result failure the consumer schedules a server task; the task calls result.message().getString(256) without a null check and constructs/throws `RuntimeException` with the `YSM Loading Failed: ` prefix. A null message would fail before the intended exception construction. Native result invariants, actual startup ordering and exception propagation are not established. Captured annotations do not prove execution.

## Connected review

Use MODEL-ADMIN-CHECKPOINT alongside SERVER-SYNC-BATCH and MODEL-TRANSFER-BATCH. Keep admission, model publication, callback result, message delivery, selected capability state and rendering distinct. No speculative product patch or native behavior claim follows from these static limitations.
