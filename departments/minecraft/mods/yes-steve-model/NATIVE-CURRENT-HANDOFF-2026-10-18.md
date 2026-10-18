# Current YSM native-analysis handoff — October 18

Read this entry first. Current report: [DT_INIT return](NATIVE-DT-INIT-RETURN-RESULT-2026-10-18.md). Branch: jolly/ysm-analysis-20261016. The project remains unfinished. Older linked reports describe historical states, not today's frontier.

## Goal and unchanged confidence

Recover reusable entity state → Molang → controller → bone → renderer behavior from the exact release artifact. Native initialization and Java/native bindings are separate tasks. Java map remains669 entries (405 CONFIRMED+264 HIGH), SHA-256 dc7abc78b1db9401b89ded2e97e2d8341179ccb62d69aa67698c87d8a7174e30. No native cohort has promoted a mapping. Independent semantic review NOT_RUN. Counts of instructions, tests or mappings are not completion percentages.

## Exact input

- Modrinth version Zqooxsd2, YSM2.6.5 Forge1.20.1 release.
- JAR SHA-256 25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f.
- META-INF/native/libysm-core.so SHA-256 15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22.
- Keep original binaries, package installations, Ghidra projects, snapshots and raw traces outside Git. Never infer they still exist in a replacement environment.

## Current DT_INIT route

Entry0x152eb19 is simulated with a protected Unicorn2.1.4 backend and explicit synthetic environment inputs. Its immutable file/reference is preserved. The separate opt-in working-image driver permits only bounded recorded guest-state writes with transactional rollback and complete expected-image verification. No target host-native execution, real imports or OS permission changes occur.

Two masked CRC32 loops have pinned code/table contracts and60 full-state differential cases. Fifteen summaries cover528,156,776 logical loop-instruction effects; these are not actually interpreted instruction counts. CRC acceleration turns off conservatively after any working-image mutation.

Current working-image ledger contains two eight-byte context/object pointers at0xedf060 and0xedf068. A fresh full run now completes DT_INIT:3,290,734 native instruction/model invocations, final RET0x1d963d, declared return sentinel and exact post-return stack. This is conditional DT_INIT completion only;45 init-array callbacks and JNI lifecycle remain.

The latest completed-DT_INIT checkpoint preserves full CPU/private/image/model state and CRC diagnostics. Prepare the next callback frame rather than resuming its sentinel RIP. Early snapshots omitted CRC diagnostic counts; their prior CRC history is now explicitly marked incomplete. Architectural/private-state restart equivalence was independently checked against a fresh full-prefix run; see the checkpoint report for exact scope.

## Reuse and runtime contracts

- tools/native_unicorn_guarded_ysm_265.py: default read-only image, known/opaque bytes, private heap, virtual clock/proc/file/loader/platform inputs; unsupported operations stop.
- tools/native_crc32_loop_profile_ysm_265.py: two exact masked-CRC profiles; full architectural/scratch-state summary, not unchecked loop skipping.
- tools/native_shadow_image_ysm_265.py: opt-in separate simulated working-image state, protection restoration, bounded lazy C++ allocations and private memset.
- tools/native_guarded_checkpoint_ysm_265.py: trusted local JSON checkpoint and bounded restore; no pickle.
- CLI shadow run requires --image ORIGINAL_SO --out EXTERNAL_TRACE; optional --checkpoint-out EXTERNAL_JSON or --resume-checkpoint EXTERNAL_JSON. Model inputs are explicitly synthetic; no claim of real OS/CPU metadata.
- Official Unicorn2.1.4 wheel SHA-256 9d6e6dea140560de4ebd8446661f7ef84a357d428c14a3ef09dacd306ec8c239. Use an external venv, not a committed installation.

## Important corrections and other unfinished fronts

Ghidra12.1.4 memory XCHG32 upper-register clearing and SHR overflow-flag behavior disagreed with independent authored CPU fixtures. XCHG normalization was added to the Ghidra harness; its SHR issue remains. Prefer the guarded Unicorn backend for continued CPU execution. Keep Ghidra for byte-verified static inspection. A normal Unicorn write-hook emu_stop is not a pre-write barrier; transactions and page guards are essential.

CPUID leaf1 ignores incoming ECX. File-backed executable addresses below0x1000 are valid in this ELF;0xf38 is protected code. Address0 still stops. These corrected harness assumptions must not be reported as target bugs.

JNI_OnLoad's conditional candidate continuations still depend on file-state words0xd2cd48..0xd2cd5a. DT_INIT progress is not proof that those words retain their file values in real runtime. JNI_OnUnload,45 init-array callbacks, Android bodies and Windows virtual-only export regions remain separate unresolved work. Windows RVAs are not file offsets.

## Historical evidence index

These reports retain exact previous scopes, source hashes and limitations. Do not treat a historical pending frontier as current.
- [first guarded image-state store](NATIVE-FIRST-IMAGE-STATE-WRITE-RESULT-2026-10-18.md)
- [continuation](NATIVE-CONTINUATION-RECOVERY-2026-10-18.md)
- [prologue](NATIVE-INIT-PROLOGUE-RECOVERY-2026-10-18.md)
- [further guard chain](NATIVE-INIT-GUARD-CHAIN-RECOVERY-2026-10-18.md)
- [Inventory](NATIVE-INITIALIZER-INVENTORY-RECOVERY-2026-10-17.md)
- [Write/import audit](NATIVE-INITIALIZER-WRITE-AUDIT-RECOVERY-2026-10-18.md)
- [cross-check recovery](NATIVE-GHIDRA-CROSSCHECK-RECOVERY-2026-10-18.md)
- [static propagation probe](NATIVE-STATIC-PROPAGATION-PROBE-RECOVERY-2026-10-18.md)
- [bounded result](NATIVE-BOUNDED-SIMULATION-RESULT-2026-10-18.md)

- [working-image/checkpoint evidence](NATIVE-SHADOW-CHECKPOINT-RESULT-2026-10-18.md)
