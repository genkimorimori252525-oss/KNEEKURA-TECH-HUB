# Normal-matrix rotation and scale: bounded static contract

Separate external cohort; earlier renderer receipts unchanged. Original image SHA25615d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22. Original machine bytes only. No target/native/JVM execution. Independent semantic review NOT_RUN.

## Rotation and layout

Inherited nine normal-matrix floats are packed column-major in per-bone scratch at+0x50..+0x70. At0x37cf27..0x37cfe6, the vector shuffles compute Nrot=Nparent*R, using the same Rz*Ry*Rx rotation coefficients established by the affine cohort. Output packing is4+4+1 floats: column0 XYZ and column1 X; column1 YZ and column2 XY; column2 Z. Translation and pivot do not directly modify these nine values. Parent-state publication copies them into the112-byte next-depth bank alongside the affine matrix.

## Exact branching after affine basis scale

At0x37d01a..0x37d052:
1. Compare sx and sy with UCOMISS. Unequal OR unordered goes to general scale.
2. Compare sy and sz similarly.
3. If both equal and sx is ordered greater than0, skip all normal rescaling, leaving Nrot.
4. Otherwise on the equal path, XOR the sign bit of all nine normal values, then CONTINUE to general scale.

The fourth case is not an early-return shortcut. Exact ordinary-path evidence:
-0x37d058 loads four0x80000000 sign masks.
-0x37d05f/0x37d066/0x37d06d XOR normal registers; stores follow.
-0x37d075 reloads original sx/sy from input+0x18;0x37d07b reloads original sz from+0x20.
-0x37d081 unconditionally jumps to0x37d0ac.

There is no absolute-value or scale-sign normalization between those reloads and reciprocal multiplication. Tracking variant0x37e7a9..0x37e84b repeats this structure. For ordinary nontracking traversal, earlier zero-scale gates can prevent reaching this block; the tracking path occurs before those gates. This report does not claim all zero-scale inputs reach an identical outcome.

## General scale arithmetic, in instruction order

Let fl denote a separate binary32 operation under the target's FP environment, whose mode is not established by this cohort.

ux=fl(1/sx); uy=fl(1/sy); uz=fl(1/sz)
q=fl(fl(ux*uy)*uz)

q retains its sign. The seed operation uses the signed32 interpretation i of q's float bits. If q is NaN, only the integer seed input is canonicalized to0x7fc00000; the floating q used by refinement remains unchanged.

seedBits=(0x54a2fa8c - truncTowardZero(i/3)) modulo2^32
h=reinterpretFloat32(seedBits)

Two iterations follow, each in this exact operation grouping:
- d=fl(fl(fl(3.0*h)*h)*q)
- correction=fl(1.0/d)
- h=fl(fl(c*h)+correction)

c is the stored binary32 constant0x3f2aaaab, numerically0.6666666865348816. It is not an exact real2/3. The3.0 constant is0x40400000. No fused multiply-add appears in this slice.

Then compute fx=fl(h*ux), fy=fl(h*uy), fz=fl(h*uz), and multiply corresponding normal columns by these factors. Preserve the prior sign XOR if the equal/nonpositive branch took it. Do not replace fl(h*fl(1/sx)) with a single h/sx and assume identical rounding.

The signed seed arithmetic is backed by CDQE, IMUL0x55555555, logical high-half shift, signed arithmetic shift and correction at0x37d0e7..0x37d104. Its simplification to negative signed division-by3 was checked against a separate integer instruction model for1031 selected and deterministic random32-bit inputs.

## Why a generic inverse-transpose replacement is not certified

For moderate positive determinant scales, the refinement resembles an inverse-cube-root normalization of q, followed by reciprocal-axis scaling. That interpretation is useful but must not replace the actual bit seed and two iterations. In particular, negative q is not converted to abs(q), and the signed-bit seed formula does not implement a general real cube root.

Owned rounded-binary32 arithmetic fixtures illustrate the distinction:
-Scale(2,2,2): uniform-positive branch, normal factors exactly1 in the model.
-Scale(2,3,4): modeled factors approximately(1.44225192,0.96150130,0.72112596).
-Scale(-1,-1,-1): model takes the signflip-then-refine branch, q=-1, seedBits0x6a22fa8c, and produces very large factors after the two iterations.

The last example is evidence about the independently written arithmetic model, not a target execution, observed game defect, visual consequence, or proof that downstream code fails to normalize. The static facts are the signed q, exact seed and fallthrough instructions. No bug-fix recommendation follows from these fixtures alone.

## Checks, artifacts and unresolved boundaries

`fixtures.py` passes1031 signed-seed comparisons and128 packed-rotation algebra comparisons, and retains six scale examples. The rotation comparison uses independently assembled matrix multiplication. Rounded-f32 fixtures explicitly emulate scalar rounding with Python; they do not establish the target's MXCSR rounding/FTZ/DAZ state or every IEEE edge case.

[Evidence receipt](NATIVE-NORMAL-MATRIX-EVIDENCE-2026-10-18.json) contains9 exact source-byte anchors,3 raw disassembly windows, constants, prior affine receipt hash and fixture hash. `build_receipt.py` verifies the original image hash and captures source-backed evidence. Original research artifacts stay outside Git; this compact report/evidence is published separately.

Unresolved: target FP environment, external trig result bits, full zero/subnormal/NaN/infinity behavior, downstream normalization, exact runtime reachability of pathological examples, and actual rendering consequences. Status remains PRIMARY_STATIC/NOT_INDEPENDENTLY_REVIEWED.
