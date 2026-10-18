# Independent bounded review: visitation and coded capability

2026-10-18. Result: ACCEPT WITH PRECISION NOTES. No substantive contradiction found in the two bounded lifecycle conclusions. This is an independent semantic review and fresh classfile rescan, not independent parser validation or runtime validation.

## Reviewed claims

- `CONTROLLER-VISITATION-ORDER.md`: per-controller process then visit; final shared-bone commit only after the controller loop; conditional skipped-tick producer premise.
- `CODED-CONTROL-CAPABILITY-LIFETIME.md`: four mutation actions use the event's coded pointer, available during predicates and cleared before normal subsequent player/poll evaluation; fresh-event skipped processing leaves that capability absent.

## Verification

Freshly opened the fixed original JAR and parsed all 955 classfiles using the existing audited Python parser, without importing the primary scan scripts. All selected method records in both original-evidence JSON snapshots match the fresh parse, including exact owner/name/descriptor, instruction operands, code hashes, and exception tables. Independently recovered the three exact visitor calls, one direct coded-field write, and two direct setter calls. No matching BootstrapMethods handles found. Independently checked all twelve source entries from the two receipts against their recorded hash and pinned Git blob. These source matches do not establish source/artifact equivalence.

JAR SHA-256: `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`.
Source revision: `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.

## Semantic checks and precision

1. Processor updateModel at147 precedes shouldTick153→168. Thus skipping process163 does not skip dirty update. Bedrock normal clear sets state null and clears active queues, and visitor's state-null branch4→79 emits nothing. The report correctly does not equate skipped tick with immutable retained state or a completed earlier generation. The base frame flag write287 precedes processor call342, so a prior throwing call cannot certify producer completion.

2. Process163, visitor191, and back edge196→108 establish per-controller interleaving. The consumer evaluates polls during visitation, before the next controller's process. The commit580 lies after loop exit115→199. There is no process-all barrier. Hybrid process14/75/125 and active-delegate visitor5 are consistent with the stated normal-return ordering, including the Bedrock-to-Coded selection and Coded-to-Bedrock finalization paths.

3. Bedrock child dispatch needs a construction invariant, not merely lexical call ordering. Process checks depth==5 at96→273, while visitor tests state/subentry/child but not depth. The fresh all-class scan finds exactly two depth writers: constructor87 initializes 1, and private hierarchy setter7 stores its supplied depth. The only direct setter call is process252, passing parent's depth+1. Child field has only allocation/store212 in that guarded processing branch and null-clear46. Under ordinary non-reentrant construction, each child remains at its parent's fixed depth+1; depth-5 nodes never acquire children. Thus no normal shipped counterexample was found. The report should mention this invariant if its child-forwarding claim is presented independently of ordinary-state assumptions. Reentry, reflection, arbitrary preexisting object state, and externally altered state remain excluded.

4. Coded process publishes this at2, invokes Molang predicate7 and optional Java predicate23, and clears null32 before all player-processing branches. No exception handler guarantees cleanup if predicate execution escapes. A stale retained event can therefore retain capability. A different fresh event is not affected by that stale object's field. Same-event reentry is also not stack-disciplined: an inner normal process clears the field rather than restoring an outer controller. The report appropriately excludes reentry rather than claiming general dynamic-scoped safety.

5. The four actions obtain the context's event9, obtain its coded pointer14, and return null22–23 on the null branch before their normal argument evaluation. This proves absence of this specific mutation route, not general expression purity. The passed event and evaluator context must refer to the same event. Child Molang contexts copy the event reference, not the pointer value; ordinary clear is therefore shared.

6. Precision correction requested: the original opening 'each call constructs a fresh AnimationEvent' is too broad. Base update has model-field check1, ifnonnull4→9, and null return7–8. Qualify as invocations that pass that guard and reach allocation411/constructor454. Also, event/context allocation does not imply queue polling: base tick is virtual at488; the base implementation excludes empty models165→374 and skips the processor on shouldUpdate=false277→361. The skipped-controller-process conclusion concerns shouldUpdate=true with shouldTick=false, not every skipped base update. This correction does not undermine the capability-null result on the matching fresh-event path.

## Acceptance scope

Accept the two joins for ordinary, normal-completion, matching-event/context, non-reentrant shipped paths with the above branch prerequisites. Preserve SOURCE_ARTIFACT_DIVERGENCE and source/artifact equivalence NOT_ESTABLISHED. This review does not prove asynchronous result reuse, callbacks' purity, arbitrary controller mutation safety, runtime success, all external callers, reflection/JNI closure, or thread safety. The hierarchy writer scan is direct-instruction evidence; no new whole-program or bootstrap-hierarchy closure is claimed.

No target Java, native code, or assets were run. No asset decoding, CI, network, downloads, Git edits, or blocked-runtime retry. Outputs were written only to this Git-external review directory.

Artifacts: `review-receipt.json` and reproducer `review_scan.py`. The receipt contains compact provenance and reference records, not complete original method bodies.
