# Function arguments and loop/foreach ordering

Primary static review; independent review NOT_RUN. Fixed artifact SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, source
candidate `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`. 29 selected complete
methods in five owners: StandardBindings, ExecutionContext, Function,
ArgumentCollection and five evaluator methods. No runtime execution/map promotion.

## Arguments remain expressions until a getter evaluates them

visitCall passes the function its ArgumentCollection without eagerly evaluating
all arguments. The collection keeps the supplied expression List, exposes its
size/raw expression, and value/typed getters evaluate the indexed expression on
each call. There is no general memoization. Repeating a getter can repeat expression
side effects. Typed getters use ValueConversions after evaluation.

ExecutionContext.evalSingleExpression catches Exception and returns null after
logging; it does not catch all Throwable. The actual unsafe evaluator has the
return/control cleanup already documented in VARIABLE-AST-RETURN. The argument's
List.get happens before invoking that safe wrapper, so invalid indexing is not
magically protected by the wrapper. Function.validateArgumentSize defaults true;
particular functions/parser rules must provide stronger arity constraints.

## loop count and body are treated differently

The standard loop function requires exactly2 arguments or returns null. It evaluates
argument0 as float, rounds with Math.round, caps with Math.min(...,1024), then
requires raw argument1 to be an ExecutionScopeExpression. Count evaluation occurs
before that body-type check. Negative counts are not clamped upward here; the
for(i=0;i<times;i++) loop simply performs no iteration for nonpositive times.
The function returns null after processing. This is not a universal1024-operation
budget: nested loops and arbitrary body work are separate, and foreach has a
different path.

## foreach selection and assignment

The standard foreach function requires3 arguments. It first requires raw argument0
to be an AssignableVariableExpression and raw argument2 an ExecutionScopeExpression.
Only then does it evaluate argument1, requiring an Iterable. This ordering can
skip evaluation of the iterable expression when either raw-node type is wrong.
Each iteration assigns the element to the target before executing the scope.
There is no restoration of the previous target value after completion, break or
failure in the inspected outer foreach method, and no numeric1024 cap on its
iterator. Actual iterable behavior/finite size are caller dependencies.

## Scope control and cleanup

The loop-scope helper increments inLoop and decrements it in a real finally.
After each expression it checks popReturnValue; nonnull signals stop. Otherwise
it snapshots and clears controlOp: CONTINUE ends this iteration's remaining
expressions, BREAK signals outer stop. The outer loop/foreach tests that signal.
Ordinary execution scopes also return early for pending loop control when inLoop>0.

Do not say every return is propagated identically: popReturnValue clears its field
when returnThrough==0, whereas user-function multi-expression evaluation raises
that counter. The helper returns a stop boolean, not the return Object. The
surrounding return-through mode from VARIABLE-AST-RETURN matters. Finally restoring
inLoop does not roll back variable assignments or argument side effects.

## Verification and next step

172 static checks pass;12 missing/corrupt-evidence controls reject changed arity,
loop cap/rounding, foreach node type, removed inLoop finally and broadened safe
catch. These are exact evidence checks, not executable language conformance tests.
Source/global equivalence remains unproven and mapping669 unchanged. Next join
parser call-argument/assignment validation and user-function dispatch to these
runtime rules; avoid extrapolating default Function arity into all call sites.
