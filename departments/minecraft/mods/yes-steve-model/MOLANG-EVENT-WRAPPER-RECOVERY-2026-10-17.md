# Molang event wrapper and retained argument lists

PRIMARY_STATIC_REVIEW_ONLY. Exact SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source revision `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.Five wrapper declarations;36 integrity checks/6 negative controls. Separate955-class scan finds5 direct calls in5 methods,0 bootstrap target handles (2 checks/6 negatives). No expression/packet/target execution, independent review or central-map promotion.

## Wrapper captures references, not an event snapshot

`OOOoOO000000o0o0oOooo0o0` declares player_init/player_update/sync/defer strings. The FloatArrayList overload replaces null with FloatLists.emptyList; the no-argument-list overload supplies ObjectLists.emptyList. The generic List overload simply captures handler list and argument list in an IValue lambda. It does not copy, freeze, evaluate or validate their elements when wrapping.

When evaluated, the lambda checks evaluator.entity instanceof IContext. Otherwise it returns null. For matching context it iterates retained handlers in list order, calls context.callUserFunction(evaluator,handler,retainedArgs) and discards each result, then returns null. There is no per-handler catch/finally or local emission flag change. An exception escaping user-function handling can skip later handlers; existing value/context error contracts remain relevant. Wrapping does not promise all handlers executed once or all arguments represent their creation-time values.

## Three external call sites, plus two overload delegations

[Caller evidence](MOLANG-EVENT-CALLERS-EVIDENCE-2026-10-17.json) identifies:

- CustomHumanoidEntity.onLoadModelContainer: after parent load and texture update, look up player_update; present handlers produce a retained wrapper over the same updateHandlerArgs list, absent handlers clear the wrapper.
- CustomHumanoidEntity.preAnimationSetup: after parent setup, a true fireInitEvent is cleared BEFORE handler lookup/scheduling. Present player_init handlers are wrapped and submitted with emission/pre-animation flags true/true. A missing handler or later failure does not leave that flag true for automatic retry. Existing resetGeoModel sets it again.
- CustomPlayerEntity.molangSync: nonnull syncHandler creates a wrapper over supplied FloatArrayList (null becomes empty through the overload) and submits with emission/pre-animation flags true/false.
- The other two calls are wrapper overloads delegating to the generic List form.

The update path reuses a BooleanList of length1, sets index0 to shouldTick, then submits the prebuilt wrapper. It is scheduled even when shouldTick is false; false is the data argument, not a local skip condition. The reference capture means later mutation before execution would be visible to the wrapper; actual queue timing/thread races require the processor's caller contract and are not observed here.

## Relation to reset and execution

Resetting the humanoid model container clears its wrapper reference, but does not itself rewrite a previously queued lambda's captured handler/argument objects. The processor's clear-model/pending-task behavior is a separate step. The [instruction executor](INSTRUCTION-DEBUG-EVALUATION-RECOVERY-2026-10-17.md) likewise distinguishes expression execution from effect permission, while [runtime storage](RUNTIME-STORAGE-FRAMES-RECOVERY-2026-10-17.md) bounds call-frame cleanup. Do not infer a frozen, immutable event payload or transactional batch merely from the method name wrap.

This closes the small Java adapter between model event lists, mutable tick arguments and existing user-function dispatch. It does not expand native model parsing or prove external delivery. Later fixed event-transition verification explicitly joins this cohort rather than altering older manifests.
