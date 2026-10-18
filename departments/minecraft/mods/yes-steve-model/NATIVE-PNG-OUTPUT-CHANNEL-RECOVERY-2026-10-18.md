# Selector 2 PNG output: channel contract

## Result
Selector 2 requests and returns an RGBA8-format buffer on its successful output path: byte offsets 0,1,2,3 are red, green, blue, alpha. The conversion preserves component values independently; it does not premultiply RGB by alpha. The pointer join, requested mode, format dispatch and actual stores are supported by original bytes. This is a static format contract, not evidence of an actual image successfully decoding. No result is generalized to selectors1/3/4/5.

The semantic bridge is the dated primary [W3C PNG Recommendation, 24 June 2025](https://www.w3.org/TR/2025/REC-png-3-20250624/), sections4.5,6.1,6.2 and11.2.1. It assigns type6 to RGB followed by alpha and type4 to grey followed by alpha; type2 is RGB and type3 palette indices. PNG samples are unassociated with alpha. This reference supplies field meanings only; no particular codec library provenance or source-code identity is asserted. It was read via web tool2026-10-18. No library match was necessary.

## Requested mode and actual output pointer
Within provider4ceab0,4ceb82 loads the immediate pair (6,8) into rax.4cebe8 stores it at requested format stack+128/+12c.4cebdd sets conversion flag stack+d4=1. The header helper fills actual source type and depth at stack+160/+164 from IHDR offsets+19/+18 (4ea6df..4ea6ed).

At4cfd16 the enabled conversion gate compares requested and source formats. If all compared format fields agree, the already-produced r13 buffer goes directly through4cf265 to output. Otherwise requested(6,8) takes4cfe0f..4cfe94: allocate a replacement r14, then call4e7e90 with rdi=new output,rsi=old r13,rdx=requested format stack+128,rcx=source format stack+160,r8d=IHDR width,r9d=IHDR height. At4cff50..4cff6d, the old r13 is freed, zero status marks success, r13 becomes r14, and control rejoins4cf265. Successful4cf2c6 stores that r13 into D+8.4cf2d0/+d5 stores IHDR width/height into D+20/+24. Thus the converter writes the buffer returned to the geometry path; it is not a detached temporary.

The requested-format fields are fixed by this provider's explicit setup. Full inflater/filter/interlace validation is outside this receipt; statements below describe the successful conversion contract for valid source-format state.

## Four-byte stride and size
4e7eb7..4e7ebd multiplies zero-extended uint32 width and height as64-bit N. The converter processes N sequential pixels, producing four consecutive bytes per pixel. Requested-format allocation4cfe32..4cfe62 uses component table entry6=4 and bitdepth8, reducing exactly to4*N within the valid-size domain. Table67bbc is (1,0,3,1,2,0,4).

D+10 and D+18 are recorded separately as zeroExtend(low32(4*width*height)) at4cf2ae..4cf2cb. Therefore the recorded size and mathematical allocation agree only without32-bit product overflow; this report does not infer missing size checks or runtime safety from the format contract. The natural contiguous row stride is4*width. The final converter preserves incoming linear pixel order. Full PNG reconstruction/orientation was not retraced, so this receipt does not separately validate decoder row ordering or Adam7 handling.

## Actual conversion stores for requested type6/depth8
4e827f..4e82bf selects the dedicated8-bit destination path and dispatches by actual source type using signed-relative table597ec:
0→4e82c1,2→4e8697,3→4e863b,4→4e86e9,6→4e8718. Invalid1/5 go to the return boundary; prior header validation is not replaced by this table.

| source | directly supported behavior |
|---|---|
|type6,8bit|4e8718..4e873e copies4*N bytes unchanged. The provider can also bypass conversion entirely for equal format.|
|type6,16bit|4e8faa..4e8fc9 takes source offsets0,2,4,6 and writes output0,1,2,3; paired loop4e8f40 has the same operation. These are the high bytes of four big-endian samples.|
|type2,8bit|4e9676..4e9687 copies source RGB to output0..2 and writes255 to+3.4e96b0..4e96e9 optionally makes+3 zero on full equality to the transparent RGB key.|
|type2,16bit|4e89bc..4e89d9 takes source offsets0,2,4 as RGB high bytes, defaults alpha255; subsequent comparisons use complete16-bit samples against the key and write alpha0 on equality.|
|type4,8bit|4e8ead..4e8eba reads grey/alpha and shuffles with original369d0 bytes00 00 00 01: output(g,g,g,a).|
|type4,16bit|4e8f25..4e8f38 writes source0 to output0..2 and source2 to output3.|
|type0,8bit|4e9402..4e9413 expands one grey byte into RGB; seed385c0 and shuffle369d0 give alpha255.4e9423 onward optionally zeros alpha for the transparent key.|
|type0,16bit|4e8619..4e862f duplicates the high grey byte, with full16-bit transparent-key comparison at4e85ef..4e8607.|
|type0,1/2/4bit|4e8b65..4e8c92 extracts the packed sample MSB-first, computes floor(255*sample/((1<<depth)-1)), duplicates it to RGB, and uses key equality for alpha0/255.|
|type3|4e8de9..4e8df1 copies the indexed four-byte palette record. Packed indices use4e87a1..4e8887, also copying whole records.|

The source sample meanings follow the cited PNG specification; the order, truncation, replication and alpha placement are independently confirmed by stores. There is no gamma conversion, blending or RGB-by-alpha multiplication in these selected format-conversion paths. No claim is made about display color management elsewhere.

## Palette and transparency provenance
Provider chunk recognition4ceea3..4ceee1 recognizes PLTE and calls4ea870 on the source-format state.4ea950..4ea994 transfers each PLTE triple in original order into palette bytes0..2 and writes255 to byte3. The helper first initializes the256-entry allocation to(0,0,0,255).

The tRNS branch4cef18..4cef78 distinguishes source0/2/3. For indexed input,4cf22a..4cf23e copies each tRNS payload byte to palette[4*i+3], leaving RGB untouched.4cf07a..4cf105 supplies transparent keys for source2/0. This closes palette byte3 as alpha rather than an unspecified fourth byte.

## Implication and stopping boundary
For selector2 only, the earlier classifier's buffer[4*(y*W+x)+3] is the RGBA8 alpha byte and W/H come from IHDR. Consequently the earlier proven classes can be described on this provider path as empty/all-zero-alpha→0, any intermediate-alpha→1, mixed0/255→2, all255→3, subject to its original bounds and numerical domain. This does not establish that any real asset selected provider2 or decoded successfully.

No PNG decompression/filter implementation, original assets, native/JVM execution, or repository edits were used. Next independent boundary, if needed, is another selected provider's output format; selector2 channel ordering is closed. Geometry coordinate naming is outside this receipt.

## Evidence
Original SO SHA25615d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22. reproduce.py verifies14 original-byte selections,6 exploration windows, exact component-count table and prior provider receipt unchanged. The converter selection includes some unrelated output-mode branches for reproducible dispatch context; only requested(6,8) paths are interpreted here.

Evidence: [NATIVE-PNG-OUTPUT-CHANNEL-EVIDENCE-2026-10-18.json](NATIVE-PNG-OUTPUT-CHANNEL-EVIDENCE-2026-10-18.json). [Preceding contract](NATIVE-PROVIDER-OUTPUT-FORMAT-RECOVERY-2026-10-18.md). Raw ranges/reproduction scripts remain external.
