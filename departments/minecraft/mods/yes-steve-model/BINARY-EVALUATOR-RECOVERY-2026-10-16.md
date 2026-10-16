# YSM 2.6.5 binary evaluator recovery — 2026-10-16

## Bounded result

The previously deferred **16-entry binary evaluator cohort is now statically evidence-backed**.
This continuation adds **20 method mappings and 1 field mapping**, all semantic CONFIRMED:
16 operation bodies, three lazy wrapper factories, `visitBinary`, and `BINARY_EVALUATORS`.
The nine compiler-generated wrapper/thunk bodies, constructor and child factory, and relevant
AST/enum members are supporting evidence rather than inflated new mapping counts. No new class
mapping is needed. The additive mapping batch is also retained separately in
[BINARY-EVALUATOR-MAPPINGS-2026-10-16.json](BINARY-EVALUATOR-MAPPINGS-2026-10-16.json).

CONFIRMED means bounded semantic correspondence, **not original unobfuscated names**. In particular,
`binaryAnd`, `binaryAssign`, etc. are descriptive research labels for synthetic bodies; the source
expresses them as anonymous lambdas. Whole-source equivalence remains **NOT_ESTABLISHED**, with the
previous global **SOURCE_ARTIFACT_DIVERGENCE** finding preserved. No local mismatch was found in
this cohort. Whole-target completion, parser correctness and game/runtime compatibility are not claimed.

## Exact anchors and method

- Distributed ANCHOR: Minecraft 1.20.1 / Forge / YSM 2.6.5, Modrinth `Zqooxsd2`.
- JAR SHA-256: `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`;
  size 63,269,843 bytes. Raw artifact remains outside Git.
- Official release-line source candidate:
  [`f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`](https://github.com/YesSteveModel/YesSteveModel/tree/f184edabd1b5115ce5a24cb6d155ba5a669f5ba6).
  [Evaluator lines 36–142, 154–173 and 347–353](https://github.com/YesSteveModel/YesSteveModel/blob/f184edabd1b5115ce5a24cb6d155ba5a669f5ba6/src/main/java/com/elfmcys/yesstevemodel/molang/runtime/ExpressionEvaluatorImpl.java#L36)
  and [BinaryExpression operation enum](https://github.com/YesSteveModel/YesSteveModel/blob/f184edabd1b5115ce5a24cb6d155ba5a669f5ba6/src/main/java/com/elfmcys/yesstevemodel/molang/parser/ast/BinaryExpression.java#L117)
  were read locally; exact file hashes are in the dossier. No FRONTIER/comparative claim is imported.
- Exact evaluator owner: `com/elfmcys/yesstevemodel/oo00Oo00o0ooooOooo0Oo0OO`.

The chain is retained enum name → constructor's **explicit index argument** → stored index field →
index getter → `visitBinary` array lookup → `<clinit>` slot store → `invokedynamic` bootstrap →
exact implementation handle → complete body/control flow. No guessed ordinal, source-array order,
synthetic name or unordered reference set substitutes for that chain.

`visitBinary` reads the exact array at offset 0, gets the enum at 4 and its index at 7, performs
`aaload` at 10, gets left/right nodes at 13/17, and calls `Evaluator.eval` at 20. This dispatch passes
nodes, not already evaluated values. The array is private static final (access 26), allocated with
length 16; all slots 0–15 and the store at `<clinit>` offset 170 are retained.

[BINARY-EVALUATOR-EVIDENCE-2026-10-16.json](BINARY-EVALUATOR-EVIDENCE-2026-10-16.json)
contains full owner/name/descriptor identities, flags, ordered instruction/reference paths, numeric
and branch operands, complete encoded operands, code hashes, exception handlers and 25 exact
bootstrap-callsite links. Sixteen operator-table records explicitly join names, slots and handles.

## Operation findings

Offsets below are relative to each exact body identified by its mapping ID in the dossier.

| Slot | Operation | Supported local semantics / decisive offsets |
|---:|---|---|
| 0 | AND | Left lazy evaluation at 1; false branch 6→22 skips right evaluation at 10. |
| 1 | OR | Left lazy evaluation at 1; true branch 6→18 skips right evaluation at 10. |
| 2 | LT | Lazy left/right at 1/7; `fcmpg` 12, false branch `ifge` 13→20. |
| 3 | LTE | Same evaluation order; `fcmpg` 12, false branch `ifgt` 13→20. |
| 4 | GT | Same evaluation order; `fcmpl` 12, false branch `ifle` 13→20. |
| 5 | GTE | Same evaluation order; `fcmpl` 12, false branch `iflt` 13→20. |
| 6 | ADD | Visit left/right at 2/10, then convert left/right at 18/23, `fadd` 26, Float boxing 27. |
| 7 | SUB | Lazy left/right at 1/7, `fsub` 12. |
| 8 | MUL | Lazy left/right at 1/7, `fmul` 12. |
| 9 | DIV | Evaluate both operands at 1/8; divisor compared to zero at 16; nonzero branch 17→22 reaches `fdiv` 24, zero returns positive float zero at 20. |
| 10 | ARROW | Left visit 2; null returns null; nonnull creates child 16, visits right with child 24, reads child pending return 34 and writes parent pending return 37. |
| 11 | NULL_COALESCE | Left visit 2; nonnull 9→20 returns left unchanged; only null visits right at 14. |
| 12 | ASSIGN | Right visit 2 precedes all target handling. Copy/assign and struct-access paths described below. |
| 13 | CONDITIONAL | Left visit 2 and boolean conversion 9; false 12→23 returns null, otherwise visits right 17. |
| 14 | EQ | Both visits 2/10; identity first; Number conversion before null test; then right StringExpression, left StringExpression, fallback left Object.equals. |
| 15 | NEQ | Same evaluation and case order as EQ; corresponding boolean result negated. |

### Lazy wrappers and evaluation order

The `bool`, `compare`, and `arithmetic` factories capture an operator in a LambdaMetafactory
closure. Their wrapper bodies create left/right thunks with the respective node and evaluator,
invoke the operator, then box Boolean or Float. Each thunk evaluates its node and calls the exact
previously recovered `ValueConversions` helper. Creating the thunks does not evaluate the nodes.
The actual operation bodies determine whether to invoke the right thunk.

This matters for side effects and escaping exceptions: **ADD visits both nodes before either
conversion**, while SUB/MUL/DIV/comparisons convert the left through its thunk before visiting the
right. AND/OR are genuinely short-circuiting. The dossier retains operand locals and bootstrap
handles, including the otherwise body-identical left/right conversion thunks.

### Numeric boundary

DIV tests the **divisor**, after evaluating both operands. Both positive and negative zero select
positive float zero; no float division is executed on that branch. An unsanitized NaN supplied
directly to this private lazy interface would take `fdiv`, and the relational compare opcodes yield
false for NaN. These are JVM instruction-level observations, not evidence that ordinary expression
inputs reach those bodies as NaN: the normal thunks call `ValueConversions.asFloat`, whose prior
recovery includes NaN-to-zero conversion. This pass neither executes NaN fixtures nor broadens
external conversion semantics.

### Assignment and arrow state

ASSIGN visits RHS first, even for an unsupported target. For an assignable-variable expression it
retrieves the target at 19, calls Struct.copy at 35 if applicable, then assigns at 45. The resulting
value, including the returned copy, is the expression result. This does not establish deep-copy
semantics; the prior HashMapStruct recovery preserves its map-sharing caveat.

For a struct-access target, a Struct-valued RHS returns at 67–68 **without evaluating the base or
writing the property**. Otherwise the base is evaluated at 81. An existing Struct receives the
property at 107. A non-Struct base whose expression is assignable instead gets a new HashMapStruct
(139/143), property insertion (156), then variable assignment (166). Other cases return the RHS
without throwing an unsupported-target error in this method. Referenced methods can still throw.

ARROW creates a new entity-bound evaluator, using the previously recovered `createChild` contract;
this does not inherit parent return/control/depth fields. On normal right-side completion it copies
**child → parent** pending return, even when that value is null, then returns the saved right-side
result. No control-op copy appears. There is no exception handler around this sequence: an escaping
right-side exception bypasses the copy. This is not a finally-cleanup guarantee.

### Equality precedence

EQ/NEQ evaluate left then right once. Reference identity wins first, including two null references
or the same boxed NaN object. If either result is Number, both are converted (right first, then
left) and compared as floats **before** the null branch. Consequently one null and one Number
are not automatically unequal at the dispatch level. Only after that path is excluded does a null
operand decide false/true. Right StringExpression's equals takes precedence over left
StringExpression's equals; the fallback is left.equals(right). Delegated equals behavior is not
redefined by this pass. The exact branches, calls and boxing are audited.

## Verification and reproducibility

Fresh scoped verification: **291 existing-auditor checks + 368 scoped/relational checks, zero
failures**. Fifteen deliberately corrupted evidence controls were each rejected:

1. Wrong enum index / array slot
2. Wrong slot implementation handle
3. AND branch polarity
4. OR short-circuit target
5. LT `fcmpg` replaced by `fcmpl`
6. DIV zero-guard target
7. DIV arithmetic opcode
8. ASSIGN RHS local replaced by LHS
9. ARROW child-return source local replaced by parent
10. ADD second-visit / conversion call ordering swapped
11. Missing assignment instruction evidence
12. Missing support thunk row
13. Missing operation-table entry
14. Missing bootstrap-callsite link
15. Missing table-field candidate

These are corrupt-evidence audit controls, **not execution tests or mutated-JAR runtime results**.
Snapshot matching establishes byte identity/control flow; the finite semantic interpretations above
come from reviewing those paths and the pinned source. The custom auditor independently derives
all 16 enum/index/slot/bootstrap joins rather than trusting the descriptive table.

Run from the YSM research directory with the exact artifact outside Git:

```bash
python tools/binary_evaluator_ysm_265.py \
  --jar /absolute/path/to/ysm.jar \
  --evidence BINARY-EVALUATOR-EVIDENCE-2026-10-16.json \
  --out /tmp/ysm-binary-audit.json
```

The existing `audit_seed_recovery_ysm_265.py` also accepts this dossier directly. The central mapping includes the 21 reviewed additions while preserving all 604 prior rows.
See [current verification](SEMANTIC-VERIFICATION-2026-10-16.json) for the integrated result. Raw JARs, decompiled trees and copied source bodies are not published. No native,
model-protection, decryption, authorization-bypass or runtime operation was performed.

## Remaining boundary

The formerly deferred binary-lambda table is closed at static Java semantics. This does not close
all 432 previously unseeded main owners, the whole evaluator/AST/runtime, source-build equivalence,
or the required whole-target history and runtime facets. Useful next evidence would be explicitly
scoped Java fixtures for side-effect ordering and conversion/delegated-equals boundaries, with
separate authorization and dependency identities if execution is requested. Prior creator/community
reconnaissance remains a fixture lead only; it did not establish any new mapping here.
