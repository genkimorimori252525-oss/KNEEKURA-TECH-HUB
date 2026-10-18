# Failed parsing can affect a later successful temp-address capture

2026-10-18. BOUNDED_STATIC_JOIN; [independent review CONDITIONAL_STATIC_ACCEPTANCE](PARSER-FAILURE-TEMP-ADDRESS-REVIEW-2026-10-18.md). This resolves the specific consequence left conditional in PARSER-POOL-LIFETIME: what happens if a failed parse has already allocated temp bindings and that parser is used again. It is a bounded parse-time/runtime storage join, not a whole-language audit or reproduced game bug.

## New result

A failure after allocating temp names, but before the normal transient reset, can affect the numerical addresses captured by the next successful expression parsed on the same parser. That next parse's successful cleanup does not repair or renumber its already-created variable objects. Consequently successful expression parsing alone does not guarantee that temp addresses start at zero independently of prior failure history.

Runtime temp storage does not translate those captured addresses by variable name. It reads the current frame at the address. Thus failure-dependent compilation history can change which retained root slot an uninitialized temp read accesses, under the explicit fixture conditions below. It need not cause an out-of-bounds failure: getTemp returns null when the address is beyond current logical varSize, and setTemp expands storage.

## Minimal symbolic witness, not target execution

Premises: one parser starts with an empty temp-binding map/top0; a parse binds name a and then throws before the facade's successful reset; returning it to the pool completes normally; the next relevant rental selects this same parser with no intervening successful transient reset. Pool order/identity is a premise, not a measured scheduling fact.

1. Failed prefix creates a→0, top=1. Existing a remains at0 if referenced again.
2. Scoped-only return/reset leaves that temp map and top intact.
3. A later successful expression referencing previously unseen b captures b→1.
4. The successful facade resets the parser's temp map/top to empty/0. The emitted b variable retains final address1.
5. A subsequent successful expression c on the cleaned parser captures c→0.

For a current root frame with varOffset0, varSize2 and slots [11,22], the b object from step3 reads22. A b compiled on a clean parser would capture0 and read11 in that same fixture. A newly pushed logical frame with varSize0 instead returns null for either unassigned address. Assign-before-read can mask the address difference because both assignment and lookup use the same captured slot.

The string `t.a )` is an illustrative statically derived failure candidate: namespace/property binding occurs before the parser's end-of-expression delimiter test rejects a closing parenthesis outside an enclosing expression. It was not fed to the target parser. The core result requires only the evidenced bind-then-later-throw path, not an executed malformed-string fixture.

`witness.py` checks this authored abstract sequence and writes `symbolic-witness.json`. It does not implement the target lexer/parser or run original code. This example is not a claim that a real model uses uninitialized temps, that the behavior violates a declared language specification, or that a player's data crossed any security boundary.

## Exact original-code anchors

Owner prefix: `com/elfmcys/yesstevemodel/`.

### Bind first, possible rejection later

ParserImpl `ooOO0OoOO00Ooo000o0O0o0O`:

- `Oo0Oo0o00O00Oo0OOoOOoooo(Lcom/elfmcys/yesstevemodel/OoO00O0O0ooo0oO0O00Oo00o;)Lcom/elfmcys/yesstevemodel/oOOOOoo0O0Oo0O00oo0oooO0;` performs root getProperty429 and namespace property getProperty542. The identifier AST captures that resulting variable object, as established by the existing parser/AST dossier.
- `Ooooo0oooO0oooOOOoO0000O()Lcom/elfmcys/yesstevemodel/oOOOOoo0O0Oo0O00oo0oooO0;` calls compound parse60 before EOF/SEMICOLON acceptance tests81/91; the rejection path throws116. There is no rollback of earlier binding work in these bodies.

### Failed facade and pool return do not reset temp allocation

MolangParser `OooOoOoOOOOo000oo0oo00oo`, unsafe method `o0OOooo0o0OO00OoOOOo0o0O(Ljava/lang/String;Z)Lcom/elfmcys/yesstevemodel/O0o0OOO00000oO00O00oOOo0;`: engine parse20, MolangValue construction26, transient reset34. There are no exception handlers, so failures before34 bypass it. Its public `Oo0Oo0o00O00Oo0OOoOOoooo()V` calls PrimaryBinding's scoped reset at4.

CustomMolangParser `O00o0ooOoo00o00o0OOOO0o0`, return method `Oo0Oo0o00O00Oo0OOoOOoooo(Lcom/elfmcys/yesstevemodel/OooOoOoOOOOo000oo0oo00oo;)V`: parser reset1, pool.add8. Its String unsafe helper has a genuine catch-all/finally covering4..11 and returns the parser on the exceptional path. Rent polls the pool at3; it does not establish that a caller receives the most recently returned instance.

PrimaryBinding `oOOOoooooO00ooo0o0OOOooO` has separate scoped and transient lists. TempVariableBinding is an ObjectBinding/TransientObject, not a ScopedObject; the pinned interfaces are independent, not an inheritance alias. Thus ordinary scoped cleanup does not incidentally clear temp bindings. The safe parser facade's fallback-to-zero is also not successful transient cleanup: its handler returns a fallback after the unsafe call failed.

### Captured integer survives successful cleanup

Temp binding `oo0oO0o0ooo0oo0oO0oOo00O.getProperty(Ljava/lang/String;)Ljava/lang/Object;` delegates computeIfAbsent. Its allocation lambda `Oo0Oo0o00O00Oo0OOoOOoooo(Ljava/lang/Object;)Lcom/elfmcys/yesstevemodel/oo0oO0o0ooo0oo0oO0oOo00O$Oo0Oo0o00O00Oo0OOoOOoooo;` reads old top6, increments/stores top12, then constructs the variable15 with the old integer.

Nested variable constructor `(I)V` stores final address at6. evaluate obtains current context tempStorage9, reads captured address15 and calls getTemp18. assign likewise reads address15 and calls setTemp19. No name-based relocation or parent binding lookup occurs during evaluation.

The binding's reset method clears the map4 and sets top=0 at11. It does not traverse emitted ASTs or alter their final address fields. Therefore resetting after a successful parse cannot renumber that parse's result.

### Runtime does not neutralize the address difference

StackMemory `O00o0OooOOOooo000ooOo00o.Oo0Oo0o00O00Oo0OOoOOoooo(I)Ljava/lang/Object;` checks addr against varSize at5; valid reads use mem[varOffset+addr] at18, otherwise null20–21. Its `(ILjava/lang/Object;)V` writer extends varSize14, ensures capacity24, writes array38. It has no variable-name map.

Existing STORAGE-CALLERS evidence already establishes processor-owned memory persistence, clearModel's lack of StackMemory replacement/reset, and direct task eval without universal push/pop. Those are reused premises, not newly claimed caller closure. The new contribution is failure-dependent capture surviving the next successful parse and selecting a different current-frame slot.

## Limits and reuse decision

No effect is claimed if failure occurs before any temp binding, the next rental gets another parser, an intervening successful parse resets the binding, runtime frames are freshly empty, or every relevant variable is assigned before reading. Repeated-failure overflow/resource-exhaustion scenarios are not analyzed. Arbitrary native parser lifecycle, external setters, concurrency and whole-model behavior remain outside scope.

For faithful reconstruction, do not assume parser return/reset or a fallback value restores a clean temp-address namespace. For a new design, failure cleanup could be made explicit, but that would be a deliberate behavior change rather than an evidenced original guarantee. No upstream patch is proposed or applied.

## Provenance

Original JAR SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`. Seven selected owners freshly parsed; their retained snapshots match the existing parser-binding, pool and storage evidence. Six source files match Git blobs at `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Source/artifact equivalence remains NOT_ESTABLISHED; prior divergence and central map669 remain unchanged.

`receipt.json` contains source/class hashes, method digests, seven structural checks and the authored symbolic-witness hash. `evidence.json` holds original snapshots outside Git. Reproduce with inspect.py, witness.py, verify.py in that order. Counts are evidence scope, not completeness or independent approval.

No target Java/native/assets execution, asset decoding, download/network, CI, runtime/403 retry or Git edits occurred.

Published evidence: [structural receipt](PARSER-FAILURE-TEMP-ADDRESS-EVIDENCE-2026-10-18.json), [authored symbolic witness](PARSER-FAILURE-TEMP-ADDRESS-WITNESS-2026-10-18.json). Reproduction scripts and original class snapshots remain outside Git.
