# YSM 2.6.5 concrete evaluator recovery — 2026-10-05

This bounded milestone adds **2 classes and 10 methods** to published baseline
`e333e96aa7ee1fa10884cc5b9dc156a4ee847584`. The resulting map has **282 mappings: 245 CONFIRMED /
37 HIGH**, with **107 class / 170 method / 5 field** exact contracts and **0 failures**.
All 270 prior mapping rows are preserved. CONFIRMED denotes supported semantic correspondence;
original unobfuscated symbol names remain unproven. **SOURCE_ARTIFACT_DIVERGENCE** and whole-source
**NOT_ESTABLISHED** equivalence remain explicit.

## Coherent boundary

The previous milestone resolved Function arguments, ExecutionContext wrappers, Expression's typed
visitor entry and ValueConversions. This pass connects those contracts to a concrete entity-bound
evaluator: two factories → single/multi Expression.visit dispatch → return/control state → selected
call/unary/statement visitor methods. It stops before execution-scope/loop traversal, createChild,
full operator/lambda dispatch or wider AST class recovery. The state below belongs to each evaluator
instance; no controller-wide/global ownership or thread-safety claim follows.

| Exact owner suffix | Semantic counterpart | Access flags | Fields / methods | Normalized class candidates |
|---|---|---:|---:|---:|
| `O0Oooo00oOo00O00OoOOOooO` | `ExpressionEvaluator` | 1537 | 0 / 2 | 1 / 955 |
| `oo00Oo00o0ooooOooo0Oo0OO` | `ExpressionEvaluatorImpl` | 49 | 6 / 52 | 1 / 955 |

Both declarations are unique among 955 classes using order-independent access/normalized-descriptor
member multisets. The interface extends the previously CONFIRMED ExecutionContext; its typed factory
constructs the concrete owner. That owner is the sole direct implementer of the evaluator interface
and the exact visitor type used by the prior Expression contract. The visitor's whole class was not
added as a mapping. Compiler-generated member metadata does not prove full behavioral equivalence.

## Exact method contracts

Owners are given above and retained in every JSON member record; exact identity includes owner,
member and the complete descriptor.

| Semantic method | Exact member | Full JVM descriptor |
|---|---|---|
| `ExpressionEvaluator.evaluator` | `Oo0Oo0o00O00Oo0OOoOOoooo` | `(Ljava/lang/Object;)Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;` |
| `ExpressionEvaluator.evaluator` | `o0OOooo0o0OO00OoOOOo0o0O` | `()Lcom/elfmcys/yesstevemodel/O0Oooo00oOo00O00OoOOOooO;` |
| `ExpressionEvaluatorImpl.entity` | `Oo0Oo0o00O00Oo0OOoOOoooo` | `()Ljava/lang/Object;` |
| `ExpressionEvaluatorImpl.evalSingleExpressionUnsafe` | `o0OOooo0o0OO00OoOOOo0o0O` | `(Lcom/elfmcys/yesstevemodel/oOOOOoo0O0Oo0O00oo0oooO0;)Ljava/lang/Object;` |
| `ExpressionEvaluatorImpl.evalMultiExpressionUnsafe` | `Oo0Oo0o00O00Oo0OOoOOoooo` | `(Ljava/lang/Iterable;Z)Ljava/lang/Object;` |
| `ExpressionEvaluatorImpl.popReturnValue` | `O00OOOooOoooOoo0o0o0oO0O` | `()Ljava/lang/Object;` |
| `ExpressionEvaluatorImpl.visitCall` | `Oo0Oo0o00O00Oo0OOoOOoooo` | `(Lcom/elfmcys/yesstevemodel/OOoo00oo0OoOOO0o0OO0oOoo;)Ljava/lang/Object;` |
| `ExpressionEvaluatorImpl.visitUnary` | `Oo0Oo0o00O00Oo0OOoOOoooo` | `(Lcom/elfmcys/yesstevemodel/O0o0Oo0oo0oOooOO000oO00o;)Ljava/lang/Object;` |
| `ExpressionEvaluatorImpl.visitStatement` | `Oo0Oo0o00O00Oo0OOoOOoooo` | `(Lcom/elfmcys/yesstevemodel/ooOo0OO0OOOoo0ooooo00Oo0;)Ljava/lang/Object;` |
| `ExpressionEvaluatorImpl.visit` | `Oo0Oo0o00O00Oo0OOoOOoooo` | `(Lcom/elfmcys/yesstevemodel/oOOOOoo0O0Oo0O00oo0oooO0;)Ljava/lang/Object;` |

The entity factory constructs a new implementation with its Object argument. The no-argument factory
reads the exact static binding fallback field and calls that factory. Bounded ObjectBinding initializer
and null-return helper evidence is retained; no runtime property lookup was performed. The entity
getter returns the private final Object field set by the constructor.

Single-expression unsafe dispatch and generic visitor fallback have **the same full parameter/return
descriptor** and public flags: two exact candidates. Dispatch invokes the known Expression.visit
contract and clears pending return/control state in its finally paths. Fallback allocates and throws
UnsupportedOperationException instead. Normalized AST descriptors admit 15 method candidates;
coarse unordered reference-presence predicates reduce selected roles to one, followed by exact
ordered instructions/references, branch/switch targets and exception tables. Coarse presence counts
are explicitly distinct from the audit's complete ordered reference paths.

## Return state, finally lifecycle and control flow

| Entry | Supported Java behavior | Exact boundary |
|---|---|---|
| single unsafe evaluation | visit expression; clear pending return/control on normal completion and protected exception; return saved result or rethrow | protected [0,8), handler20; athrow32 |
| multi unsafe evaluation | optionally increment return-through depth; initial boxed0D; iterate, visit, pop pending return; stop on nonnull pending value; clear state and conditionally decrement | protected iteration [19,78), handler105, plus normal cleanup |
| popReturnValue | save pending value; clear it only when depth is0; return saved value | ifne at9 targets17 |
| visitCall | obtain function and arguments from node; call the already mapped Function.evaluate(this,args); return result | accessor calls1/8; evaluate11 |
| visitUnary | evaluate operand; logical/float negation branches; RETURN stores operand and returns boxed0D | named switch key3 targets73 |
| visitStatement | set BREAK or CONTINUE state and return null | named keys1/2 target36/46 |

Finally cleanup **does not suppress exceptions**: the unsafe entries rethrow escaping throwables
covered by their protected region. The prior safe ExecutionContext wrappers separately catch
java/lang/Exception, log and return null. Multi depth increment at0–11 and initial Double.valueOf at15
precede its protected iteration region; this pass makes no whole-method cleanup guarantee for every
possible exception. It does not execute the code.

The multi sequence stops on a **nonnull** pending return value; null is the sentinel checked by this
path. Empty iteration returns its initial boxed0D. BREAK/CONTINUE are state writes here: downstream
loop consumption remains outside this milestone. The selected multi loop does not test controlOp.
No field mapping rows were added: entity/return/control/depth field relations are supporting evidence;
inLoop and the binary-evaluator array remain deferred.

## Enum relations without ordinal assumptions

The exact enum initializers connect retained names to obfuscated fields. The generated `$1` initializer
connects those fields to switch-map keys; decoded signed tableswitch/lookupswitch targets connect keys
to evaluator branches. All three supporting initializers are audited without new enum/AST mappings.

| Retained operation | Generated key | Branch target | Selected effect |
|---|---:|---:|---|
| LOGICAL_NEGATION | 1 | 48 | boolean conversion / negation |
| ARITHMETICAL_NEGATION | 2 | 64 | float conversion / fneg |
| RETURN | 3 | 73 | pending return store / boxed0D |
| BREAK | 1 | 36 | BREAK control store |
| CONTINUE | 2 | 46 | CONTINUE control store |

PLUS exists in the unary enum but has no generated assignment in this switch map and reaches default
83, which throws IllegalStateException. Statement default53 returns null. Enum ordinals index generated
maps at runtime; this research derives meaning from name→field→key→branch relations, never a guessed
ordinal. Generic fallback's exception type and throw path are checked; full string-concat bootstrap
payload semantics are not claimed.

## Source provenance and reused reconnaissance

Source comparisons use immutable official release-line candidate
[f184edabd1b5115ce5a24cb6d155ba5a669f5ba6](https://github.com/YesSteveModel/YesSteveModel/tree/f184edabd1b5115ce5a24cb6d155ba5a669f5ba6).
The dossier retains exact paths, URLs and SHA-256 values for ExpressionEvaluator, ExpressionEvaluatorImpl,
ObjectBinding, UnaryExpression and StatementExpression. Documentation @since labels and compiler
synthetics do not establish distributed-build identity. This local subset shows no source divergence;
the known global divergence is preserved. Pinned OpenYSM remains comparative only.

Previously inspected Chinese creator/compatibility sources are reused as fixture/provenance leads:
Anan1a's nested fn/argument scripts, Vivecraft's speculative hook negative, and YES_SlashBlade's precise
cross-version adjacent contracts. Their revisions and limits remain in the prior
[MOLANG-EVALUATION-EVIDENCE-2026-10-05.json](MOLANG-EVALUATION-EVIDENCE-2026-10-05.json).
No new broad crawl was needed; no community evidence promoted these identities or proved runtime behavior.

## Fresh validation and rerun

Exact official Modrinth Zqooxsd2 JAR: SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, SHA-1
`151ac7b24da8beeca1a20864565743cfd77af286`, size63,269,843 bytes. Artifact identity was rechecked before
analysis. Full scanner: 282 contracts, 955 classes, **0 contract / parse failures**. Old audits:
**66 / 0** and **106 / 0**; new evaluator audit: **92 / 0** checks/failures. Mapping IDs and exact
owner/member/full-descriptor targets remain unique; no divergent new CONFIRMED rows.

Six durable negative controls each exit1: wrong single reset field, wrong multi depth field, changed
pop branch target, changed RETURN switch target, swapped BREAK/CONTINUE switch arms and replacing a
finally catch-all with java/lang/Exception. They verify concrete lifecycle/operation risks. Separate
comparison controls preserve only their coarse reference-presence predicate, not ordered paths.

The audit's optional detailed_operands mode decodes numeric constants/immediates and signed switch
keys/targets for this dossier. Older dossiers retain their previous instruction schema and pass unchanged.
Foundation regeneration uses **107 seeds** over the same **955 nodes / 3,618 undirected edges / 3,823
references / 19 components**. MOLANG's propagated domain now has255classes; these labels are search
hints, not additional semantic recoveries. Fifteen isolated UNKNOWN classes remain.

```bash
python tools/scan_ysm_265.py --jar /scratch/ysm-2.6.5-forge+mc1.20.1-release.jar --map OBFUSCATION-MAP-2026-10-05.json --out /scratch/ysm-scan.json
python tools/audit_seed_recovery_ysm_265.py --jar /scratch/ysm-2.6.5-forge+mc1.20.1-release.jar --evidence SEED-RECOVERY-EVIDENCE-2026-10-05.json --out /scratch/ysm-seed-audit.json
python tools/audit_seed_recovery_ysm_265.py --jar /scratch/ysm-2.6.5-forge+mc1.20.1-release.jar --evidence MOLANG-EVALUATION-EVIDENCE-2026-10-05.json --out /scratch/ysm-evaluation-audit.json
python tools/audit_seed_recovery_ysm_265.py --jar /scratch/ysm-2.6.5-forge+mc1.20.1-release.jar --evidence MOLANG-EVALUATOR-EVIDENCE-2026-10-05.json --out /scratch/ysm-evaluator-audit.json
python tools/cluster_ysm_265.py --jar /scratch/ysm-2.6.5-forge+mc1.20.1-release.jar --map OBFUSCATION-MAP-2026-10-05.json --out /scratch/ysm-foundation.json
```

Run from the YSM research directory with the official JAR outside the repository. No JAR/native
entries or private helper are needed in Git: the retained audit and
[MOLANG-EVALUATOR-EVIDENCE-2026-10-05.json](MOLANG-EVALUATOR-EVIDENCE-2026-10-05.json) rerun the selected
checks. javap remains unavailable locally; bytecode inspection is static, not JVM/Minecraft execution.
No native/protection/decryption or full parser/runtime correctness claim is made.

This is a useful stopping point: the recovered Function/Context boundary now reaches a concrete
per-instance evaluator with dispatch, return and cleanup semantics. A future separate milestone can
inspect execution-scope/loop consumption; it is deliberately not folded into this pass.
