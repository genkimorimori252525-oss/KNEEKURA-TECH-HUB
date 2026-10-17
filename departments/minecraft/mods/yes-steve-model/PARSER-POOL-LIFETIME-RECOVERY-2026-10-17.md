# Parser pool and user-function binding lifetime

Primary static review; independent review NOT_RUN. Exact artifact SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, source
candidate `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. Eleven complete methods in
CustomMolangParser `O00o0ooOoo00o00o0OOOO0o0` and UserFunctionArgument
`OO0OO0000O0ooO0oO000Oo0O`. No target/native execution or mapping promotion.

## Rent/return separates parser reuse from cached AST targets

rentInstance polls a ConcurrentLinkedQueue and creates a parser only on null.
returnInstance invokes parser.reset before adding it back. The prior parser
facade evidence shows resetScoped, not resetTransient. parseSingleExpressionUnsafe
rents before its try, parses with isUserFunc=false, then returns the parser in a
real finally on success or parse failure. A reset failure during return can prevent
queue insertion; no stronger all-exception pool guarantee is claimed.

Creation lazily fills shared EXTRA_BINDING with ysm/ctrl/tlm/args, copies that map,
adds a NEW UserFunctionBinding under fn and constructs MolangParser. Thus fn is
not a single global binding reused by every parser. Returning a parser clears its
scoped binding caches, including the fn lookup map; ASTs already emitted can still
retain their old UserFunction objects. A later rental can obtain fresh function
objects without mutating those older AST caches. This resolves the Java helper's
pool lifetime; arbitrary/native model-loader rent/return sequences are not proven.

On successful parse, the earlier unsafe facade resets transient temp binding
addresses; on failed parse before that reset, returnInstance still only resets
scoped caches. Do not silently assume failure cleans every temp binding entry.
The actual consequences depend on the next rental/parse and runtime storage and
have not been reproduced. No target parser implementation is changed.

## Args is a dynamic context lookup, not a captured argument snapshot

The shared UserFunctionArgument singleton tests context.entity instanceof IContext
and returns ctx.userFunctionArgs, else null. That context returns the StackMemory
ArgsAccessor described previously. A singleton binding here does not mean a shared
immutable argument list across calls; it resolves through the current context.

## Initialization and completion-hint limits

EXTRA_BINDING and COMMAND_HINT are ordinary HashMaps; the concurrent queue alone
is not a proof that all lazy map initialization is thread-safe. The creation block
catches ConcurrentException from lazy bindings and wraps it in RuntimeException.
No transactional rollback of earlier put operations is present in that handler.

getAllBinding fills COMMAND_HINT only while it is empty, copies the then-current
EXTRA_BINDING and adds math/q, then returns the map reference. It does not force
parser creation first. If invoked before extras are populated, later calls do not
automatically rebuild the now-nonempty hint map. This is an ordering-dependent
limitation, not evidence that actual command completion hits that order.
The roaming-assignment regex method is a lexical predicate, not full parsing or
proof of authorization/semantic safety; no network behavior was exercised.

## Checks and next seam

70 static checks pass;10 missing/corrupt-evidence controls reject lost return
finally, reset call, hint gate and altered initialization handler. This is another
post-checkpoint cohort; do not revise the fixed17-cohort receipt to include it.
Whole-source equivalence remains unproven; central map669 unchanged. Next inspect
Struct copy/property/assignment semantics and their Java storage consumers, keeping
opaque model-loading/native lifetime outside the established proof.
