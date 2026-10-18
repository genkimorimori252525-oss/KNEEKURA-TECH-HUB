# Complete initializer array in the isolated scenario

## Verified result

All45 ELF init-array callbacks return in their original order after the already verified DT_INIT. The driver reaches phase=done, completed indices0..44, no in-progress callback. **45/45 applies only to this synthetic initializer phase.** It does not establish that YSM runs in Minecraft, that Java/native bindings have been recovered, or that native deobfuscation is complete.

One batched continuation from the verified17-callback checkpoint executes98112 attempted instructions/model invocations. Cumulative completed count3464756. An independent split continuation through the24-callback semaphore checkpoint reaches exactly the same complete state and checkpoint SHA-256 a63e08364467e41d0bfa61cbb80b44f63baf5c32b431d5c770dc8c40a31f267d. CPU payload, private memory, opaque state, sparse pages, image patches and model records all match. The final working-image/reference and sparse ledgers pass.

[Machine-readable receipt](NATIVE-INITIALIZER-SEQUENCE-COMPLETE-2026-10-18.json). Combined scoped regression244 test methods pass. Final sparse guest backing:89 pages/364544 bytes; logical anonymous reservations remain256GiB+16MiB without corresponding host reservation. Java map unchanged669 entries(405 CONFIRMED+264 HIGH); no mapping promotion. Independent semantic review NOT_RUN.

## Batch implementation

Four sem_init calls are needed, all pshared0/value0. Their32-byte Linux64 sem_t spans are represented by bounded opaque side-table objects rather than fabricated internal bytes. Native/model reads and writes through those spans stop, including private copies, sparse memory and working-image storage. Native write guards preserve rollback journals before stopping; range changes/discards cannot silently invalidate semaphore state. Checkpoints retain and validate these objects and their lifecycle.

The reusable single-virtual-thread model also covers post, positive-count wait/trywait and destroy. Zero-count wait stops as would-block, never fakes progress. Zero-count trywait returns-1 with virtual EAGAIN11; overflow uses EOVERFLOW75; invalid initial value uses EINVAL22. Success preserves errno. Reinitialization of a live object, destroyed/unknown operation, unsupported process-sharing and overlapping/invalid storage stop conservatively. These extra branches are unit-tested, not claimed observed during initialization. No cancellation, signal or scheduler model is implied.

Added bounded memchr and strchr models use only known bytes, stop at the first match/terminator, and never consult host libc. The observed memchr frontier is followed through to the last callback without further external-call assumptions. All earlier explicit TLS, clock, entropy, C-locale, opaque-stdio, loader and sparse-memory scenario inputs remain in force. The PSHUFB correction from the previous cohort remains enabled.

## Next: JNI lifecycle

A preliminary post-initializer JNI_OnLoad probe, using an explicitly opaque virtual JavaVM table, advances346001 completed instruction/model invocations and stops on that unknown table atPC0x4120f6. Static bytes show copying64 bytes of the invoke table, followed by a call through offset0x30(GetEnv), requesting0x000a0000. This is a new frontend to investigate; no real JVM call was made and no Java/native registration is yet claimed. Preserve the completed-initializer checkpoint separately from JNI experiments.

Continue with an explicit JNI invocation-table contract and pinned Java-version input. Record native method names/descriptors/pointers only when observed and validate against the original JAR before mapping promotion. JNI_OnUnload, Android/Windows bodies and other platforms remain separate tasks.

## Reproduction and references

Use tools/native_initializer_sequence_ysm_265.py with the exact original ELF outside Git, a trusted prior guarded checkpoint, --out and --checkpoint-out outside Git. It now uses SyncGuardedCPU, a sparse CPU subclass. The default basic backend is still readonly. Re-run the scoped cohort tests together after meaningful batches, not whole-repository CI for individual models.

- [POSIX unnamed semaphore initialization](https://pubs.opengroup.org/onlinepubs/9699919799.2008edition/functions/sem_init.html)
- [glibc sem_t Linux ABI](https://github.com/bminor/glibc/blob/master/sysdeps/unix/sysv/linux/bits/semaphore.h)
- [glibc sem_init](https://github.com/bminor/glibc/blob/master/nptl/sem_init.c), [sem_post](https://github.com/bminor/glibc/blob/master/nptl/sem_post.c), [sem_wait/trywait](https://github.com/bminor/glibc/blob/master/nptl/sem_wait.c), [sem_destroy](https://github.com/bminor/glibc/blob/master/nptl/sem_destroy.c)

No target host-native execution, host synchronization, filesystem/entropy access, host permission changes or binary redistribution occurs. The original ELF/JAR stays immutable; only the simulated working state changes.
