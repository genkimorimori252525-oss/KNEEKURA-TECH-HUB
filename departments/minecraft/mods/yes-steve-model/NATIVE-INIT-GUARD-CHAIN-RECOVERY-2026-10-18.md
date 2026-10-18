# DT_INIT candidate: three further local predicates

Status: PRIMARY_STATIC_REVIEW_ONLY; independent semantic review NOT_RUN. [Scalar evidence](NATIVE-INIT-GUARD-CHAIN-2026-10-18.json), [expanded cross-check](NATIVE-INIT-GUARD-CHAIN-GHIDRA-CROSSCHECK-2026-10-18.json). Reachability depends on the earlier conditional DT_INIT return candidate.

## Results

JB at 0x14995c7 is taken to 0x1603de3; JNS there is taken to 0x14444e0; JA at 0x1444517 is taken to 0x174b8f0. These three local predicates do not require a concrete value for the newly loaded byte. Later use of that byte and its derived memory addresses is not thereby proven harmless.

- R10D is 0x3935 before SBB and EDI is 0xd19e3937. The preceding OR AL clears carry. The unsigned subtraction borrows and leaves 0x2e61fffe, so CF=1 and SF=0. NOT BL preserves the flags. Both JB and the following JNS therefore take their branches.
- CWDE writes EAX and clears upper RAX. Later byte/word changes do not set bit 63, so CQO yields RDX=0. PUSH RDX puts zero at stack byte four. XADD with R9B=0x36 returns that zero into R9B, leaving R9=0.
- A subsequent CQO clears intervening DL arithmetic. SBB EDX,0x462fd526 borrows for either possible incoming BTS carry. Writing EDX zero-extends RDX. The following 64-bit SBB RDX,R9 therefore leaves 0xb9d02ad9 or 0xb9d02ad8, with CF=0 and ZF=0. JA is taken in both cases. Treating the 32-bit intermediate as a sign-extended 64-bit negative value would be wrong.

## Boundary

Following the fixed direct CALL/JMP prefixes reaches RET 0x18 at 0x1539420. Its concrete destination is unresolved in this cohort. No claim is made that this completes initialization, that all memory operations are stack-only, or that the JNI candidate data is immutable.

Seven scoped tests passed, including both incoming carry cases, invalid carry values and changed/missing prefixes. Exact-JAR replay matches. A separate 112-range / 1013-instruction-occurrence Ghidra/GNU comparison matches addresses, lengths and bytes, plus all seven file-backed load segments. Earlier receipts remain unchanged.

Only explicit scalar expressions and a small byte-interval calculation are used. No target execution or native emulator has been used for this cohort; no central mapping promotion or whole-project CI occurred.
