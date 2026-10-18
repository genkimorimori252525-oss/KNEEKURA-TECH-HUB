# Selector 5: bounded output descriptor and fourth-channel stage

## Result
Selector5 requests eight-bit, four-byte output with channel offsets0,1,2,3. Its output dimensions and returned D+20/+24 pair come from context C, while allocation capacity and row pitch come independently from supplied S+20/+24. No equality between those pairs is established.

A directly traced fallback stage initializes output byte3 to255 when no usable separate source plane is available. If C+40 is nonnull and C+48 is nonzero, that stage copies/converts the plane into byte3. Eight-bit samples are copied exactly; wider samples are normalized into0..255 with float32 rounding/clamping. This is a conditional stage contract. The helper's fast dispatches and subsequent color-processing paths were not exhaustively audited, so neither a universal final fourth-byte policy nor an RGBA semantic label is claimed.

## Source / preservation
Original SHA256: `15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22`.
The local evidence.json/reproduce.py contains byte-verified VA windows. Previous receipts remain unchanged, including selector4's unresolved596090/table d35fd0[1] converter. Pair provenance is separately documented under [pair provenance](NATIVE-SELECTOR5-PAIR-PROVENANCE-RECOVERY-2026-10-18.md).
Only static original-file reads, extraction and disassembly were used; no original assets, decoder/native/JVM execution, emulation or repository edits.

## Output descriptor O and helper Q
At4cc13c/4cc165/4cc16a, r15=D, r13=C, r14=S. At4cc1a5..4cc1a9 C's first qword is copied to D+20. Allocation at4cc1ad..4cc1c6 is zeroExtend(low32(4*S.u32[20]*S.u32[24])).
O=provider stack+b8:
- O+0/+4 = C+0/+4
- O+8 =8
- O+c =1
- O+10 =2
- O+18/+1c/+24 =0 from zero initialization
- O+30 =D+8
- O+38 =low32(4*S.u32[20])
Other captured O fields start zero. No capacity value is placed in this descriptor.

4cc274 calls b2a220(O,Q), Q=stack+f8. For depth8/layout1, its jump table62b18 index1 targets b2a358. Result:
- Q+0 =1, Q+4 =4 (sample size and record step as used by later stores)
- Q+8/+c/+10/+14 =0/1/2/3
- Q+1c =255, Q+20 =float32(255)
These are numeric channel slots, not inferred RGB names.

4cc28e calls b2a430(C,Q+24). It accepts only source depths selected by bitmask0x11500 within0..16 (8,10,12,16), C+c in1..4, and C+10<=1, plus the documented source-code tests. Atb2a713..b2a721 it stores source sample step1 for depth8 and2 for wider depths at(Q+24)+c =Q+30. The provider additionally updates fields around Q+5c and zeroes the first three source-parameter fields for selected numeric source codes; these branches are preserved in provider_conversion_call.asm without semantic renaming.

4cc32a calls b2a7b0(C,O,Q,flag), where flag is0 unless C+40 is nonnull and C+50 nonzero, in which case it is2. This is distinct from the source-plane eligibility test using C+48 below.

## Conditional fourth-channel stage
The converter's early fast-path dispatch depends on source depth, source-code fields, the caller flag and callback tables. The trace stops short of assigning all callbacks or runtime path selection.

Atb2aca8 the fallback-stage entry branches around fourth-channel processing when the computed r13b OR r12b is nonzero. Otherwise it builds temporary T atstack+108 from O and Q:
- T+0/+4 =O width/height
- T+24 =O depth8
- T+28 =O data pointer
- T+30 =O row pitch
- T+34 =Q+14 =3
- T+38 =Q+4 =4
If C+40 and C+48 are both nonzero, T+8=C+8 source depth, T+10=C+40 source plane, T+18=C+48 source row pitch, T+1c=0, and T+20=Q+30 source step. It calls b2f350(T) atb2ad53.

When the source plane/stride is unavailable, the depth8 case entersb2af2a. The byte stores atb2af80..b2afad andb2afd0 write255 with step Q+4=4, starting O.data+Q+14 =O.data+3. Row increment is O+38 and loop dimensions come from O. Zero dimensions skip stores. No supplied-height or capacity comparison appears in these selected stage operations.

### Plane copy/conversion stores
b2f350 compares source depth and destination depth.
- Equal eight-bit depth branches to b2f627. Atb2f690..b2f6ad it reads one byte from source and writes it to destination; source step is T+20 and destination stepT+38=4. Initial destination is T+28+T+34=O.data+3; row increments are the respective source/output pitches.
- For source depth>=9 and destination depth8, b2f4b9..b2f4d3 prepares float32 source maximum (2^depth−1) and destination maximum255, then selectsb2f807. Atb2f870..b2f89e it reads a little-endian uint16, computes float32(sample/sourceMax*255+0.5), truncates to an integer, clamps to0..255, and stores a byte. Constant4835c is original float32(0.5). Steps and pitches are the same T fields.
The primitive stage thus preserves eight-bit plane values and scales wider ones. It does not itself prove that C+40 is a semantic alpha plane, that it is present for any particular image, or that later processing never writes the channel again.

## Pair and bounds consequence
Nearest pair writer: provider4cc0fe loads P=[J+30], then4cc10c calls619290(C,P). At6192f7/6192fc that helper copies the first16 bytes of P into C, including its first pair;4cc1a5/4cc1a9 later copies the pair into D. P's upstream producer/header semantics remain unresolved; no width/height header label follows from the copy alone. See the companion pair receipt.

C+0/+4 are used consistently for the returned pair and requested output iteration dimensions. Supplied S dimensions determine allocation and pitch. Passing O to these immediate helpers cannot by itself prove buffer-capacity sufficiency: no capacity was supplied in O. This is a missing verified invariant, not a claim that a vulnerability or runtime failure occurs. Upstream validation and all post-stage branches were not reconstructed.

## Concrete finite boundary
The fourth-channel stage is now reusable without inferring a universal provider policy. The next output-only boundary, if needed, is b2ae47 onward and the source-dependent fast dispatch around b2ccb1, to determine whether subsequent operations preserve or transform the initialized/copied fourth byte. It must stay tied to a specific source-code/depth case; expanding every table would exceed this bounded task. Selector4's separate596090 case remains unresolved and is not covered by selector5 findings.

Evidence: [NATIVE-SELECTOR5-OUTPUT-EVIDENCE-2026-10-18.json](NATIVE-SELECTOR5-OUTPUT-EVIDENCE-2026-10-18.json). [Provider boundary](NATIVE-PROVIDER-OUTPUT-FORMAT-RECOVERY-2026-10-18.md). Raw ranges/reproduction scripts remain external.
