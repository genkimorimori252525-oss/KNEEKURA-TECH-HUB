# Per-bone affine transform and parent propagation

New static cohort, preserving prior renderer receipts. Original image SHA25615d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22. No target/JVM/emulator execution. Independent semantic review NOT_RUN.

## Useful bounded slice

The most useful ordinary parent-producing slice is0x37cc1e..0x37d29b inside preparation helper0x37bd80. It constructs affine and normal matrices, then publishes child state. The tracking variant0x37e3ad..0x37e9d2 performs the same affine construction and records a transformed pivot before returning to ordinary routing. Selected-root bank seeding occurs at0x37c8c4..0x37c989; traversal gates at0x37cb40..0x37cc1e.

## Affine contract

Use column vectors, right multiplication, and inherited matrix P. Let position=(input[3],input[4],input[5]), rotation=(input[0],input[1],input[2]), scale=(input[6],input[7],input[8]). Let p be native bone descriptor float fields+0x60,+0x64,+0x68.

M = P · T((-positionX,positionY,positionZ)/16) · T(p) · Rz(rotationZ) · Ry(rotationY) · Rx(rotationX) · S(scaleX,scaleY,scaleZ) · T(-p)

This specifies matrix composition; a vertex receives the rightmost operation first. It does not mean animation input angles are applied in a procedural X/Y/Z call sequence.

Source-backed steps:
- Load inherited four4-float matrix columns from the depth-slot bank.
- Translate by(-positionX,+positionY,+positionZ)/16 using inherited basis columns.
- Add native descriptor pivot p using the same inherited basis.
- Evaluate sinf and cosf on each original X/Y/Z input angle. No intervening radians conversion or axis sign flip appears. The imports establish radian trig semantics.
- Construct the Rz·Ry·Rx rotation coefficients, postmultiply the inherited basis, and then multiply its three resulting columns by scaleX/Y/Z.
- Subtract p weighted by those final scaled/rotated basis columns from translation.

The rotation columns, with sx=sin(rx),cx=cos(rx), etc., are:
- column0=(cy*cz, cy*sz, -sy)
- column1=(sx*sy*cz-cx*sz, sx*sy*sz+cx*cz, sx*cy)
- column2=(cx*sy*cz+sx*sz, cx*sy*sz-sx*cz, cx*cy)

These coefficients are read from the scalar/vector dataflow at0x37cdb3..0x37cf27. Their external call chains are independently resolved from original bytes:0xd148a0→slot0xd308d8→stub0x13d6f08→ELF import0x184d0f8(sinf);0xd148b0→slot0xd308e0→stub0x13d6f0e→import0x184d100(cosf). Import identity is metadata proof, not live binding execution.

The native pivot p is already in the coordinate system expected by these multiplications. This cohort does not independently recover its construction from Java/model-file pivots, so do not apply an additional /16 or X inversion to p without that evidence.

## Parent propagation uses depth slots, not parent-pointer recursion

Native descriptors are120 bytes. Descriptor byte+0x70 selects a112-byte bank slot d. The transform reads bank[d], and after final inverse-pivot translation writes its complete affine and normal state into bank[d+1]. The next descriptor at the same depth reads the same parent slot; a child at the next depth reads the newly published state. This is consistent with depth-first flattened traversal.

The selected first bone's d slot is seeded with the incoming pose-derived matrix/normal values. A subtree-mode render therefore starts from its supplied pose seed at that selected depth; the shown path does not recompute omitted ancestors before the selected first index.

Descriptor u32(+0x6c) acts as contiguous descendant count: skip paths add this to current index, then the common loop increments once. The loop bounds are the selected half-open interval[startBone,endBone). Ordinary mode0 is[0,totalBoneCount); named subtree modes derive the end as start+descendantCount+1. No per-iteration depth-index validation is visible in these slices; valid descriptor/bank relationships remain a precondition, not a proven safety property.

## Visibility and scale gates matter

Input slots9,10,11 are own-hidden,children-hidden,tracking in the established Java contract. Native comparisons use nonzero or unordered(NaN) rather than exact1.

- Tracking is tested before scale/children gates. Its branch computes a transform and pivot output, then returns to routing.
- An exactly zero scale component causes subtree skipping on the ordinary gate. NaN is not classified as zero by these branches.
- children-hidden causes skipping of descendants while allowing the current bone's own geometry route. It bypasses publishing child state because descendants are skipped.
- Own-hidden suppresses current geometry after possible child-state publication; it does not inherently hide descendants.
- With neither tracking, descendants nor renderable geometry needing a transform, the routine can avoid construction. Do not assume every selected bone receives a freshly computed scratch matrix.

For tracked bones, the output writer observes transformed pivot-position translation before final T(-p) removal. It applies the earlier observed output axis/unit conversion(-16,+16,+16). The larger matrix manipulation used to derive that reported coordinate frame is not fully algebraically certified here; do not call it world-space merely because Java calls its XYZ getters absolute pivot.

## Normal matrices and numeric limits

Nine normal-matrix floats accompany the affine state. Rotation and scale handling are separate from the affine basis path. Uniform positive scale has a shortcut; negative/nonuniform cases enter sign/reciprocal and approximation arithmetic. This cohort does not replace that arithmetic with a generic inverse-transpose and claim bit equivalence.

The affine formula is a mathematical reproduction contract for reached, well-formed transforms with finite inputs and nonzero scales. Native operations are float32/SSE and external sinf/cosf. Operation rounding, trig library bits, singular/NaN/infinity behavior, normal approximation, invalid descendant ranges and malformed depths are not certified by the formula.

## Verification and owned numerical fixtures

The external original fixtures.py compares independently composed4x4 matrices against lifted scalar coefficient/translation formulas on128 deterministic finite cases, including nonuniform/negative scales and nontrivial parent matrices. Three hand checks verify position-X sign, pivot invariance and parent-Z-rotation propagation. All pass; maximum binary64 error3.552713678800501e-15. These are owned algebra consistency tests, not execution or differential testing of the target.

`build_receipt.py` verifies13 original-byte anchors,5 disassembly windows and2 complete original-ELF trig import chains. [Evidence receipt](NATIVE-BONE-AFFINE-EVIDENCE-2026-10-18.json) retains original-byte hashes/backing, constants, prior-cohort receipt hash and fixture source hash. Pending independent semantic review; no central mapping or whole-renderer completion claim.

## Optional reusable algebra check

The same owned formulas and128+3 checks are available in tools/check_native_affine_contract_ysm_265.py. Default execution prints JSON; optional --out writes to an explicitly selected path. Importing it executes no checks or file writes. [Bounded result](NATIVE-BONE-AFFINE-ALGEBRA-2026-10-18.json). Tool SHA-256066ac33c45aa603c397e01781a65c3cd78861cea22fca71a9e92807b8eb81b42. This checks mathematical composition only; it is not a replacement for the native float32 pipeline or a claim of rendering equivalence.
