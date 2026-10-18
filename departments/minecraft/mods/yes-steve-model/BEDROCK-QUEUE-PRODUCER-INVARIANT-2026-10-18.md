# Bedrock producer → blend-consumer subtype invariant

## Result

A conditional built-in proof closes the previously unspecified producer requirement: on a normally completed controller initialization/processing path, with unchanged state data, no independent player/queue mutation or reentry, and either the exact built-in linear or segmented transition, all accepted points are BeginningTransitionPoint while the common beginning phase lasts. They all cease being beginning points on the same controller processing call. Missing animations, empty axis lists and false holder conditions do not independently break this subtype property.

This is a static conditional proof, not a universal safety claim or an observed exception. It does not establish that every runtime/native-supplied transition is one of these implementations, that callbacks cannot reenter/mutate the objects, or that arbitrary malformed animation/search inputs complete normally. Independent semantic review of this bounded join: [ACCEPT_WITH_PRECISION_NOTES](BEDROCK-QUEUE-INDEPENDENT-REVIEW-2026-10-18.md). Whole-project semantic review remains NOT_RUN. No target/JVM execution, assets, runtime reproduction, mapping promotion.

## Scope and evidence

Exact original JAR SHA-256: 25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f.
The external inspect.py reparses classfiles and compares access, complete instructions, encoded operands, handlers and code hashes to existing evidence. 94 method records across nine owners matched. These are structural matches, not 94 independent semantic reviews. The small duration prerequisites reuse ORDERED-SEGMENT-TRANSITION evidence; this report does not reopen interpolation, clock, conditions or time-factor cohorts.

Owners (all under com/elfmcys/yesstevemodel/):
- C: O00Oo0oo0Ooo0oOOOo0OO0oO, Bedrock controller
- Q: C$o0OOooo0o0OO00OoOOOo0o0O, blend consumer
- P: OOOO0o0oo0o000oOOooOoOo0, player
- B: oooO000oOoOooooOooo00oOO, bone queue
- T: O0O0O00OOO0o00o00ooooOo0, beginning point
- I: o0OoOoOO0oooO0O000oO0o0o, transition interface
- L: OoooOo0OOOoOOoOOooOOoO00, linear transition
- S: o0o00oo00Oo0oo00ooOO0ooo, segmented transition
- R: oOOOO0oo00o0oOoo0oOoooOO, ordered searcher
Exact method identities and hashes are in BEDROCK-QUEUE-PRODUCER-INVARIANT-METHODS-2026-10-18.json; METHOD numbers in the local dumps are classfile-order indices, not semantic mappings.

## Consumer requirement, precisely

For each bone axis separately, form the accepted sequence in actual iteration order: condition true AND underlying bone queue active AND axis point non-null. If its first point is a beginning point and its saved progress is <= -e or >= +e, where e is Java binary32 1e-5f (exactly 9.999999747378752e-06), every later accepted point must also be a beginning point at the time it is read. This is the minimal cast requirement. Full homogeneity is sufficient, but stronger than necessary. If the first point is non-beginning, this particular beginning-only cast branch is not entered. The strict near-zero band and NaN early return do not establish producer homogeneity.

Q rotation/position/scale first subtype tests: 125/122/125. Unguarded later beginning casts: 278/260/283. The early return behavior is retained from the existing consumer cohort; no new runtime claim is made.

## Producer → consumer invariant table

| Case | Exact producer evidence | Accepted sequence / consequence | Qualification |
|---|---|---|---|
| Successful selection | C.transition calls startNew at 526, assigns transition at 531, indicateReload at 539, selection at 555. P.setAnimation stores nextAnim at 97. P.loadNextAnim consumes/nulls nextAnim at 13; sets current animation/loop at 24/35 and activates bone queues at 119. C.process calls every holder P.process at 336 before aggregation at 383–465. | Successful selected players initialize on the same controller process call and renderTicks. P.process writes offset at 132 and local ticks=0 at 135–136. With common stable L>0, each takes beginning; L<=0 all take running. | Requires normal completion, built-in duration behavior, no external state/queue changes and a synchronized controller-managed player cohort. |
| Missing animation | P.setAnimation resetToIdle at 46; missing lookup returns at 75 without setting nextAnim. P.loadNextAnim null branch returns false at 9–10. P.process returns at 129 if no next animation. resetToIdle deactivates queues at 69 and clears active list at 79. | Under the ordinary consumed-nextAnim invariant, missing selection contributes no active queues; it cannot contribute an old running point alongside newly beginning players. | resetToIdle itself does NOT clear nextAnim; full reset clears it at 7. Therefore the missing-selection statement requires nextAnim already null (normal completed prior processing or fresh/reset player). Multiple direct selections before process or interrupted/reentrant lifecycle are outside this proof. |
| Missing bone | P.loadNextAnim missing map entry branches 93→96→56 before activation. | No queue contribution for that bone. | No attempt to synthesize a default point. |
| Empty axis lists | B.setActive empty-list branches at 9/50/91 write null searchers at 38/79/120. It resets point fields at 148. P.process resets queues at 170; B.resetQueues null writes at 2/7/12. P.runBeginningTransition gates each axis at 89/119/149; runAnimation likewise only writes existing searchers. | Empty axes remain null after each normal processing pass and are rejected by Q; they do not introduce a different subtype. | A bone queue can be active with every axis null. This is not equivalent to accepting three default points. |
| Beginning phase | P.runBeginningTransition invokes the typed beginning factory at 108/138/182-or-202 and writes rotation/position/scale at 111/141/205. Factory creates T at 10 and invokes its constructor at 36. | Every non-null emitted axis point has the beginning subtype. | Factory requires frames.search(0) cast to TransitionKeyFrame at 29; malformed data can fail before the successful completion assumed here. No claim of malformed-input safety. |
| Scale beginning disabled | Both scale branches call the same beginning-point factory (182 and 202), with the disabled branch using transition length and progress 1. | The scale flag changes numerical arguments but never substitutes a keyframe point during the beginning phase. | Equal progress is unnecessary for subtype safety and should not be inferred from subtype homogeneity. |
| Beginning→running boundary | P.process resets queues at 170, compares ticks with length at 189–195, enters running at 240, then calls runAnimation at 379. P.runAnimation writes keyframe points at 85/108/131; its factory creates KeyFramePoint at 9. | With synchronized offset and common stable duration, if/when the epoch reaches its boundary, all successful players cross on the same call, including exact equality. Finite render times alone do not prove eventual progress. No old beginning fields survive reset. | Consumer must run after the whole controller processing call, not midway through player updates. A numerical mixture of later running/ending/idle states is possible, but no built-in return from those states to beginning without a new synchronized controller selection. |
| Filtered holders | C.process condition evaluation at 305 and allowEmitting AND at 317–335 still converge on P.process at 336. Dirty aggregation adds condition/queue pairs at 465. Q checks condition, active and non-null gates (rotation 69/92/107; position 66/89/104; scale 69/92/107). | False conditions remove accepted entries, but do not postpone initialization or beginning completion. Any filtered subsequence of a homogeneous cohort remains homogeneous. | Callback side effects/reentry are excluded, rather than assumed impossible. Zero weight alone is not an exclusion gate. |
| After beginning completes | Running emits KeyFramePoint; ending emits EndingTransitionPoint (P ending writes 90/118/146); idle deactivates/clears. | Different animation lengths/loop types may mix running/ending/absent points after the shared beginning phase; this does not trigger a first-beginning cast requirement because no accepted beginning point remains. | This proves subtype compatibility only, not equal weights, transforms, progress or semantic equivalence of blended output. |

## Why both built-in transitions preserve the common boundary

Linear: I.startNew is return-this at 0–1. Exact L supplies no override; length returns its stored duration. Every holder gets the same state transition object, and the built-in object does not change its duration during get(). Hence length cannot vary across ordinary player calls.

Segmented: S.startNew (typed method) allocates S at 0 and passes the existing segment-list field at 5 into the list constructor at 8. That constructor creates a new R at 10–24. R caches the final segment endpoint into its right-bound field at constructor offset 35. S.length delegates at 4 to R.rightBound, which only reads that cached field at 1. No other method of R writes this right-bound field. Thus cursor advancement from get() cannot vary length, either within a player's calls or between players initialized from the same unchanged segment list. The clones have independent search cursors, but common duration. This uses successfully constructed built-in data; it does not infer native input validity.

The required invariant is common branch outcome at the beginning gates, not equal transition object identity. Equal finite duration and synchronized initialization are simple sufficient conditions. The proof here deliberately assumes finite render times and finite duration to avoid claiming a broad floating-point/state theorem. Progress is not the exit predicate; length is. Even different progress values alone cannot change BeginningTransitionPoint into KeyFramePoint.

## Exact remaining boundary and reuse requirement

C.transition invokes the interface at 526; P.process invokes length at 142/189/220; the point factory invokes length again at 20. Those calls contain no local contract enforcing equal/stable results for an externally supplied implementation. The interface declares length/get and a default return-this startNew; the declarations alone do not impose cross-player duration equivalence. The supplied state object and animation lookup/data provenance are not established by this bounded join.

Public player operations, mutable exposed queue collections and public axis fields also mean these producers are not a whole-program invariant over arbitrary writers. Likewise, called evaluation/search/vector code must return normally and not mutate/reenter these controller/player/queue objects for this sequential proof. No particular external implementation or actual failure is asserted.

Reuse contract: preserve synchronized initialization and complete all player processing before visitation; require stable/equal beginning-boundary decisions for every accepted player; clear old axis points before regenerating; preserve inactive/null/condition filters; and constrain external mutation/reentry. If the reuse cannot enforce these conditions, it needs a separately chosen mixed-type consumer policy rather than treating the original unchecked cast as universally safe. No policy/code change is proposed by this read-only task.

[Invariant table](BEDROCK-QUEUE-PRODUCER-INVARIANT-EVIDENCE-2026-10-18.json), [exact method identity/hash records](BEDROCK-QUEUE-PRODUCER-INVARIANT-METHODS-2026-10-18.json). Existing [controller](BEDROCK-CONTROLLER-RECOVERY-2026-10-17.md) and [queue consumer](BONE-COMMIT-QUEUE-RECOVERY-2026-10-17.md) evidence remains authoritative for previously recovered operations.
