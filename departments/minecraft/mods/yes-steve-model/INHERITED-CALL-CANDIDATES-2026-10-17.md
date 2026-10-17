# Optional inherited symbolic-owner candidate check

Use this only after selecting one ordinary instance method and finding that an exact owner/name/descriptor caller scan may be too narrow. It is not a startup task, full call graph, JVM method resolver or instruction to install a dependency stack. The fixed YSM2.6.5 artifact is read as bytes; no target classes execute.

## A concrete reason for the extra check

IGeoRenderer's default getRenderColor method has zero invocation sites whose symbolic owner is exactly that interface in the fixed artifact. Yet three already inspected renderer bodies have matching method name/descriptor invocation references owned by their concrete renderer classes. Each of those classes declares the interface in its ancestry.

The [render-color report](RENDER-COLOR-INHERITED-CANDIDATES-2026-10-17.json) therefore distinguishes zero exact-symbolic-owner sites from three nominal-descendant candidates. Their known paths are direct to IGeoRenderer, with no same-signature declaration on that chosen path before the interface. The Minecraft renderer superclasses are not bundled in this JAR; their missing declarations remain explicit. These observations support inspecting those known renderer calls, not certifying dynamic dispatch for every receiver.

This does not invalidate a correctly labeled exact-symbol inventory. It shows why `zero exact references` must not be rewritten as `unused` or `cannot execute`.

## Do not match by obfuscated name and descriptor alone either

The [Color red-channel report](COLOR-RED-INHERITED-CANDIDATES-2026-10-17.json) finds six exact sites and no known descendant candidates. Nineteen other sites share the same short obfuscated name and `()I` descriptor but have no proven ancestry to Color in this artifact. They are kept in a separate unresolved/unrelated-signature category, not counted as Color calls. The two cases jointly demonstrate both undercounting by exact owner and overcounting by signature alone.

## Operation and limits

`tools/inherited_call_candidates_ysm_265.py` takes explicit `--jar`, `--owner`, `--name`, `--descriptor` and `--out` arguments. It:
1. Enforces the fixed artifact hash/size and confirms the exact target declaration exists.
2. Rejects constructors, class initializers, static and private targets. Abstract/default/public/protected/package instance declarations can be inspected, but access resolution is not proved.
3. Reads class superclass/interface declarations and direct invokevirtual/invokespecial/invokeinterface references. Matching bootstrap argument references are reported separately.
4. For a different symbolic owner with the same name/descriptor, searches for the first breadth-first nominal path to the declared owner within the artifact.
5. Reports same-signature declarations on that path and missing ancestor declarations encountered during the search. This is not an exhaustive enumeration of all paths or missing external classes.

The categories are EXACT_SYMBOLIC_OWNER, NOMINAL_DESCENDANT_CANDIDATE and SAME_SIGNATURE_NO_PROVEN_ANCESTRY. Every site explicitly says dispatch_resolved=false. A candidate can be affected by overrides, class/interface resolution rules, access checks, external ancestors and runtime receiver types. Reflection, native code, invokedynamic target resolution and unlisted method-handle forms are not closed. This helper never loads an external classpath or downloads/installs tools.

Reports retain caller identity/code hash, exact reference instruction, target declaration, dependency hashes and artifact identity. They are focused evidence for a follow-up review, not new semantic mapping confidence. Existing full method snapshots should be reused to inspect the candidate body.

## Verification

Eleven small unit tests cover exact owners, interface inheritance, same-signature overrides, external unknowns, unrelated owners, overload/name mismatches, cycles, diamond interfaces, missing targets, unsupported target kinds and abstract instance declarations. Two actual artifact cases check the counts above and preserve unresolved-dispatch flags. See [verification](INHERITED-CALL-CANDIDATES-VERIFICATION-2026-10-17.json). No whole-project CI, game or target method execution occurred.

A more complete hierarchy/call-graph analysis may require an explicit external classpath and a suitable analyzer. That is a separate task with its own scope; this bounded helper does not silently approximate it as completed.
