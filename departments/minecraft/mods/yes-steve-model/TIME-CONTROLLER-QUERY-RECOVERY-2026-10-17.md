# Time and controller-completion queries — 2026-10-17

## Scope

Exact official JAR SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, comparison source
YesSteveModel/YesSteveModel `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.
25 selected methods across seven owners join registrations, nullable contexts,
completion-flag producers and time conversion. Constructor/support records are
included, not counted as newly recovered central mappings. Central map stays
669. Independent semantic review NOT_RUN; no target/runtime or game execution.

## Seven different query values

| Query | Raw boxed result and producer |
|---|---|
| anim_time | Float from AnimationContext.animTime, or 0f when context absent |
| all_animations_finished | Boolean from ControllerContext, or false when absent |
| any_animation_finished | Boolean from ControllerContext, or false when absent |
| life_time | Double: animatable seekTime widened from float, divided by 20.0d |
| time_of_day | Float: normalized world day-time calculation below |
| time_stamp | Long: client level day time, not wall-clock milliseconds |
| delta_time | Float: state tracker's render-tick delta divided by 20f |

QueryBinding constructor's invokedynamic offsets 187,198,209,220,264,275,286
bind the respective query callbacks. All/any use different getter method handles
(bootstrap 49/48); anim_time getter is bootstrap 50. Optional.ofNullable wraps
the animation/controller context before map/orElse. Absence is not an exception
or evidence that the animation completed.

## Day time is floating remainder, not a floor-mod promise

MolangUtils.normalizeTime performs long addition of 6000, casts to float,
divides by 24000f, then FREM 1f. There is no double computation or floorMod in the
captured body. Do not assume exact precision at large world times or a normalized
[0,1) result for arbitrary negative timestamps. This query is distinct from the
unmodified Long time_stamp and from animatable-relative life_time.

## anim_time writer phases

AnimationPlayer writes 0 during beginning-transition sampling, animTicks/20f in
RUNNING, endingTransitionSrcTick/20f during the ending blend, and animationLength/
20f while resetting remaining event keyframes. Ending anim_time thus reports a
captured source sample time, not the elapsed ending-blend duration. The clock and
strict boundary details remain in ANIMATION-PLAYER-CLOCK evidence; this cohort
joins those writes to the registered query getter.

## All and any are not universal aliases

ControllerContext owner `O0oo0oOo0OOOO00Oo0oo0o00` has separate mutable boolean
fields. Its coded-controller producer sets both from its one AnimationPlayer's
currentAnimFinished before evaluating a nonnull Molang predicate. It installs
controller/animation contexts, permits emission, evaluates, then clears those
contexts on normal return. No new finally guarantee is inferred from the query.

Bedrock controller `O00Oo0oo0Ooo0oOOOo0OO0oO` differs. In updateState's existing-
state branch it initializes any=false (setter offset 73), all=true (81). It scans
active holders whose condition currently applies. Finished holders set any=true
(137); unfinished holders set all=false (148). With zero applied holders it
explicitly sets any=true (166), leaving all=true. Thus:

- all considered holders unfinished: any=false, all=false
- mixed finished/unfinished: any=true, all=false
- all considered holders finished: any=true, all=true
- zero applied holders: any=true, all=true

These are conditional truth-table consequences of the captured Java body, not
executed controller test results. The initial-state branch does not perform that
same recomputation. As documented in BEDROCK-CONTROLLER, state evaluation precedes
that update's condition reevaluation; do not silently replace its stored condition
sample with a newly evaluated one.

A source comment suggesting all/any are equal is not a global runtime contract.
The actual coded/Bedrock producer distinction above takes precedence. Likewise,
currentAnimFinished is the player's stored flag, not a fresh test for IDLE; the
prior player evidence includes loop completion and ending-transition writes.
Do not interpret a true query as proof that all visual blending or event work
has stopped.

## Verification and continuation

`tools/time_controller_query_ysm_265.py` uses --jar, --source-root, --evidence,
--out. 160 integrity checks passed; 13 mutated fixtures rejected, including a
changed day-time offset. No source comment, test count or method inventory is
used as runtime proof or independent semantic review.

Continue context creation/child-context delegation and query lookup lifetime to
establish where nullable controller/animation contexts are visible. Preserve
raw boxing and units until the final typed conversion point.
