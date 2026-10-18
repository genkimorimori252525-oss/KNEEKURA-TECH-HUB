# Renderer batch-header decode coverage

## Result
All seven producer routes in the existing non-GUI backend inventory contain four located begin/end XOR-decoding sites, for28 verified sites. Their header contracts agree:

B=LE64(V+0) XOR LE64(V+0x1d)
E=LE64(V+8) XOR LE64(V+0x25)

Every selected block is straight-line reconstruction without a state-byte check, capacity-word read, conditional branch or call inside the decode. Each then reaches a begin/end equality comparison before the corresponding nonempty path. This is finite header-contract coverage, not full rendering, memory-safety or runtime equivalence.

A material distinction is preserved: sites1/3 in every producer load uint32(V+0x18) as quota metadata immediately before decoding; sites2/4 do not load that field in their immediate decode prefix. The representative quota/padding semantics previously proved for381f30 site1 must not be generalized to all four sites.

## Supported producer coverage
The entry-to-producer association comes from the preserved original NATIVE-RENDER-BACKENDS receipt:

| Backend | Producer | Located decode starts |
|---|---|---|
|1,mode0|37fae0|37fd94,3805df,380e54,381829|
|1,mode nonzero|381f30|3821d4,382a0d,383084,383a56|
|2|38a580|38a824,38b6b4,38c2eb,38d2b7|
|3|38dbe0|38de84,38ed04,38f93b,390907|
|4|394890|394b34,3959b4,3965eb,3975b7|
|5|391230|3914d4,392364,392f9b,393f67|
|6,Java-array compatibility|388a20|388c19,38943d,389968,38a203|

[coverage matrix](NATIVE-GEOMETRY-UNMASK-MATRIX-2026-10-18.md) provides all28 exact decode start/end ranges, equality-gate addresses and quota-load addresses. `evidence.json` includes each decode span's original-byte SHA256 and source-window backing. Site numbers are local order in each producer, not newly assigned semantic names or an asserted mapping to descriptor offsets.

GUI bypass wrappers385080/385390 remain outside the existing producer mapping and this coverage. Additional undocumented producers or a differently represented header would require separate inspection. The scan alone is not a proof that no other header interpretation exists anywhere in the image.

## Verified instruction structure
Candidate discovery searched source-backed objdump for the first mask-byte read. Each candidate was then checked as a whole instruction sequence, rather than accepted from a byte-pattern match. All28 blocks read the same alternating mask/header offsets:

1d,0; 1e,1 (four bytes); 22,5; 23,6; 24,7;
25,8; 26,9 (four bytes); 2a,d; 2b,e; 2c,f.

The byte/four-byte XORs assemble the two64-bit words with shifts40/48/56 and the two pshufb/pshufd/OR reconstructions. The shared shuffle layout at39c80 and its66 authored algebra checks were established by the representative receipt. Register choices and instruction scheduling differ, while the decoded byte association remains the same. Raw-format producers2..5 visibly reuse the same patterns with relocated addresses and route-local registers; they were each independently included in the offset/branch assertions.

The selected blocks contain no header access to +0x1c (state),+0x10 (capacity),or+0x2d..+0x34 (capacity mask). They do not write decoded pointers back into V. Direct jumps from a finished decode to its later gate were followed by address; the receipt records the actual gate rather than assuming adjacent fallthrough. Gates are only equality/inequality comparisons of the reconstructed values. No proof of allocation extent, address provenance, alignment, begin≤end, exact0x5c divisibility or cryptographic authenticity is supplied by these header blocks.

The prior representative receipt traces the ensuing packed-record dereference and0x5c walk. This inventory deliberately stops before repeating transform/emission math for all28 paths. It does not claim that an earlier producer invariant or later check is absent outside the inspected spans, nor infer safety or exploitable runtime behavior from a missing local check.

## Count preconditions
The14 quota loads are documented explicitly in MATRIX.md. Sites1/3 enter their immediate gate with quota in a register or stack slot and a local emitted-count accumulator. The equality case has quota-minus-count handling visible beside the gate. Sites2/4 instead take their empty-range path directly toward the next batch. This distinction explains why a single representative quota limit cannot serve as a universal source-range validation claim.

The producer-owned begin/end/mask relationship remains a required precondition across all28 sites. Stored header masking is reversible with the mask embedded in the same batch, as established earlier; it is not an authentication mechanism. Actual provider seeds, mask values, backend eligibility and successful rendering were not observed.

## Verification and stop
reproduce.py re-reads the pinned original SO, verifies its complete SHA256, exports seven containing source windows, identifies exactly four selected decode signatures in each window, verifies the20 offset sequence and two shuffle-reconstruction sequences, rejects conditional branches/calls inside each decode, follows direct gate jumps, and checks28 equality gates plus the14 quota prefixes. Three prior receipts are linked unchanged by hash. Source-window ends are containing boundaries and are not asserted exact function ends.

Result: PASS,7 source windows,28 straight-line decode blocks,28 equality gates,14 quota prefixes. This authored analysis parses bytes and objdump text; it does not execute or emulate original instructions, assets, callbacks, JVM code or renderer backends. No repository changes.

Finite coverage task complete. Remaining frontiers are GUI-bypass producer mapping, route-specific quota/emission equivalence, and ownership/concurrency invariants beyond the immediate header seam. Those are intentionally not expanded here.

Evidence: [NATIVE-GEOMETRY-UNMASK-COVERAGE-EVIDENCE-2026-10-18.json](NATIVE-GEOMETRY-UNMASK-COVERAGE-EVIDENCE-2026-10-18.json). [Representative decode](NATIVE-GEOMETRY-BATCH-UNMASK-RECOVERY-2026-10-18.md). Raw ranges/reproduction scripts remain external.
