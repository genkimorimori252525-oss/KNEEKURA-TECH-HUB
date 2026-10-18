# Independent async event handoff review addendum

2026-10-18. ACCEPT WITH CONSUMER PRECISION CORRECTION. The successful Future result does not itself recreate coded-control capability. A meaningful omitted consumer forwarding edge was found and closed below. No whole scheduler, memory-coherence, or runtime claim is made.

## Producer, wait, and fallback

Verified original submission invokedynamic9 uses bootstrap5 to bind the precise CustomEntity worker `(F)AnimationEvent`, followed by Callable submission14 and Future field store17. Worker calls base update3 with true2, stores the result6, executes storeFence10, then returns14. Its catch-all covers0..7 and fences19/rethrows23. A base-update failure before normal return does not yield that event through the ordinary successful Callable/Future result contract. Callback escape during processing is still possible.

Base update's model-null guard and matching fresh event/context construction retain the earlier qualifications. Its event return493 follows tick488. Successful task return certifies this invocation returned; it does not certify every controller was processed, since base tick may skip updating or processing.

Wait initializes result null7–8, calls get13/casts18/stores21, and only then executes loadFence25. The protected9..28 region catches InterruptedException and Throwable. Normal handler completion clears Future42 and returns local result46. A failure before21 leaves null; a helper/fence failure after21 can leave the already-obtained event. Reporting itself can throw, so cleanup is not unconditional. No assertion that any caught error must produce null is justified.

The level-exclusive + existing-Future branch returns wait15→18 directly. Otherwise wait20's result is discarded23 before fresh base call27. This is ordinary branch behavior, not a proof that interrupted waiting completed or cancelled the worker; fallback may proceed while such work remains. No shared-array rollback or coherence follows from event absence.

## Consumer correction found by independent local tracing

A scan of direct event-member calls in the four render entry methods misses same-owner helper forwarding. The humanoid entry stores returned event in local8, uses null gate59 and extraData72, and also loads that event at453/561 for helper calls457/565. Therefore a broad claim that renderer event use is only nullability plus extraData is incomplete.

The precise downstream closure is:

- Base humanoid helper on `OOoo0o0oO000ooO0Oo00OoOo` reads event limb floats at43/48, then calls its layer at67 with scalar floats and the animatable, not the event.
- The renderer family contains a shipped override bridge on `O00OOo0oo0O000OOooOOooOo`, access4164. It casts the first parameter and forwards the event at15 to its specialized helper.
- That specialized helper reads the same event float getters at49/54 and passes scalar floats plus EntityMaid to external `GeoLayerRenderer.render` at73. It does not pass the event to that external layer.
- The other three entry methods load the event only for their null gates. Exact local load traces and helper identities/digests appear in the addendum receipt.

These concrete shipped helper bodies still neither read/set the coded pointer nor create a MolangContext. The all-class constructor scan finds only the known base construction and child construction. This supports the narrow no-renderer-created-context conclusion after including the forwarding chain. External helper overrides, callbacks that retained an earlier event, Object/container aliases, reflection and JNI remain outside the claim. Exact typed-field scarcity is not an object-escape proof.

## Verification and result

Freshly parsed all955 original classes using the same existing audited parser implementation, matched every selected async method snapshot, checked submission bootstrap binding and renderer event local operands, and verified seven pinned source entries. Reproducer: `review_async_scan.py`. Compact receipt: `async-review-receipt.json`. This is independent semantic review, not independent-parser validation.

The primary worker was informed of the omitted helper forwarding and bridge. Accept the successful-return lifecycle claim with those consumer corrections and the existing exception/interruption limits. Source/artifact equivalence remains NOT_ESTABLISHED. No target Java/native/assets execution, network, download, CI, or Git edits occurred.

## Correction verification

Re-read the corrected primary report and receipt after the worker update: opening now includes limb swing/amount; renderer section explicitly includes calls457/565, base reads43/48 and layer67, maid bridge15 and specialized reads49/54/layer73. All17 primary receipt predicates are true. The consumer precision issue is addressed; final disposition ACCEPT within the stated scope.
