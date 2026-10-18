# Pair processing and fourth-byte classifier

## Result

The selected consumer computes a half-open rectangle from four serialized float pairs and the external unsigned integer pair (W,H), then scans byte+3 in4-byte cells of an external buffer. The classifier is now exact:0 for rejected/empty rectangles or all sampled bytes0;1 if any sampled byte is between1 and254;2 for a mixture of0 and255;3 when every sampled byte is255. These are byte categories, not newly assigned image-channel or transparency semantics.

Each source record produces at most one packed record per external item on the scoped successful paths. Class1/2 goes to the first vector. Class3 goes to the second unless the caller override selects the first. Class0 is skipped unless the override selects the first. Neither vector receives the same record twice from these branches.

Static-only original-byte analysis, no target/emulator/JVM/assets/repository edits.11 byte selections and the original-ELF lroundf import chain PASS. Prior packed evidence remains6e594c8b3131a1e0dfc437e5fef4677e236ba8472961ffddc70d977bbd9e05e3. Original SO SHA25615d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22. evidence.json is authoritative.

## Numeric vocabulary and reusable domain

Let pairs p0,p1,p2,p3 be Q offsets(+40,+44),(+68,+6c),(+90,+94),(+b8,+bc). Let D be the external0x28-byte record, W=uint32(D+20), H=uint32(D+24), buffer=pointer(D+8). These pointer identities were established by the prior cohort.

The compact formulas below are exact for the ordinary bounded numeric domain: W,H in1..65535, each pair component finite and in[0,1], floating arithmetic evaluated with the target's float32 operations and ordinary IEEE behavior, and successful valid external-buffer access. This domain is an analysis precondition, not an upstream validation claim. It avoids invalid cvttps2dq/lroundf inputs and row-index multiplication overflow. Outside it, instruction-level low-word truncations, signed conversion details, NaN handling, floating exceptions and register arithmetic must be retained; no generic floor/round/clamp replacement is warranted.

Define f32 operation results at each machine arithmetic step. lroundf means its external API contract (nearest integer, halfway away from zero), not an executed runtime binding. Original thunk d14870 -> original pointer d308c0 -> stub13d6ef6 -> JUMP_SLOT184d0e0 resolves symbol lroundf. Runtime symbol binding remains unverified.

The mode m is derived from an unsigned caller integer v at375e4c..375eae:
- v<6: m=0
-6<=v<=16: m=1
-17<=v<=27: m=2
-v==28: m=3
-v>28: m=4

This receipt does not assign v a serialized field name.

## Modes0 and4: per-pair quantization

377613 tests mode bits so only0/4 use377637..37774b. The constants are original f32(0.6)=0x3f19999a, f32(0.4)=0x3ecccccd. X threshold is0.6 in both modes; Y threshold is0.6 for0 and0.4 for4. The threshold vector is built by insertion into original vector at39100.

For each component c with scale S, let t=f32(c*f32(S)), n=truncToInt32(t). The implementation clears the upper16 bits of n before converting it back to float and computes residual against that value. It compares residual>=threshold, then increments the low16-bit value when true, using psubw against an all-ones compare mask. Thus, even in the bounded domain, the exact stored integer coordinate is:

q = low16(n + (f32(t-f32(low16(n))) >= threshold ? 1 : 0)).

All four pairs undergo this. The corresponding packed float pairs initially become f32(q/f32(S)). Do not simplify this to lroundf or conventional nearest rounding: thresholds differ and the low16 operation is explicit.

37774e..37777e computes componentwise unsigned16 minima L=(Lx,Ly) and maxima U=(Ux,Uy) across the four quantized pairs. Then degenerate intervals are expanded:

X, both modes:
- If Lx!=Ux, unchanged.
- If equal and W>Ux, set Ux=low16(Ux+1), pairs unchanged.
- Else if Ux>0, set Lx=Ux-1 and add f32(-1/f32(W)) to p0.x and p3.x of the processed pairs.
- Otherwise unchanged.

Y, mode0:
- If Ly!=Uy, unchanged.
- If equal and H>Uy, set Uy=low16(Uy+1), pairs unchanged.
- Else if Uy>0, set Ly=Uy-1 and add f32(-1/f32(H)) to processed p2.y,p3.y.
- Otherwise unchanged. The last boundary case reaches37840e..378422 and rejoins377b2c; this short side block is included in the receipt.

Y, mode4:
- If Ly==Uy and Uy>0, decrement Ly and shift processed p2.y,p3.y by-1/H, regardless of whether Uy<H.
- If Ly==Uy==0 and H>0, set Uy=1.
- Otherwise unchanged.

Original constant at482bc is-1.0, not+1.0. These shifts are backward by one scaled cell, not an upward expansion of the float coordinates. The rectangle's opposite endpoint can be expanded without changing any pair.

## Modes1,2,3: extrema rounding and selective shifts

3777c0..3779da uses finite float comparisons to obtain component minima/maxima before quantization. Four calls to lroundf yield:
Lx=low16(lroundf(f32(min_i(p_i.x)*f32(W))));
Ux=low16(lroundf(f32(max_i(p_i.x)*f32(W))));
Ly,Uy similarly with H.

The packed pairs initially preserve the original p values; they are not individually rounded to the rectangle coordinates.

Mode1 (377c6d..377d14): if X bounds are equal, increment Ux with low16 publication; if Y bounds are equal, increment Uy similarly. No pair shifts. An increment can wrap65535 to0; subsequent rectangle validation rejects invalid order. No saturation is established.

Modes2/3 share these rectangle corrections:
- Equal X: if W>Ux, increment Ux; otherwise if Ux>0 decrement Lx and set dx=f32(-1/f32(W)); otherwise dx=0.
- Equal Y: if Uy>0 decrement Ly and set dy=f32(-1/f32(H)); otherwise if H>0 set Uy=1. Non-equal axes set their shift to0.

Mode2 applies dx and dy to all four pairs (377d14..377d4b).
Mode3 applies dx only to p0.x and p3.x, dy only to p2.y and p3.y; p1 is unchanged (377c39..377c5b then377d47). This is an actual pair-index-dependent operation and does not establish any semantic corner names.

All additions/divisions are machine float operations. Replacing add(+0) by a no-op could change signed-zero behavior outside an ordinary value-equivalence interpretation; no bitwise cross-platform oracle is claimed.

## Rectangle validation and exact classifier

At377d52 the bounds are unsigned16 words, while W/H remain unsigned32. Set class=0. Continue only if:
Ux<=W AND Uy<=H AND Ly<Uy AND Lx<Ux.

The code does not separately test buffer byte length or allocation extent here. On valid paths, it scans rows y=Ly..Uy-1 and columns x=Lx..Ux-1, reading:
buffer[4*(y*W+x)+3].

Machine y*W accumulation is32-bit and then zero-extended into address arithmetic. The stated bounded numeric domain prevents its overflow; no whole-input validation is proven. x span comparisons use the low16-bit width.

377dbd..377e23 is equivalent to this finite classifier:
- Start result=3 and no255Seen=true.
- A byte255 clears no255Seen and continues.
- A byte0 sets result=2 and continues.
- Any byte1..254 immediately sets result=1 and exits the scan.
- At normal scan completion, if no255Seen is still true, set result=0.

Therefore:
-0: invalid/empty rectangle, or every sampled byte0.
-1: at least one sampled byte1..254 (early return).
-2: only0/255 were seen, with at least one of each.
-3: all sampled bytes255.

This supplies content-based categories for the previously opaque classifier. The sample's byte+3 position is proven; calling it alpha would additionally require the external provider's format contract.

## Cardinality and packing consequence

The previous receipt maps source Q to packed0x5c record P. Its first3 and four groups of3 scalars remain copied from Q. The last two lanes of each group use the processed pairs defined above.

At377e9a, class1 marks a per-external-item byte and enters the first-vector insertion path. At3780e0, unsigned(class-1)<2 also enters that path (class1/2). If not, a nonzero caller override byte at stack+128 sends any remaining class there. Without override, class3 enters the second vector and class0 jumps directly to next Q.

For each Q and each external-item index k, assuming successful allocation and normal control flow:
- override==0: class0 gives0 outputs, class1/2 gives1 in vectorA, class3 gives1 in vectorB.
- override!=0: all classes give1 in vectorA.

No polygon splitting or multi-emission occurs in these selected insertion branches. This statement is local to one Q,k; the outer loop repeats over external items, so one source record can have outputs for multiple k. Allocation exceptions, downstream attachment, later processing, and final visibility are not covered.

## Bounded stop and next frontier

Numeric and classifier/storage contract is complete for the stated domain, with the exact machine boundaries documented. Next useful work is the immediate provider output-format contract behind4c8000/d35cb8 (to establish whether the fourth byte is alpha and W/H are image dimensions), or378430 packed-vector attachment. No broad renderer expansion is necessary. Out-of-domain numerical behavior is explicitly unresolved rather than silently modeled as clamping.

Evidence: [NATIVE-PRIMITIVE-PAIR-CLASSIFIER-EVIDENCE-2026-10-18.json](NATIVE-PRIMITIVE-PAIR-CLASSIFIER-EVIDENCE-2026-10-18.json). [Preceding contract](NATIVE-PRIMITIVE-PACKED-CONSUMER-RECOVERY-2026-10-18.md). Raw ranges/reproduction scripts remain external.
