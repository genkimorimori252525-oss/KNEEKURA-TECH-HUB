# Packed records: attachment, ownership and immediate renderer join

## Result
The two temporary packed-output routes become owned nested geometry data through an additional routing step. A 0x78-byte bone descriptor has four vector headers at +0, +0x18, +0x30, +0x48. Each vector contains one 0x28-byte container per external-item index; each container owns a vector of 0x38-byte batches; each batch owns a copied vector of 0x5c-byte packed records. Temporary packed buffers are freed after attachment. The descriptor vector is subsequently transferred into the shared geometry payload and geometry registry.

The classifier-1 byte flags have a separate lifetime: accumulated bytes are copied into the builder result and then a Java boolean array. They are not stored as that vector in the geometry payload. Container+0x20 is another, distinct flag: it records whether the original bone name starts with the seven literal bytes `ysmGlow`.

Static original-byte analysis only. No assets, target/native/JVM execution or repository edits. Prior pair-processing domain and local cardinality limits remain applicable. The reproducible receipt verifies 17 instruction-aligned source windows and four prior receipts.

## Objects and exact source identity
Use F for a bone descriptor; A for the first temporary packed vector (begin stack+0, end R12), B for the second (begin stack+0x40, end RDI), and k for the external-item index. These A/B names describe the proven classifier routes, not semantic rendering categories.

375e30 receives the hierarchy aggregate and external pointer/count. Source setup and previous receipts establish F stride0x78. Within this function R15 points just past F, so the setup LEAs at 376570,376690,3767b0,3768d0 correspond to F+0,+0x18,+0x30,+0x48. Their saved addresses are stack+0x38,+0x2a0,+0x2a8,+0x2b0. Each collection is resized to the external count, using 0x28 stride (376574..3769e6). Existing descriptor-vector growth moves the four vector headers and zeroes their sources at 3760de..37615a.

At 377501..377544 the A/B temporary vector triples are reset for one source item and one k. 3775fb..37760b computes 0x28*k and saves it at stack+0x70. The record loop finishes at 3775f5→378430. Attachment therefore adds batches per source item and external index, rather than creating a single batch for the entire bone.

## Additional routing at 378430
Let C be the local byte at stack+0xc. It is explicitly set to zero at 3774b0 or to one along 377496..37749c; its preceding geometric/math predicate is outside this cohort. Let J be the incoming R9 low byte saved at stack+0x129. The branch condition is exactly:

G = ((source inner byte span == 0x480) & J) | C.

The span is captured at 376c4e..376c58. The bitwise operations at 37843c..378446 are byte operations, so do not replace arbitrary J by a general truth-value conversion.

For nonempty temporary vectors:
- G nonzero: A → container k in F+0x48 (378471..37847c); B → container k in F+0 (37874b..378754).
- G zero: B with exactly 0x228 bytes, i.e. six 0x5c records, → F+0 (37855b..378568). Other nonempty B → F+0x18 (3785d9..3785e4).
- G zero: nonempty A → F+0x30 (37899d..3789b1).

Empty vectors create no batch on these normal paths. The six-record case is a storage routing test, not proof of a source primitive type. This extra partition preserves the preceding cohort's one-output-per-Q,k contract.

## Batch metadata and copying
Before header finalization, batch V has:
- +0,+8,+0x10: packed begin/end/capacity pointers;
- +0x18: uint32 metadata q;
- +0x1c: state byte, initialized zero;
- +0x1d..+0x34: 24 zero-initialized bytes, subsequently used as a header mask;
- remaining tail padding is not assigned a value by this claim.

q is 3 on G-nonzero/C-zero paths and on the six-record B special case. If C is nonzero, q=min(low32(packedCount),5) (378b31..378b66). On ordinary G-zero non-six B or A paths, q=min(low32(packedCount),3) (3785f4..378611;3789c1..3789d6). Exact machine count derivation shifts the byte difference by2 then multiplies by the modular inverse of23; valid packed byte spans are multiples of92. Large-count truncation remains explicit.

The fast-capacity path performs two allocations and copies: A example 378481..3784b9 copies the temporary into an intermediate owned vector, then 3784f4..37851b allocates and copies into the batch. The batch receives metadata and advances the container end by0x38 at37851f..37853e. The intermediate is freed at378718..37871e. Equivalent B/A branches are retained in the attachment window. The original temporary vectors are freed at378aed..378b27 before proceeding to the next external item.

A full container uses growth helper37ac20. It deep-copies the incoming packed vector at37ac99..37ad11, then deep-copies each existing batch's packed buffer and metadata at37ad7a..37adec. It destroys old buffers and the old batch allocation at37adf1..37ae70, then publishes the replacement header. This is not a transfer of the temporary packed pointer, nor merely a shallow copy of batch headers. These statements apply to the construction phase before header masking; arbitrary later uses of the helper were not generalized.

Helper5767d0 is directly verified as a byte copy: 32-byte vector loop, 4-byte loop and byte tail copy RSI→RDI for RDX bytes, returning destination. No named external memcpy binding is required.

Each container has uint32 accumulators +0x18/+0x1c. After insertion the first increment is computed exactly as 4 * (((low32(end)-low32(begin)) mod 2^32) >> 2) * 0xe9bd37a7, with multiplication/addition modulo2^32; the second increment is4*q. For packed byte spans below2^32, the first equals4*packedCount modulo2^32. The larger-span expression must not silently be replaced with that count identity. Packed32 addition updates +0x18/+0x1c (3786e9..378712 and equivalent branches). These are counts used downstream; no unproven draw-topology interpretation is attached.

## Distinct flags
1. Container flag: 3761da..376207 reads original bone name pointer/length, requires length≥7 and compares the first seven bytes against `ysmGlow` using overlapping four-byte constants. It does not require exact name length7. The resulting BPL is copied to every external container's +0x20 in all four collections at376b85..376c0b.
2. Classifier-1 flags: local byte vector stack+0x180/+0x188/+0x190 is initially empty. 3769f0..376b84 resizes it to external count, initializes newly appended bytes to zero, and retains existing bytes. 377ea3..377eab sets byte[k]=1 for class1. Thus for the scoped normal loops it accumulates whether any processed Q for k reached class1; starting another bone does not reset existing bytes. If there are no bone descriptors, this resize is never reached and the returned vector remains empty.
3. Geometry payload flag: incoming stack argument byte saved at375ea7 becomes payload+0x54 through378c8d..378c95. This is distinct from both flags above.

At37a213..37a28e the accumulated classifier byte vector is allocated/copied into output+0/+8/+0x10; handle low32 is output+0x18 at37a295. Its old local buffer is freed at37a318..37a330. Caller36c360..36c392 creates a Java boolean array and fills it from this copied byte vector through JNI slots+0x578/+0x678; the array is passed to the previously proven GeoModel constructor at36c423/36c42c. No callback or Java construction was executed here.

## Geometry payload, registry and stored-header boundary
At378b79..378bc8 a 0x68-byte shared-control allocation C receives the descriptor-vector triple at C+0x10/+0x18/+0x20, and clears the original stack triple. Geometry payload P=C+0x10 therefore owns that descriptor vector at P+0/+8/+0x10. Its auxiliary map is also transferred with inline-bucket repair at378bc9..378c87. Max-depth+1 goes to P+0x50 and the separate incoming flag to P+0x54.

The existing geometry lifecycle receipt supplies the registry ownership contract. Exact nearby stores here agree: new registry node+8 is full64 handle, node+0x10/+0x18 receives payload/control pair at378deb..378df8. Successful insertion clears the local pair at37903d..379049. Registry buckets remain d341b8, distinct from texture registry d348b0. Allocation/insertion failures and handle collisions are not asserted successful.

Important stored representation: after obtaining registry payload,379102..379154 visits all four collections. For each batch it fills mask storage +0x1d..+0x34 and XORs the first24 bytes (three pointer words), then toggles +0x1c. First route's exact XOR is379190..3791a9; equivalent blocks are3795c0..3795d9,3799f0..379a09,379e20..379e39. The generator internals and actual mask values are outside this task. Consequently final stored +0/+8/+0x10 cannot always be treated as plain pointers. The allocated packed records themselves are not rewritten by these located header-XOR blocks. Cleanup37ae09..37ae28 conditionally unmasks those header words when state byte is nonzero before freeing. The code path remains within the conditional registry-lock region until37a29a..37a2a1; no runtime race/completion guarantee is added.

## Immediate renderer join and bounded stop
Existing renderer source at37d29b..37d322 reads F+0,+0x18,+0x30,+0x48, computes exactly40*k, and examines each selected container's batch begin/end. This is the same descriptor/container layout produced above. At37e9d2..37ea32 the F+0x48 selected container is queued and its +0x1c accumulator added to d34bc8; the F+0x30 container is queued and +0x18 added to d34be8. Helper398640 fast path stores a borrowed container pointer at work-record+8 beside a transform pointer at+0 and count/offset at+0x10; it does not copy packed data there.

This closes the immediate producer→stored payload→renderer collection identity. It does not prove every draw backend's batch-unmasking/emission semantics, eventual GPU consumption, all exceptional cleanup, concurrent release safety, or successful visual rendering. Those remain separate frontiers; no full renderer retrace was performed.

Evidence: [NATIVE-GEOMETRY-PACKED-ATTACHMENT-EVIDENCE-2026-10-18.json](NATIVE-GEOMETRY-PACKED-ATTACHMENT-EVIDENCE-2026-10-18.json). [Preceding contract](NATIVE-PRIMITIVE-PAIR-CLASSIFIER-RECOVERY-2026-10-18.md). Raw ranges/reproduction scripts remain external.
