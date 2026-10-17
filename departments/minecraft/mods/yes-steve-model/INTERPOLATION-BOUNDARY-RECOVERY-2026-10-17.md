# Interpolation boundary — exact Java semantics, 2026-10-17

## Scope

The processor and point wrappers delegate to owner
`com/elfmcys/yesstevemodel/oooOO00ooooooOO0ooO00O0O`. Its declaration shape and
18 retained bodies match the selected MathUtil source counterpart sufficiently
for **one class-role and 16 method-role proposals**. Constructor/static initializer
are support, not mapping-count additions. Independent review passed for the stated local Java semantics.

Official artifact: Zqooxsd2, SHA-256
`25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`.
Source: [MathUtil at f184eda](https://github.com/YesSteveModel/YesSteveModel/blob/f184edabd1b5115ce5a24cb6d155ba5a669f5ba6/src/main/java/com/elfmcys/yesstevemodel/geckolib3/core/util/MathUtil.java).
Original names and whole-source equivalence are not established. The method
labels with Scalar/Vector/Into suffixes are descriptive aliases distinguishing
source overloads, not assertions about original JVM names.

## Rotation interpolation is quaternion-based, not componentwise Euler lerp

- Euler-to-quaternion constructs Quaternionf and calls rotateZYX with z,y,x,
  in that order (field reads8/12/16, call19).
- Rotation interpolation copies the begin vector and adds initial rotation;
  it separately adds initial rotation to the end into the temporary vector.
- Two Euler-to-quaternion calls feed **Quaternionf.nlerp**, at offset43, not slerp.
  The end quaternion is also the nlerp output argument.
- Local quaternion-to-Euler conversion follows, then initial rotation is
  subtracted into the caller's destination at offset60.
- There is no local progress clamp, local wrapRotation call or local explicit
  antipodal/normalization algorithm. Those details must not be inferred without
  the actual JOML dependency implementation. The Java call sequence is established;
  loaded-library numeric equivalence, performance and game motion are not.

The local quaternion-to-Euler helper computes X/Z with org.joml.Math.atan2 and Y
with safeAsin. It writes x,y,z in order and returns the supplied vector. The source
comment calls this a fix for a historical JOML issue; this pass records the actual
formula/calls, **not verification of that historical bug claim**.

## Scalar and vector boundaries

- Scalar lerp is `start + progress * (end - start)` in float instructions; no
  clamps/finite-value guards or fused-multiply-add call appear.
- Vector lerp computes X,Y,Z through that scalar helper before one Vector3f.set
  call, or before constructing the returned Vector3f. Thus input reads precede
  the one final set call; concurrent mutation is not covered.
- Weighted scale is `1 + (value - 1) * weight`, not value multiplied directly by
  weight. Vector forms likewise call the scalar helper per component before set
  or construction. No local weight clamp appears.
- Catmull-Rom uses two half-difference tangents, squared/cubed progress and the
  retained cubic float-expression ordering. Vector form evaluates three scalar
  calls before construction. No local domain clamp appears; this is not a generic
  guarantee about all spline consumers.
- Degree/radian helpers multiply by embedded float constants
  0.01745329238474369 and 57.2957763671875. These are observed artifact values;
  no external Minecraft constant-name equivalence is required for that claim.

## Rotation wrapping and constants

The scalar wrap applies float remainder by ROUND, subtracts ROUND when the result
is at least HALF_ROUND, then adds ROUND when below negative HALF_ROUND. Positive
half-round therefore maps to its negative counterpart; negative half-round remains.
This is float/JVM control flow, not a real-number precision theorem. NaN does not
become a finite rotation through these operations. Vector overloads use the same
scalar helper before construction/set.

The initializer obtains ROUND/HALF_ROUND from Math.toRadians of double360/180 then
casts to float. ZERO and ONE are freshly constructed Vector3f objects. A final
reference does not prove those shared vectors are immutable; this pass does not
establish that no other method can mutate them.

## Evidence and acceptance

[Evidence](INTERPOLATION-BOUNDARY-EVIDENCE-2026-10-17.json) retains full declarations,
all18 method records, ordered refs, encoded operands, handlers, constant values and
source SHA. [Proposals](INTERPOLATION-BOUNDARY-MAPPINGS-2026-10-17.json) are separate
until review/integration.

Local checks:116 retained-auditor checks plus100 strict cohort checks; zero failures.
All15 corrupt-evidence controls reject, including omitted methods/initializer,
operand omission, ZYX→XYZ mutation, nlerp→slerp substitution, scalar arithmetic,
wrap boundary, tangent coefficient, safeAsin, missing constants and wrong artifact.
These are static evidence regression checks, not execution of the MOD or JOML.

```bash
python tools/interpolation_boundary_ysm_265.py --jar /absolute/path/ysm.jar \
  --source-root /absolute/path/to/pinned/source \
  --evidence INTERPOLATION-BOUNDARY-EVIDENCE-2026-10-17.json \
  --out /tmp/ysm-interpolation-audit.json
```

Next connected work: AnimationPoint time/context setup and concrete beginning,
ending and keyframe point generation; retain progress/domain and external easing
boundaries. Continue those questions after this checkpoint, rather than treating
this finite helper cohort as whole-YSM completion.

## Integrated checkpoint

This cohort passed independent static review and is included in the 662-mapping
checkpoint. See [verification](ANIMATION-PIPELINE-VERIFICATION-2026-10-17.json).
The continuing research queue remains active; runtime and whole-source equivalence
are not established.
