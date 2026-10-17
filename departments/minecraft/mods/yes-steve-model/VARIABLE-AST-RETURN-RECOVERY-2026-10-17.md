# Variable AST dispatch and expression-return cleanup

Primary static review; independent review NOT_RUN. Fixed artifact SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, source
candidate `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. 28 selected complete
methods across IdentifierExpression, VariableExpression, AssignableVariableExpression,
MolangValue and six evaluator methods. The selection is fixed by exact member
keys and all five owner declarations/bootstrap records are retained. This is not
full parser/evaluator recovery, runtime execution or a mapping promotion.

## Binding target selects the AST class

IdentifierExpression.get tests Number, String, Function, AssignableVariable,
Variable in that order, constructing the corresponding constant/call/variable
node. Numbers narrow via floatValue. Assignable takes precedence over Variable;
it is not erased by the more general interface match. Other targets retain an
IdentifierExpression. Its private constructor requires nonnull name and calls
String.toLowerCase() without a Locale argument. Equality/hash use its normalized
name, not target identity. This is the exact call/field behavior, not proof that
all user identifiers are locale-independent or all parse-time lookup is handled
by this factory.

Variable nodes retain their target and dispatch through the visitor. Evaluator
visitVariable and visitAssignableVariable call target.evaluate(this) and return
that Object directly. No numeric sanitation or local catch is inserted in either
visitor. Evaluating a remaining generic IdentifierExpression throws
RuntimeException with the retained unknown-identifier diagnostic.

## Single/multiple expression boundaries have actual finally coverage

Single-expression unsafe evaluation invokes visit then clears returnValue and
controlOp on both normal and exceptional exits. It does not convert the returned
Object or catch the exception as a success value.

Multi-expression unsafe evaluation optionally increments returnThrough, starts
lastResult as boxed double0, visits expressions in sequence and checks
popReturnValue after each. A nonnull return value replaces lastResult and breaks;
null does not trigger this break condition. The finally paths clear returnValue
and controlOp and decrement returnThrough only if this invocation incremented it.
popReturnValue clears its stored value only when returnThrough==0. Handler ranges
and normal/exceptional cleanup stores are captured, not inferred from a comment.

MolangValue stores the supplied expression list and user-function flag without
copying, then evalUnsafe delegates to this multi-expression method with that flag.
It inherits IValue defaults rather than overriding eval. Joined with the preceding
conversion dossier, a raw variable Object (including a boxed NaN) can pass through
these visitors/multi-expression returns unchanged; a caller using inherited
IValue.evalAsFloat subsequently maps NaN to0. A caller requesting raw eval receives
the raw result, unless an exception was caught by the inherited IValue.eval.
This is a bounded dispatch/conversion chain, not a claim that all expression
operators or all IValue subclasses preserve the same values.

## Verification and next step

167 static checks pass;11 malformed-evidence controls reject missing finally,
changed return-null branch/returnThrough clearing, replaced variable call and
changed unknown-identifier path. A test-selector typo found during preparation
was corrected before this passing receipt; no target-code change was made.
Independent semantic review is not claimed. Mapping669 remains unchanged and
source/artifact global equivalence remains unproven.

Next inspect parser property resolution/binding lookup and assignable-variable
storage semantics, including when a target reference is captured versus looked
up again. Do not infer dynamic rebinding or parser case normalization from these
AST nodes alone.
