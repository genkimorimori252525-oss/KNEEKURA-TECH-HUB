# Mode 1 conditional fourth-byte callback contract

Source: original libysm-core.so SHA256 15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22. Static-only evidence; original virtual addresses. All extracted ranges are verified against original PT_LOAD file backing in manifest.json. No target/JVM execution, asset access, or repository edits.

Names: C is the callback first argument, K = pointer at C+0x38, O = pointer at K+0. Mode = DWORD O+0. Names alpha/output/row are descriptive inferences from the byte-addressing, not recovered type names.

## Setup and invocation

- 0x593841/0x593845 zero K+0x50..0x6f, including K+0x60 and K+0x68.
- Mode 1 belongs to the bit mask 0x103a at 0x593826..0x59382f. It follows the path with r13=0. Setup must first succeed at call 0x593858.
- For C+0x88 == 0 (test 0x5939ec), the selected main callback is installed at K+0x58; at 0x593d92..0x593dab mode 1 reaches 0x59437a. Since mode 1 < 11, the lea/cmov/store at 0x59437a..0x594390 writes K+0x60 = 0x596df0.
- 0x5937cc invokes K+0x58, preserves its EAX as n, then 0x5937d1..0x5937e2 invokes non-null K+0x60(C,K,n). The third argument n is not used by 0x596df0; this callback instead reads C row/width/height fields. K+0x20 is advanced by n afterward (0x5937e4).

## Unscaled branch, mode 1

- 0x596df3..0x596dfd reads source S = [C+0x98]. If S == NULL, it returns without output stores.
- 0x596e0e..0x596e31 reads y=[C+8], w=[C+0xc], h=[C+0x10], O=[K+0], and mode=1. The test for mode 4 or 9 is false, so alpha-first flag bpl=0.
- When [C+0x58]==0, y and h are unchanged. Otherwise 0x596e37..0x596e68 adjusts the source/row/count: if y !=0, S-=signed [C+0], y'=y-1, provisional h'=h+1; if y==0, y'=0, provisional h'=h. If [C+0x80]+y+h != [C+0x84], h'=h for y!=0 or h-1 for y==0.
- At 0x596e6a..0x596e87, D=[O+0x10]+signed(y')*signed[O+0x18]+3. The +3 is explicit: mode 1 gives !(mode==4||mode==9)=1, multiplied by 3 at 0x596e83.
- At 0x596e8a..0x596e91, helper [0xd35d38] receives (S, signed[C+0], w, h', D, signed[O+0x18]).
- For w>0 and h'>0 the helper copies source byte S[row*sourceStride+x] to D[row*outputStride+4*x]. Therefore the callback overwrites byte 3 of each four-byte destination pixel with source-plane bytes. It neither produces nor proves any particular values for those bytes. Without S it does not overwrite the main callback's fourth-byte values.
- Mode 1 always skips the later helper [0xd35d30] due to the unsigned comparison at 0x596e9c..0x596ea9. No extra invocation of that color-transform helper is taken by this callback for mode 1.

## Byte-scatter helper implementation and selection

- Setup stores 0x597610 to global 0xd35d38 at 0x5943e1..0x5943e8. CPU-dispatch branch stores 0x5b4c00 at 0x594490..0x594497 instead. This report does not execute CPUID or claim which branch would run on a particular machine.
- 0x597610: guards width and height; 0x597670..0x59769c copy four source bytes to D+4*x + {0,4,8,12}. Tail 0x5976c0..0x5976c5 copies the remaining bytes. Row increments at 0x597650..0x597653 use source and output strides.
- 0x5b4c00: scalar stores at 0x5b4d54, 0x5b4d84/0x5b4d91/0x5b4d9b/0x5b4dab and smaller-width paths have the same four-byte spacing. Vector path uses zero-extended source bytes and MASKMOVDQU at 0x5b4ca8/0x5b4cb4/0x5b4cc1/0x5b4ccf. Mask at original VA 0x3c5d0 is ff000000ff000000ff000000ff000000, selecting only the first byte of each 4-byte slot relative to D; because D already has +3, these are destination fourth bytes.

## Scaled setup alternative (bounded finding)

- If [C+0x88] !=0, mode 1 follows 0x593e2f..0x594049, allocates/setup state and ultimately writes K+0x60=0x594b90 at 0x59433f..0x594346 and K+0x68=0x595250 at 0x594350..0x59436c.
- 0x594b90 is a no-op if [C+0x98]==NULL or main callback count<=0 (0x594ba8..0x594bba); it delegates pending rows to K+0x68 at 0x594bed.
- 0x595250 computes destination base plus output-row*O.stride, then mode 1 adds 3 at 0x5952a7..0x5952dd. At 0x595329..0x59533d it copies one intermediate byte row into every fourth destination byte through the same [0xd35d38] helper. It skips mode-7..10 color transformation for mode 1 at 0x5953af..0x5953b4.
- Intermediate resampling kernels are deliberately not traced. This only establishes where already-produced intermediate plane bytes are stored.

## Limits

This conditional callback contract does not establish that C+0x98 is non-null for a particular asset, that any decode succeeds, that all output pixels are covered, or that source-plane values are always255. It is not a complete codec recovery or an executed verification.

Evidence: [NATIVE-SELECTOR4-FOURTH-BYTE-EVIDENCE-2026-10-18.json](NATIVE-SELECTOR4-FOURTH-BYTE-EVIDENCE-2026-10-18.json). [Provider boundary](NATIVE-PROVIDER-OUTPUT-FORMAT-RECOVERY-2026-10-18.md). Raw ranges and reproduction artifacts remain external.
