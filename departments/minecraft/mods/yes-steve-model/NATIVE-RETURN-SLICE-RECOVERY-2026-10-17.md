# Stack-rewritten return: a bounded symbolic target expression

PRIMARY_STATIC_REVIEW_ONLY. Fixed Linux image SHA-256 `15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22`. This advances the RET frontier at 0xfa14e5 from NATIVE-LOAD-FLAG-CHAIN. The target expression is resolved under the existing normal-execution assumptions; the concrete destination and native function meaning are not resolved.

## Constant register slice

The captured tail sets R11D=0x14df0f and R10D=0xd6bd2601. BTC toggles bit 2, giving 0xd6bd2605. Later XCHG transfers that value into R11 and 0x14df0f into R10. CX is loaded with 0x0f. A 14-bit shift of R10W=0xdf0f yields carry 0. ADC of R11W with CX therefore changes 0x2605 to 0x2614, preserving the upper word. Subsequent NOT R11D produces 0x2942d9eb with zero upper 32 bits.

The intervening instructions and relevant sequences are pinned by full-prefix byte hashes. The arithmetic uses explicit operand widths and does not carry undefined flags. The earlier [flag-chain proof](NATIVE-LOAD-FLAG-CHAIN-RECOVERY-2026-10-17.md) supplies its path context; the shift/ADC/NOT operation rules are consistent with the [Intel instruction reference](https://cdrdv2-public.intel.com/782151/253667-sdm-vol-2b.pdf).

## The final write addresses the current stack top

At 0xfa14d8, POP R10 removes the ordinary return address just pushed by the CALL from 0x11a3ada. ADD RDI,RSI follows. The store at 0xfa14dd uses effective address RSP+R11−0x2942d9eb. The constant slice makes that offset exactly zero, so this instruction writes the sum to the CURRENT stack top. RET at 0xfa14e5 consumes that newly written value; treating it as a normal return to 0x11a3adf would be unjustified.

This establishes a stack-rewritten return under ordinary successful execution. It does not show that every stack operation in the entire library follows this pattern or identify a specific obfuscator.

## Symbolic destination

The latest captured assignment of RDI before the final ADD is a RIP-relative LEA naming image-relative 0x10bf959. No subsequent captured instruction changes RDI until that ADD. RSI is sign-extended from ESI immediately before the final callee. Consequently the RET destination is:

`(load_bias + 0x10bf959 + sign_extend_32(decoded_ESI)) mod 2^64`

Here load_bias is symbolic, not an observed runtime mapping. decoded_ESI names the value produced by the earlier load/arithmetic sequence; its actual value is still unresolved. The formula does not yield a concrete destination by itself. This narrows the next task to that value's data provenance rather than blindly following the CALL fallthrough.

## Verification and limits

Four fixed byte ranges and the preceding flag-chain result are rechecked. Eleven synthetic tests cover register arithmetic, carry/modulo cases, stack-offset cancellation, positive/negative signed offsets, wrapping and changed/missing range rejection. The target library is never loaded or executed; only byte parsing and scalar constant/address calculations run. This is not a general native emulator, decompiler, full function proof, or independent semantic review.

No native payload is unpacked, no binary is patched, and no protected model is decoded. Actual loader transformations, native reachability, the concrete return address, Java-native bindings and whole native implementations remain unverified. Central mappings are unchanged.
