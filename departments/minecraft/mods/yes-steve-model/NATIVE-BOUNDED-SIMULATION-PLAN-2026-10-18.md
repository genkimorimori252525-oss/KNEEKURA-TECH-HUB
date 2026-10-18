# Proposed bounded initialization simulation

Status: Owner approved the bounded simulation on October 18, then explicitly requested continuing with narrowly scoped lock-marker support. Two trials have now run; see [result](NATIVE-BOUNDED-SIMULATION-RESULT-2026-10-18.md). The latest stopped at an uninitialized stack read, without a non-stack write. The original constraints below still apply.

The requested scope is the Linux DT_INIT path in the pinned native image, in isolated emulator memory, with no host MOD/JNI execution or external/OS calls. Stop at the first non-stack write or 10,000 instructions. Do not start on the basis of this document alone; require the owner's response to that request.

## Available implementation route

The installed Ghidra 12.1.4 includes PcodeEmulator and PcodeEmulationCallbacks. Source inspection confirms beforeStore and beforeStepOp callbacks, plus uninitialized-read callbacks. The older EmulatorHelper/MemoryAccessFilter APIs are deprecated and their write filter is after-write, so prefer the current API and pre-write guards.

The implemented harness follows a bounded harness with these constraints:

- Only the exact Linux image SHA-256 15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22, DT_INIT entry 0x152eb19, analysis image base zero.
- Load bytes into disposable emulator state; do not load the library into the host process. Keep the original JAR/native file and read-only Ghidra program unchanged.
- Use an explicitly documented synthetic initial register/flag state and a private bounded stack. A concrete trial is not evidence for every possible caller state. Do not substitute silent zeroes for subsequent uninitialized reads.
- Before STORE, resolve its destination and stop before a non-stack write. Also check direct RAM p-code outputs before execution, because some direct-address writes are COPY operations rather than STORE. Register/unique-space writes are not image-memory writes.
- Stop on uninitialized reads, unimplemented/OS user operations, external/null targets, unexpected segmented-memory dependencies, oracle disagreement, cancellation, or the instruction limit. No system-call models, host callbacks or native imported functions are to be connected.
- Use one bounded trial initially, at most 10,000 instructions; add stricter p-code-operation and wall-time guards to avoid an internal repeated instruction bypassing the instruction budget.
- Compare the path and flags with retained static oracle facts. A disagreement is a reason to stop and diagnose, not to force an expected branch or patch the target.
- Report the first attempted non-stack write or precise stop reason. Do not continue past it without a scope decision. Do not process protected model assets or unpack/patch native protection as a side effect.
- Retain reproducible scripts and derived evidence in GitHub; keep raw images, project database and raw traces outside Git. Verify preservation hashes and remote publication before reporting saved results.

The current static frontier remains recorded by NATIVE-INIT-GUARD-CHAIN-RECOVERY-2026-10-18.md. The constant-propagation experiment is explicitly INCOMPLETE and does not itself authorize simulation.
