# Instruction-keyframe evaluation and debug observation side effects

PRIMARY_STATIC_REVIEW_ONLY. Exact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.25 declarations across instruction executor and debug owner/item/phase;148 integrity checks/9 negative controls. No expression/game execution, mapping promotion or independent semantic review.

## Emission false does not skip instruction evaluation

InstructionKeyFrameExecutor `OoOOo0O0oo0OO0o0ooOO0OO0` retains the supplied list directly. executeTo first writes context.allowEmitting from its boolean argument, then visits eligible frames in current list order. Every IValue in a frame is evaluated in array order and its result discarded, regardless of that flag. Effect-specific functions may honor it, but variable assignments, computations or other functions are not globally skipped by this executor.

It increments nextIndex only AFTER all values for that frame return. This differs from the [sound executor](SOUND-KEYFRAME-CLEANUP-RECOVERY-2026-10-17.md), which advances before attempting sound dispatch. If an exception escapes a value's own handling, earlier values may already have side effects while this frame's index remains unchanged; a retry can reevaluate them. The [IValue conversion/error dossier](VARIABLE-CONVERSION-RECOVERY-2026-10-17.md) explains why default eval catches are not a guarantee for every override.

executeRemaining iterates with a local index from retained nextIndex and writes nextIndex=list.size only at the successful end. An escaping error can therefore leave even earlier completed frames from that call uncommitted to the retained cursor. Both methods set allowEmitting=false only on their normal tails, not in a finally and not by restoring the incoming value. reset merely sets nextIndex0. No sorting/copy or per-call frame-count cap is added locally.

## Debug evaluation executes values, it is not a read-only snapshot

DebugInfo `o0oo00Ooo0oOooOo0OOo00oo` appends items without name uniqueness enforcement. remove applies name.equals to all matching items; clear empties the list. Pre/post methods iterate the live list and evaluate entries matching that phase. There is no copied iteration list or global synchronization in this owner.

DebugItem calls value.evalUnsafe directly, then formats null as"null", Number through shared DecimalFormat("#.#####"), other objects through toString. A Throwable from evaluation/formatting becomes an"Error: "+message result string. This captures an error presentation but does not roll back expression side effects. The formatter uses its constructed defaults; no stable cross-locale serialization format is promised.

The result field is volatile, but the list, phase selection and shared formatter are not made generally thread-safe by that field. enumerate delivers each retained name/result to its callback; it does not reevaluate, and result can still be null before a successful/failed evaluation has assigned it. Enumerating/displaying a prior result differs from scheduling another evaluation.

## Existing frame hook relationship

The already captured CustomEntity owner in [model-readiness evidence](MODEL-READINESS-SCOPE-EVIDENCE-2026-10-17.json) has a nullable debugInfo field. Its preAnimationSetup delegates to the parent, then when debugInfo exists enqueues a pre task and a post task, both with emission false. The captured lambdas access the owner's debugInfo when executed; they do not capture an immutable DebugInfo snapshot. The hook does not add its own shouldTick condition around these enqueues. Actual processor execution gates and task context belong to the existing processor/frame dossiers, not a new guarantee that every render executes both observations.

Consequently debug expressions should be treated as evaluations with side effects possible, not invisible probes of model state. A changed/cleared debugInfo between scheduling and execution is a conditional reference-lifetime question, not a demonstrated race. No target expressions were run to test it.

## Reuse

Preserve frame cursor commit points, expression order, emission permission versus execution, error handling scope and observation timing. When adapting a debugger or timeline runner, define whether a failed frame is retryable and whether observing may mutate state. These findings extend the earlier player/context chain without changing its mappings or silently expanding frozen checkpoint coverage.
