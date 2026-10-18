# Decoder transform: initial lazy dispatch boundary

The original ELF independently explains the checkpoint values. Both pointers have R_X86_64_RELATIVE (type 8, symbol index 0) relocations: global slot 0xd2ff30 has addend 0xd1dee0; table slot 0xd1df08 (0xd1dee0+0x28) has addend 0x574b10. Their raw file values are zero. Relocation adds the image load bias. This confirms the initial table chain, not the final selected transformation implementation.

## Immediate target and interface

Source-backed range [0x574b10,0x574b5e) is a lazy dispatch trampoline:

- 0x574b18..0x574b21 save RCX, RDX, RSI and RDI in callee-saved registers.
- 0x574b24 calls resolver 0x576990. Its body is outside this continuation.
- 0x574b29..0x574b2c test its returned RAX table pointer.
- On nonzero, 0x574b2e publishes RAX to global 0xd2ff30, and 0x574b35 loads qword[RAX+0x28]. The four arguments are restored at 0x574b39..0x574b42; 0x574b50 tail-jumps to the loaded target.
- On zero, 0x574b52..0x574b5d restore the stack/registers and return. This trampoline does not write the output on that branch. Resolver side effects and reachability of this branch are unproven.

The preserved caller [0x4dc4aa,0x4dc4c4) supplies K, K+0x20, a stack output temporary, and 0x1e. The trampoline forwards all four unchanged; it performs no input copy, input free, pointer/length validation or round-count bound check. No transformation primitive can be assigned from this forwarding code. The meaning and bounds of these arguments remain dependent on the selected implementation.

The checkpoint table is therefore the initial unresolved dispatch table. A zero-instruction read of that checkpoint alone cannot identify the later resolver result or final +0x28 implementation. The table update here is an ordinary store; this small scope establishes no synchronization guarantee.

## Evidence and limits

reproduce.py reads the pinned original SO, verifies both relocations, extracts two exact ranges and emits evidence.json plus source-backed objdump excerpts. It links the existing shared-decoder evidence and the separate zero-instruction checkpoint proof by SHA256. The pre-existing shared-decoder receipt is unchanged. No original target, resolver, payload, JVM or callback was executed; no assets were extracted. The exploratory 0x574b10..0x574e00 excerpt includes neighboring code and is not used to infer this function's boundary or semantics.
