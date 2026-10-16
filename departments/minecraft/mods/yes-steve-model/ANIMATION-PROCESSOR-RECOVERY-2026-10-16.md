# AnimationProcessor lifecycle continuation — 2026-10-16

## Status and identity

Independently reviewed lifecycle/direct-caller static boundary, with a reproducible
exact-bytecode regression dossier.
**No new central mappings are promoted by this pass.** The current total remains
625. Independent semantic review of the bounded findings is complete; it does not
certify every retained method body or runtime behavior.

- Exact artifact: Modrinth `Zqooxsd2`, 63,269,843 bytes, SHA-256
  `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`.
- Processor owner: `com/elfmcys/yesstevemodel/OOOooo0o0OOOO0O0OOoOo0OO`.
- Existing owner role is HIGH, not an original-name recovery guarantee.
- Official candidate: [AnimationProcessor at f184eda](https://github.com/YesSteveModel/YesSteveModel/blob/f184edabd1b5115ce5a24cb6d155ba5a669f5ba6/src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/processor/AnimationProcessor.java).
- Source/artifact equivalence remains NOT_ESTABLISHED. In particular, the source
  parameter named GeoModelState must not silently rename the artifact parameter
  whose current semantic map calls it AnimatedGeoModel. Full type correspondence
  is not established by this pass.

The dossier retains all 19 processor methods and all 8 nested task-record methods,
including full operands, handlers and both owners' bootstrap tables. This is
snapshot completeness for those owners, not semantic completion of all 27 bodies.
Research role names in the dossier aid navigation; they are not new original symbols.

## Findings from the actual instruction paths

### 1. shouldTick does not stop all animation work

In the tick method, offset 153 skips the controller process call at 163 when the
boolean is false, landing at 168. The controller queue visitor at 191, active-bone
tail update and commit at 580, and postProcess at 617 are outside this branch.
Thus this parameter gates controller advancement, not every processor side effect.
This is a control-flow conclusion, not a measured cost/performance claim.

Model-dirty controller updates at 147 occur before the shouldTick branch. The dirty
flag clears at 201 after the controller loop. An exception during that loop can
skip the clear. Context initialization and preProcess also precede the loop.

### 2. Tick-tail cleanup is not finally cleanup

The tick method has zero exception handlers. Controller-context and animation-
context clearing at 606/611, followed by postProcess at 617, are ordinary tail calls.
An escaping earlier exception can bypass those calls. This does not prove an actual
in-game failure: the caller and callee exception contracts remain to be traced.

### 3. Queue phase selection and removal order

The two private evaluator-only methods iterate the same ConcurrentLinkedQueue.
The pre flag read at 28 is tested with opposite branch opcodes at 31: preProcess
skips false flags, postProcess skips true flags. Selected tasks execute at 37;
Iterator.remove follows at 41. If execution escapes, that iteration does not reach
remove. No claim is made about cross-thread snapshot visibility, exactly-once
execution, or the behavior of ConcurrentLinkedQueue beyond those calls.

### 4. Nullable callback on an error path is a concrete risk candidate

executeMolangTask checks the callback for null at 29/32 only after successful
expression evaluation at 21. That successful null-callback path resets emission
and returns at 48. A caught evaluation exception instead goes through the Throwable
handler at 102, resets emission at 125, then reaches callback retrieval at 150 and
Consumer.accept at 154. There is no null guard on this error path.

Consequently, **if evaluation throws and the task callback is null**, this method's
error-reporting path can itself throw NullPointerException. The task record stores
the provided callback and exposes it unchanged. This is a static conditional risk,
not a reproduced game defect or proof that callers enqueue such a task. The public
candidate explicitly permits a nullable callback, which makes caller analysis useful.

A subsequent exact-JAR caller pass found two CustomEntity enqueue callsites with
explicit null callbacks (offsets 28/41), but also important counterevidence:
their lambda objects implement evalUnsafe and inherit IValue's default eval.
That default method catches Throwable from evalUnsafe, logs and returns null.
Ordinary expression failures on those paths therefore enter the processor's
successful-null-result branch and do **not** establish the suspected failure.
Logger/context-setter failures or a different overriding eval implementation
would require separate evidence. Do not file this as a reproduced bug.

The caller pass scanned all 955 class files for exact direct invocation references:
one direct tick call and three enqueue calls (one forwarding method and two
CustomEntity sites). The immediate tick caller has no handlers; higher callers
and reflective/dynamic entry points are not closed. See
[caller evidence](ANIMATION-PROCESSOR-CALLER-EVIDENCE-2026-10-16.json).

Consumer.accept is outside the protected ranges. A callback exception likewise
escapes this method and can prevent the queue's following removal. Do not infer
infinite replay: later caller handling and queue lifecycle still matter.

### 5. Emission resets to false rather than restoring a prior state

The task's emission flag reaches the context setter at 13. Normal early-return,
normal result, caught-error and exceptional-finally paths write false at 45,96,125,
143 respectively. They do not save/restore a former flag. Cleanup calls can themselves
throw; this is not an unconditional no-throw restoration guarantee. Successful strings
are formatted with quote characters, null as the literal null, and caught errors
with the retained error prefix in the StringConcatFactory bootstrap recipe.

### 6. Model reset and tail transitions

clearModel empties the bone map, active deque, and model list; invokes memory
initialization with null; assigns an empty handler map; clears pending tasks; and
calls the sound stop method, in that order. It does not write the dirty flag, last
trim timestamp or random source. loadModel invokes this clear first and sets dirty
true after its optional bone-loading section, even for an empty bone map.

For each active bone, three tail progress divisions occur at 302/422/532 and are
compared to one at 309/429/539. There is no local reset-speed validation or clamp.
Rotation uses a different interpolation signature than position/scale, so no generic
linear-rotation equivalence is asserted. The delegated interpolation bodies are not
closed here. Commit at 580 precedes inactive removal at 596. Both removal and final
context cleanup can be skipped by an escaping commit exception.

## Regression verification

- 146 static snapshot/source checks: zero failures.
- 11 corrupt-evidence controls: all rejected, covering missing whole methods,
  missing instructions/bootstrap data, wrong artifact, phase/shouldTick branches,
  removed/expanded handlers, null-callback branch and emission-reset polarity.
- Fixed artifact hash/size enforced independently of the evidence's own claims.
- Complete exact 27-method identity set enforced; omitted records cannot pass.
- Pinned full source checkout revision and processor source SHA verified.
- No target execution, native extraction, game launch or runtime test performed.

These tests detect evidence corruption; they do not independently certify the prose.
Independent review reproduced the 146 processor checks, 11 controls, 26 caller checks
and exact direct-call scan, and verified all three source files against pinned Git
blobs. Higher-caller/dependency closure and runtime interpretation remain open. No code changes to YSM are proposed
or applied here.

From this directory:

```bash
python tools/animation_processor_ysm_265.py \
  --jar /absolute/path/to/ysm.jar \
  --source-root /absolute/path/to/pinned-official-source \
  --evidence ANIMATION-PROCESSOR-EVIDENCE-2026-10-16.json \
  --out /tmp/ysm-processor-audit.json
```

## Next evidence needed

1. Expand beyond the now-recorded direct enqueue callers only if needed; preserve
   IValue default-eval counterevidence and distinguish exceptional logger/setter
   failures from ordinary expression errors.
2. Review caller exception handling around tickAnimation and task scheduling before
   deciding whether the static callback/cleanup risks are observable defects.
3. Close BoneTopLevelSnapshot.commit and queue point consumers separately, keeping
   native renderer/runtime claims outside the Java-level evidence.
4. Only then promote additional member mappings with their actual confidence.
