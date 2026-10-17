# Post-return guards and third symbolic return

Status: PRIMARY_STATIC_REVIEW_ONLY; independent semantic review NOT_RUN. Exact artifact and instruction-range hashes: [evidence](NATIVE-POST-RETURN-GUARDS-2026-10-17.json). This extends the conditional [second return candidate](NATIVE-SECOND-RETURN-RECOVERY-2026-10-17.md); it does not establish runtime reachability.

## Two predicates

1. At 0xee9ad7, NEG CX immediately precedes JBE at 0xee9ada. For any 16-bit input, either the input is zero (ZF=1, CF=0) or nonzero (CF=1, ZF=0). JBE tests CF OR ZF, so the branch to 0x10d1774 is taken for every input, if the instructions execute normally. All 65,536 scalar inputs are checked; this is not native CPU execution.
2. The fixed prefix initializes EAX to 0x7d8ea0b6; CQO sets RDX=0, CWDE preserves low AX=0xa0b6, and SUB AX by the known-zero R10W leaves AX negative. CWD sets DX=0xffff; ROR DX by four leaves it unchanged. RDX is therefore 0xffff and MOVZX R11D,DL gives 0xff. After PUSH RDX, the OR address is exactly current RSP (RDX-0xffff=0). The 64-bit result is 0xffff, positive and nonzero: SF=0, ZF=0, OF=0. MOV, LEA and NOT preserve those flags, so JG at 0x10d179a is taken to 0xf0ae94.

## Third return remains symbolic

At 0xf0aec3 the store address is RSP + RDX*4 - 0x3fffc = RSP. RDI is stored there and consumed by RET at 0xf0aecb. The return advances the stack by eight bytes. RDI contains the result of ADD RDI,R11 at 0xee9aaf; R11 was sign-extended from a transformed third data word.

The concrete third destination is deliberately unresolved in this cohort. It depends on the data word and carried key entering this prefix. Do not reuse the second destination, assume a normal call-return continuation, or infer a model-loading function from these blocks.

## Verification and limits

Eight scoped tests cover the complete 16-bit NEG domain, zero/nonzero flags, fixed-register calculation, zero/negative OR counterexamples, and changed/missing instruction ranges. Re-capture from the exact JAR matches the stored evidence. Earlier 77-test checkpoint remains frozen, rather than rerunning unrelated cohorts for this local proof.

All memory operations are assumed to complete normally without external interference. Earlier writable-data file-state assumptions still apply. No target execution, native emulator, function recovery, binding recovery, central mapping promotion, or whole-project CI occurred. Artifacts and raw disassembly stay outside Git.

Primary instruction reference: [Intel SDM Volume 2B](https://cdrdv2-public.intel.com/782151/253667-sdm-vol-2b.pdf), NEG/OR/RET and flag semantics; conditional jump definitions in [Volume 2A](https://cdrdv2-public.intel.com/812383/253666-sdm-vol-2a.pdf). Results are derived from the pinned original image.
