# DT_INIT prologue: three predicates and first return candidate

Status: PRIMARY_STATIC_REVIEW_ONLY; independent semantic review NOT_RUN. [Scalar/interval evidence](NATIVE-INIT-PROLOGUE-2026-10-18.json), [105-range Ghidra/GNU cross-check](NATIVE-INIT-PROLOGUE-GHIDRA-CROSSCHECK-2026-10-18.json). This pass investigates the separate DT_INIT entry, not the JNI_OnLoad path.

## Recovered boundary

From DT_INIT at 0x152eb19, three conditional transfers are taken under the pinned-path assumptions:

1. JNE at 0x174d06f -> 0x166685c.
2. JAE at 0x16668ff -> 0x17cfc5e.
3. JAE at 0x16b05fe -> 0x167addc.

The first rewritten return at 0x171695b has file-state candidate load_bias + 0x1499584. Its next prefix ends at JB 0x14995c7 -> 0x1603de3; that predicate is unresolved in this cohort. This is not completion of DT_INIT or a proof that later initialization preserves the JNI candidate data.

## Stack value that initially looks unknown

Let S be RSP at DT_INIT entry. The fixed prologue writes literal 0x162e9a61 at S-8. After its captured PUSH/CALL/POP/LEA stack adjustments, Q (RSP at 0x166685c) equals S-128. The later DWORD read at Q+0x78 therefore reads that literal at S-8, not an unknown incoming register. The retained model checks the stack delta and relevant byte intervals.

At the first predicate, EBP starts as 0x953b89a2. NEG RBP followed later by NEG BP leaves BP=0x89a2, so ZF=0 and JNE is taken.

For the second predicate, the initial pushed 0x2c82613f supplies a DWORD value 0x2c to the seven-bit SAR; carry is zero. Stack exchanges reduce RCX to zero, then BTC ECX,ECX makes it one. The word XADD/shift sequence and the known saved literal yield R11D=0xd99b4c01. The final R9+RCX has no unsigned overflow, so JAE is taken. Variations of the saved R15 value and load bias do not alter these results in the tested byte-interval model.

A later RSI-derived stack store uses offset 0x98 from that moment's RSP, not zero. It overwrites the old literal slot only after R11D has read it. The stack is subsequently repositioned to an aligned address derived from Q; normal stack availability is an assumption, not a measured runtime property.

## Data pointer, key, and return

Byte-swapping R11D gives 0x014c9bd9. Adding the derived load bias and later subtracting four identifies the next data word at load_bias+0x14c9bd5. The file word is 0xcd4bfbff.

The key calculation cancels load bias: the saved immediate byte rotation gives EDI=0xb499a397 before a 20-bit shift, whose outgoing carry is zero; the following SBB therefore leaves relative key 0x014c9bd9. This carry source is explicitly checked instead of assumed from an earlier instruction.

For the third predicate, the fixed EDI word/byte operations give EDI=0x927ce000 before BTC. EBX selects bit six, which is zero; JAE is taken. The data transform then gives signed delta 0xffde8fe9 (-2191383). The preceding pushed RDI has zero byte five, so the later byte shift supplies carry zero to ADC RSI,RAX. Adding the delta to load_bias+0x16b059b yields load_bias+0x1499584.

R10 is zero at the final store, so RSI is written to current RSP and consumed by RET 8. Total stack advance is 16 bytes.

## Limits and verification

None of the 9,114 known-width relocation writes overlaps the selected instruction ranges or this four-byte data word. The word is in a file-backed executable load region. These checks are not a general proof against runtime rewriting or external interference. Initializer-wide memory effects and JNI data immutability remain unresolved.

Ten scoped tests cover the predicates, saved-slot calculation, register/bias independence, key cancellation, changed data and changed/missing ranges. Exact-JAR replay matches. The separate expanded Ghidra manifest has 105 ranges / 940 instruction occurrences, all matching GNU addresses, lengths and bytes; all seven file-backed load regions match. Existing 73- and 83-range receipts remain frozen.

Only explicit scalar expressions and stack byte intervals are evaluated. The target library is never loaded for execution, no native emulator is used, no protection is patched, and no protected model content is processed. No central mapping or runtime-confidence promotion and no full-project CI occurred.
