# Linux JNI first-transfer prefixes: stop at unresolved conditions

PRIMARY_STATIC_REVIEW_ONLY. Exact Linux image SHA-256 `15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22` inside the fixed YSM artifact. This follows the file-backed entry branch targets from NATIVE-EXPORT-BACKING. No native target was loaded, executed, emulated, unpacked or modified.

## Bounded traversal

At each known start address, installed objdump decodes a bounded byte window. The recorder checks consecutive instruction addresses and exact bytes, stops at the FIRST transfer, and follows only an immediate CALL or JMP target. CALL/JMP opcode and signed-displacement arithmetic must agree with objdump's target. It does not assume a call returns, follow its fallthrough or merge arbitrary linear-disassembly output into one function. A non-direct transfer is a frontier; depth exhaustion is an error rather than success.

The JNI_OnLoad chain reaches three prefixes:

- 0x121fe24 → direct call at 0x121fe30 to 0x1189f87
- 0x1189f87 → direct call at 0x1189fae to 0x129ea6d
- 0x129ea6d → conditional JP at 0x129ea88 to 0x13b4244; traversal stops

The JNI_OnUnload chain reaches eight prefixes:

- 0x10e09d2 → 0x12aa5a0 → 0x11edd7d → 0x126d4c5
- → 0x1172010 → 0x10bfb4e → 0x10f8ef5 → 0x11f64cc
- Last prefix ends at conditional JE, address0x11f6526, target0x11a0c5f; traversal stops

The JSON records each first-transfer site, byte count and prefix hash. Full windows and raw disassembly remain outside Git. These eleven prefixes are not eleven recovered functions, and neither chain is a proof of runtime execution: image loading/rewriting and native state remain unobserved.

## Why simple linear decompilation is insufficient here

The local windows contain stack saves, arithmetic and stack-relative writes before their first transfers; the load-side callee also writes to a stack slot associated with the incoming call context. The current record does not reconstruct those stack values or choose conditional outcomes. Instructions printed after a CALL or conditional in a linear dump cannot simply be labeled the next executed steps. No RegisterNatives invocation, Java binding table or full initialization/unload semantics has been identified.

The useful boundary is now explicit: conditional state and subsequent control flow must be justified before extending either path. Do not turn first-transfer metadata into a whole call graph or use the source-level Java native declarations as guessed names for these target blocks. No conclusion about a particular obfuscator/vendor, correctness, or harmful behavior is drawn.

## Verification

Ten synthetic tests cover byte/address agreement, stop-at-call, no-control rejection, forward/backward displacement, mismatched target/mnemonic rejection, and indirect/conditional boundaries. The real fixed-image result recomputes identically with GNU binutils 2.44. This is parser/control-flow-scope validation, not independent semantic review or runtime validation. Central mappings remain unchanged.

A separate [local parity proof](NATIVE-LOAD-PARITY-PROOF-RECOVERY-2026-10-17.md) subsequently justifies the load-side JP's taken edge under explicit assumptions. It does not change this recorder's conditional stop policy or resolve the unload frontier.
