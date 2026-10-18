# Shared inherited-animation user-function target cache

## Finding

The original Java closes a concrete ownership gap left by USER-FUNCTION-CACHE-RECOVERY: inherited default player animations can share the **same mutable user-function resolution node across model containers**. The lookup source is the current entity's model assets, but the successful target cache and normal-miss marker belong to the retained UserFunction node, with no model key on the inspected path.

Consequently, conditionally on an inherited animation expression containing such a node and reaching it in two sequential contexts, the first successful lookup supplies the target IValue used by the second context. Execution still receives the second/current context and evaluator. A normal first miss can instead prevent the second lookup. This is a code-backed conditional semantic result, not a claim that shipped assets contain a triggering expression or that a rendered defect has been observed.

## Exact original-code join

All owners below have prefix `com/elfmcys/yesstevemodel/`; full owner/name/descriptors, instructions and code hashes are retained in `evidence.json`.

1. Builder `OOOOOO00o0Oo000O0OO0OOO0.Oo0Oo0o00O00Oo0OOoOOoooo( LooOOOo00o0000o0oO000oooO; LOoO00O0oOo0000oo0OOO0oO0; Z Ljava/util/List;) LOo0o0o0o0OOo0000ooo00o00;` (spaces here only for readability): branch149 skips defaults when its boolean is true. Otherwise default main map152–158 and first-person map221–227 feed computeIfAbsent214/283. Bootstrap callbacks named `Oo0Oo0o00O00Oo0OOoOOoooo` and `o0OOooo0o0OO00OoOOOo0o0O`, descriptor `(Ljava/util/Map$Entry;Ljava/lang/Object;)LOo0OOo00Oo00oO00Ooo0O00O;`, return entry.getValue at1, cast6, return9. They do not clone the Animation. This reuses the previously established CLIENT-MODEL-COMPOSITION/CONDITIONAL-ANIMATION-NAMES bootstrap mapping.
2. Animation `Oo0OOo00Oo00oO00Ooo0O00O` constructor stores the supplied blendWeight IValue directly in field `Ooooo0oooO0oooOOOoO0000O` at41. MolangValue `o0o0OoOoO0Oo0oOoOOOooOOo.<init>(Ljava/util/List;Z)V` retains the expression list at6; `evalUnsafe(LO0Oooo00oOo00O00OoOOOooO;)Ljava/lang/Object;` passes that list to evaluator at9. CallExpression `OOoo00oo0OoOOO0o0OO0oOoo` retains its supplied Function; its visitor dispatch reaches evaluator `oo00Oo00o0ooooOooo0Oo0OO` call visitor, which obtains function/arguments at1/8 and invokes Function.evaluate at11. These nodes are retained objects, not freshly parsed per evaluation.
3. Player `OOOO0o0oo0o000oOOooOoOo0` has three blend routines named `Oo0Oo0o00O00Oo0OOoOOoooo`, `o0OOooo0o0OO00OoOOOo0o0O`, `O00OOOooOoooOoo0o0o0oO0O`, all descriptor `(LO0Oooo00oOo00O00OoOOOooO;F)V`. Each reads current Animation at11, its blendWeight at14, then evaluates that same IValue as float at18. The null branch uses the fallback rather than evaluating a node. IValue `O0o0OOO00000oO00O00oOOo0` float adapter calls its object evaluator at2; the object evaluator calls evalUnsafe at2 and has its existing exception-to-null boundary. No claim about thrown-path numeric outcomes is needed here.
4. MolangContext `O0O00Oo0o0oO0oo0oO00OOoO.Oo0Oo0o00O00Oo0OOoOOoooo(Ljava/lang/String;)LO0o0OOO00000oO00O00oOOo0;` delegates to its animatable entity at5. CustomEntity `oOo00OoOO00O000ooO0Oo00o.O00OOOooOoooOoo0o0o0oO0O` with the same descriptor obtains current model at1, common assets at4, function map at7 and map.get at11. This method is final. Thus the lookup source can differ between models even when the expression is shared.
5. UserFunction `ooo0o0OoOooOOOo0OOOo00oO$Oo0Oo0o00O00Oo0OOoOOoooo.evaluate(LoO0OoO0O0OoO0oo0oo0OOooo;LO00OOo00o0O00ooo000OOo0O$Oo0Oo0o00O00Oo0OOoOOoooo;)Ljava/lang/Object;`: current context eligibility at10/13; nonnull cache at23 branches26→85, bypassing lookup44. Lookup result stored49 before execution. On null result, diagnostic73 must return normally before name=null80. Thereafter null name returns36–37. Cached invocation92 uses current context from local3, current evaluator and arguments, and retained target88.

## Bounded witnesses and reuse consequence

`verify.py` runs only an authored Python model of the inspected branch structure, never YSM. Ten checks pass, including original offset assertions and three conditional cases:

- Same node, A.f=FA then B.f=FB: target/context pairs (FA,A), (FA,B); B lookup count remains zero.
- Fresh node in B: (FB,B), the independence counterexample.
- Same node, A lacks f and diagnostic returns normally: later B.f=FB is not looked up and returns null at this node.

The result matters to reuse: sharing animation data is not sufficient to establish model-independent expression resolution. A fresh per-model evaluator alone does not freshen the target node. It also does not freeze all query values or execution context: those still come from the current invocation. Identical targets across models can mask the difference. Clearing the binding's map only affects future property acquisition; existing CallExpression references retain the old Function object, as established by the existing cache dossier.

## Provenance and limits

Original JAR SHA256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`. `extract.py` freshly reads 14 classfiles and 207 methods as bytes using the existing bounded class reader; it exactly matches the independent review's overlapping extraction. `receipt.json` pins this evidence hash. Existing composition, ownership, evaluator and user-function dossiers supply semantic aliases; no new central mapping promotion is proposed.

No assets were inspected and no original Java/native code was executed. No network, downloads, CI, runtime retry or Git edits. Actual inherited expression contents, actual ordering across entities, parallel/racing evaluations, reflective/native mutation, external subclasses and complete lifecycle replacement are outside this finding. It is restricted to the same retained node, eligible current context, and specified normal lookup/diagnostic behavior. It does not establish universal model contamination, all-animation effects, global immutability, final renderer output, or whole source/artifact equivalence.

Published [independent conditional review](SHARED-ANIMATION-FUNCTION-CACHE-REVIEW-2026-10-18.md), [final primary acceptance](SHARED-ANIMATION-FUNCTION-CACHE-ACCEPTANCE-2026-10-18.json), and [integrity evidence](SHARED-ANIMATION-FUNCTION-CACHE-EVIDENCE-2026-10-18.json).
