# Candidate-prefix stack guard: an untaken local branch

PRIMARY_STATIC_REVIEW_ONLY. Exact Linux image SHA-256 `15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22`. This resolves the local JB at 0x12c4638 identified in NATIVE-NEXT-ANALYZER-PLAN, using existing binutils evidence and scalar/byte-interval reasoning. Ghidra remains unused. Reaching this candidate from JNI still has the previous file-state assumption; the local condition proof does not establish runtime reachability.

## Known register/flag slice

The prefix at 0x12c3a51 resets the relevant registers from constants before its word/byte-dependent work. Explicit partial-register arithmetic yields EAX=0xffffff10 before the AX shift. Later DEC R9B yields 0x44, fixing SF=0 and ZF=0. The following rotate's undefined OF is not used: the subsequent one-bit rotate of a known zero R10B establishes OF=0. MOVZX does not change these flags, so SETG writes AL=1.

AX is then 0x2001. CWD makes DX zero, with the remaining RDX bits already zero from MOVZX; later zero rotates/AND retain zero. CWDE/subtraction leave RAX=0x2001. The callee's two CBW instructions replace AX with the sign-extension of AL=1, leaving RAX=1. The relevant known inputs are therefore RAX=1 and RDX=0, irrespective of the loaded data word and byte. The [Intel instruction reference](https://cdrdv2-public.intel.com/782151/253667-sdm-vol-2b.pdf) supports the operand-width and flag-preservation rules; the result values come from the pinned prefix.

## Stack intervals, not guessed memory contents

With those inputs, the callee's first store at 0x12c460b writes eight zero bytes at current RSP. The next unknown-value store starts at RSP+8+CL, with CL restricted to 0…255 because its upper register bits were zeroed and only the byte was updated. Its start is therefore at least RSP+8. The word exchange affects only offsets 1–2.

The later shifted word is at offsets 6–7: neither intervening store/exchange can change it. It is zero. SHR by 15 leaves carry 0, so JB at 0x12c4638 is NOT taken and the local ordinary path is fallthrough 0x12c463e, not 0x1186a8d. Unknown saved-register values written elsewhere on the stack do not invalidate this interval argument. Faults/interference or altered entry bytes remain outside the assumptions.

This proof does not require assigning values to the loaded word/byte or guessing an inherited carry. It also does not remove the separate uncertainty about whether the earlier file-state return candidate is the actual runtime destination.

## Verification

The two full prefixes (207 and 61 bytes) are hash-pinned. Test-first checks were observed failing before the corresponding helpers existed, then passing after implementation. Six tests cover known register inputs, all 256 CL values with representative word writes, a nonzero-store counterexample that reverses the carry, input-domain rejection and changed/missing prefix rejection. The finite CL sweep supports the interval proof, not a full native-state test. Exact-image recomputation agrees.

No native target or machine emulator was run; the helper models only selected scalar values and three byte writes. No tool installation, payload unpacking, code patching or protected-model decoding occurred. Independent semantic review NOT_RUN; Java-native bindings and whole native implementations remain unresolved. Continue from 0x12c463e only with the same explicit reachability assumptions.
