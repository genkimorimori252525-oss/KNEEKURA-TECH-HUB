# Geometry batch header unmasking and immediate use

## Result
The first collection path in existing renderer producer381f30 unconditionally reconstructs batch begin/end as stored64-bit words XOR adjacent stored masks. It then uses the resulting addresses for a0x5c-stride record walk. It does not consult the batch's encoding-state byte or capacity word in this selected path. There is an empty-range equality gate, but no address-membership, allocation-extent, alignment, begin≤end, stride-divisibility or authentication validation in the decoded-pointer-to-first-read span.

The masks originate from a per-thread312-word generator at TLS+0x14e8. Its seed is formed from two32-bit provider returns and ANDed with a constant. Each batch stores its own24-byte mask, so this renderer does not need the generating thread's TLS state or seed. Actual source selection, seed values, allocations and execution remain unobserved.

No target, initializer, callback, CPU random instruction, asset or JVM was executed. No repository edits. reproduce.py verifies12 original instruction windows, three ELF import chains, three prior receipts and66 authored shuffle-basis cases.

## Consumer identity and pointer reconstruction
Prior attachment evidence establishes V as a0x38 batch inside a0x28 external-item container. Work helper398640 retains a borrowed container pointer at work-record+8. At3820c9..3820e0, the renderer obtains exactly that work record's+8 pointer. It reads container+0/+8 into the batch begin/end at3820f6..3820fd. Container+0x20 selects literal0x00f000f0 versus caller-supplied lighting at3820e3..3820f3, independently corroborating the earlier prefix-flag consumer without assigning any further naming convention.

For each V,3821d0 loads uint32 q=V+0x18.3821d4..382235 reconstructs:
B=LE64(V+0) XOR LE64(V+0x1d).
382238..3822a2 reconstructs:
E=LE64(V+8) XOR LE64(V+0x25).

The implementation uses byte XORs, one four-byte XOR, shifts and pshufb, rather than two simple64-bit XOR instructions. Original shuffle constant0x39c80 has hash in the receipt. The authored66-case basis check verifies that this shuffle/OR assembly reproduces the original little-endian64-bit word for zero,all-ones and each single bit. It is algebra validation only, not native execution equivalence.

No V+0x1c flag branch precedes either reconstruction. No V+0x10 capacity or mask+0x2d is read here. No writeback unmasks V in place. The consumer uses local decoded pointers while leaving the stored representation unchanged.

3822a7 compares B==E. If unequal,3822f9 immediately reads floats at B+0xc,+0x10,+0x14 and subsequent packed fields. The loop increments by0x5c at3822f0 and checks equality with E at3822f4; it is not a signed/unsigned less-than bounds test. This establishes a producer-required valid-range invariant, without diagnosing an observed defect or claiming malformed records can safely be used.

## Metadata q and local traversal stopping
q is the bounded-count metadata from the attachment cohort, not a decoded pointer-length validation. The shown branch keeps a local32-bit count initially0. At38254c..382557 it updates count from the floating comparison's carry flag and conditionally skips the emission block. After an emission,38274e advances the destination by0x90 bytes,382755 compares count to q, and equality skips to the next batch. Otherwise traversal returns to B+=0x5c.

If the source range is exhausted first,3822ac subtracts count from q. A positive signed remainder invokes zero-fill at382763..382777 for the computed144-byte-per-remaining-unit output region. This is an emission-quota/padding use in the selected path; it neither authenticates B/E nor proves the source range has q records. Floating/culling semantics and all output stores remain in the existing backend scope.

Batch traversal advances V by0x38 and compares to the container's batch end at3822bd..3822c9. No general validation of the outer container's pointer range is established by this equality loop either.

## Mask source and scope
Builder finalization obtains TLS base T through d14e80, original ELF import __tls_get_addr, with descriptor d2cf38.3790ae sets generator base G=T+0x14e8. Init byte is T+0x3c00. When unset,379497..379579 sets it to1, constructs provider object at T+0x160 using exact literal `default`, registers thread cleanup, and calls4df620,344520,3445e0. Only4df620 seeds the generator consumed here; the other initializers target distinct neighboring state offsets.

At4df641..4df678, two calls2fa460(T+0x160) yield a,b as32-bit values. The seed written G[0] is:
s=((uint64(a)<<32)|b) & 0xe7cae6049901fa65.

4df6a0..4df6ee fills31264-bit state words using:
x[i]=0x5851f42d4c957f2d * (x[i-1] XOR (x[i-1]>>62)) + i, modulo2^64.
Index G+0x9c0=T+0x1ea8 is set312 at4df6f0. The inline refresh/temper code in3791d0..379492 consumes that state; constants and exact instructions are retained, with earlier generated-word receipt linked. No new named-primitive or security-strength assertion is needed here.

For each batch, three successive generated words y are converted to mask words using the exact machine formula:
m=((y>>3) | uint32(uint32(y)<<29)) XOR 0xe7cae6049901fa65.

The shift-left is32-bit, zero-extended, and the right shift is64-bit. This is not a64-bit rotate-right.379211..379221 writes each result at V+0x1d+8*j for j=0,1,2.379228..37922f bounds that loop to three words.379190..3791a9 XORs the24-byte vector header with those masks and toggles V+0x1c. The packed0x5c records remain in their own allocation; these operations mask header pointers, not their record contents. Equivalent construction loops cover all four descriptor collections in the prior attachment receipt.

Generator state is mutable per-thread and is not reset per batch in these loops. Other uses of that TLS generator can affect subsequent masks. The masks are embedded alongside encoded words, so this local representation supplies reversible masking, not a proven integrity or authenticity check.

## Seed-provider boundary
2fa460 reads provider+8. If nonzero, it tail-calls that pointer with provider+0 as argument. Otherwise it reads four bytes using fd at provider+0x10, retrying interrupted reads and accumulating positive partial reads. The original read import is verified; no file was opened/read by this research.

The literal-default setup includes CPUID-dependent choices and a fallback path naming `/dev/urandom`, passing flags0 to the original open import. Original callback-store candidates in the retained setup are2f9ba0 (contains RDRAND),2f9be0 (RDSEED with callback fallback) and2f9c30 (RDSEED then RDRAND fallback). These bodies are retained as static dependency evidence. This bounded report does not assert which CPU branch is eligible or taken, that an OS read succeeds, or that any generated value meets a security property. Complete CPU-vendor gating and provider failure translation are the precise remaining provenance boundary.

## State byte and cleanup contrast
Construction initializes state byte0 and later XORs/toggles it. Cleanup37ae09..37ae28 checks that byte and conditionally XORs all three header words back, then clears the byte before freeing. The selected renderer instead always XORs only begin/end and leaves state unchanged. Therefore cleanup's conditional contract must not be substituted for this renderer's unconditional decoding contract. Normal freshly finalized batches provide the intended encoded input; arbitrary damaged or partially finalized objects are not proven acceptable.

## Stop
The immediate masked-header→decoded-pointer→packed-record-read contract is closed for one representative381f30 path. No all-backend equivalence is claimed. A useful separate frontier is checking that the remaining route-specific/backend consumers preserve the same unmasking and quota contracts, or auditing the setup's precise CPUID/provider error branches if seed-source completeness is needed. Neither requires an asset decoder or target execution.

Evidence: [NATIVE-GEOMETRY-BATCH-UNMASK-EVIDENCE-2026-10-18.json](NATIVE-GEOMETRY-BATCH-UNMASK-EVIDENCE-2026-10-18.json). [Preceding contract](NATIVE-GEOMETRY-PACKED-ATTACHMENT-RECOVERY-2026-10-18.md). Raw ranges and reproduction scripts remain external.
