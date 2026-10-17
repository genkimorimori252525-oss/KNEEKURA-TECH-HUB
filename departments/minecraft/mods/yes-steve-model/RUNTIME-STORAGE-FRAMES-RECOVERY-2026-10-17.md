# Runtime variable storage, call frames and deferred reset

Primary static review; independent review NOT_RUN. Fixed artifact SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, source
candidate `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. 88 declarations across
MolangMemory/holder, StackMemory/accessor/iterator, MolangContext and AnimationContext.
Seven source records cover four files. Complete snapshots are supporting evidence,
not full semantic approval of every unrelated context method. No runtime execution.

## Scoped/public aliasing is intentional storage sharing

MolangMemory.getScoped and setScoped compute a holder if absent; new holder value
is null. getPublic performs lookup only and returns null if absent. initialize
clears the scoped map, constructs holders for configured public names and inserts
the same holders into both scoped and new-public maps, then replaces publicMap.
Thus scoped writes to those names affect the values seen through public lookup.
An arbitrary newly created scoped name is not automatically public.

initialize does not reset its StackMemory in this body. The public-map field is
not evidence of a synchronization protocol by itself; the source comment about
thread safety is not adopted as a verified concurrency guarantee. Actual memory
initialization callers and publication need their own ordering evidence.

## Temp values are addressed relative to the active frame

StackMemory begins with Object[16], grows by repeated doubling and uses argOffset,
argSize,varOffset,varSize. getTemp tests addr<varSize, then indexes mem[varOffset+addr];
otherwise null. There is no explicit nonnegative guard in this method. The parser
normally allocates nonnegative addresses, but this body is not a safe arbitrary-index
API. setTemp extends varSize to addr+1, ensures capacity, and stores the object.
It does not clear intermediate cells when extending within existing capacity.

push succeeds only while saved-frame count<32. New arguments start after current
locals; new locals start after arguments. The old argument size/offset are packed
into a long, then active offsets change and varSize becomes0. pop restores offsets
and derives the previous local size from the old argument offset; empty pop is a
no-op. Neither pop nor push clears the backing array. Logical inaccessibility of
old locals differs from erasing their references. Writing a higher local address
can expose previously occupied intermediate cells; this is a conditional storage
property, not a reproduced user-function failure or a target-code fix.

The List push copies supplied values. The ArgumentCollection push increments the
current varSize by argument count before evaluating arguments, then installs the
new frame after evaluation. Neither push has a rollback/finally handler. If argument
evaluation throws, some preparatory state may remain changed; do not describe push
as transactional. The intended nesting/argument-evaluation discipline must be
joined with caller behavior before claiming a runtime defect.

## User calls and argument views

MolangContext.tempStorage returns memory.stackMemory; scopedStorage returns memory;
contextStorage returns the current AnimationContext. A child context shares memory,
animation event/data and animation-context references, while changing its entity
and selecting foreign storage from the child's capabilities. This is not wholesale
cloning of all parent context fields or isolated variable storage.

Both callUserFunction overloads call push before entering their try/finally. On
successful push, they invoke value.eval and pop on normal or exceptional exit.
Failed depth gate returns null without evaluating the function. A throwing push
is outside the protected function body; its partial changes are not rolled back
by this finally. This precisely qualifies the otherwise useful pop guarantee.

ArgsAccessor is a live view: size/get use current argument offsets. get outside
0..argSize-1 returns null. Its iterator captures start/end offsets at creation but
reads the shared array; exhausted next returns null. Most other List operations
throw UnsupportedOperationException. It is not a conventional immutable snapshot
nor a fully implemented general-purpose List.

## Animation-local storage and deferred reset

AnimationContext stores variables in a lazily allocated integer map. get before
allocation returns null. reset first handles deferred calls when present: deferred
argument groups are visited in reverse group order, handlers in their list order;
allowEmitting is enabled around that ordinary path, then disabled, deferCount is
cleared and variable storage is cleared. There is no finally protecting the entire
reset sequence. The user-call helper's frame pop does not guarantee this outer
emission/count/map cleanup when a failure escapes. No actual failure is asserted.

## Checks and continuation

475 static checks pass;13 malformed-evidence controls reject changed frame limit,
size equality, removed body cleanup and invented push finally. Mapping669 is
unchanged; source/artifact whole-equivalence remains unproven. Next follow memory
initialize/reset callers and argument evaluation/assignment ordering to decide
when root/temp state is deliberately retained. Do not confuse parser binding-cache
resets with runtime memory erasure or infer all storage is per-expression.
