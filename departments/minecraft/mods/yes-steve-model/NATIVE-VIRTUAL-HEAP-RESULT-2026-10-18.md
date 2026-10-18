# Virtual heap and verified XCHG32 emulation correction

## Current result

The approved isolated heap stage now runs with the explicit mixed clock scenario and a maximum 1 MiB virtual heap. One malloc model request allocates 424 writable bytes, reserving 432 bytes for alignment. Seven 8-byte stores occur at object offsets 0x188,0x18,0x198,0x28,0x68,0x50,0x60. Their meaning as native structure fields is not yet established. The latest corrected trial completes 100,000 steps and stops at its instruction budget before 0x1815afd. No original-image write is applied, and no actual imported/native function or OS call is executed.

The trial has 19,977 unique instruction addresses, 893,113 actual p-code operations, 467 paired atomic markers, 4,277 modeled copy steps, 776 opaque copy events retaining 80 unknown origins, two virtual-clock reads, and one virtual malloc. Those are model/coverage counts, not recovered functions or an overall completion percentage. Original file and all seven program-segment hashes are preserved. Central mapping remains669 with no promotions.

## A real discrepancy in the pinned Ghidra model

The first heap trial had stopped at a write to 0x6fff00007afb from instruction0x14d8c08. That was outside the private stack/heap, but NOT an original-image write. R9 had incorrectly retained upper bits after XCHG dword memory,R9D, leading to an apparent stack address about4GiB below the intended area. Do not describe this stopped address as YSM's actual behavior.

A minimal assistant-authored fixture (no YSM bytes) reproduced the discrepancy: initialR9=0xffffffffffffffff, exchanged memory DWORD=0, Ghidra resultR9=0xffffffff00000000, expectedR9=0. The installed Ghidra12.1.4 lockable.sinc memory-XCHG32 constructor lacks the upper-register-clearing construct present in the register/register variant. Its file SHA-256 is de3639160b248e993c53986ac59b4f8d8ea8d449373c9771c76a19a0914b7d10.

The independent tools/xchg32_zero_extension_toy.c fixture compiles and runs only assistant-authored native instructions, never the target library. All36 combinations of six register inputs and six memory inputs on the x86-64 host confirm zero-extension. The Ghidra harness then normalizes only a successfully completed memory/register XCHG with one32-bit register operand and a64-bit base register. It copies the resulting low32-bit value into that base register, preserving flags and memory effects. Eight-,16-,64-bit exchanges and already-correct register/register32-bit exchanges are untouched. Target bytes, branches and unknown inputs are not patched or guessed.

Forty focused normalization tests pass, including the36 combinations, exchange width/canary preservation, flags, other operand widths and register/register behavior. Existing17baseline,24opaque-copy,8clock and13heap/oracle tests also pass:102 harness tests in total, plus the36 independent host-fixture cases. This is a specific tested model correction, not certification of every x86 instruction.

The earliest changed register state in the target trace occurs at step18,923, address0x152c6cf (R10 upper bits). All three clock scenarios were rerun with the correction. Their full instruction paths and stopping boundaries remain unchanged, although old register-state dumps after that point should not be treated as authoritative ISA states. The corrected heap run retains the old trial's entire63,811-instruction prefix, then completes the formerly faulting store and continues. It records28 actual zero-extension corrections by100,000 steps. The older bad write remains only a documented emulator artifact.

## Heap contract and guards

Only the pinned malloc thunk (PUSH original GOT slot0x184d828, then RET0x13d8472) is modeled. The original file/ELF metadata names malloc; the raw slot is zero because relocations are deliberately disabled. The model verifies the expected thunk bytes, slot value, known private-stack frame and allowed return address before allocation. It returns an aligned synthetic pointer and performs the wrapper/external-return stack transition without executing an external function. Caller-saved registers/flags other thanRAX are preserved as an explicit model choice, not a guarantee about a real allocator.

The model is a bounded, successful-allocation bump allocator. It does not implement free/calloc/realloc, errno, concurrency, host allocation behavior or real loader resolution. Requested allocation bytes, not alignment padding or the whole arena, are writable. A zero-size allocation reserves a distinct pointer but gives no writable bytes. Unknown allocated bytes remain unknown. Oversized/unsigned-overflow/capacity-exhausting requests stop rather than invent an allocation. Original image and every region outside the private stack and allocated heap remain write-blocked.

Heap tests cover allocation bounds/alignment, zero-size, oversized/unsigned requests, known write/read, padding protection, unknown reads, unexpected thunk value, invalid return, blocked program-memory write, and opaque-copy propagation into the heap. The old absolute-RSP oracle was specific to the original entry. Oracles are now checked on their first visit only, yielding12 checks; later reused protected prologues are not forced to use the original frame. The older47 observations included repetitions and remain historical.

## Reproduction

- self-test-virtual-heap OUTPUT runs102 toy checks, no target simulation.
- probe-xchg32 OUTPUT intentionally disables normalization only for the tiny fixture to reproduce the pinned tool discrepancy; it does not run YSM.
- run-approved-virtual-heap-init-100k OUTPUT MANIFEST IMAGE SEED_HEX STRIDE_HEX selects the isolated heap stage, preserving its100,000-instruction,1,000,000-actual-p-code and60-second guards.
- Compile xchg32_zero_extension_toy.c with an installed GNU-compatible x86-64 compiler into an external output directory, then run that fixture only.

The corrected100,000-step trace was independently checked against GNU decoding of the pinned original bytes:19,977 unique addresses in1,275groups all agree in address/length/bytes. This does not independently certify p-code or allocator semantics. Detailed trial and replay receipts are in NATIVE-VIRTUAL-HEAP-NORMALIZED-2026-10-18.json. Raw traces and original packages remain outside Git.

Next work stays inside the isolated model: inspect the seven heap writes and continue with a reasoned bounded resource budget. Do not ask the owner repeatedly about safe reversible technical adjustments within this already requested analysis. Charges, actual host/native imports, persistent access changes or other materially different actions still need their applicable authorization. The native initialization and its effects on the watched decoder data are not resolved.
