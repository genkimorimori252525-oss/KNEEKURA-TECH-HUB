# Bone-parameter query views and tracking request — 2026-10-17

## Scope

Exact official JAR SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`, comparison source
YesSteveModel/YesSteveModel `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`.
51 selected methods across 11 owners cover four functions/their vector views,
BoneParamFunction, Vec3fStruct and the 14 GeoBoneState getter/tracking methods they
call. Primary static review, independent semantic review NOT_RUN; central map
669 unchanged. No target game, native transform computation or render executed.

## Lookup and live result

All four functions inherit EntityFunction and accept exactly one argument under
their arity contract. BoneParamFunction obtains its pooled-string key. EMPTY or
missing animatable bone returns null; otherwise it creates the corresponding
vector-view object. This query path does not add lowercase/trim normalization.
It obtains the bone from context.animatableEntity, which can remain the parent
animatable in the previously documented child-context case.

The returned object is a Vec3fStruct with a retained IBone reference. Reading x/y/z
calls the current bone getters at property-read time. It is not an eager snapshot
of three numbers or an automatic rebinding to whatever bone later takes the same
name. Vec3fStruct.copy returns itself and putProperty is a no-op; callers must not
assume assignment clones values or that writing .x changes the bone.
Unknown property IDs return null. The pooled IDs for x/y/z are process-local,
not stable external wire IDs.

## Coordinate and unit contracts

| Function | Property reads |
|---|---|
| bone_rot | x/y are negative degrees of the corresponding radian bone value; z is positive degrees |
| bone_pos | position x/y/z directly, without division by 16 in this query |
| bone_scale | scale x/y/z directly, without subtracting the identity scale |
| bone_pivot_abs | absolute-pivot output-array x/y/z directly |

Rotation calls Math.toDegrees after widening the float input, narrows the result
to float, then negates x/y. Preserve both signs and units. Position is not replaced
with pivot or world-position data. These callbacks return a view; its properties
are boxed Float through Vec3fStruct, not a vector copy with independent storage.

## Absolute pivot has a side effect but no recomputation

BoneAbsolutePivot tests isTracking and, when false, calls setTracking(true) before
returning its view. This path has no local allowEmitting test. That does not prove
that every outer caller evaluates it under every engine state, but it means the
function itself is not a pure read-only operation.

For captured GeoBoneState, tracking reads inputState[inputOffset+11] == 1 and the
setter writes 1f/0f. Absolute pivot getters read outputState[outputOffset+0/+1/+2].
The original BONE-STATE allocation evidence records output stride FOUR; exposing
three pivot coordinates does not establish that the fourth slot is absent or
known. No Java matrix solve, render invocation or output refresh is performed by
these getters or this tracking request.

Accordingly, this cohort does not certify output freshness, coordinate frame,
world-unit scale or native implementation details. The native/render boundary
remains separate. Keep last output values versus requesting tracking versus
actually producing new output distinct in a reconstruction.

## Verification and continuation

`tools/bone_parameter_query_ysm_265.py` takes --jar, --source-root, --evidence,
--out. 306 integrity checks passed and 16 mutated fixtures were rejected. Exact
method selection includes getter/tracking implementations matched to the interface
invokes; abstract/support declarations retain their real Code presence/absence.
This is not an independently reviewed mapping promotion or running bone test.

Continue first/second-order smoothing functions and manager update timing, then
Molang side-effect gates. Avoid silently fixing unit/sign conventions or assuming
a read-looking function is side-effect free.
