# Independent collector lifetime review

Verdict: CONDITIONAL_STATIC_ACCEPTANCE of `native-collector-lifetime/REPORT.md`, with its stated selected-path limits. Reviewed report and receipt hashes are pinned in `collector-lifetime-receipt.json`.

## Confirmed

- Scheduler call 0x41cf7c fixes ECX=0 at 0x41cf74. Helper 0x2e3ec0 tests CL and takes 0x2e3ff0, calls imported syscall, and returns EAX=1 at 0x2e4007 on ordinary return. The caller's masked-state comparison and AL test therefore cannot normally escape the wait while state is not 1. Timed-helper false returns do not apply to these arguments. This does not establish syscall success or liveness.
- Guard fallback 0x41d070 constructs the 0x360430 closure and calls 0x360450; it neither submits nor invokes task vtable slot 0. The closure moves task+0x18 into the result destination. The 0x360690 completion method is reached through the original pthread_once/TLS trampoline and calls that closure; it is not the collector body. On normal completion, state result installation at 0x3606b3 precedes ready exchange at 0x360522.
- Queued invocation 0x41cbf0 calls task slot 0 at 0x41cbfd before the normal completion call 0x41cc37. Independent original EH-table decoding confirms both calls' catch-all landing pads, plus cleanup-only pads for fallback and wait. The body exception route has already left the body before its handler attempts exception completion; no guarantee of successful exception allocation/cleanup is added.
- Extra virtual-call disambiguation: emitter initialization 0x35ac0f/0x35ac16 installs state vtable 0xd1c0b8; task+8 receives this state at 0x35ac3b. Original RELATIVE relocation 0xd1c0c8 targets 0x2aade0, whose instruction is RET. Thus scheduler state virtual +0x10 call at 0x41cf46 is a no-op for this emitter state, not hidden collector invocation.
- Guard-race consumer skip 0x41c85c→0x41c8fc leads to destruction rather than slot-0 invocation. The destructor's remaining-result branch can install an error-bearing result and publish readiness. Completion state therefore cannot be promoted to successful callback, successful queue submission, or successful Java map update.

## Evidence and limits

The independent script checks all 15 final worker windows against original PT_LOAD bytes, 13 instruction assertions, four independently decoded LSDA edges, original pthread_once/syscall relocation chains, and the additional state initialization/no-op virtual target. No original executable or target code was executed. Parsing/disassembly and authored assertions only; no network, assets, CI, or Git edits.

For the selected normal queued completion, body use of captured builder vectors ends before ready publication; the ordinary caller remains in dispatch/wait until ready is observed. Guard fallback does not invoke the body and leaves task cleanup to the caller. This is a bounded ordering result. Other state writers, transitive queue correctness, abnormal unwind/termination and eventual execution remain outside the proof. Shared-state lifetime does not extend the captured stack-vector lifetime by itself. No unconditional drain, global exception-safe lifetime, future exception consumption, or Java tick/publication ordering is certified.
