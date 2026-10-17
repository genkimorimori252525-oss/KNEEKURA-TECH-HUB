# One load-side conditional resolved by local constant arithmetic

PRIMARY_STATIC_REVIEW_ONLY. This advances the JNI_OnLoad frontier at 0x129ea88 from NATIVE-LINUX-PREFIX-FRONTIER. It proves one local predicate for unmodified fixed bytes under ordinary successful execution, not that the native library has been executed or fully decoded. Exact Linux SHA-256 `15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22`.

## Fixed sequence and result

The contiguous 21-byte sequence starting 0x129ea79 is checked exactly before applying the proof:

1. PUSH immediate 0xad14cb90 in 64-bit mode.
2. DEC WORD PTR [rsp+3].
3. MOV QWORD PTR [rsp],r14.
4. JP at 0x129ea88 to 0x13b4244.

The pushed value is sign-extended to 0xffffffffad14cb90. Its little-endian bytes at stack offsets 3 and 4 form word 0xffad. Decrement produces 0xffac; the low byte 0xac has four set bits, so PF=1. The intervening ordinary MOV does not change flags. JP therefore takes 0x13b4244 rather than fallthrough 0x129ea8e, provided the sequence executes normally without interference. R14's value does not affect this predicate: its write happens after DEC and preserves PF.

This inference uses the fixed bytes plus documented instruction semantics: PUSH sign extension and MOV flag preservation in [Intel Volume 2B](https://cdrdv2-public.intel.com/782151/253667-sdm-vol-2b.pdf), DEC/PF and JP conditions in [Volume 2A](https://cdrdv2-public.intel.com/812383/253666-sdm-vol-2a.pdf), and low-byte even-parity meaning in Intel's [basic execution environment manual](https://www.intel.com/content/dam/support/us/en/documents/processors/pentium4/sb/25366521.pdf). No raw code was executed; the helper evaluates only integer/byte arithmetic for this exact local pattern.

## Scope and assumptions

- Fixed sequence entered at its start in x86-64 mode; no altered or mid-instruction entry.
- Stack accesses complete without fault and no external interference changes bytes/flags during the sequence.
- No inference that initialization reaches this code at runtime, that all later paths are known, or that JNI method bindings have been recovered.
- The unload-side JE remains unresolved by this proof.

The general first-transfer recorder still stops at conditional instructions. This separate proof justifies one further edge without silently teaching that recorder to guess conditions. The target is independently file-backed under the ELF program-header map. No payload unpacking, native emulation, binary patch, model decryption or protection bypass was performed.

## Verification

Six synthetic tests include the actual arithmetic result, sign extension, a changed constant yielding opposite parity, eight byte-level mutation rejection subcases and truncation rejection. The fixed-image proof recomputes identically. Mutation rejection guards the proof's applicability; it is not a native behavioral test. Independent semantic review NOT_RUN, whole native implementation unresolved, central mapping unchanged.
