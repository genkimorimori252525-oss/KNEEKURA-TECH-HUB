# Selector 3 output: finite mode/row-dispatch boundary

## Result
Selector3 returns the **supplied** unsigned pair unchanged, allocates low32(4*pair0*pair1) bytes, requests numeric mode12 in an embedded processing context, and supplies row pointers with pitch low32(4*pair0). Actual channel stores remain behind an indirect row-processing callback. RGBA/BGRA and opaque-alpha labels are **unproven** here. No source-library identity is inferred from mode12 or structure resemblance.

No assets, target execution, emulation, JVM, external decoder execution or repository edits were used. This is an exact unresolved boundary rather than a complete codec trace.

## Context and ABI
4ce470 allocates a0x770-byte context C, zeroes it, and establishes the following selected defaults before c15d50:
- C+6d8/+6dc/+6e0/+6e4 =0xffffffff;
- C+6e8=8,C+6ec=0xffffffff;
- C+70c=1;
- C+71c/+720=1,1 and C+728/+72c=1,1;
- C+748=2.

c15d50 configures internal allocator/error/input interfaces and embedded state J=C+208. It returns the original C pointer on its selected success path atc161ff..c16207, having set C+600 bit1 atc161f8. It does not return a replacement image buffer. Failure can return zero atc15e35..c15e44.

4ce54b calls c16350(C,S+8,S+18,D+8,low32(4*S.u32[20])). c16350 checks C nonnull; C+600 bit1; input/output pointers and input length nonzero; and supplied pitch signed-nonnegative atc16385..c163b4. That is a machine-level pitch check, not an independent dimensional validation.

## Pair provenance and mode
4ce4fc..4ce524 computes the allocation length with32-bit multiply and shift, zero-extends it into D+18, and allocates through4c4aa0.4ce529..4ce52d copies S+20/+24 into D+20/+24. No later copy from C to this returned pair occurs on the selected provider success path4ce550..4ce56d.

Inside c16350, after c19300/c170c0, c165a2..c165b6 separately copies J+30/J+34 (C+238/+23c) into C+6e0/+6e4. These are internal header/result values; equality to the supplied S pair is not established here. C+6e0/+6e4 do not become returned D+20/+24.

c16667 explicitly stores12 at C+248, equivalently J+40. c166b9/c166c3 copy C+728/+72c into C+24c/+250 (J+44/+48). On state0xca, c1670f calls c1da20(J). Numeric12 is therefore an actual requested processing mode, not merely a constant elsewhere in the binary. Its channel meaning is not proven by the scoped original instructions.

## Output pointer and rows
The caller-provided D+8 is saved stack+48 atc1643d. Pitch from r8d is saved in ebp atc1638e and subsequently r15d atc16ca2. If pitch is zero, c16ca9..c16cb0 instead uses4*C.u32[290] (J+88). Otherwise the supplied pitch is retained.

c16cd7 obtains row-pointer count from an internal output-height/crop field; c16ce2 allocates that pointer array. c16d17 reloads original D+8. c16d22 selects forward/reversed row-pointer construction based on C+6d0. Fresh caller context initializes C+6d0 to zero; this field is not written in the selected constructor/c16350 code. Forward scalar tailc16f68..c16f80 yields row[i]=D+8+i*signExtend(pitch), with equivalent vectorized pointer arithmetic preceding it. This proves stride/addressing, not the contents written to each row or that supplied allocation dimensions match decoded output dimensions.

c16fd1/c16fff call c1cbf0(J, rowPointerArray+currentRow, requestedRows). In c1cbf0:
- c1cc81 loads U=*(J+228), equivalently *(C+430);
- c1cc88 loads callback=*(U+8);
- c1ccb7..c1ccc4 calls it with rdi=J,rsi=rows,rdx=&producedCount,ecx=requestedRows;
- c1ccca adds producedCount to J+a8 (C+2b0).

The callback's actual component stores are the exact unresolved output boundary. The provider calls no post-decode byte swizzle before returning D. c16350 ultimately returns status;4ce550 requires zero and returns D after context cleanup. This shows a pipeline to the returned buffer but does not supply channel names.

## Stopping point / smallest next frontier
Resolve the initializer store of *(J+228) and its callback+8 under requested J+40=12, starting from c1da20's initialization path. Follow only that dispatch to its selected output-store routine; stop after establishing channel positions and fourth-byte policy. Do not expand entropy decoding, transforms, or all modes. A primary library enum comparison alone would still be insufficient to assert this target's provenance or channel implementation.

The previously proven selector2 RGBA8 contract remains separate. No inference that selector3 alpha is255 or that classifier class3 necessarily results is supported yet.

## Evidence
Original SHA25615d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22. reproduce.py verifies8 aligned original ranges,5 exploratory windows, and the preceding provider receipt unchanged. Exploratory c1da20/c35c50 windows were inspected only to locate the finite boundary; no complete initialization or row-conversion semantics are claimed for them.

Evidence: [NATIVE-SELECTOR3-CHANNEL-BOUNDARY-EVIDENCE-2026-10-18.json](NATIVE-SELECTOR3-CHANNEL-BOUNDARY-EVIDENCE-2026-10-18.json). [Preceding contract](NATIVE-PROVIDER-OUTPUT-FORMAT-RECOVERY-2026-10-18.md). Raw ranges and reproduction scripts remain external.
