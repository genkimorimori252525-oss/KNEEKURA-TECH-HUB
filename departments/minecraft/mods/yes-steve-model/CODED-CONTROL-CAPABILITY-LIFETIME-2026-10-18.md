# Coded-control mutation capability across predicates and cached queue polling

2026-10-18. BOUNDED_STATIC_JOIN; [independent review ACCEPT_WITH_PRECISION_NOTES](CONTROLLER-EVENT-BOUNDARIES-REVIEW-2026-10-18.md). One bounded continuation of the controller-visitation-order join. This traces four existing public Molang mutation functions to the event pointer that permits them to reach a coded controller. It does not prove all expression evaluation is pure or all queues immutable.

## Result and reuse consequence

On the ordinary base updateAnimation path, each invocation that passes the model-present early guard and reaches event construction creates a fresh AnimationEvent and a context holding that exact event. The null-model path returns null at7–8. Tick dispatch at488 is virtual; actual processor polling also requires its model-nonempty/shouldUpdate gates. The only direct original-JAR writer of its coded-controller pointer is its setter; the only two direct setter calls are in CodedAnimationController.process: publish this before predicates, clear null after predicates and before player processing.

Consequently, under normal completion and no external/reentrant mutation:

- The four control actions can target the active coded controller during its predicate evaluation.
- They cannot reach that controller from later player/point evaluation or queue polling: the event pointer has already been cleared.
- When shouldTick=false skips controller processing, the fresh event pointer remains null. Calling one of these actions while evaluating retained queues returns null before its argument expressions run.
- Child Molang contexts copy the same AnimationEvent reference. They do not retain a separate snapshot of the coded-controller pointer. Clearing the pointer is visible through that shared event, even though other context fields are selectively copied.

This closes one concrete candidate mutation route that had prevented narrowing the cached-queue premise. The guard is coded-controller availability, not allowEmitting and not controllerContext presence. A reimplementation that uses a permanently attached controller, or copies its pointer into child contexts, would permit mutations that the ordinary shipped lifecycle suppresses.

## Exact boundary identities

All owners are under `com/elfmcys/yesstevemodel/`:

- Event `OO00O0o0OooOOOo00OO00o00`; protected field `o0OOooo0o0OO00OoOOOo0o0O:Lcom/elfmcys/yesstevemodel/oo000oooo0OOoo00O0o0OOOO;`.
- Event setter `Oo0Oo0o00O00Oo0OOoOOoooo(Lcom/elfmcys/yesstevemodel/oo000oooo0OOoo00O0o0OOOO;)V`; getter `o0OOO0o0o0OOo000oO00o00O()Lcom/elfmcys/yesstevemodel/oo000oooo0OOoo00O0o0OOOO;`.
- Coded controller `oo000oooo0OOoo00O0o0OOOO`; process `Oo0Oo0o00O00Oo0OOoOOoooo(Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;Z)V`.
- Base Animatable `o0000OoOooO0oo0o0oooo0Oo`; update `o0OOooo0o0OO00OoOOOo0o0O(FZ)Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;`.
- MolangContext `O0O00Oo0o0oO0oo0oO00OOoO`; event field `O00OOOooOoooOoo0o0o0oO0O:Lcom/elfmcys/yesstevemodel/OO00O0o0OooOOOo00OO00o00;`.
- SetAnimation `o0Oo0oO0OO00O0ooOo0o0Ooo`; SetBeginningTransitionLength `OOo00o0o0oo0oOOOoOOOoooO`; ResetController `ooOoo0OooooOOOO0oOoO0OOo`; IndicateReload `O0o00oo0Oo0O0oo0oOOOOOOO`.

All four action implementations use method `Oo0Oo0o00O00Oo0OOoOOoooo(Lcom/elfmcys/yesstevemodel/oO0OoO0O0OoO0oo0oo0OOooo;Lcom/elfmcys/yesstevemodel/O00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;`.

## Bytecode-backed lifecycle

1. Base update allocates Event at411, invokes constructor454, stores it457. It allocates MolangContext459 and passes the stored event to constructor469. The same event/context local references reach tick488. Event construction contains no explicit coded-pointer assignment, so fresh ordinary instances start with Java's null reference default.
2. MolangContext's public constructor `(Object,Animatable,AnimationEvent,EntityModelData)V` stores the supplied event at16. Its private child constructor `(Object,MolangContext)V` reads the parent's event19 and stores it22. Its event getter directly returns this field. These are aliases to an event object, not copied controller values.
3. Coded process loads this at1 and invokes event setter2; after Molang predicate and optional Java predicate it loads aconst_null31 and invokes setter32. The player-processing/state branches follow the clear. The process body has no exception handlers.
4. Each action obtains IContext.animationEvent at9, calls event.getCodedController14, and tests nonnull19→24. The null path returns null22–23. For SetAnimation, first argument evaluation begins27, after the guard. The other three share the same guard, so absence of a controller suppresses their mutations, and any parameter evaluation, before their normal body.
5. Fresh scan of all955 original classfiles finds exactly one direct field write, the setter's putfield2, and exactly two direct setter callsites, Coded.process2/32. No original Event subclasses are present and no matching writer/setter handles occur in parsed BootstrapMethods. This is original-artifact direct-reference closure, not a claim about arbitrary runtime entry points.

Joined with [controller visitation order](CONTROLLER-VISITATION-ORDER-2026-10-18.md), per-controller visits occur only after normal process return, or without process on a skipped tick. Therefore these four actions are unavailable during normal later queue polling on the matching fresh-event path. There is no need to assume allowEmitting=false for that conclusion; these action bodies do not check it.

## Exception and scope limits

If a predicate throws before32, the old event can retain the nonnull coded-controller pointer because clearing is not in finally. Subsequent evaluation against that same event could regain mutation access. That is a conditional retained-object risk, not proof of an observed exception or exposed event. A later ordinary base update creates a new event, so one must not claim the stale capability automatically persists into that next call.

A caller supplying a different evaluator/event pair, a custom IContext, a retained event, reflection, JNI, external subclasses, direct public setter invocation, reentry, or concurrent mutation is outside this conclusion. Public controller methods may be invoked by other routes; only these four action-query routes are narrowed. Async result reuse is not a fresh base update, and is not silently included.

The coded predicate is deliberately a mutation-enabled phase. Child contexts share this capability during that phase even though their controllerContext/allowEmitting fields need not be copied. After normal clearing they share its absence. The result does not classify every Molang function or prove global side-effect freedom, queue generation completion, thread safety, renderer output or successful runtime registration.

## Evidence and reproduction

Original JAR SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`; source candidate `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Eight relevant source files match pinned Git blobs. Whole-source equivalence remains NOT_ESTABLISHED and prior SOURCE_ARTIFACT_DIVERGENCE remains unchanged. Central map669 is untouched.

[control capability evidence](CODED-CONTROL-CAPABILITY-EVIDENCE-2026-10-18.json) holds exact direct-writer/callsite identities, source hashes, method digests and21 passing structural assertions without full original method bodies. `scan_control_capability.py` reproduces the static scan using the prior local scanner. Full selected class snapshots remain only in Git-external `control-capability-evidence.json`. Counts describe evidence scope, not semantic completion.

No original Java/native/assets execution, asset decoding, network, downloads, CI, blocked-runtime retry or Git edits occurred.
