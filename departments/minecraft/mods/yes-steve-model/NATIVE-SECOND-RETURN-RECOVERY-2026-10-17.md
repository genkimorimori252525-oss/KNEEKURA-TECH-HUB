# Linux native second stack-rewritten return

Status: PRIMARY_STATIC_REVIEW_ONLY. Independent semantic review NOT_RUN.
Exact artifact/image identities and fixed instruction-range hashes are recorded in [evidence](NATIVE-SECOND-RETURN-2026-10-17.json). No target execution or native emulator was used. This is a local static scalar proof, not a recovered native function.

## Result

After the [untaken candidate guard](NATIVE-CANDIDATE-STACK-GUARD-RECOVERY-2026-10-17.md), the fixed prefixes are 0x12c463e (13 bytes), 0xf9cc3c (69 bytes), and 0x1060bbd (137 bytes), ending at RET 8 at 0x1060c43. The final store writes RDI to the current stack top. RET consumes that value, then advances the stack by 16 bytes in total. Ordinary call-return fallthrough is therefore not the destination under these assumptions.

The earlier guard's zero-store/interval argument also leaves the word OR-ed into SI zero. SI enters this continuation at 0x89. INC RSI, SHL RSI by masked count 14, and ROL ESI by masked count 8 yield 0x22800000. The masked R10D constant has low byte zero; the SIL exchange leaves that low byte zero. NOT SI yields 0x2280ffff. Consequently the final store displacement is exactly 2 * 0x2280ffff - 0x4501fffe = 0.

RDI is set by ADC at 0x12c3ac6 and is not subsequently changed on these fixed prefixes. The scalar calculation derives carry zero from the preceding 64-bit ADD. Its symbolic destination is load_bias + 0x12c3a51 + sign_extend_32(decoded_second_word).

## Conditional file-state destination

The second data word at virtual address 0xd2cd4c has file value 0x3b7414a3. Using the preceding key 0xd2cd48 XOR 0x2040f8 = 0xf28db0, the captured XOR/add/byte-swap/rotate/add sequence yields 0xffc25fec, or signed -0x3da014. The resulting file-state candidate is load_bias + 0xee9a3d; that relative address is file-backed.

This requires BOTH data words at 0xd2cd48 and 0xd2cd4c to retain their file values. Writable-data initialization or other runtime changes remain unresolved. The first word's prior relocation check is not a check of the second word; second-word relocation overlap is explicitly NOT checked here. All memory operations must complete normally, with unmodified instructions and no external interference. Reachability is conditional on the preceding candidate proof. No binding, native implementation, semantic mapping or runtime correctness is promoted.

## Reproduction and next frontier

Run tools/native_second_return_ysm_265.py with --jar pointing to the exact external artifact and --out NATIVE-SECOND-RETURN-2026-10-17.json --check. The six scoped tests include changed SI, changed data, missing ranges and mutated ranges. Range hashes reject an altered instruction sequence; synthetic tests are not independent semantic review.

The first-transfer inspection at candidate 0xee9a3d found 35 instructions / 163 bytes (SHA-256 994988bacb9f6a24f7c0a63b0cf14c2c7f9a6f23604984a8f7e22eb4e998c79f), ending in JBE at 0xee9ada to 0x10d1774. That predicate is not resolved in this cohort. Next: trace its flag/data dependencies, using an approved static data-flow analyzer if needed to reduce further manual register bookkeeping. Raw artifact, native image, disassembly and analyzer projects remain outside Git.

Instruction semantics reference: [Intel SDM Volume 2B](https://cdrdv2-public.intel.com/782151/253667-sdm-vol-2b.pdf), including RET, shifts/rotates and partial-register operations. Conclusions above are derived from the exact artifact, not from public-source name equivalence.
