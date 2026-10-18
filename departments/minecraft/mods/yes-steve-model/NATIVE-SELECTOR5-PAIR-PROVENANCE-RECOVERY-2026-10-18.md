# Selector 5: nearest first-pair provenance

## Result

For original `libysm-core.so` SHA-256 `15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22`, the nearest explicit writer of context C's first pair is a 16-byte copy at VA `0x6192fc`, reached by the call at `0x4cc10c`:

`P = load64(J + 0x30); store16(C + 0, load16(P + 0)); store64(D + 0x20, load64(C + 0))`.

J is the separately allocated 0xc0-byte decoder context. C is the separately allocated 0xe0-byte context retained in provider stack+0x10. P is an object pointer loaded from J+0x30, not the original supplied S pointer. The extraction proves the copy chain, not the upstream producer or file-field meaning of P's two u32 fields.

## Exact addresses

- `0x4cad17/0x4cad1c`: request and allocate C (0xe0 bytes). `0x4cad91` initially zeroes C+0 through C+0xf; `0x4cad9d` stores C in stack+0x10.
- `0x4cada2/0x4cada7`: separately allocate J (0xc0 bytes); `0x4cadac` sets r13=J. `0x4caf6f` stores J in stack+0x18. `0x4cb350` restores that saved J during the preceding decode loop.
- `0x4cae4b/0x4cae54`: read original S+0x8 and S+0x18 for the input adapter. `0x4cae4f` saves S in stack+0x78. Decoder setup includes the call `0x4caecc -> 0xb202b0`; upstream parsing/codec work is outside this subtrace.
- `0x4cc0fe`: rsi=load64(J+0x30), named P here.
- `0x4cc102`: rdi=C from stack+0x10. `0x4cc107`: edx=0xff. `0x4cc10c`: call 0x619290. `0x4cc111–0x4cc113` requires its return value zero on the output path.
- `0x6192a1`: r13=P. `0x6192a4`: rbp=C. `0x6192f7`: xmm0=load16(P+0). `0x6192fc`: store16(C+0,xmm0), covering both u32 fields at C+0 and C+4.
- `0x4cc165`: restore C to r13; `0x4cc16a`: restore S to r14. D is restored from stack+0x80 at `0x4cc13c`.
- `0x4cc1a5`: rax=load64(C+0); `0x4cc1a9`: store64(D+0x20,rax).
- Independently, `0x4cc1ad/0x4cc1b1/0x4cc1b6` compute the allocation size from S+0x20 and S+0x24 using 32-bit multiply and shift: `zero_extend(low32(4 * S20 * S24))`. This does not establish equality with C's copied pair.

## Immediate helper check

The complete bounded copy function `[0x619290,0x619a90)` was inspected. Its later direct stores target other C fields or independently pointed-to subobjects. It invokes two immediate C helpers:

- `[0x619a90,0x619c40)` reads the first two u32 fields at `0x619a9b/0x619aac`, sizes separately allocated payload buffers, and writes pointer/stride/ownership fields. No direct write to C+0 or C+4 is present.
- `[0x618e30,0x619290)` reads the first two u32 fields and copies rows through pointers at C+0x18, +0x20, +0x28 and +0x40. No direct write to C+0 or C+4 is present.

This is a static ordinary-object-layout provenance claim, not a proof against malformed-pointer aliasing or memory corruption. Allocator/free/copy primitives and recursively copied subordinate objects are not a new codec trace.

## Boundary and unresolved facts

Stop at `P = load64(J+0x30)`. Its first-pair producer requires following the larger decode path, including callbacks and codec-specific work; that expansion was not performed. No source byte offsets, endian rules, codec identity, dimensions equality, semantic field names, or transformed-header relation are established. The fields are two 32-bit values because the consumer/helper accesses them that way; naming them exact file header width/height would exceed this receipt.

No native/JVM execution, emulation, asset processing, unpacking, or repository modifications were performed. Only 7 bounded original-file ranges totaling 4,693 bytes were extracted outside the repository. The earlier provider window is independently checked against the pinned original image.

## Reproduction and hashes

Run `PYTHONDONTWRITEBYTECODE=1 python reproduce.py --check` from this directory. It rechecks the original-image hash, all 7 binary/assembly windows, and 16 exact instruction-byte assertions. Verification result: PASS.

Evidence JSON SHA-256: `32b74636131856f4811b421d489d2c137820fdd9b32d33ac5ba250d999e41521`.

Per-range source backing and binary/assembly hashes are in `evidence.json`; all package-file hashes are in `SHA256SUMS`.

Evidence: [NATIVE-SELECTOR5-PAIR-PROVENANCE-EVIDENCE-2026-10-18.json](NATIVE-SELECTOR5-PAIR-PROVENANCE-EVIDENCE-2026-10-18.json). [Provider boundary](NATIVE-PROVIDER-OUTPUT-FORMAT-RECOVERY-2026-10-18.md). Raw ranges/reproduction scripts remain external.
