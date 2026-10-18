# Fresh deferred-thread capability scenario

This is a new explicit fixture scenario, not a patched continuation of the completed negative JNI result. The exact weak undefined __pthread_key_create relocation is verified against the pinned ELF and bound to a pre-instruction model gateway before DT_INIT. Other weak symbols are unchanged. Original bytes and host thread state are untouched.

Fresh DT_INIT and all 45 init-array callbacks complete: 3,465,313 cumulative instruction/model invocations. The two actual guest pthread_once callbacks return and are marked done; 44 once calls reuse their completed results. No worker has been created or executed yet. JNI_OnLoad is being replayed from this fresh initializer checkpoint with the same JVM/JAR/JMOD and pinned commons-lang3 dependency.

## Bounded lifecycle contract

- pthread_create reserves a bounded record with an opaque guest thread ID, validated original-code entry and argument. The declared scheduling choice defers all workers through the main JNI boundary. This is pending work, not execution or completion.
- pthread_detach retains the pending record. pthread_join stops with THREAD_SCHEDULER_REQUIRED; it cannot report a worker result. Main-thread TLS keys are bounded and tracked; pthread_key_t uses its unsigned low 32 bits, while TLS pointer values retain 64 bits.
- A main-JNI return emits an explicit pending-worker boundary and runtime_complete=false. Host pthread APIs, target native code and JVM bodies are never invoked.
- pthread_once executes its actual guest callback. Running/done control objects remain opaque; native/model reads, writes and copies cannot treat placeholder bytes as real pthread internals. Reentrancy stops. Normal return requires correct stack, callee-preserved registers and DF. Unfinished or failed callbacks stay running, never done.
- Checkpoints validate queue, key, once and callback-frame schemas, storage, gateway bytes and exact weak binding. Loading an enabled-thread or active-once snapshot into an incapable backend rejects instead of dropping lifecycle state.

The 13 affected modules pass 208 own-byte test methods, including batched callback differentials and checkpoint continuation. A focused independent review reproduced two guard gaps, now fixed and independently rechecked: page-rounded mapping/advice requests must not alter opaque controls outside their originally requested byte count, and top-level initializer/JNI returns cannot complete while once or program-header callback frames remain live. The completed initializer prefix was not observed to exercise either defect. These results do not establish a completed collector, JNI success, real concurrency, or a new native registration.

Use native_initializer_sequence_ysm_265.py --deferred-threads for a fresh scenario, optionally --batch-size 256. A resumed initializer snapshot must already carry this capability; it cannot be silently added afterward. The JNI driver preserves the lifecycle automatically. Keep all input binaries, raw traces and snapshots outside Git.

[Receipt](NATIVE-DEFERRED-THREAD-INITIALIZERS-2026-10-18.json) records the fresh checkpoint and lifecycle state. [Collector static map](NATIVE-GLOBAL-REFERENCE-COLLECTOR-2026-10-18.md) distinguishes reference entries, control/work entries, daemon attachment, TLS cleanup, waiting and shutdown obligations still needed for worker execution.
