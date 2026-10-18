# First guarded image-state store

Two declared CPUID leaf1 fixtures, (EAX,EBX,ECX,EDX)=(0,0,0,0) and (0,0,0x02000000,0), reach the same first attempted image write. Their instruction paths are identical through this boundary; that does not imply all CPU inputs or later paths are equivalent. The fixtures are hypothetical inputs, not claimed real CPU configurations. No host CPUID query is made.

Both complete1,907,962 native instruction/model steps, retain15 CRC summaries (528,156,776 logical loop-instruction effects), pass all12 static oracle checks, and stop before instruction0x14a66e9 writes8 bytes to0xedf060. The instruction bytes4c890c26 decode as MOV [RSI],R9 (the SIB has no index). Canonical registers RSI=0xedf060 and R9=0x710000000000 independently match the write-hook receipt.

The destination is an all-zero eight-byte image slot. The intended value is the start of the424-byte private virtual allocation already tracked in R15. This establishes a conditional initialization-time global context-pointer store, not recovered Java/native bindings or a decryption routine. The store is not applied, and no original-image bytes or source file change. There are13 preceding private heap-write events.

Six CPUID fixture tests verify exact four-DWORD outputs/upper clearing, flag and unrelated-register preservation, default blocking, invalid tuples and unsupported leaves. Existing guards pass. CLI --cpuid-leaf1 takes explicit hexadecimal EAX,EBX,ECX,EDX. Resource ceilings are now4million steps and180seconds; the observed runs stop before2million, so the increase does not alter their result.

Reproduce the preceding protection-success command with --cpuid-leaf1 0,0,0,0 (or0,0,2000000,0), --steps4000000 and --seconds180, supplying option/value arguments separately. The paired JSON records exact source/trace hashes and both canonical states. Central map669 unchanged; independent semantic review NOT_RUN.

Next separate the immutable reference artifact from a bounded simulated working-image view if continuation requires state stores. Such a mode must retain transaction rollback, explicit allowed ranges, a complete mutation ledger, original-file/reference verification, and no actual native imports or OS permission changes. The current default remains read-only and has not passed this store.
