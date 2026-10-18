# Decoder resolver 0x576990: CPU table selection and candidate tests

The resolver's complete immediate body [0x576990,0x576b10) selects among seven statically relocated tables. No dynamic-library loader call, environment-variable lookup or unresolved literal string appears in this body. This statement does not extend to all transitive helper implementations.

## Returned table choices

Each table is 0x30 bytes: required feature mask at +0, label pointer at +8, and function pointers at +0x10/+0x18/+0x20/+0x28. Exact ELF R_X86_64_RELATIVE relocations establish all 35 pointer slots. Labels are original NUL-terminated literals, not algorithm-name guesses.

| Table | Required mask | Literal label | +0x28 target |
|---|---:|---|---|
| 0xd1dd90 | 0x400 | avx2 | 0x1db0e2 |
| 0xd1ddc0 | 0x200 | xop | 0x1dbe8a |
| 0xd1ddf0 | 0x100 | avx | 0x1dcd38 |
| 0xd1de20 | 0x20 | ssse3 | 0x1ddaf5 |
| 0xd1de50 | 0x8 | sse2 | 0x1de981 |
| 0xd1de80 | 0x1 | x86 | 0x1df17e |
| 0xd1deb0 | 0 | generic | 0x576430 |

## Exact selection and failure behavior

0x5769a1 loads cached qword feature mask 0xd35d00. If zero, 0x5769ad calls 0x1df431, and 0x5769b2..0x5769b4 zero-extend EAX and store the result. A pre-existing nonzero cached value bypasses this computation.

0x5769bb starts at the first table. NOT of the feature mask and TEST against each required mask implement `(required & ~features) == 0`. Ineligible entries advance by 0x30 at 0x576ae7. Eligible entries are published to global 0xd2ff30 at 0x5769e0 BEFORE testing.

The resolver generates 0x800 bytes of deterministic arithmetic test data on its stack (0x5769e7..0x576a21), then calls 0x574b60 twice with the same source and destination pointers differing by one byte. It calls internal code 0xd13ba0 after each of these calls. It generates a shifted copy of the deterministic test bytes (0x576a66..0x576aa3), then calls 0x574b60 twice more with source shifted by one byte, once for each destination alignment. All six 32-bit return values are combined by OR. These are internal candidate-check dependencies; no helper or backend was run in this research, and full helper contracts remain outside scope.

At 0x576ad8 the final OR establishes flags; the intervening MOV at 0x576adb preserves them. Zero branches to 0x576afb and returns the candidate table. Nonzero advances unless the current table's required mask is zero. In that terminal generic case, 0x576af9 clears RBX and the resolver returns null.

Important failure boundary: candidate publication happens before testing. If every eligible candidate fails including generic, this resolver returns null while its last store leaves global 0xd2ff30 pointing at the generic table. No rollback to the original lazy table is visible here. This is a static state transition, not evidence that any candidate test fails or an installed process reaches it. Ordinary global stores also do not establish concurrency/once semantics.

## Concrete CPU and OS-state dependency

The complete feature helper [0x1df431,0x1df5a0) contains CPUID instructions and XGETBV; it makes no calls. It initializes feature accumulator ESI=1, checks CPUID leaf 0, then leaf 1 on the usual path. Relevant table-mask producers include:

- Mask 0x8: CPUID leaf 1 EDX bit 26 (0x1df4de..0x1df4e6).
- Mask 0x20: CPUID leaf 1 ECX bit 9 (0x1df4c8..0x1df4d0).
- Mask 0x100: leaf 1 ECX bits 27 and 28 must be set, then XGETBV(ECX=0) low EAX must include mask 0x6 (0x1df4ff..0x1df526).
- Mask 0x400: after that gate, leaf 0 maximum >=7 and CPUID(7,0) EBX bit 5 (0x1df52c..0x1df542).
- Mask 0x200: after the earlier XGETBV gate, maximum extended CPUID leaf >=0x80000001 and that leaf's ECX bit 11 (0x1df564..0x1df593).
- Mask 0x1 is initially set and retained. Generic mask zero is always feature-eligible.

The helper also computes other feature bits not required by these seven tables. Its early special branch at 0x1df450 tests maximum basic leaf against 0x500, ORs mask 2 and exits when nonzero; it is preserved as literal control flow without assigning a CPU-vendor meaning. No host CPUID or XGETBV instruction was executed.

## Scope and reproducibility

reproduce.py verifies the original SO SHA256, extracts three bounded code ranges, checks all table relocations and seven literal labels, and links the two prior receipts without modifying them. evidence.json records exact ranges/backing offsets and hashes. Neighboring exploratory disassembly is not treated as a function-boundary claim.

Backend labels resolve CPU implementation choices; they do not identify the transformation primitive. The exact remaining implementation boundary is the selected table's +0x28 target above. No backend was substituted or assumed successful; no parser expansion, target execution, JVM execution, assets or repository changes occurred.

ABI wording retained for the earlier parser boundary: the decoder wrapper does not inspect a status register after the parser's normal return. This does not establish that a failed Boolean was ignored; the parser may have a void/exception-based contract.

Evidence: [NATIVE-DECODER-RESOLVER-EVIDENCE-2026-10-18.json](NATIVE-DECODER-RESOLVER-EVIDENCE-2026-10-18.json). Reproduction scripts and raw binary ranges remain external.
