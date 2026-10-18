# Bounded DT_INIT simulation result

## Outcome and limits

A concrete isolated trial completed 9,203 instruction steps (9,204 attempted; 3,550 unique attempted addresses), then stopped BEFORE reading an uninitialized stack byte at 0x700000007d90 in REP MOVSB at 0x143beae. Repeated instruction steps are not unique native instructions or recovered functions. No non-stack write was applied, no MOD/JNI/native image was loaded for host execution, and original-file plus seven program-segment hashes were unchanged. This is a synthetic input trial, not real-process runtime validation or proof for all caller states.

All 47 reached static-oracle checks matched, including the known rewritten-return value and JB/JNS/JA predicates. The former RET 0x18 frontier at 0x1539420 returned to 0x1499584 seven times, then to 0x15ced58 once in this trial. These are observed synthetic-state successors, not an exhaustive CFG. REP MOVSB accounts for 97 attempted steps at the final address. Unknown caller/stack bytes were not filled with zero and the stopped read was not bypassed.

See the [derived machine-readable receipt](NATIVE-BOUNDED-SIMULATION-2026-10-18.json). Central map remains 669, no promotions; independent semantic review NOT_RUN. Do not turn step counts into completion percentages or claim the watched decoder words are immutable.

## Why the first trial stopped and what changed

The initial all-userop-denied harness passed 12 synthetic guard tests, completed 67 target instructions and stopped at the first CALLOTHER of XCHG at 0x1666896. Static lift shows CALLOTHER 0x11 before the exchange and 0x12 afterward. The pinned Ghidra x86 language sources ia.sinc (LOCK/UNLOCK declarations and alwaysLock constructors) and lockable.sinc (memory XCHG) identify these as atomicity markers, not external native imports.

After the owner requested continuing with lock support, the harness gained a narrowly scoped single-thread atomic-marker model. LOCK/UNLOCK have no data-memory effect in this isolated one-thread model with no asynchronous observers. The guard allows only those two names, zero arguments/output, XCHG instructions, and correctly paired non-nested markers. It does not claim to model concurrent threads, hardware lock timing or shared memory. All other userops, including CPUID, remain blocked. No target bytes, flags, branches or caller stack values are patched.

The revised harness passed 14 toy tests: private stack exchange/value preservation; computed and direct non-stack writes blocked before application; uninitialized reads; syscall; other userop; instruction, p-code and time budgets; direct and computed external calls; straddling stack write; paired XCHG stack exchange and XCHG non-stack write refusal. The target trial recorded 52 completed marker pairs. The non-stack guard remains active inside an exchange.

## Reproduce with existing verified tools

Use tools/ghidra/YsmGuardedInitSimulation.java with the existing read-only libysm-core.so Ghidra program, x86:LE:64:default, analysis base zero and relocations/libraries disabled as in the static handoff. Keep output outside Git. Modes:

- self-test OUTPUT.tsv: toy bytes only, must report SELF_TEST_PASS 16 (14 execution guards plus two read-only known/unknown inspection checks).
- run-approved-ysm-init OUTPUT.tsv NATIVE-GHIDRA-MEMORY-2026-10-18.tsv ORIGINAL-LINUX-IMAGE: exact image hash and seven file-backed program segments verified before and after. This mode requires the applicable owner authorization; its name is not authorization.

Run via analyzeHeadless with -process libysm-core.so -readOnly -noanalysis -scriptPath tools/ghidra -postScript and the selected mode/arguments. Use the verified full JDK and scoped HOME/XDG paths from the current handoff. There is no host API/syscall model. Private stack is [0x700000000000, 0x700000010000), initial RSP=0x700000008008; only the synthetic return sentinel is initially present. Limits: 10,000 instruction steps, 1,000,000 p-code operations, 60 seconds. Program decode context is retained; other base registers initially zero except PC/RSP/IF. The instruction interrupted at a guard may have performed earlier private-stack/register micro-operations; counts distinguish attempted and completed.

Raw traces and original harness snapshot remain external; their hashes are in the receipt. The initial 67-step trace used the earlier all-userops-blocked source, not the revised source. Do not overwrite that distinction.

## Next useful work

Statically inspect the REP MOVSB source interval and its producer to determine why the first unavailable byte is needed. Keep unknown bytes unknown. Do not extend the private stack initialization, skip the copy, execute imports, or run beyond the agreed non-stack-write/instruction boundary merely to obtain a longer trace. The present trial ended normally at its guard; analysis itself can continue statically.

## Stopped-copy diagnosis

A diagnostic replay adds only read-only register reporting after the guard has halted stepping. Removing these reporting rows makes the entire trace byte-for-byte identical to the earlier atomic-marker trial. The 14 guard tests still pass. The retained [copy-frontier receipt](NATIVE-SIMULATION-COPY-FRONTIER-2026-10-18.json) is regenerated by tools/native_simulation_copy_frontier_ysm_265.py without target execution; six scoped tests verify its count, ranges and rejection of modified paths, missing/wrong registers and the wrong image.

The producer at 0x15ebcb3..0x15ebd10 sets the count to 0x148 (328) and copies the old RSP region into a newly aligned stack area. GNU disassembly of extracted file-backed segments agrees with the captured instructions. In this synthetic trial, source is [0x700000007d30, 0x700000007e78), destination [0x700000007c00, 0x700000007d48), with 24 bytes of overlap. Destination lies below source; CLD selects the appropriate forward direction. Both ranges lie within the private stack. This is a stack-to-stack copy, not an attempted image/global write.

Ninety-six byte copies completed. The next source byte, 0x700000007d90 (initial RSP minus 0x278), was never initialized in this synthetic state. Its corresponding destination 0x700000007c60 was not written. Why the original caller's stack supplies that byte, and whether it is subsequently semantically used, remain unresolved; do not label it harmless padding without proof.

Important micro-op detail: Ghidra ia.sinc rep decrements RCX and eseDI1/dseSI1 increment RDI/RSI before the LOAD. Thus stopped RCX=0xe7, RSI=0x700000007d91, RDI=0x700000007c61 are partial emulator micro-op state, not an x86 architectural exception snapshot. Reconstructing the attempted byte uses the preceding addresses. No unknown bytes were zero-filled and no execution continued beyond the read.

## Complete stopped-state observation and conditional post-copy contract

The final observer captures all general registers/flags and the 328 source bytes' knownness after the guard has stopped. Inspection throws on an unknown byte and records UNKNOWN; it never initializes that byte. Two extra tests check known-byte inspection and preservation of the original stop when inspecting unknown memory. Sixteen toy tests pass. Removing all read-only STOP_REGISTER/SOURCE_BYTE rows again reproduces the earlier executed trace exactly.

There are 248 known and 80 unknown source bytes, distributed across multiple intervals. This disproves any assumption that the entire remaining tail is known or that only a single byte is missing. The intervals are in [conditional post-copy evidence](NATIVE-POSTCOPY-CONTRACT-2026-10-18.json). No copy completion or target execution past the stopped read is claimed.

Static analysis can still describe the following conditional contract: if the copy completes while preserving opaque bytes, its epilogue restores the saved flags/RDI and reaches the unchanged R11 target 0x160cc74 via 0x173afdb. That block's SHR DX,12 makes SF zero for all 65,536 DX values, so JS is untaken. BTC CX,0x83 selects bit 3 of fixed 0x9c26, old bit zero, so JAE is taken. A later fixed carry/subtraction chain gives DL=0xea, SF=1, OF=0, hence JL to 0x14cb406. None of these three scalar predicates consumes copied unknown bytes.

Using the observed R8=0x1544201, EBP=0xb564a469 and file word 0xe1aab868 at R8-4, the specified rotate/negate/byte-swap chain yields signed delta 0xffe3312a and candidate R11=0x143fd9e. This is a conditional register candidate, NOT an observed jump or recovered whole function. Later memory effects and consumers remain unresolved. The exact byte segments are hash-pinned; the helper never executes the target. Six scalar proof tests pass, including an independent bit-string rotate reference at boundary values.
