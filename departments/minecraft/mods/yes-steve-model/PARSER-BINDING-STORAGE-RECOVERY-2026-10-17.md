# Parser binding capture and variable storage indirection

Primary static review; independent review NOT_RUN. Fixed artifact SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, source
candidate `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. 43 methods across nine
owners: primary binding, parser facade, parser implementation and three binding/
variable pairs. Nine source records cover six files. Full snapshots support the
following selected claims, not complete lexer/language/storage implementation
recovery. No runtime execution, native work or central mapping promotion.

## Parse-time binding versus runtime storage

The parser's identifier path looks up the root token in ObjectBinding and rejects
null. An immediately following dot requires another identifier and ObjectBinding
target, performs a second lookup, rejects null, then creates the corresponding AST
node. Subsequent compound dot processing creates StructAccessExpression on the
left expression instead of repeating that same initial namespace-lookup branch.
Do not collapse namespace lookup and runtime struct access into one operation.

The resulting variable AST captures a variable object, as the previous dossier
showed. That object can still read mutable runtime storage: scoped/context
variables capture pooled integer names; temp variables capture assigned integer
addresses. Their evaluate/assign methods obtain the current IContext storage on
each call. Thus captured target identity does not mean the value itself is frozen.
These assignable wrappers cast the context directly; they do not inherit the
ContextVariable type-check/Integer0 fallback from the preceding query wrappers.

ScopedVariableBinding caches by StringPool-computed name and delegates get/set to
scopedStorage. ContextVariableBinding similarly caches names but reads contextStorage;
if storage is null, evaluate returns null and assign does nothing. TempVariableBinding
caches by String name, assigning topPointer++ only when creating a new variable;
its variable delegates to getTemp/setTemp at that address. Actual storage bounds,
clearing/value lifetime and StringPool semantics remain separate next questions.

## Aliases and reset scopes

PrimaryBinding first copies supplied extra bindings, then installs its built-ins,
so same-key built-ins overwrite those extras on this constructor path. query/q,
variable/v, context/c and temp/t share object references. Transient/scoped object
lists are collected from map values without a distinct operation; aliases can
therefore put the same object's reset callback in a list more than once. No
observable defect is claimed: the inspected reset bodies are simple cache clears.

resetScoped clears scoped/context binding variable caches; resetTransient clears
the temp binding map and resets topPointer to0. These binding resets do not by
themselves clear values inside a particular runtime IContext's storage. Old ASTs
can still retain the variable objects created before cache reset; actual execution
is indirect through that context's storage/address semantics.

## Parser facade: ordinary-tail cleanup, not universal catch

parseExpressionUnsafe optionally filters comments only for user functions, calls
the engine parser, constructs MolangValue, then resets transient bindings at34 and
returns. There is no finally. A failure before that reset does not run it on this
path. The public parseExpression catches Exception, not Throwable, logs according
to debug mode, and returns FloatValue.ZERO. Its handler covers the unsafe call,
not arbitrary failures in the logging/error-reporting handler itself.

Public reset delegates to primaryBinding.resetScoped, not resetTransient. Constant
construction narrows double to float. Comment filtering is a separate character
state machine that preserves single-quoted text and removes line/block comments;
this dossier does not claim a complete lexical edge-case specification from that
body alone. Do not infer transaction-like reset behavior or all-error recovery.

## Verification and continuation

258 static checks pass;12 malformed-evidence controls reject altered catch type,
invented finally, comment gate/reset call and context-null read/write guards.
Mapping669 remains unchanged. Source candidate identity is pinned but whole
artifact equivalence is unproven. Next follow concrete scoped/temp/context storage
owners and reset boundaries to determine actual value lifetime and address reuse.
