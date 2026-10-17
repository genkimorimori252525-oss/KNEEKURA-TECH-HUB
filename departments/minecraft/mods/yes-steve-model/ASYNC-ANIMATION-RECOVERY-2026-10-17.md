# Java asynchronous animation ownership and wait boundary

Primary static review; independent semantic review NOT_RUN. Fixed artifact
SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f` and
source candidate `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. No JVM/game execution,
thread-safety proof or central mapping promotion. Source/artifact equivalence is
still NOT_ESTABLISHED. This cohort closes the previously open base-class-to-worker
boundary without claiming that every renderer/override path is covered.

## Evidence scope

46 methods across CustomEntity `oOo00OoOO00O000ooO0Oo00o` (32),
AnimationParallelTicker `o0ooooOo0o000OOo0oO00OoO` (5), ThreadTools
`oO0OoOo0OOoOo0OO000OO0oO` (6), and named mixin/client/WorldRendererMixin (3).
All bodies, declarations, encoded operands, handlers and bootstrap records are
retained. Abstract methods retain absence of Code. Four official source files
are pinned and checked. The verifier does not decode Mixin annotations, so the
exact injection positions below remain source-candidate context, not a verified
runtime hook attachment or a bytecode-annotation claim.

## Submission and actual worker entry

CustomEntity.beginAsyncUpdate(F) invokes Unsafe.storeFence at3, constructs a
Callable through invokedynamic at9, submits at14 and stores the Future at17.
BootstrapMethods index5 identifies instance method
`O00OOOooOoooOoo0o0o0oO0O(F)AnimationEvent`, not a generic task inferred by name.
This worker calls the AnimatableEntity superclass updateAnimation(FZ) directly
with true at2–3. It therefore bypasses CustomEntity's render-thread assertion and
its own future-wait override. The worker has a catch-all handler for offsets0–7;
normal return and exceptional exit both call storeFence, then return/rethrow.
This is actual finally coverage, unlike the unprotected controller/processor tails.

The pool uses max(2,availableProcessors/2) for both core and maximum sizes,
30 SECONDS keepalive, a no-argument LinkedBlockingQueue and a ThreadFactory.
The factory creates `YSM Worker` threads, priority5, daemon=true. No assumption
about actual CPU count, thread launch timing, throughput or external tasks is made.

## Waiting and reuse versus synchronous reevaluation

CustomEntity.updateAnimation(FZ) first calls RenderSystem.assertOnRenderThread.
If renderingInLevelExclusive is true and asyncTask is nonnull, it returns the
waitForAsyncUpdate result directly. Otherwise it calls waitForAsyncUpdate and
then superclass updateAnimation with the requested boolean. Thus a nonexclusive
render waits before performing its own base update; it does not blindly reuse a
level-exclusive result for mutable UI rendering.

waitForAsyncUpdate calls Future.get at13, casts/stores its result, then loadFence
at25. Its exception table has InterruptedException and Throwable handlers covering
9–28. InterruptedException is ignored; other Throwable is printed. Both ordinary
handler paths reach asyncTask=null at42 and return the result (initially null).
The fence is not reached when get throws. There is no explicit cancel, retry or
interrupt-status restoration in this method. Consequently an interrupted wait
clearing the stored future is not proof that the underlying job completed; this
is a conditional static limitation, not a reproduced race or deadlock report.

beginAsyncUpdate itself has no preexisting-future guard. Whether duplicate
submission is possible depends on caller/lifecycle constraints; do not assert
one task per entity universally from this field alone.

## Registry and render-phase aggregation

AnimationParallelTicker holds weak registered entity references and a separate
strong task list. scheduleAll returns immediately with no local player. It removes
collected/inactive entries, calls checkModelUpdate, then filters by canUpdateAsync,
initialized and model-present flags. Model-disable configuration gates distinguish
self/other players, projectiles and remaining vehicle category. It invokes
beginAsyncUpdate before appending the entity to TASK_LIST. The base CustomEntity
canUpdateAsync returns true; concrete overrides remain to inspect.

waitAll iterates TASK_LIST, catches Throwable around each entity's wait call,
prints it and continues; list.clear is after the loop. There is no outer finally
covering iterator failure or an unexpected throw from error reporting. These are
precise exception boundaries, not a blanket guarantee that every worker is joined.

WorldRendererMixin's first hook body, when YesSteveModel.isAvailable, sets the
RenderUtil flag true then calls scheduleAll. Its second body calls waitAll then
sets the flag false under the same availability test. Neither hook has a finally.
Pinned source annotations target renderLevel around FogRenderer.setupColor and
RenderType.entitySolid respectively; annotation decoding and actual successful
Mixin injection have NOT been verified by this cohort. Do not interpret the
source placement alone as a runtime rendering trace.

## Checks and continuation

253 static integrity checks passed and 17 malformed-evidence controls rejected.
Controls include loss of worker finally, loss of interrupt catch, changed
supercall/render flag, changed submit overload and task-list clear. See
ASYNC-ANIMATION-VERIFICATION and tools/async_animation_ysm_265.py. Hash/snapshot
consistency is not independent semantic approval; mapping remains669.

Next inspect concrete canUpdateAsync/isImmutableRender overrides, actual renderer
consumers and model-update eligibility. Resolve annotation identities separately
if claiming exact injection locations; keep interrupted-wait safety conditional.
