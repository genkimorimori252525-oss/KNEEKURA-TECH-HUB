# Independent execution backend preflight

## Why a second backend is needed

The Ghidra heap trace reached 172,883 completed steps and stopped at an fopen import. Read-only arguments in isolated state are exactly /proc/self/status and r. Actual host files were not read. ELF slots0x184d858/0x184d860/0x184d868 identify fopen/fgets/fclose; the first two use PUSH-slot/RET thunks, fclose uses JMP-slot. The stage's safe reversible step budget was raised to500,000 with a5,000,000 actual-p-code limit and60-second time guard, retaining private-stack/allocated-heap-only writes and no actual native/OS calls.

Three explicit file scenarios were prepared: synthetic open failure, or an assistant-authored minimal status fixture with TracerPid0 or1234. All stopped after175,521 completed steps, before their first fgets or fclose. Therefore neither fixture was consumed, and these trials provide NO evidence about how YSM responds to either TracerPid value. The model helpers' seven fixture tests passed, but passing those tests does not prove the whole CPU model accurate.

The stopped read at0x14fd705, address0x9596c06b, follows SHR R10B,0xe1 at0x14fd6e6 and JL at0x14fd6ea. A separate toy using input0xde and count0xe1 (masked to1) shows Ghidra produces result0x6f with OF0, while the x86-64 ISA/host toy gives OF1. The pinned ia.sinc shrflags macro sets OF0 for count1. A full4096-case assistant-authored host toy checks every8-bit value, two initial OF states, and eight raw counts that mask to0 or1. It executes no YSM bytes. This confirms another local model discrepancy; do not label the resulting stopped read as actual native behavior or intentional anti-analysis without further evidence.

The first memory-XCHG32 issue is already normalized and tested. This second SHR overflow-flag issue has NOT been patched in the Ghidra harness in this checkpoint. Raw/provisional traces remain available, but further target execution should first use a corrected/independently checked backend. The precise first affected state/branch in the longer trace remains to be established. Existing original-byte inventories and Java map669 are unchanged; no native mapping promotion follows from these diagnostics.

## Official independent backend and preflight

Unicorn2.1.4 was installed from the official PyPI distribution into an isolated external virtual environment, not the system Python or repository. The [official Python binding instructions](https://github.com/unicorn-engine/unicorn/blob/master/bindings/python/README.md) recommend the PyPI package; [project documentation](https://www.unicorn-engine.org/docs/) describes the emulator. The installed manylinux x86-64 wheel SHA-256 is9d6e6dea140560de4ebd8446661f7ef84a357d428c14a3ef09dacd306ec8c239. No target has yet been simulated with Unicorn in this checkpoint.

Own-code preflight confirms Unicorn handles the two demonstrated instruction cases as expected. It also exposes an important safety difference: stopping from a normal memory-write hook does NOT prevent the pending write. Code-hook stopping prevents the instruction, and read-hook stopping prevents the register load in the tested fixtures. A future guard MUST NOT assume write-hook cancellation is a pre-write barrier.

Planned safe design: original-image pages mapped read/execute without write; explicit private stack and bounded allocated heap; initialized/opaque-byte tracking; transactions for candidate instructions so disallowed private writes and CPU state are discarded rather than retired; no actual OS/import execution; typed synthetic clock/file models only; exact-image hash checks and first-image-write boundary retained. Verify these properties with toys before any target run. Do not use an unguarded generic emulator invocation to bypass the existing boundaries.

## Reproduction

- tools/shr_overflow_flag_toy.c contains only assistant-authored instructions. Compile to an external output directory and run on GNU-compatible x86-64; expected HOST_TOY_SHR_FLAGS_PASS4096.
- The existing Ghidra script mode probe-shr-flags reproduces the uncorrected pinned result without target simulation.
- tools/unicorn_guard_preflight_ysm_265.py uses only own toy bytes. It intentionally reports that normal write-hook stop still changes memory; this is a diagnostic, NOT a validated target guard.
- The current Ghidra file models remain explicit modes, with authored fixture content and no real file/OS access. They are provisional until backend semantics are checked.

Detailed input/trace hashes and stopped-state summaries are in NATIVE-SECOND-EMULATOR-PREFLIGHT-2026-10-18.json. Keep raw binaries, full traces, tool packages and venv outside Git.
