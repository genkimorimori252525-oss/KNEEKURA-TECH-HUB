# Independent bounded review: inherited animation user-function cache

## Result

The Java identity path supports a conditional, sequential cross-model first-resolution counterexample. It does not establish that a shipped/default asset contains the relevant call, or that an actual player reaches it. The ownership question is narrower than a reload defect: two coexisting model containers can inherit the identical default Animation, hence identical contained expression graph and captured UserFunction node, while their lookup methods consult different common assets. With the alias and visitation premises below, a successful lookup in one model is reused during evaluation under the other model. This is a target-expression identity cache, not a cached numeric result or a cached ExecutionContext.

## Exact artifact and independent checks

Read only the fixed JAR (SHA-256 25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f), parsing 955 classes without loading them. scan.py writes 100 complete selected method records and class/bootstrap metadata to exact-evidence.json, plus methods.txt for human inspection. receipt.json records nine passing structural checks and 33 exact prior-method comparisons across USER-FUNCTION-CACHE, CONDITIONAL-ANIMATION-NAMES, ANIMATION-DATA-OWNERSHIP and VARIABLE-AST-RETURN. Existing notes/source supplied symbol leads only; these conclusions were checked against class instructions. This is not a source/artifact equivalence promotion.

## Identity chain

- Builder OOOOOO00o0Oo000O0OO0OOO0 player construction performs computeIfAbsent at offsets 214 and 283 for inherited main/first-person animation maps. Its two synthetic (Map.Entry,Object)->Animation methods return Entry.getValue (offset 1), checkcast (6), areturn (9). Neither clones the Animation.
- Animation Oo0OOo00Oo00oO00Ooo0O00O keeps supplied scalar IValue references and wraps supplied element arrays. Inheriting that same Animation therefore retains those contained references; it does not construct a new expression graph.
- MolangValue o0o0OoOoO0Oo0oOoOOOooOOo constructor stores the supplied List directly at offset 6, and evalUnsafe passes that list to the evaluator at offset 9. CallExpression OOoo00oo0OoOOO0o0OO0oOoo stores its Function reference, rather than performing a model-keyed function acquisition on each evaluation. UserFunctionBinding computeIfAbsent supplies the captured node. Same-name lookups in the same binding scope can alias that node; distinct parsers/scopes are not automatically aliases.
- MolangContext O0O00Oo0o0oO0oo0oO00OOoO lookup delegates at offset 5 to its AnimatableEntity. CustomEntity oOo00OoOO00O000ooO0Oo00o final lookup calls current getModelContainer (1), assets (4), userFunctions (7), map.get(name) (11), and returns the IValue. Thus lookup is model-dependent when performed.

## Cache, reset, null and exception limits

UserFunction owner ooo0o0OoOooOOOo0OOOo00oO$Oo0Oo0o00O00Oo0OOoOOoooo:

- evaluate tests context.entity instanceof IContext before cache handling. An incompatible entity returns null without resolving or clearing the name.
- Nonnull cache branches from offset 26 to 85, bypassing model lookup. Dispatch at 92 uses the current context and stored IValue.
- Null cache with null name returns null at 36–37. Otherwise lookup returns into the sole cache field write at 49. Null lookup invokes debugPrint, then writes name=null at 80. Normal misses therefore do not retry on that retained node, even if a later model defines the name.
- A thrown lookup or a thrown debugPrint is not equivalent to a normal miss. No local exception handler guarantees the name=null write; debug failure before offset 80 leaves the name available for retry. A nonnull target whose evaluation returns null or throws remains cached: target lookup and target evaluation are distinct phases.
- Across all 955 class records, the node has exactly three direct field writes: constructor name at 6, evaluate cache at 49, evaluate name at 80. The sole bootstrap handle to this class is its constructor. No direct successful-cache invalidation or model-key update was found. Binding resetScoped clears the binding map; it does not walk retained nodes or mutate their fields. A fresh node/reparse can isolate future evaluations; map clear alone cannot repair an old reference.
- These are closed direct-classfile findings, not claims excluding reflection, native/external mutation, races, or all possible object replacement paths.

## Concrete symbolic counterexamples and negative cases

These are authored sequential traces, not executed assets or a native/runtime oracle.

1. Both model A and model B lack local animation key k and receive the same default animation D. D contains reached call node U for name f. A.common.f=VA and B.common.f=VB, VA != VB. First evaluation U(A) stores VA. Later U(B) skips B's lookup and evaluates VA in B's current context. This refutes a universal claim that inherited animation calls always rebind to each model's own f.
2. Under the same aliases, A.common lacks f; U(A) has a normal debug return, sets name=null. U(B), even when B.common.f exists, returns null without lookup. This refutes universal retry-after-model-change.
3. If A and B have their own separately parsed animation graph, sharing an animation name is insufficient; U_A and U_B may resolve independently. If their function maps point at the identical IValue, cache identity differs from lookup freshness but this trace does not demonstrate different dispatched bodies. Local override k blocks this default-inheritance route.
4. First resolution need not occur in the default model. Whichever compatible context first reaches this node establishes its successful target or normal miss. This is per node, not one winner for an entire animation or model.
5. A target body's child call node that was not reached under A has no resolution merely because its parent target was cached. If later reached under B, that child can resolve through B. Thus a parent body from A and a newly resolved child body from B can coexist. This mixed-context trace requires a genuinely unvisited, distinct child node; if the child aliases an already resolved same-name binding node, or was already visited, its existing state governs. No eager recursive binding was inferred.

## Premises and remaining unknowns

The claim requires actual object alias, an expression carrying the captured user-function node, compatible current contexts, the stated lookup contents, reachability/ordering, and no intervening replacement/mutation. The builder proves an aliasing route, not the existence of a relevant default expression. No assets, example models, native code, Java guest classes, CI, network requests, or Git edits were executed. No security impact or runtime reproduction is claimed. Data-dependent reachability, runtime scheduling, actual asset contents and broader reload lifecycle remain open.
