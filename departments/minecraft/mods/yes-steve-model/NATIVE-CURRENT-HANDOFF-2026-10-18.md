# Current native-analysis handoff — October 18

Read this before resuming native work. Latest entry: [second CRC summary and CPUID frontier](NATIVE-SECOND-CRC-FRONTIER-RESULT-2026-10-18.md). Branch: `jolly/ysm-analysis-20261016`. Last verified analysis publication before this handoff: `02fc35cdbc7a0fef0206dc9e2b08c835e1983e79`. The project is unfinished.

## Scope and confidence

Goal: reusable understanding of YSM's entity state, Molang, controllers, bones and rendering, with exact-artifact evidence. Java-side native declarations/callers are inventoried; native implementations and runtime Java/native bindings are not recovered as a whole.

Central mapping remains 669 entries (405 CONFIRMED + 264 HIGH); mapping-file SHA-256 is dc7abc78b1db9401b89ded2e97e2d8341179ccb62d69aa67698c87d8a7174e30. These native cohorts make no mapping promotion. PRIMARY_STATIC_REVIEW_ONLY, independent semantic review NOT_RUN. Test counts, addresses, prefixes and file-state candidates are not completion percentages.

## Exact inputs

- Modrinth release Zqooxsd2: [original JAR](https://cdn.modrinth.com/data/86xjpqqS/versions/Zqooxsd2/ysm-2.6.5-forge%2Bmc1.20.1-release.jar).
- JAR SHA-256: 25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f.
- Linux member META-INF/native/libysm-core.so SHA-256: 15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22.
- Keep original binaries, downloaded tools, raw disassembly/lifts and Ghidra project databases outside Git. Temporary environments can lose these files; do not infer that a past tool output is still present.

## Two separate Linux frontiers

### JNI_OnLoad path

The retained scalar/interval work gives conditional third/fourth return candidates 0xf69c60 and 0x132d8e6, plus two computed transfers and a parity predicate. See [continuation](NATIVE-CONTINUATION-RECOVERY-2026-10-18.md). These depend on file-state bytes at 0xd2cd48..0xd2cd5a retaining their values. Initializer effects remain unresolved. Do not confuse this path with DT_INIT.

### DT_INIT path

The entry is 0x152eb19. The [prologue](NATIVE-INIT-PROLOGUE-RECOVERY-2026-10-18.md) resolves three predicates and first rewritten-return candidate 0x1499584. A previously unknown-looking stack DWORD is the earlier literal 0x162e9a61 at original RSP-8; preserve that proof rather than guessing an incoming register.

The [further guard chain](NATIVE-INIT-GUARD-CHAIN-RECOVERY-2026-10-18.md) resolves JB/JNS/JA at 0x14995c7, 0x1603de3 and 0x1444517. The current frontier is RET 0x18 at 0x1539420. Its concrete destination is unresolved. File word 0x14c9bd5, relative key 0x14c9bd9 and initial delta 0xffde8fe9 belong to DT_INIT, not JNI_OnLoad.

JNI_OnUnload's earlier JE frontier is still unresolved. Android work is limited to headers/exports/initial branch evidence. Windows exports occupy virtual-only sections in the file layout; do not read RVA values as file offsets or claim recovered Windows bodies.

## Initializer effects: important negative boundaries

- [Inventory](NATIVE-INITIALIZER-INVENTORY-RECOVERY-2026-10-17.md): 45 zero raw init-array slots resolve via RELATIVE relocations; two fini slots are separate. DT_INIT is separate again.
- [Write/import audit](NATIVE-INITIALIZER-WRITE-AUDIT-RECOVERY-2026-10-18.md): 70 direct writes in 46 first-transfer prefixes do not overlap the watched 19 bytes. There are 146 unresolved STORE operations plus uninspected continuations/callees. This is NOT an immutability proof.
- Two-hop stubs resolve declared imports __cxa_atexit (11 prefix sites) and secure_getenv (one). Callback registration is not immediate callback execution. GLIBCXX_TUNABLES supports a shared C++ exception-runtime attribution hypothesis, not an exact compiler-version or whole-function identity claim.

## Reproducible static tools

Ghidra 12.1.4 and a full JDK 21.0.12.1+1 were approved, installed and verified. The existing Java runtime alone lacked javac. Official package hashes and recovery details are in [cross-check recovery](NATIVE-GHIDRA-CROSSCHECK-RECOVERY-2026-10-18.md).

`tools/ghidra/run-scoped-lift.sh` takes the exact JAR and a NEW external output directory, with GHIDRA_HOME and JAVA_HOME supplied. It verifies input hashes and creates a static project with image base zero, relocation application/external-library loading/automatic analysis disabled. HOME/XDG/cache are scoped to the output directory. The target library is not loaded for host execution.

Fixed manifests/receipts are retained separately: 73 ranges / 673 instruction occurrences; 83 / 760; 105 / 940; latest 112 / 1013. All seven file-backed PT_LOAD segments match. Do not overwrite old receipts with a larger scope. The baseline has 669 unique instruction addresses; that number is unrelated to the 669 Java mappings.

Import logs include 47 zero-slot function-creation warnings and 233 unresolved external symbols under the deliberately non-relocated/no-library configuration. The byte-verified lift is usable; this is not a fully analyzed runtime program.

## Automatic propagation and bounded simulation

The [static propagation probe](NATIVE-STATIC-PROPAGATION-PROBE-RECOVERY-2026-10-18.md) is INCOMPLETE. It matches ZF=0 at the first DT_INIT predicate, then stops with unknown CF at 0x16668ff (87 before-instruction records, 400 visited bytes). It does not replace the explicit byte-interval proof. Unknown values were not filled with zero.

The owner approved isolated DT_INIT simulation, then explicitly requested continuing with lock-marker support. The [bounded result](NATIVE-BOUNDED-SIMULATION-RESULT-2026-10-18.md) and receipt supersede the previous pending status. The current harness passes 16 toy tests (14 guards and two safe inspection checks). The strict target trial completed 9,203 steps and stopped at uninitialized stack read 0x700000007d90 in REP MOVSB at 0x143beae. The latest optional opaque-copy trial completes 10,000 steps and stops at the original instruction limit before 0x1446652, with all 47 reached old oracle checks matching. No non-stack write applied; original file and seven program segments preserved. This is one synthetic initial-state path, not actual MOD/JNI runtime validation.

LOCK/UNLOCK are modeled only for paired XCHG atomicity markers in a single isolated emulator thread; all other userops remain forbidden. Preserve unknown stack bytes. The old static RET frontier 0x1539420 has observed synthetic successors 0x1499584 (seven times) and 0x15ced58 (once); exhaustive/static proof remains separate. The stopped copy has now been identified as a 328-byte forward stack-to-stack relocation; 96 bytes completed, then the source at initial RSP-0x278 was uninitialized. See the result and copy-frontier receipt. A diagnostic replay is trace-identical except for read-only stop registers. Ghidra increments string-op pointers before LOAD, so those stopped registers are partial micro-op state. The full stopped-source observer finds 248 known and 80 unknown bytes. Conditional static post-copy evidence proves three local predicates and candidate R11=0x143fd9e without running beyond the stopped read. See NATIVE-POSTCOPY-CONTRACT-2026-10-18.json and the result narrative. The optional opaque-copy model now preserves unknown origin identities without concrete substitution; ordinary reads of those values still halt. Its 24 tests include ten differential concrete-copy comparisons. It reaches two completed stack copies and the 10,000-step limit; see NATIVE-OPAQUE-COPY-TRIAL-2026-10-18.json. The 100,000-step extension is requested but NOT approved/run as of this handoff update. Keep the old cap until the actual owner response is checked.

## Resume discipline

1. Check actual environment files, branch/diffs and remote head; preserve other work.
2. Restore missing tools/inputs from verified sources only as authorized; use persisted scripts, not a claim that a lost temporary trace still exists.
3. Respect the approved simulation bounds and latest stopped-read frontier. Keep unsupported input state unknown; static diagnosis can proceed without treating a tool stop as the end of the research task.
4. Publish derived evidence with explicit assumptions and verify the remote commit/tree. Keep batches scoped; no full-project CI, self-hosted runner, merge or deployment is part of this work.

## Latest read-only validation

NATIVE-SIMULATION-DECODER-CROSSCHECK-2026-10-18.json verifies the 10,000-step trace's 3,557 unique instruction addresses across 238 contiguous groups against GNU objdump and the original file-backed ELF bytes. Six parser/grouping tests pass. This is decoder-boundary/byte agreement, not semantic equivalence or completed native recovery. The instruction-budget expansion remains pending; do not infer approval from completed evidence saving.

## Newest frontier and scope (supersedes earlier pending-budget text)

The 100,000-step increase was approved and used. Start with NATIVE-VIRTUAL-CLOCK-RESULT-2026-10-18.md and its receipt. Clock-disabled mode stops at RDTSC after 28,869 completed steps. Three explicit clock samples show input-sensitive paths: two hit 100,000 cap, the mixed seed reaches a malloc import boundary after 48,846 completed steps. Raw slot 0x184d828 is zero because relocations were disabled; ELF GLOB_DAT symbol277 names malloc. RDI requests424 bytes; caller return candidate0x13d91f2. No actual import was executed. Tests17+24+8pass, original hashes preserved.

The owner approved the next virtual-heap/malloc stage: maximum1MiB, allow private-stack and virtual-heap writes, stop before original-image writes, retain100000-step bound and no actual external/OS calls. Not yet implemented/run. Avoid unnecessary confirmation for safe reversible changes within the requested isolated analysis. Existing absolute-RSP oracle at0x174d06f was proved for the original entry context; scope it to that entry before reusing the harness across later protected prologues, rather than forcing a later caller frame to match.

## Latest verified heap/model checkpoint

NATIVE-VIRTUAL-HEAP-RESULT-2026-10-18.md supersedes the older not-yet-run heap status. The isolated malloc model allocates424 bytes and records seven8-byte object writes. A genuine pinned-Ghidra memory-XCHG32 zero-extension discrepancy was reproduced with a toy and independently with36 host toy cases (no target code). A focused post-instruction normalization fixes only that ISA effect.102harness tests pass. Replayed clock paths remain identical; corrected heap run reaches100000cap before0x1815afd, with28normalizations and no original-image write. The old63,810-step out-of-region write is an emulator artifact, not native behavior. Oracles are first-visit-scoped (12checks), avoiding invalid absolute-RSP assumptions across reused prologues. Working mode remains explicit synthetic clock+virtual heap, not actual runtime.

## Current execution caution

A second Ghidra discrepancy (SHR masked-count1 overflow flag) is confirmed by a toy and4096 independent host-toy cases, but not corrected in the retained Ghidra script. File failure and two authored proc-status fixtures all stop before any fgets/fclose at the same bad read. Do not infer TracerPid behavior or actual native failure from them. Unicorn2.1.4 is installed in an isolated external venv for an independent backend; only own-byte preflight has run. Normal Unicorn write-hook emu_stop still permits the write, so target work requires protected image pages plus tested transactional private-state guards first. Next implement/validate that bounded guard; no target Unicorn execution yet.

## Latest independent-backend result

Unicorn guarded backend is now implemented and24toy tests pass. Original pages are read/execute-only; rejected private candidate writes and CPU state roll back atomically. Strict9204-step prefix matches Ghidra; corrected SHR/JL path diverges at step175518 as expected. Two virtual proc fixtures each reach500000; TracerPid0 extended run reaches2000000 and fclose, with no image writes. Caller/clock/heap/file remain explicit models, not actual runtime. Current useful optimization: prove and accelerate the28-instruction masked-table CRC32 loop (standard table XOR0xa30cc68d, canceled each iteration), preserving all outputs and stack effects. No acceleration implemented yet. See NATIVE-UNICORN-GUARDED-RESULT-2026-10-18.md.

## Latest checkpoint: verified CRC summary

The optional CRC summary passes 30 full-state differential cases and reaches dladdr after nine summarized blocks. See the latest entry above; older frontiers and pending-optimization sections are historical. No target host execution or original-image mutation.

## Latest checkpoint: loader/platform scenarios

Both declared loader scenarios reach mprotect(0xec5000,0x510e52,7). No host or guest permission change applied; see latest entry and paired JSON. Older frontier statements remain historical.

## Latest checkpoint: second CRC and CPUID

Two-profile validated summaries reach CPUID leaf1,0x16b44ff. Protection-return inputs never change permissions; all original-image writes still blocked. See latest entry; earlier frontiers are historical.
