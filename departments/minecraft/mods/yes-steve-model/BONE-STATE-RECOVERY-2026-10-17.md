# Java bone-state array boundary — 2026-10-17

Status: initial static analysis, pending independent semantic review. **No central
mapping additions from this cohort yet.** The snapshot closes all 35 methods of the
existing AnimatedGeoBone semantic owner, but reviews the twelve setters and their
input/output data contract rather than asserting all methods are fully understood.

Exact owner: `com/elfmcys/yesstevemodel/OO0oo000o00O0O0oo00oO000`.
Artifact SHA-256: `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`.
The [official GeoBoneState candidate](https://github.com/YesSteveModel/YesSteveModel/blob/f184edabd1b5115ce5a24cb6d155ba5a669f5ba6/src/main/java/com/elfmcys/yesstevemodel/geckolib3/model/GeoBoneState.java)
is used as a separately pinned comparison, not a replacement for the established
artifact owner label. Its historical source-artifact-divergence flag is retained.
Source SHA and complete declarations/operands/handlers are in the evidence.

## Java backing-array contract

The constructor stores the caller-provided input/output arrays and integer offsets
without copying them. The nine float setters each load inputState, add a fixed
slot to inputStateOffset, and execute fastore. They make no native call, local clamp,
finite-value validation, dirty-flag write or synchronization call.

| Input offset + slot | Meaning observed through the IBone/source comparison |
|---:|---|
|0,1,2|rotation X,Y,Z|
|3,4,5|position X,Y,Z|
|6,7,8|scale X,Y,Z|
|9|hidden|
|10|children hidden|
|11|tracking|

Absolute-pivot getters instead read outputState at outputStateOffset +0/+1/+2.
That distinction is directly visible in different array/offset field references;
it does not establish who produces outputState or how a native renderer consumes
inputState. Native implementation/protection remains outside this pass.

No extra explicit bounds checks appear in these methods, but JVM array access
still performs its ordinary checks. Invalid/null/overflowing offsets are not proven
safe. Shared array identity does not establish atomic snapshots or thread safety.

## Boolean encoding and ordered writes

The two-argument hidden setter converts each argument to float 1 or float 0 and writes
slot 9 before slot 10. A failure on the second write can leave the first write done.
The one-argument overload passes the same boolean twice; it does not preserve a
separate prior children-hidden flag. Tracking writes slot 11 with the same 1/0 encoding.

The corresponding getters compare the stored float to **exactly 1**, not merely to
nonzero. An externally written 2, negative value or NaN is therefore not interpreted
as true by those getters. This describes the getter, not a guarantee that arbitrary
external writes occur.

## Initialization and references

Constructor calls initialize hidden/children-hidden and rotation from the supplied
bone descriptor, then set scale X/Y/Z to 1. It does not call the position setters or
tracking setter, and makes no bulk zero-fill/copy. Existing contents in those input
slots therefore are not reset by this constructor's instruction path. Whether caller
allocation supplies zeros is a separate producer question.

Initial rotation is a newly constructed Vector3f from another round of descriptor
rotation reads. Its getter returns the stored reference directly, not a defensive
copy. Name, pooled name and pivot fields are similarly initialized from the descriptor.
No concurrency or immutable-descriptor guarantee is inferred.

The final TLM lazy-conversion method is retained as support only; conversion behavior,
classloading, cache lifetime and compatibility are not promoted by this review.

## Relation to the earlier commit evidence

BoneTopLevelSnapshot.commit calls these setters in order. Thus the already-reviewed
Java path now reaches concrete float-array writes: hidden flags, initial-relative
rotation result, position and scale. The cache reset after those calls is still not
an atomic renderer submission. A source comment mentioning native association is
not a native execution observation.

## Allocation follow-through

A separately retained Java model-state constructor allocates fresh float arrays
of **12 × bone count** for input and **4 × bone count** for output. It passes input
offset 12×i and output offset 4×i to each bone constructor. The output stride is four,
not three merely because this bone exposes three absolute-pivot getters. The fourth
output slot's meaning remains unknown in this pass.

The new float arrays supply zero-initialized slots before per-bone initialization;
therefore position/tracking begin zero on this specific allocation path. This does
not change the bone constructor's more general caller-array contract. Array getters
return the backing arrays directly. The pooled-name map is wrapped unmodifiable,
which does not make the bone objects or underlying arrays immutable. No duplicate
name, arithmetic-overflow or concurrency safety guarantee is claimed.

Exact allocator owner: OOOO0O0O000O000000oOOO0o. Allocation constants are at 53/68,
newarray at 62/76, per-bone offset multipliers at 140/149 and the constructor call
at 151. Complete constructor and two array-getter records plus the pinned
GeoModelState source hash are retained and checked separately. Only the allocation
slice is semantically reviewed; the rest of that constructor is contextual evidence.

## Verification

218 retained-auditor checks plus 204 strict cohort checks passed; 18 corrupt-evidence
controls rejected. The tool fixes exact artifact/source identities, requires all 35
method records and the class record, checks all code operands/handlers and the
published slot contract. Controls change slots, array identity, stores, boolean
branches/arguments, records, source and artifact identity.

These are static evidence regression checks. Independent semantic review is pending;
no target code, JNI, renderer, game or concurrency test ran. The twelve setter-role
findings are retained without increasing the central mapping count yet.

```bash
python tools/bone_state_ysm_265.py --jar /absolute/path/ysm.jar \
  --source-root /absolute/path/to/pinned/source \
  --evidence BONE-STATE-EVIDENCE-2026-10-17.json \
  --out /tmp/ysm-bone-state-audit.json
```

Next: trace the Java allocator and constructor callsites to determine stride,
offset allocation and publication boundaries, preserving any source-era differences.
Also trace existing Java wait/schedule ownership before suggesting concurrency claims.
