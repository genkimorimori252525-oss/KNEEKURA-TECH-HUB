# Provider output format: bounded original-byte contract

## Result
The static initializer registers selectors 2, 3, 4, and 5 with distinct native methods. Selector 1 bypasses that registry and copies bytes unchanged. The consumer's pair cannot universally be described as decoded dimensions copied from a single source: selector 2 replaces it with two big-endian header values; selectors 1, 3, and 4 copy the supplied pair; selector 5 copies a decoder-context pair while sizing its output using the supplied pair. Four-byte record geometry is supported. A universal RGBA channel-order / alpha interpretation is **not established** by these selections.

No target, JVM, emulation, or asset decoding was performed. No repository files changed. Original SO SHA256: 15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22.

## Static registration and dispatch
Original RELATIVE relocation at init-array slot d16518 resolves to343fa0. The slot lies within DT_INIT_ARRAY/DT_INIT_ARRAYSZ.343fa0 constructs four eight-byte objects and stack (uint32 selector, pointer) records:

| selector | installed vtable | vtable+10 RELATIVE target |
|---|---|---|
|2|d1d6f0|4ceab0|
|3|d1d6b8|4ce470|
|4|d1d728|4d3ff0|
|5|d1d680|4cad00|

343fc2,343fe3,344004,344025 write the keys.344032..34406f initializes registryd35cb8.34410c reads each key,3441cb..3441e2 copies key/pointer into node+8/+10, and3440fe..344106 advances sixteen bytes to a total of0x40. Therefore this initializer supplies exactly these four records. This is not a claim that runtime initialization occurred or that no other mutation mechanism could exist.

4c8000 first tests S+28==1. Otherwise it searches by the unsigned32 selector and dispatches provider-vtable+10, ABI rdi=output D,rsi=provider,rdx=S. Missing provider takes the error path at4c80a5.

## Selector 1: byte-preserving output
4c8150 calls S.virtual+18 for source pointer, then S.virtual+20 for byte count N. It installs output vtabled1d530, zeros D+8/+10, sets D+18=N, calls4c4aa0(D,N,0) when N!=0, and tail-calls5767d0(D+8,source,N). The complete small5767d0 selection shows byte-for-byte copy, vectorized in32-byte blocks then4-byte blocks and final bytes. No swizzle, conversion or decompression occurs here.

4c811f..4c8123 copies S+20/+24 unchanged into D+20/+24. There is no shown requirement N=4*pair0*pair1. Source virtual accessor implementations remain beyond this boundary. Allocation helper4c4aa0 rejects requested size >=0x4200001; successful fresh allocation stores pointer D+8 and capacity D+10. This does not establish input channel names.

## Selector 3: supplied pair and four-byte stride
4ce4fc..4ce524 computes N=zeroExtend(low32(4*S.u32[20]*S.u32[24])), sets D+18 and allocates through4c4aa0.4ce529..4ce52d copies S+20/+24 to D+20/+24.4ce531..4ce54b calls c16350 with:
- rdi=context produced by c15d50
- rsi=S+8 input pointer
- rdx=S+18 input byte count
- rcx=D+8 output pointer
- r8d=low32(4*S.u32[20])
Success is return0. This establishes a four-byte-per-column stride argument and rectangular allocation formula, not the callee's channel order. The codec/helper body is not traced.

## Selector 4: supplied pair and external-output setup
4d4007..4d402a computes the same low32 allocation formula and stores D+18.4d402f..4d4033 copies the supplied pair. Its local descriptor has mode1 at stack+250, D+8 at+260, low32(4*S.u32[20]) at+268, D+18 at+270, flag1 at+25c. The first immediate call5853e0 at4d4167 receives the original input pointer/count and descriptor-related state. Subsequent large decoder/control flow was not semantically traced. No RGBA enum meaning is assigned to literal1.

## Selector 2: exact header-derived pair
4cec26..4cec44 passes pointers to stack+84 and stack+80, state stack+a0, original S+8 bytes, and S+18 length to4ea5a0. That immediate header helper:
- requires nonnull input and length>32;
- compares all eight bytes 89 50 4e 47 0d 0a 1a 0a;
- requires big-endian32 at input+8 to equal13;
- compares input+0c..0f to literal IHDR;
- reads big-endian32 at input+10 into its first output and input+14 into its second output, at4ea6ce..4ea6dd.
These are exact PNG-signature/IHDR-coordinate provenance, rather than a format guess from a library resemblance. At the successful provider return4cf2a0..4cf2ee, these locals become D+20/+24; D+8 takes the produced r13 buffer and D+10/+18 become zeroExtend(low32(4*first*second)). They are PNG IHDR width/height on this branch. The first source pair copy at4ceac4 is not the final output pair provenance.

The producer initializes numeric format fields to6 and8, but this receipt does not independently establish every conversion path or emitted byte order. Do not promote byte+3 to alpha solely from these numbers or from PNG recognition.

## Selector 5: two distinct pair sources
Entry4cad11..4cada2 saves original S at r15 and D at stack+80; S is then saved stack+78 at4cae4f. Context C allocated at4cad17 is saved stack+10. At4cc13c,4cc165,4cc16a these become r15=D,r13=C,r14=S.4cc1a5..4cc1a9 copies C[0..7] into D+20/+24. Separately4cc1ad..4cc1c6 allocates and records low32(4*S.u32[20]*S.u32[24]) bytes.4cc207..4cc224 puts supplied first*4 and D+8 into output descriptor fields. Thus neither the returned pair's original decoder provenance nor its equality to the allocation pair can be assumed. Helpers b2a220/b2a430/b2a7b0 appear beyond this output-setup boundary; no format name is assigned.

## Evidence and finite frontier
reproduce.py rechecks original image hash, eleven aligned selected byte ranges, five RELATIVE records including the init-array link, and prior classifier receipt unchanged. Ten exploratory disassembly windows are separately inventoried and hashed; those are reading aids, not claims of complete method decoding. No files from earlier receipts were overwritten.

The bounded provider boundary is reached. A universal pixel-channel contract remains open. The smallest next useful question is the exact output mode/channel contract of selector3's c16350 (including the context fields supplied by4ce470), or selector2's final conversion into r13. Select one provider; do not expand all codecs or infer semantics across selectors. Selector1 additionally needs its source-type accessor/creator contract before any byte-format claim. No actual asset selector was observed, so there is no basis to choose a runtime format.

Evidence: [NATIVE-PROVIDER-OUTPUT-FORMAT-EVIDENCE-2026-10-18.json](NATIVE-PROVIDER-OUTPUT-FORMAT-EVIDENCE-2026-10-18.json). [Fourth-byte classification](NATIVE-PRIMITIVE-PAIR-CLASSIFIER-RECOVERY-2026-10-18.md). Raw excerpts/reproduction scripts remain external.
