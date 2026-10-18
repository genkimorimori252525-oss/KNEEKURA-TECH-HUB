# JNI artifact bridge and bounded continuation

## Result and limits

All 45 initializers remain complete in the declared isolated scenario. JNI_OnLoad now reaches two GetEnv calls and exact Java metadata lookups for:

- java/io/File.<init>(Ljava/lang/String;)V
- java/io/File.toPath()Ljava/nio/file/Path;
- java/nio/file/Path.toString()Ljava/lang/String;

These three lookups are standard-library method metadata, **not three recovered YSM native bindings**. There are still no recovered RegisterNatives registrations. The existing 669-entry Java map is unchanged. Independent semantic review is NOT_RUN. No original native library or JVM body executed on the host.

The bounded continuation currently stops on a private stack boundary: PC 0x32a4cb attempts an eight-byte store at 0x6fffffffff90, RSP 0x6fffffffff50. The original fixture provides only 32 KiB below its entry SP. The trace shows a recursive guest call path through 0x32a4b0. This is a fixture-capacity frontier; an explicit 1 MiB stack extension has now passed this frontier, although JNI completion is not yet established. Do not describe it as a target bug or silently grant unbounded memory.

Machine-readable evidence, exact source hashes, checkpoint hash, metadata proofs and actual-checkpoint differential reports are in [the paired receipt](NATIVE-JNI-ARTIFACT-BRIDGE-2026-10-18.json).

## Read-only artifact-backed environment

The supplied Temurin 21.0.12.1+1 libjvm.so is 26,963,256 bytes, SHA-256 462fa559157ee8a862e7e4b8a4a74f8abbf5e1a9deb64f22ee23c7e8c43f698b. java.base.jmod SHA-256 is f8d258a856a691c81ad9dd16964635bbc8a8fdd7f40edec37dcf3d904feb7ae1. Keep these inputs and their original archives outside Git. This JDK is a declared analysis input, not a claim about the user's installed runtime.

- JNIEnv has JNI10's 234 slots; JavaVM has eight invoke slots. All 235 nonreserved function pointers are uniquely resolved from the supplied JVM's local function symbols. Guards intercept each modeled entry before its first JVM instruction. Neighboring JVM code remains forbidden.
- Nonwritable JVM PT_LOAD file bytes are available for inspection. Writable runtime segments and BSS remain unknown. Immutable-view verification is required before checkpointing.
- dlopen, dlsym and dladdr are explicit bounded virtual models. No host loader is called. Only artifact-proven definitions are resolved; local symbols are not presented as exported dladdr names.
- dl_iterate_phdr actually invokes the guest callback for the declared YSM and JVM modules, respecting early nonzero return, stack and callee-saved ABI. Unknown JVM TLS fields remain unknown.
- Three JVM function imports are guarded and bound: JNI_GetCreatedJavaVMs, JNI_CreateJavaVM and JNI_GetDefaultJavaVMInitArgs. This does not authorize calling their real bodies.
- Java class and method availability is verified from immutable JAR/JMOD classfiles. No Java bytecode is executed. Changed archives, module bytes or interface addresses require a fresh scenario.
- File paths, stat attributes other than artifact size, clock, entropy, CPUID and locale remain explicit synthetic inputs. They are not observations of a real host.

Earlier placeholder-JVM experiments returned JNI_ERR with a pending RuntimeException. Exact target instructions compare the module file size against 0xa00000 at 0x3ddb53 and take the failure branch at 0x3ddb59 for the placeholder size zero. The actual supplied artifact passes that size comparison. Those negative experiments are superseded as continuation seeds, not evidence of a real YSM failure. Exceptions were not cleared to force success.

## Guarded acceleration and tests

The scoped 30-module suite passes 371 test methods, including 15 stack-layout/migration tests and 29 batched-engine differential tests. Three additional masked-CRC profiles have 90 full-state differential cases across lengths and seeds, including GPRs, flags, ZMM state, scratch bytes and known-byte masks. Code, all 256 table entries and immutable source bytes are checked before summary use. Unlike the two older profiles, these profiles can operate after unrelated working-image writes; changed source bytes still reject acceleration.

Two actual checkpoint A/B comparisons also pass: profile 0x111f65b consumes 3,953 bytes (138,355 native steps versus 36 summary-path invocations); profile 0xfdb44c consumes 3,985 bytes (95,640 versus 25). Logical effects and remaining complete state match. Acceleration counters/configuration and rollback diagnostics are explicitly distinguished from semantic state.

Unicorn 2.1.4's pinned x86 CPU context includes a host translation return address at bytes 5600..5607. That host-only pointer and unused memory-snapshot header fields are normalized; all remaining context bytes are compared. This is source-backed by Unicorn's CPUX86State.retaddr, offsetof(end_reset_fields) context size, and x86_cpu_tlb_fill assignment. Guest registers or vector bytes are never masked to hide differences.

Sources: [JNI invocation specification](https://docs.oracle.com/en/java/javase/17/docs/specs/jni/invocation.html), [Unicorn CPU context layout](https://github.com/unicorn-engine/unicorn/blob/2.1.4/qemu/target/i386/cpu.h), [context size](https://github.com/unicorn-engine/unicorn/blob/2.1.4/qemu/target/i386/unicorn.c), [host return address assignment](https://github.com/unicorn-engine/unicorn/blob/2.1.4/qemu/target/i386/excp_helper.c).

## Continue

Use tools/native_jni_onload_ysm_265.py with explicit --image, --jvm-image, --java-base and --jar inputs. Supply either --initializer-checkpoint for a completed initializer state or --resume-jni-checkpoint for an unfinished JNI state, plus external --out and --checkpoint-out paths. Default budgets are four million invocations and 180 seconds; a budget/frontier stop is not completion.

The current resume snapshot is unicorn-jni-crc-fast-next.checkpoint.json (hash in receipt). Preserve it unchanged before testing any explicit stack-capacity extension. The fresh initializer snapshot with all three JVM imports guarded is unicorn-init-jvm-guard-fresh.checkpoint.json. Earlier fixture/table variants must not be mixed with the current scenario. Optional --batch-size 256 now selects a guarded batched CPU; the default remains the single-step backend. An actual 100,000-instruction continuation compared both backends after the same explicit stack migration: the complete serialized checkpoint hashes are identical (87132c24260938fac37a83357f6d23a4d8a423cab5a45c26599b671704de1514). Timings were 2.541 versus 1.528 seconds in this run, not a universal speed guarantee. Executable-page stores end a batch so Unicorn self-modifying-code replay behavior stays consistent with the single-step backend.

The stack now spans [0x6ffffff10000,0x700000010000), with entry SP unchanged at 0x700000008008. Added 960 KiB bytes are unknown until written. Legacy checkpoints require --allow-stack-extension in the JNI driver; migration validates exact original regions/lengths/masks, records scenario provenance and does not assert equivalence to the small-stack scenario. Newly written checkpoints resume without that flag. Other older drivers deliberately reject old-layout snapshots unless callers explicitly opt into the migration API. Cross-layout checkpoint comparison reports mismatch rather than pretending equality.
