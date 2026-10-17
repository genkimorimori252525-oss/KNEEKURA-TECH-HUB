# Easing factory and raw-keyframe preparation — 2026-10-17

Status: primary static review complete; independent semantic review pending.
No central mapping promotions from this cohort. Exact snapshots cover five owners,
27 methods (one abstract), five pinned source files and every bootstrap table.

Artifact: Zqooxsd2 / SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`.
Official source candidate: `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.
Full source URLs/hashes and exact owners are retained in the evidence. Semantic
names are research counterparts, not proven original names. Whole-source identity
and native-side field production remain unestablished.

## Connected owners

All share com/elfmcys/yesstevemodel/:

- EasingType: o00o00ooO000OoOoooO0000O — five methods
- RawBoneKeyFrame: ooOooo0oOooOO0O0O00000oO — seven methods
- FloatValue: oOoOoOOooOOO0OO0oooO00oO — seven methods
- RotationValue: o0Oooo0OO0o00oOoOoo0oOOo — five methods
- BoneKeyFrameProcessor: oO0O00O0oOOO0OoO0oOo0OoO — three methods

## Built-in factory selection and point identity

The EasingType initializer has two LambdaMetafactory sites tied to the exact linear
and Catmull factory handles. The field compared by the processor is the Catmull
singleton, using reference equality, not a class-name or value comparison.

Both built-in factories route index zero to a transition factory. That factory
reads list element zero, passes its narrowed start time, pre-value and post-value
to TransitionKeyFrame. This is a local built-in factory statement, not proof that
all possible interface implementations generate a transition at index zero.

The linear factory at nonzero index takes begin=index−1 and end=index. Duration is
end.startTick minus begin.startTick, in float. It passes begin.postValue as the
interpolation start, end.preValue as its end, and end.postValue as the separate
end-gate return value. Thus the previously reviewed LinearKeyFrame's endpoint jump
has an explicit producer: pre and post need not be the same object or value.

Catmull chooses left=max(0,index−2), begin=index−1, end=index and
right=min(size−1,index+1). It passes left.post, begin.post, end.pre, right.pre and
end.post. The edge duplication is explicit at the first/last interior neighborhoods.
These clamps do not validate the caller's overall index. No local sorting,
monotonic-time check, empty-list guard or exception handler occurs in these factories.
Higher-level input guarantees remain separate.

## Preparation precedes construction, with asymmetric easing selection

The processor first iterates every input frame and calls init(isRotation), then
allocates a BoneKeyFrame array and constructs one result per list index. It does not
sort the list. Empty input skips both loops and wraps an empty result array.

For each end frame:

- If its easing object is the Catmull singleton OR its index is zero, use that end
  frame's easing object.
- Otherwise use the previous frame's easing object.

The resulting object receives buildKeyFrame(list,index). No null check or local
catch appears. This is not simply 'always use the preceding keyframe's easing'.
The array overload delegates after ReferenceArrayList.wrap; dependency-specific
view/copy semantics are not independently established by seeing that call.

## Raw initialization and aliasing

init(isRotation) returns immediately when preValue is already nonnull. It does not
compare the new rotation flag or reread/rebuild the pre/post primitive fields on
that path. First preparation chooses rotation behavior for those cached wrappers.

When preparing, X and Y pass flip=true; Z passes flip=false. A new pre Vector3v is
stored before the contiguous branch. Contiguous frames assign postValue to the
same preValue reference. Otherwise post receives a separate Vector3v. This is an
identity alias, not just equal component values. No local synchronization or rollback
exists. If an exceptional failure occurs after pre publication but before post
publication, a later init can hit the early-return guard; this is a conditional
instruction-path limit, not a reproduced failure or a claim that it commonly occurs.

The primitive start time is stored as double but its getter narrows to float.
Consequently factory duration calculation uses the narrowed values, not direct
double subtraction. That numeric distinction is established without claiming a
visible timing defect.

## Primitive and dynamic rotation values are different paths

For a null IValue field, getValue narrows the primitive double to float. Nonrotation
wraps it in FloatValue. Rotation first invokes RotationValue.processValue, then
wraps the returned float in FloatValue. For a nonnull IValue, nonrotation returns
that same object; rotation allocates a RotationValue wrapper rather than eagerly
evaluating it.

RotationValue.processValue promotes float to double, calls Math.toRadians(double),
narrows the result back to float, then optionally negates. This differs in operation
sequence from MathUtil's float-multiplication degrees helper; no bitwise equivalence
is claimed. Dynamic evalAsFloat invokes the wrapped value first and applies this
conversion. Its eval/unsafe methods delegate and box, with no local catch.

FloatValue's constructor substitutes positive zero for NaN and otherwise stores the
provided float, including infinities. Its value evaluations return that field. This
does not mean every dynamic IValue path sanitizes NaN or catches exceptions: the
RotationValue overrides do not use the inherited default eval catch. The earlier
CustomEntity callback analysis remains limited to its actual lambda/default-eval
path, rather than a universal interface guarantee.

## Verification and boundary

162 strict checks and 16 corrupt-evidence controls pass. Fixed artifact hash/size,
complete 27-method identity set, declarations, full operand/handler records,
bootstrap tables and all five source records/checkouts are checked. Controls alter
initialization and alias gates, axis flips, narrowing/promotion, NaN guard, sign,
processor selection, ordering and omitted evidence.

This validates retained evidence fidelity; it is not target execution or an
independent proof of the semantic prose. No new mapping rows are promoted until
review. The source's native-access and constructor-use comments are author context,
not observations of a native loader or proof that a constructor never executes.

```bash
python tools/easing_raw_factory_ysm_265.py --jar /absolute/path/ysm.jar \
  --source-root /absolute/path/to/pinned/source \
  --evidence EASING-RAW-FACTORY-EVIDENCE-2026-10-17.json \
  --out /tmp/ysm-easing-raw-audit.json
```

Next connected work: Java controller queue production, time selection/reset and
beginning-transition homogeneity; separately follow Java async wait/commit ownership.
Native input population, encrypted assets and protected binaries are outside this
continuation. This is a saved research checkpoint, not an instruction to stop.
