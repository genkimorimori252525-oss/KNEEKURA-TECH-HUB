# Selector 3: requested mode 12 callback and output-store contract

## Result
The traced byte-output path has four-byte records with a synthesized fourth byte of 255. This is directly established for the generic single-component path, the generic three-input scalar stores, the generic table/clamp converter, and the two statically registered vector backends' packing/store tails. No source fourth byte is read by those stores. The color names of the first three bytes remain unproven here; this receipt does not upgrade selector 3 to a universal RGBA8 claim.

Actual backend selection is runtime-dependent. The two mode-12 vector candidates are 0x210ec0 and 0x212720; neither was executed. Other sample-precision, alternate setup, and source-encoding paths are outside this finite trace. A successful image decode, supplied/internal dimension equality, and a universal selector-3 contract are not established.

## Scope and source
Original SO SHA256: `15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22`.
J is C+0x208 from the preceding selector3-channel-contract receipt. That receipt establishes requested J+0x40=12, supplied row pitch 4*S+0x20, and D+0x20/+0x24 copied from the supplied pair rather than necessarily from internal decoded dimensions. Those limitations remain unchanged.
All addresses are original-image VAs. evidence.json hashes original-byte ranges and original RELATIVE relocation records. reproduce.py only reads the original file and disassembles extracted bytes. No assets or target code were run; no repository files were changed.

## Callback initialization and forwarding
- At 0xc21c41..0xc21ce5, the branch with J+0x5c=0, J+0x128<=8 and (*(J+0x220))+0x14 nonzero allocates/zeros the row-controller U, stores U at J+0x228, and U+0=0xc5c150. Additional error validation exists before allocation; this is not a claim that all input headers reach this branch.
- 0xc5c150 sets U+8 for phase 0 to 0xc5c600 when (*(J+0x260))+0x20 is nonzero, otherwise 0xc5cb90; phase 2 selects 0xc5cc20. These forward row processing to (*(J+0x238))+8 rather than themselves supplying channel semantics.
- The byte-output postprocessor setup stores 0xc3ecb0 at V+0, V=J+0x238. Its phase-0/J+0x6c=0 case copies (*(J+0x260))+8 to V+8 (0xc3ed56..0xc3ed61). Alternate phases/settings retain separate callbacks.
- The captured upsampler setup 0xc35ce3..0xc35d11 installs 0xc36160 at (*(J+0x260))+8. At 0xc3623a..0xc3624f this invokes (*(J+0x268))+8 with the component row pointers, the selected destination-row pointer array, and a row count.
Thus the useful output-format boundary is the converter T=J+0x268, not the initial J+0x228 row controller. This is a conditional chain through the captured setup, not an assertion that other setup paths cannot exist.

## Mode 12 converter candidates
T is allocated at 0xc20832..0xc20857. The setup uses numeric source encoding J+0x3c and requested mode J+0x40. The table at 0x1218d0 provides output component count; mode12 entry is 4.

At 0xc22622..0xc226c1:
- Source encoding 1 selects 0xc31fb0 through 0xc2284a.
- Source encoding 2 selects 0xc32fc0. The bit-test shortcut at 0xc22696 does not apply for mode12: bit12 is set in 0x10c4 and clear in 0x144.
- Source encoding 3 selects generic 0xc31860 or runtime-dispatched 0xc1c730, depending on the feature word obtained through TLS and static constant-address alignment checks. No semantic names are assigned to these source-encoding codes.

The signed-relative mode tables use index mode-6, hence index6:
- 0x63554 → 0xc31fd1 for single-component output.
- 0x6357c → 0xc32ff1 for three-component output.
- 0x6352c → 0xc31894 for computed output.

## Direct output stores
### Single component
0xc31fd1..0xc320df writes four bytes per input sample. The shuffle mask at 0x369d0 is `00 00 00 01`: the loaded component byte is repeated at offsets0,1,2; offset3 selects an initialized 0xff byte. The scalar-tail initialization at0x385c0 starts `00 ff`; the vector loop initializes all ones. Both yield `[a,a,a,255]`.

### Three component scalar path
At0xc331f9..0xc33214, output offsets0,1,2 receive component-row0[x], row1[x], row2[x], and offset3 receives immediate0xff. The repeated scalar loop also advances by4. This directly proves those scalar stores; the separate vector loop is retained as exploratory evidence rather than used to claim a fully audited implementation.

### Generic computed path
At0xc31894..0xc3199c let a,b,c be component rows0,1,2 at x; L=J+0x1a8; t20,t28,t30,t38 be pointers at converter offsets20,28,30,38. With the signed-width conversions shown in the instructions:
- out[4*x+0] = L[a + signed32(t20[c])]
- out[4*x+1] = L[a + signed32((qword(t30[c])+qword(t38[b])) >> 16)]
- out[4*x+2] = L[a + signed32(t28[b])]
- out[4*x+3] = 255
The table builders are deliberately outside this trace. These operations justify channel position and constant fourth byte, not RGB names or codec provenance.

## Runtime-dispatched vector stores
0xc1c730 reads a TLS feature word; if -1 it calls0x219e40 to initialize it. Under mode12, original R_X86_64_RELATIVE records prove:
- slot0xd29d10 →0x210ec0
- slot0xd29d60 →0x212720
The sign of the feature word's low byte selects the first candidate when negative and the second otherwise (0xc1c7b5..0xc1c7bf). The actual machine's feature result is unknown and was not queried by executing target code.

Both captured tails establish a constant fourth byte independently of their preceding arithmetic:
- 0x2110b9..0x2111cf: vector equality produces all-ones bytes; byte/word unpacking forms records `[computed0,computed1,computed2,0xff]`; dword/lane interleaving preserves those records. Full stores write128 bytes for32 records. Tails write64/32/16/8/4 bytes for16/8/4/2/1 records.
- 0x212935..0x212a28: the corresponding all-ones/unpack operations form the same four-byte structure; full stores write64 bytes for16 records, with32/16/8/4-byte tails for8/4/2/1 records.
This proves packing/fourth-byte policy for those statically identified targets. Their preceding arithmetic was not audited for equality with the generic converter, and no backend runtime selection or successful decoding is claimed.

## Finite remaining boundary
To attach RGB names rather than neutral computed-channel positions, the smallest useful next work is the immediate generic table builder at 0xc22c0a..0xc22dce for T+0x20/+0x28/+0x30/+0x38, followed only if needed by the native source-encoding assignment. An exact primary-source comparison could support naming, but resemblance alone cannot prove library provenance. Alternate row-controller/upscaler setup and non-byte precision paths remain separate cases; do not generalize this result to selectors1/2/4/5 or every selector3 input.

Evidence: [NATIVE-SELECTOR3-CALLBACK-EVIDENCE-2026-10-18.json](NATIVE-SELECTOR3-CALLBACK-EVIDENCE-2026-10-18.json). [Preceding mode boundary](NATIVE-SELECTOR3-CHANNEL-BOUNDARY-RECOVERY-2026-10-18.md). Raw ranges/reproduction scripts remain external.
