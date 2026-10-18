# JNI metadata completion and explicit missing-thread scenario

## Observed negative result

The current declared isolated scenario completes JNI_OnLoad with JNI_ERR (EAX 0xffffffff), ABI preserved and a pending RuntimeException:

    Enable multithreading to use std::thread: Operation not permitted\n

This is **not successful JNI initialization**, not a real host permission error and not evidence that YSM itself is broken. The fixture deliberately left optional weak imports unresolved. Exact bytes at 0x2fcdb7 compare weak undefined __pthread_key_create's GLOB_DAT slot 0xd2cf70 to zero; the taken branch at 0x2fcdbf reaches 0x2fcd67, which hardcodes errno 1. pthread_create has not been called. No exception was cleared, branch patched or success return invented.

The bounded GNU strerror_r model resolves only the observed C-locale EPERM message. GNU's known-error ABI returns a stable readonly literal and does not write the caller's buffer. Unknown error numbers stop. Its fixture pointer, bytes, initialized mask and readonly reservation survive strict checkpoints. This preserves the error path through the native C++ catch into Java ThrowNew.

## New verified metadata

The scenario verifies 27 method descriptors and five field descriptors against immutable sources. These counts are Java metadata lookups, **not YSM native registrations**. New field evidence:

- java/util/UUID.mostSigBits:J and leastSigBits:J (private final)
- java/lang/Boolean.TRUE and FALSE:Ljava/lang/Boolean; (static)
- java/lang/Integer.value:I

GetFieldID and GetStaticFieldID share bounded exact-descriptor lookup, stable opaque IDs, source/class SHA provenance and restore revalidation. Private declared fields are eligible. Unsupported interface traversal stops; there is no fabricated Java field value or class initialization. The 669-entry Java mapping remains unchanged.

## Collector identified, execution remains pending

The intended worker's captured name is YSM Global Reference Collector at state 0x404001084180, with vptr 0xd1c128. The run slot is 0x41b3c0 and deleting destructor 0x41b2e0. The original start trampoline 0x2fccb0 invokes run, then the deleting destructor, then returns NULL. Captured callable at state+0x30 is 0x41c220; invoker 0x39d440 passes JNIEnv*. Static bytes show the callable dequeues entries and calls DeleteGlobalRef at 0x41c873 through JNIEnv offset 0xb0. It waits using sem_wait, retries EINTR via __errno_location, and has a sem_trywait fallback. Wrapper 0x41b460 calls JavaVM GetEnv, then AttachCurrentThreadAsDaemon when state+8=1 (the recorded state); it detaches only if it newly attached. These are exact static call-path observations; the collector has not executed in the isolated scenario, and full concurrent behavior remains unverified.

If thread support is explicitly supplied in a fresh scenario, the next pthread_create call would receive pthread_t output at 0x7000000079f8, null/default attributes, start 0x2fccb0, argument 0x404001084180. Any successful virtual-thread model must retain an actual bounded pending-worker lifecycle; join must not pretend the worker completed. A prototype is being developed separately. Current code does not silently change the weak guard or claim worker execution.

## Evidence and continuation

[JSON receipt](NATIVE-JNI-THREAD-GUARD-2026-10-18.json) contains all 27 method and five field proofs, the exact negative checkpoint hash and branch/worker addresses. The completed negative snapshot is unicorn-jni-strerror-next1.checkpoint.json, SHA-256 ebf1abc7996c2100d059197d698ed92f9df716f6ea388c88807741c8e91d4098. Do not resume it as an unfinished positive JNI call. Preserve prior snapshots and build a fresh explicit thread-support scenario for positive-path claims.

Nine affected test modules pass 165 methods. This includes exact fields, wrong-static/descriptor rejection, source-proof checkpoint restore, pending-exception guards, GNU error-string behavior and batched execution. No whole-project CI is required for this cohort. Original artifact bytes remain unchanged; no host JVM/native target code or target worker thread was run.

Sources: [JNI GetFieldID](https://docs.oracle.com/en/java/javase/25/docs/specs/jni/functions.html#getfieldid), [GNU strerror_r implementation](https://github.com/bminor/glibc/blob/master/string/_strerror.c), [GNU error strings](https://github.com/bminor/glibc/blob/master/sysdeps/gnu/errlist.h). The imported symbol is strerror_r, not the XSI __xpg_strerror_r integer-return ABI.
