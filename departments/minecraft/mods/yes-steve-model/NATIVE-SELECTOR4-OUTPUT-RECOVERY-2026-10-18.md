# Selector 4 mode 1: output bounds and conditional fourth-byte policy

## Useful result
Selector4 must not be classified as universally fourth-byte255. A traced mode1 row-converter scalar path writes three computed bytes followed by255, but its subsequent callback copies a separate source plane into output byte3. The no-source-plane case leaves that byte unchanged. Mode1 bypasses the later color-transform callback on this traced unscaled branch.

The packed-output validator checks positive internal dimensions and destination capacity against the internal dimensions, rather than asserting equality with the supplied pair. Its exact mixed-width arithmetic matters: the capacity expression is64-bit, while the pitch-versus-row-width check uses a32-bit product/signed comparison. This is a static branch contract, not proof of runtime decoding success or arbitrary-integer memory safety.

## Source and evidence
Original SO SHA256 `15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22`. evidence.json and reproduce.py preserve original-byte windows and backing/hash information. Prior receipts remain unchanged. The separate [fourth-byte callback receipt](NATIVE-SELECTOR4-FOURTH-BYTE-RECOVERY-2026-10-18.md) supplies the fourth-byte callback evidence and its qualifications. No assets, target code, emulation or JVM were executed; no repository edits.

## Original output ownership and pair
4d3ff0 constructs D with allocation count low32(4*S.u32[20]*S.u32[24]), copying S+20/+24 to D+20/+24. Local O=stack+250 has:
- O+0: mode1
- O+0xc: external-buffer flag1
- O+0x10: D+8 output pointer
- O+0x18: low32(4*S.u32[20]) pitch
- O+0x20: allocated count, zero-extended
K=stack+198 stores O at K+0. I=stack+c0 stores K at I+38; provider installs I callbacks5937b0,593800,594540 at4d4239..4d4275. There is no observed conversion of D's supplied pair into decoded dimensions in this bounded path.

5853e0 is an input/header parser, not the final byte-output routine. Original comparisons include RIFF at input0, WEBP at input8, VP8X, VP8-space, VP8L, and ALPH. These literal checks establish the format-specific entry without assigning semantics to every branch. The initial call4d4167 supplies null width/height output pointers and a separate local parsed descriptor. Later provider calls585b80 with I+0/I+4 and O (4d44c6..4d44e4; alternate4d4ae3..4d4b01).

## Exact packed bounds at585b80
First, signed width w>0, signed height h>0 and O!=null are required. Options may alter dimensions before O+4/O+8 stores at585cf3. O+0 must be unsigned<13. External flag1 takes the validation path without allocating a replacement output.
For mode1, table6db00[1]=4. At585e71..585ec7:
- p is the signed32 O+18 pitch.
- a is the32-bit absolute-value sequence `neg; cmovs`, then used via its zero-extended register. INT_MIN therefore remains0x80000000 as an unsigned magnitude.
- needed = zeroExtend(a)*(signedExtend(h)-1) + signedExtend(w)*4, using64-bit operations.
- needed must be unsigned<= O.u64[20].
- signed32(a) must be >= signed32(low32(4*w)).
- O+10 must be nonnull.
Failure returns2; passing these checks leads to0 unless later option processing changes the outcome.
For ordinary non-overflow positive widths/pitches this reads as abs(p)>=4*w and capacity>=abs(p)*(h-1)+4*w. Do not silently replace the machine-width checks with that mathematical inequality for arbitrary values. No supplied/internal width or height equality is enforced by these checks.

## Traced row path and stores
5937b0 calls K+58, then optional K+60 with its returned row count, then accumulates K+20. 593800 selects these callbacks using mode and I flags. For mode1 with I+88=0 and I+58=0, the captured packed-row branch keeps K+58=595fc0. If I+58 is nonzero, 593c17..593c1e replaces it with596090, which uses table d35fd0[mode] instead. This additional condition is important; no actual provider-default selection is assumed. Other I+88/setup paths remain distinct.

595fc0 loads a converter from table d360b0[O.mode]. It computes the first output row as O.data + I.row*O.pitch and increments by signed O.pitch for each processed row. It passes width I+0xc, and three input row pointers I+18/+20/+28. For mode1, setup writes generic candidate5a7470 to d360b8 at593aab..593ab2. Runtime capability checks may replace it with5ca010 at593b44..593b4b; another shown capability branch changes other slots. No actual runtime selection is claimed.

The direct scalar portion of5a7470 writes calculated byte0 at5a74fa, byte1 at5a7544, byte2 at5a757a, and literal255 at5a757e. The second record occupies+4..+7, with+7=255 at5a7620; output advances8 for two records. The single-record tail also sets+3=255 at5a7709. The first three values are derived from the supplied three input components with integer arithmetic and clamps. Their color names are deliberately left neutral. Its internal vector branch at5a771d and replacement5ca010 are not audited here; scalar evidence is not a claim about all of the function's paths.

## Subsequent fourth-byte overwrite
The companion alpha-subtrace establishes the bounded unscaled mode1 callback:
- Setup59437a..594390 installs K+60=596df0 when I+88=0.
- Null I+98 source pointer causes no stores.
- Otherwise destination starts O.data + adjustedRow*O.pitch +3, with width I+0xc and adjusted row count. It calls the scatter function through d35d38.
- Static generic scatter597610 stores source[x] to destination[4*x], preserving the other three bytes. Setup can substitute CPU candidate5b4c00; its scalar/vector stores were also audited in the companion receipt, using original mask3c5d0 = ff000000 repeated to select every fourth destination byte. Runtime selection remains conditional.
- Mode1 skips the later d35d30 color-transform call at596e9c..596ea9.
Thus the traced final fourth byte can be supplied by the separate plane, not merely the converter's255 initializer. The callback does not by itself establish the source plane's decoded provenance or a universal semantic alpha label. The scaled alternative is separately identified in the companion report and is not generalized from the unscaled branch.

## Finite boundary
This receipt is sufficient to reject an always255 assumption and to preserve the supplied-pair versus internal-width/pitch distinction. It does not close every selector4 path. The immediate remaining output boundaries are (a) 596090 and d35fd0[1] for I+58 nonzero, or5a771d vector branch /5ca010 replacement when I+58=0, (b) source-plane provenance before I+98, and (c) the alternate provider branch4d4b10 onward after the second585b80 call, which uses separate decode/output control. Resolve one boundary only when a consumer claim actually requires it; no full codec reconstruction is implied.

Evidence: [NATIVE-SELECTOR4-OUTPUT-EVIDENCE-2026-10-18.json](NATIVE-SELECTOR4-OUTPUT-EVIDENCE-2026-10-18.json). [Provider boundary](NATIVE-PROVIDER-OUTPUT-FORMAT-RECOVERY-2026-10-18.md). Raw ranges and reproduction artifacts remain external.
