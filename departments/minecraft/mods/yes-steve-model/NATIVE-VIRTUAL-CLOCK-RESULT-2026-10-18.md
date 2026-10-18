# Bounded virtual-clock scenarios and malloc boundary

The owner approved the 100,000-step extension. The clock-disabled run completed 28,869 steps (28,870 attempted) and stopped at RDTSC, address 0x146379a. No real CPU timestamp or imported function was invoked.

An explicitly selected run-approved-virtual-tsc-init-100k mode then treated timestamp values as scenario inputs. Seeds 0, 0x100000000 and 0x1122334455667788, each with declared per-read stride 0x3e8, were compared. Each sample encountered exactly one RDTSC, so stride effects were not tested on the target. The prior opaque stack bytes stayed unknown; none was assigned a guessed value. Concrete timestamp samples are separate explicit environmental inputs, not claims to recover the unknown actual runtime timestamp.

Results:
- Seeds 0 and 0x100000000: 100,000 completed steps, 11,336 unique instruction addresses, same instruction path, stopped at cap before 0x14127df. No non-stack write.
- Seed 0x1122334455667788: 48,846 completed steps, 48,847 attempted, 11,699 unique addresses. Stopped before transferring to raw pointer zero through 0x13d8472. No non-stack write.
- All samples retain the entire pre-clock instruction prefix and match all 47 reached old oracle observations. All preserve original image and seven loaded segment hashes. Repeated steps are not recovered functions or completion percentages.

The paths first diverge at step 47,663, after JNZ at 0x1534739. The low seeds take 0x14127df; the mixed seed falls through 0x153473f. The immediately preceding flag-producing DEC R9 at 0x15b6810 explains the local zero/nonzero branch distinction; the intervening stack MOV/CALL/PUSH/LEA sequence does not change flags. These samples demonstrate input-sensitive control flow. They do not establish the path for all clock values or identify a general anti-debug mechanism.

## Blocked external boundary

The original bytes at 0x13d846c push a qword from RIP-relative slot 0x184d828, then RET at 0x13d8472 uses it as a target. That slot is raw zero in this deliberately non-relocated program. ELF R_X86_64_GLOB_DAT, symbol index 277, names the undefined import malloc. A real loader would resolve the import; the observed null pointer is not proof of a native application bug.

At the boundary RDI=0x1a8, interpreted under the SysV x86-64 calling convention as a 424-byte allocation request. Read-only stopped-stack observation gives caller-return candidate 0x13d91f2. Its decoder enters another protected dispatch prologue. The observation replay is identical except for added stack-byte rows. No malloc, host allocator, heap model, external function or native loader has run for the target in this cohort.

See NATIVE-VIRTUAL-CLOCK-FRONTIER-2026-10-18.json and tools/native_virtual_clock_frontier_ysm_265.py. The helper resolves ELF metadata directly from pinned bytes and compares the retained external traces. Baseline/budget tests 17, opaque-copy tests 24 and clock tests 8 pass. Clock tests cover high/low halves, zero extension, unchanged flags, six fixed 64-bit values, a two-read carry across the low half and disabled-mode refusal. Only named, shape-checked RDTSC is enabled in this mode; other unsupported userops still stop. No real time source feeds target state.

Read-only GNU cross-checks agree on all instruction boundaries/lengths/bytes for the 100,000-step low-seed trace (738 groups) and the 48,847-step mixed trace (768 groups). The other low-seed trace has the same instruction path. Decoder agreement is not full p-code semantic certification or an independent review of the overall analysis.

## Reproduction and next authorized stage

Use the existing read-only Ghidra project, exact image and seven-segment memory manifest. New modes:
- self-test-virtual-clock OUTPUT: 17 + 24 + 8 toy tests; no target simulation.
- run-approved-opaque-copy-init-100k OUTPUT MANIFEST IMAGE: same guards, clock still blocked.
- run-approved-virtual-tsc-init-100k OUTPUT MANIFEST IMAGE SEED_HEX STRIDE_HEX: explicit clock sample, 100,000 instructions, 1,000,000 actual p-code operations, 60 seconds, first non-stack write blocked.

The owner subsequently approved a next stage: a maximum 1 MiB isolated virtual heap and virtual malloc, permitting writes only within that heap plus the private stack, retaining the 100,000-step cap and blocking original-image writes and actual external/OS calls. This stage is approved but not yet implemented or run in this cohort. Keep raw images/traces outside Git and preserve separate evidence for each model revision. Safe reversible analysis choices should not generate unnecessary repeated owner confirmations; do not infer permission for charges or actual host/native execution.

Subsequent model correction: see NATIVE-VIRTUAL-HEAP-RESULT-2026-10-18.md. A memory-XCHG32 upper-register defect was found in the pinned Ghidra semantics. All three clock scenarios were rerun after correction and retain identical instruction paths/boundaries. Earlier register-state dumps after step18,923 are historical and must not be mistaken for corrected ISA state.
