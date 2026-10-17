# Context variable and typed numeric conversion boundaries

Primary static review; independent review NOT_RUN. Fixed artifact SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f` and source
candidate `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. 43 method declarations across
ContextBinding, ContextVariable, LambdaVariable, EntityVariable, ValueConversions
and IValue; exact owners are in evidence. No runtime execution or map promotion.

## Registration and context validation

ContextBinding.var stores a LambdaVariable; entityVar stores an EntityVariable.
Their constructors receive the evaluator reference. ContextVariable's final
ExecutionContext overload first requires context.entity instanceof IContext and
validateContext=true, then calls its typed evaluate overload. Failure returns
boxed Integer0, not null. Base validation always returns true; EntityVariable
requires the IContext's entity to be a Minecraft Entity.

LambdaVariable's final typed evaluate simply calls the stored evaluator and
returns its Object result. It has no catch, numeric conversion or NaN filtering.
Thus a speed helper's boxed NaN is not sanitized merely by this wrapper. The
context guard can instead prevent the helper from being called at all when the
entity context is unsuitable. Other typed variable classes are not generalized
from this one subtype.

## Object result and typed conversion are different boundaries

ValueConversions.asFloat: null→0; Number.floatValue→same value unless NaN→0;
Boolean→1/0; other objects→1. Infinity is not rejected by the isNaN gate. A large
finite double may narrow to infinity before that test. asDouble uses doubleValue
and Double.isNaN with analogous fallbacks. asInt delegates Number.intValue and
otherwise null0/Boolean1-or0/other1; it does not parse numeric strings.

asBoolean returns false for null; preserves Boolean; converts Number via
floatValue and requires non-NaN and nonzero; other nonnull objects return true.
Consequently an empty String is not false on this helper, and a very small
nonzero Double can become false when its floatValue underflows. These are helper
semantics, not JavaScript-style truthiness or a claim that every expression takes
this conversion path.

IValue's default eval calls evalUnsafe inside a Throwable catch, logs and returns
null on failure. Typed evalAsFloat/Int/Boolean call eval and then the corresponding
ValueConversions helper. On those inherited paths, returned NaN becomes float0
or boolean false; returned infinity stays an infinity/true. NaN itself is not a
thrown exception. The object-returning eval does not perform numeric sanitation.

This qualifies the prior movement-query result: unchecked zero division at a
speed helper does not imply NaN reaches a bone setter unchanged. Whether the
consumer requests a float, boolean or raw object matters. Nor does IValue's default
catch protect all values: the earlier RotationValue dossier already demonstrated
an override with different behavior. Do not erase that exception boundary.

## Other binding facts and limits

ContextBinding.constValue wraps Strings as StringExpression, narrows Numbers to
float, converts Booleans to float1/0 and otherwise stores the original object.
This registration conversion is separate from evaluation-time asFloat. The map
getProperty simply returns the stored property. Full object-binding parsing and
ExpressionEvaluator variable visitation are not newly closed by these wrappers.

246 static checks pass;12 evidence-negative controls reject missing catches,
invented wrapper catch, NaN gates, object fallback and invalid-context fallback.
No independent semantic approval or runtime sample is claimed. Mapping669 and
whole-source-divergence cautions remain. Continue AST variable resolution and
consumer-specific conversion paths rather than labeling all query results as
universally sanitized or universally unsafe.
