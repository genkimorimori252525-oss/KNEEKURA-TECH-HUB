# TLS and sparse allocator initialization — October 18

## Result and scope

The guarded single-thread scenario completes callbacks0..16 in order: **17/45**, about38% of this initializer-array phase only. Callback17(entry0x33b3e0) reaches sem_init(index34), caller-return0x33b778, with semaphore0x404001014248, pshared0, initialvalue0. No overall deobfuscation-completion percentage is claimed. JNI lifecycle/bindings remain separate.

The final replay starts from the previously verified eight-callback checkpoint, not a new full DT_INIT run. It executes49339 attempted instruction/model invocations; cumulative completed count3366644. A second replay from the intermediate pre-SIMD TLS checkpoint reaches the identical complete checkpoint SHA-256 ed4375dcbf24407d44e22b88a637cc6c928b4d21d8449288e8f49b8c30a10e4b. CPU payload, private memory/initialized masks, sparse pages, image patches and model state match. Nothing is ignored beyond the previously documented unused Unicorn memory-snapshot header.

Evidence: [machine-readable receipt](NATIVE-TLS-SPARSE-INITIALIZERS-2026-10-18.json). Scoped batch regression:224 test methods pass, with additional parameterized cases. Independent semantic review NOT_RUN. Java map stays669 entries,405 CONFIRMED+264 HIGH; no promotions.

## Explicit virtual environment

- TLS: one virtual module/thread, template216 bytes, total15408 bytes, alignment16. Three exact DTPMOD64 descriptors receive moduleID1 in the working copy; offsets share one private block. Template copies current initialized bytes; BSS alone is zero-filled. No host TLS. Destructor registration records callback/argument/DSO tuples without running callbacks or registering with the host.
- Anonymous memory: guest requests256GiB plus16MiB. Reservation is interval metadata, not a host-sized allocation. Final virtual total274894684160 bytes;34 materialized pages,139264 guest backing bytes. Cap2048 pages/8MiB,1TiBvirtual,64regions. Anonymous initial bytes are zero; executable permission is rejected. Native stores use rollback journals and a separate complete page ledger.
- The native allocator has snmalloc strings/call patterns. This identifies the family, not its exact upstream version. Only observed anonymous mmap flags and VMA naming requests are modeled. munmap/mprotect/madvise affect virtual intervals/pages only.
- errno begins at explicitly chosen2(ENOENT). This is a scenario input, not recovered host errno. Earlier unavailable-open behavior had no errno model. Reads of /dev/urandom use a bounded deterministic SHA256 fixture with the seed recorded in JSON; there is no entropy or filesystem access. A monotonic clock starts at0 and advances1ms per modeled call. Other clocks/paths/flags stop.
- Original ELF/JAR and immutable image reference stay unchanged. Guest image writes remain bounded, logged and verified against the working-copy ledger. No actual target native library/JNI/import execution, OS permission changes, host thread creation or large host reservation occurs.

## Important emulator defect found and corrected

Batch-versus-checkpoint comparison initially failed on upper384 bits of ZMM0. The first mutation followed legacy PSHUFB at0x576703(bytes660f3800c1). Unicorn2.1.4's helper fills16 bytes of a64-byte temporary ZMMReg and assigns the whole temporary, copying uninitialized upper bytes. This is an emulator defect, not evidence of target behavior.

The bounded decoder now models legacy register-to-register PSHUFB: zero when controlbit7 is set, otherwise select the low-nibble source byte; preserve upper384 bits, flags and other registers. Memory forms stop rather than use the faulty helper. Tests cover all256 register pairs, all256 control-byte values and64 random cases. An independent assistant-authored SSSE3 C oracle matches256 low128-bit permutation cases. Only this small authored oracle ran natively; no YSM code did.

The corrected replays retain the same17 callbacks and guest-memory outcome and now match the full CPU context. Uncorrected exploratory sparse/thread-dtor/monotonic checkpoints are superseded and must not be used to continue. Resume the corrected pshufb-heap-pool checkpoint, or reconstruct it from the prior verified eight-callback checkpoint. Do not mask the mismatching vector bytes in comparisons.

Own-byte sparse tests also exposed a pending-store rollback edge: after a quota rejection, the invalid-memory hook could still materialize an unmapped page. The hook now refuses recovery once stopped. Cross-page, partial-backed, readonly, quota and checkpoint-negative fixtures cover this correction.

## Reuse and continuation

New modules are native_tls_fixture_ysm_265.py, native_sparse_vm_ysm_265.py, native_allocator_os_fixture_ysm_265.py and native_pshufb_semantics_ysm_265.py. The initializer driver selects the sparse subclass; the default readonly backend remains readonly. Checkpoints include sparse pages, permissions, entropy/errno/clock state and TLS/destructor records. No original binaries or raw snapshots are committed.

Next: establish sem_init's observed private semaphore contract and continue callback17. Do not silently return success from waits, pthread_once, thread creation or other synchronization operations; their actual callback/scheduling effects require explicit modeling. Unresolved C++ external objects remain guarded. Continue scoped batches, then one combined verification.

## Primary references

- [ELF TLS ABI](https://www.akkadia.org/drepper/tls.pdf)
- [snmalloc Linux PAL](https://github.com/microsoft/snmalloc/blob/main/src/snmalloc/pal/pal_linux.h), comparison only; exact target version not established
- [glibc TLS destructor registration](https://github.com/bminor/glibc/blob/master/stdlib/cxa_thread_atexit_impl.c)
- [Unicorn2.1.4 SSSE3 helper source](https://github.com/unicorn-engine/unicorn/blob/2.1.4/qemu/target/i386/ops_sse.h)
- [Unicorn2.1.4 ZMM register representation](https://github.com/unicorn-engine/unicorn/blob/2.1.4/qemu/target/i386/cpu.h)
