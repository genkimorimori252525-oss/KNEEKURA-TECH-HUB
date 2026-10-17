# Fixed-JAR storage initialization and call-frame callers

Primary static inventory; independent review NOT_RUN. Exact artifact SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`. No game/JVM
execution. This is a closed direct-invoke scan over955 classes for six fixed
constructor/initialize/push/pop signatures, not reflection/native/external closure.
Nine invoke sites in five complete caller methods are retained.

## Direct sites

- AnimationProcessor constructor constructs one MolangMemory.
- MolangMemory constructor constructs one StackMemory.
- AnimationProcessor.clearModel invokes MolangMemory.initialize with null.
- The two MolangContext.callUserFunction overloads each push once, then contain
  normal-path and exceptional-path pop sites (four pop instructions total).

The two pop instructions per overload are alternative cleanup paths, not two pops
on a successful call. No other direct matching site appears in this artifact.
The scan includes exact target signature lists and full caller bodies so omitted
calls or changed operands are detectable on rerun.

## Consequences bounded to this Java path

The sole direct initialize caller supplies null, so this normal clear-model path
clears scoped values and replaces publicMap with the empty branch. The nonempty
public-name initialization branch has no direct Java caller found by this scan.
Do not claim the public API is fully populated simply because MolangMemory has a
public-map implementation. The official source also labels processor public
variable access as not yet implemented; this comment is consistent context, not
substitute proof for all external/native behavior.

The processor owns memory across tick contexts. clearModel does not replace that
memory object; initialize does not reset StackMemory, as established by the prior
dossier. Consequently model clear on this path is not proof of root temp-slot
erasure. Binding reset also only clears parse-time variable caches/addresses.
The processor's task executor previously captured in ANIMATION-PROCESSOR-EVIDENCE
calls exp.eval directly rather than wrapping every task in a user-function frame.
Therefore not every expression evaluation is automatically enclosed by push/pop.

A conditional reasoning example, not an executed target test: if one direct task
writes root temp address0 and a later independently parsed expression captures
address0, the latter can consult the same retained root slot in that processor
unless another caller changes/reset its storage. This does not prove an ordinary
model uses that sequence, violate a specification or justify silently patching it.

## Checks and next seam

Two complete-inventory checks pass;five missing/corrupt evidence controls reject.
No central mapping promotion. Further lifetime claims must include parser reuse,
actual task/model consumers and external access. Next inspect function argument
collection and loop/foreach evaluation ordering, where callers choose frames and
assignable targets; keep this finite static inventory separate from runtime traces.
