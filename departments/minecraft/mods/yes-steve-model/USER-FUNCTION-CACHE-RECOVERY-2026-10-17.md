# User-function target cache and parser call validation

Primary static review; independent review NOT_RUN. Fixed artifact SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, source
candidate `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Fifteen complete methods
across UserFunctionBinding, its nested UserFunction and CallExpression. Three
source records cover two files. Parser/assignment joins below reuse their existing
dossiers; this is not a new whole-parser/runtime execution test or map promotion.

## Successful lookup is cached on the captured function object

Binding getProperty caches one UserFunction per name via computeIfAbsent.
CallExpression stores a Function and ArgumentCollection reference, requiring both
nonnull; its one-argument constructor uses a shared placeholder empty collection.
The variable/identifier AST path can therefore retain this function object.

UserFunction.evaluate requires context.entity to implement IContext. If cache is
nonnull, it immediately proceeds to ctx.callUserFunction with that cached IValue;
there is no lookup keyed by the current entity/model on that branch. If cache is
null but name is already null, it returns null. Otherwise it looks up by name.
A missing lookup invokes debugPrint, then sets name=null and returns null on the
normal path. Later calls through that same object do not retry the lookup. If
logging throws, that name write is not guaranteed; no finally/catch surrounds it.

resetScoped clears the binding's map, not the fields of objects already returned
to ASTs. Future lookups can create fresh functions while old AST references retain
their earlier success or miss state. Whether actual model reload reparses/replaces
those ASTs remains a caller-lifetime question, not proof of a stale-cache bug.
Successful dispatch uses the previously reviewed user-call push/pop helper.

## Parser call shape and arity join

PARSER-BINDING-STORAGE already captures the complete parser implementation. Its
call branch permits parentheses only while the CallExpression arguments are the
placeholder identity; repeated parentheses after a filled call raise ParseException.
It parses argument expressions before validateArgumentSize and rejects a false
validator result. It also validates the current argument count on a call node
without a new parenthesized list. Default Function validation is true, while loop
and foreach enforce their own runtime counts as documented separately. Do not
infer that default validation makes every call safe for arbitrary argument indexes.

The parser binary-operator branch constructs ASSIGN by precedence without a
universal assignable-left check. BINARY-EVALUATOR-RECOVERY-2026-10-16 documents
the actual runtime path: RHS is evaluated first; assignable variables receive it
(with Struct copy), supported struct access paths are handled, and unsupported
left forms can still return the RHS without assignment. Thus parse acceptance,
evaluation side effects and a successful store are distinct facts. Existing
binary evidence, rather than this cache dossier, anchors that assignment body.

## Verification and continuation

94 static checks pass;12 corrupt/missing-evidence controls reject changed cache/
name/null gates, target call, reset call and invented finally. Runtime behavior and
independent semantic review remain NOT_RUN; mapping669 unchanged. This is an
additional cohort after the fixed17-cohort pipeline checkpoint, not retroactively
part of that receipt. Next inspect model/user-function binding construction and
reset/reparse callers to bound the lifetime of these cached target objects.
