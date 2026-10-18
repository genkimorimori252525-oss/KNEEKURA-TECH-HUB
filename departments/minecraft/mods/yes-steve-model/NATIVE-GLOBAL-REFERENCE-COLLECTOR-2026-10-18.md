# Global-reference collector: byte-backed native lifecycle map

Source: exact YSM2.6.5 libysm-core.so SHA-256 15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22; immutable instructions and unicorn-jni-field-next6.checkpoint.json (7ee5412441d6d30700a7f4c9627bb5845e014cc31be967f10c79bc4e9a60c8a2). These are static reachable semantics plus captured inputs. The collector has not executed in that snapshot. Do not claim completed deletion, attachment, wakeup, shutdown or a new Java mapping.

## Identity and call chain

- State 0x404001084180 stores the name “YSM Global Reference Collector” at +0x10 → 0x404001021400.
- Vptr 0xd1c128; run slot 0xd1c138 → 0x41b3c0; deleting destructor 0x41b2e0.
- Captured function at state+0x30 is 0x41c220. Invoker at +0x48 is 0x39d440; it loads the supplied JNIEnv pointer and tailcalls the captured function.
- Thread trampoline 0x2fccb0 invokes run then deleting destructor and returns NULL.
- Creator later calls pthread_detach via 0x41af75 → 0x2fcd20 → 0xd15260. A positive model must retain detached pending lifecycle, not erase the worker.

## Startup and exit bookkeeping

At 0x41b3c8 the run method passes state+0x50 to 0x3ccb80. This uses pthread_once at PLT0xd147a0, TLS dispatch descriptors 0xd2d020/0xd2d030, and callbacks 0x360690/0x3606e0. It registers a record through 0x2e4480 → 0x2bd710, linking it into pthread-specific storage with getspecific0xd15060 and setspecific0xd15050. Key initialization0x2bd668 installs destructor0x2bd590.

This is substantive thread-exit bookkeeping. A promise/future interpretation is plausible but its complete notification semantics remain unmapped. Do not replace the startup with an empty success stub.

## JavaVM attachment ownership

Wrapper0x41b460 reads JavaVM* from0xd356d0 and calls GetEnv at table offset0x30. Version is (byte[0xd356d8]−1)|0xa0000; recorded byte1 gives JNI_VERSION_10.

An existing non-null environment sets ownership false. Otherwise state+8 chooses attachment: recorded value1 selects AttachCurrentThreadAsDaemon(+0x38); zero selects AttachCurrentThread(+0x20). Attach args have version populated, name=NULL and group=NULL, so the stored collector name is not passed as JavaVMAttachArgs.name here. Successful new attachment sets ownership true; inconsistent failure/null results reach a native exception branch. Normal and shown exception cleanup detach via +0x28 only when newly attached.

## Queue semantics

0x41c220 repeatedly removes 16-byte entries. Global0xd356e8 supplies producer chains/queue structures with atomic reservation/read counters and two layouts.

- Non-null first-word reference: call JNIEnv->DeleteGlobalRef at0x41c873, table offset0xb0/index22.
- Null-reference entry with a secondary object: call0x41cbf0, which performs a virtual callback and result/exception completion machinery. These are control/work entries; treating every entry as a jobject is incorrect.
- Secondary objects are released through virtual slot+0x10 after handling.

## Waiting and shutdown

Global0xd35958 points to semaphore/counter state, recorded0x404001014600. Fast path atomically decrements a positive counter; fallback spin count is at+0x28. Blocking calls sem_wait at0x41c2d3 through0xd148d0. EINTR4 is checked through __errno_location0xd14850; retry and sem_trywait0xd148e0 paths are explicit.

Byte0xd35988 is zero in the snapshot. When set to1, the alternate branch drains available reference/control entries before exit0x41cb82. Who sets it and posts the shutdown wakeup remains unmapped.

## Fixture frontier and reuse boundary

The existing missing-thread fixture checks weak __pthread_key_create GLOB_DAT0xd2cf70, finds zero, and throws before pthread_create. The complete negative JNI result is documented separately in NATIVE-JNI-THREAD-GUARD-RESULT-2026-10-18.md.

A bounded deferred-worker model may reserve a pending worker and postpone its scheduling through the main JNI boundary, but must expose the worker as unexecuted and stop at join/blocking operations requiring a scheduler. Complete concurrent claims require faithful pthread_once/TLS destructor, attachment ownership, queue atomic, semaphore wakeup and detached-completion behavior. Native registrations and entity→Molang→bone→renderer execution are still separate unfinished goals.

## Static positive caller continuation

After collector construction returns to0x413630, 0x41363f moves its future/state to global0xd35960. The move at0x39d539–0x39d541 clears the source ownership/wait flag+0x20; immediate destruction of that moved-from local at0x413647 therefore skips its real wait path. This establishes no immediate collector wait on this path, not freedom to defer arbitrary shutdown.

With non-null saved JNIEnv, a second std::thread is created at0x4136cc and detached at0x4136e6. Its state vptr is0xd1ba18 and captured function0x3cc080. It starts with bookkeeping0x3ccb80 on global0xd34ed8, then handles a separate queue/semaphore global0xd34ed0, blocking at sem_wait0x3cc143 and retrying EINTR. Its higher-level purpose remains unknown.

Main setup0x413728 calls0x3dbaf0 with callback0x4181c0 and uses mutex lock/unlock. The recorded negative snapshot has byte0xd35570=0, selecting queued callback handling. A callback can wake the second worker with sem_post. CPUID leaf0 at0x413753 precedes native descriptor resolution0x4193c0 at0x413bc6.

This resolver concretely uses the existing FindClass/NewGlobalRef/DeleteLocalRef, GetMethodID/GetStaticMethodID and GetFieldID/GetStaticFieldID slots. Failed lookup paths include ExceptionCheck and ExceptionClear. Exact later class/member text is still encoded in payloads such as source0x4343b length0x5d and0x43498 length0x4b; do not assign plaintext names before byte-backed decoding. No RegisterNatives arguments were established in this static slice.
