# Experimental bridge source coverage — 2026-10-01

Status: **X0–X7 bounded source coverage mapped and connected, including X5. Independent X4/X6 source review performed; post-seal packet substitution rejected. Pre-seal filesystem writer trust remains an explicit assumption. Live acceptance deferred.**

This is a source-to-plan coverage record, not runtime acceptance or a new technical approval. The original mapping did not perform tests, X4/X6 technical review or Minecraft launches; the continuation verification below records later work separately. No live acceptance has been completed. The repositories retain their separate owners and evidence stores.

The authoritative design is TECH HUB's `docs/superpowers/specs/2026-10-01-minecraft-mod-ai-experimental-runtime-bridge-design.md` (the approved 2026-10-01 design). Section and line references below identify that design. `TECH` paths are relative to TECH HUB; unqualified implementation paths are relative to LAB.

## Required source coverage

| Phase and design requirement | Existing implementation and source evidence | Remaining boundary |
|---|---|---|
| X0 — strict request/result, linkage and UNKNOWN (§4.1–4.2; §19, lines 1166–1175) | TECH `src/kneekura_tech_hub/minecraft/experiment_contract.py` validates bounded typed requests, identities, evidence planes and per-assertion results. `tests/test_minecraft_experiment_contract.py` covers strict shape, uncertainty and fixed comparison semantics. | No additional required source seam identified by this mapping. Schema validity does not establish runtime truth. |
| X1 — identities survive the handoff and returned RunSnapshot (§6; §19, lines 1177–1182) | TECH `experiment_bridge.py` prepares exact request/assertion bytes and validates immutable result/snapshot import. LAB `debug-workspace/bridge/registration.mjs`, `owner-prelaunch.mjs` and `debug-workspace/core.mjs` bind the original request to initial RunSnapshot construction. Registration and private export roundtrip fixtures cover cross-repository linkage. | Loaded target/config/resource/transformed-class equivalence remains NOT_ESTABLISHED in scoped diagnostic mode. |
| X2 — Arena baseline, bounded mutation, reset, receipts and interruptions (§19, lines 1184–1194; §20 Arena) | Java `KneekuraDebugArenaController`, `KneekuraDebugForgeArenaBackend`, `KneekuraDebugArenaRuntime`, `KneekuraDebugActionJournal` and `KneekuraDebugOwnerConnection` implement the bounded server-thread owner path. Explicit action/cleanup transport retains the existing journal and replay fences. Portable Java, real Forge API and paired control fixtures are recorded. | Actual reset/action/interruption/cleanup acceptance is unperformed. Reset covers only the declared supported state classes. Item use is explicitly excluded; see below. |
| X3 — one-client Cardinal-4 capture with exact identity (§9.1; §19, lines 1196–1200) | Java `KneekuraDebugCardinalCapture`, capture barrier/session/policy/restoration classes, owner connection and existing evidence writer provide the source path. `debug-workspace/evidence/visual-capture.mjs` validates retained raw manifests/images. Source protocol and actual API compilation records exist. | Real pause/barrier behavior, capture geometry, restoration and observer effect remain unverified. Sequential frames are not same-frame capture. |
| X4 — visual compiler and dual presentation (§10–11C; §19, lines 1202–1224) | `visual-compiler.mjs`, `visual-packet.mjs`, `visual-geometry.mjs`, `visual-presentation.mjs` and `visual-artifacts.mjs` provide sheets, labels, schematic, crops, bounded checks, lineage and separate human/AI presentations. Continuation review fixed weaker retained-check validation and post-finalization packet substitution. | Pre-seal writer trust is not compiler attestation. The visual-format benchmark and live capture acceptance remain open; the packet format is provisional. |
| X5 — selected event triggers bind to bounded pre/post capture (§12; §19, lines 1226–1230) | Private pinned trigger configuration → finite explicit watch → canonical native ARENA_EXIT event → existing fixed capture slot → immutable retained window is integrated. It reuses `EvidenceRuntime`, `TriggerCaptureController`, ring coverage and the existing writer. The paired Python/Node fixture exercises the actual source connection. | Real event-window and timing acceptance remains unperformed. Pre-roll is retained evidence only; absent or sub-millisecond-ambiguous samples remain MISSING. |
| X6 — matched before/after bundles (§13; §19, lines 1232–1234) | `debug-workspace/evidence/visual-comparison.mjs` and its tests provide exact request/setup/camera matching, explicitly declared target changes, four-row comparison images and separately attributed structured/timeline evidence. TECH also validates request comparison semantics. Continuation source review found no additional X6 issue. | Actual matched repair evidence is unperformed. A matched evidence bundle does not itself establish improvement. |
| X7 — TaskContext, explicit handoff, retained resume and repair lesson (§16–17; §19, lines 1236–1254) | TECH `experiment_adapter.py`, `experiment_control.py`, `experiment_export.py`, `experiment_bridge.py`, `task_context.py` and `task_routing.py` connect pinned control, private import and inert retained-evidence resume. LAB `owner-control-cli.mjs`, `result-export.mjs` and the existing finalizer return retained evidence. TECH's existing `history.py` supports evidence-linked repair lessons without a new database. Paired export/control and resume fixtures exist. | One real reproduce → repair → same experiment → compare cycle, second-AI resume and verified lesson remain unperformed. The scoped exporter cannot emit definitive behavior acceptance; see below. |

Java names above refer to `debug-workspace/forge-bridge/src/main/java/com/github/tartaricacid/touhoulittlemaid/sim/debug/`. TECH module names after X0 refer to the same `src/kneekura_tech_hub/minecraft/` package.

## X5 integrated source connection

`debug-workspace/bridge/owner-trigger-config.mjs` and `owner-trigger-source.mjs` provide a sealed optional configuration and finite explicit watch. `KneekuraDebugOwnerTriggers` and the owner input/dispatch/connection hooks produce an observed inside-to-outside event for the exact registered subject. Unknown or unloaded state clears its transition baseline. Native capture requests retain their absolute trigger deadline; watch requests use fixed existing capture slots.

The integrated path preserves:

- Exact request/run/experiment/event Arena revision, deterministic capture slots, deadlines, cooldown/window budgets and replay fences
- Original canonical timestamps, exact dispatched native capture IDs and explicit actual sample timing; a delayed result is not represented as an exact nominal offset
- Strictly earlier parsed milliseconds for negative slots; precision the timestamp parser cannot establish remains missing
- TECH's 27-module pinned closure and optional `triggerConfigHash`, with inert ordinary reads and read-only reconciliation after every watch result

Independent X5 review passed 46 LAB trigger/finalization checks, 55 TECH trigger checks, native input/Forge API checks and the actual paired protocol. The paired gate covers precise timestamps, the reserved capture deadline, a PARTIAL window, fresh-Store duplicate UNKNOWN, cleanup and private six-blob import/resume. The reviewed 24-file LAB change and the separate paired fixture were byte-verified during integration. This review did not repeat the blocked X4/X6 review.

Real event-window coverage remains a separate runtime acceptance gate. Continuous full-resolution recording is outside the design.

## Explicit bounded scope and uncertainty

`use_item` is excluded by the approved bounded Arena plan, `docs/superpowers/plans/2026-10-01-lab-bounded-arena-actions.md`, line 26. That plan supports `wait_ticks`, bounded palette `set_block` and registered non-player `teleport_subject`; it rejects item use before acceptance/mutation. Original architectural X2 requires typed bounded actions but does not name `use_item`. Its presence in TECH's request vocabulary does not imply that this LAB backend supports it.

Reset restores only the supported captured block and subject-pose state. A scoped baseline match is not a whole-world clean result. Loaded config/resources, transformed class definitions and full target equivalence remain deliberately NOT_ESTABLISHED under both supported scoped linkage modes.

The current `debug-workspace/bridge/result-export.mjs` hardcodes cleanup to UNKNOWN except for NOT_RUN execution, and assertions to INCONCLUSIVE or NOT_RUN. Evidence sealing is not Arena cleanup. Real-machine execution alone cannot change this exporter's status projection; source test success cannot either.

This does not establish a missing mandatory automatic assertion evaluator. Original design §3 assigns interpretation and repair decisions to TECH; §4.2 requires per-assertion results while explicitly allowing non-success outcomes after completed execution; §5 fixes criteria before mutation without specifying a separate evaluation engine. The approved TECH contracts plan, `docs/superpowers/plans/2026-10-01-minecraft-experiment-contracts.md`, lines 29, 42 and 56, prohibits definitive behavior results under uncertain execution/cleanup and distinguishes report consistency from runtime truth. The scoped exporter preserves that uncertainty. It cannot close full repair verification (§20, lines 1354–1359) or the architectural stop condition (§24, lines 1428–1434).

Optional diagnostic render channels are conditional on demonstrated value (§11B). X8 synchronized multipass remains DEFERRED until a concrete defect demonstrates that the sequential X3 rig is insufficient (§19, lines 1256–1261); it is not predeclared NOT_NEEDED.

## Historical verification snapshot and separate gates

The following is the integration handoff snapshot supplied for this coverage record, not fresh verification of later changes:

- TECH hosted standalone source run: 3,085 passed, 332 skipped, 8 warnings
- TECH local integrated run: 3,312 passed, 104 skipped, and the known `test_private_parent_validation_allows_real_external_directory` sandbox-ancestor failure; this is not an exclusion-based pass
- LAB: Node source aggregate, 53 portable Java owner checks and actual-PID Node/Java interoperability passed; genuine Forge API compilation of 23 classes plus 16 writer/world checks passed
- Whole pinned private MOD compilation: blocked before tests by the hosted checkout's repository-read scope. Selected genuine API compilation is not a substitute for the whole MOD gate

Keep these outstanding categories separate:

- **Required bounded source:** X0–X7 paths above are connected; no additional mandatory source seam was identified by the final plan mapping. This statement is limited to the declared source stage, not full repair acceptance
- **Runtime/config prerequisites:** explicit private owner registration, exact pinned runtime inputs, an authorized disposable world, and real reset/capture/cleanup/repair evidence
- **Hosted CI access:** the pinned private-source read blocker above; no new credential, runner setting or validation location is implied
- **Review:** final independent X4/X6 review is UNPERFORMED/BLOCKED; author tests and this mapping do not replace it
- **Deferred acceptance:** real visual-format benchmark, repair/resume cycle and Windows/self-hosted runtime gates. Skipped or unrun gates are not passes

### Verification after X5 integration

The final integrated `npm run test:ci` passed after all timestamp/pre-roll refinements. One prior integrated attempt failed the existing source-only restart/stop fixture's strict `stoppedAgain.ok === true` assertion. A diagnostic reproduction and the final complete aggregate passed; the original temporary state was deleted by the fixture, so its exact cleanup reason remains unestablished. Both stop assertions now include sanitized state diagnostics without changing their expectations or any production stop logic. The earlier failed run is retained and is not recast as a pass.

The final TECH source suite recorded 3,325 passed, 146 skipped, 8 warnings and the same sandbox-ancestor fixture failure, without exclusions. Independent X5 verification and the final paired protocol above passed on hash-matched bytes. Whole pinned MOD compilation remains unrun behind the hosted checkout gate. Full `npm test` still stops at the existing browser-dependent palette fixture because the required browser is unavailable; no browser or Minecraft was launched in this code-first phase.

## Continuation review and local verification

Reviewed inputs were TECH HUB `bcb9ddeea5a06ac412d75972dccb605273f88d6b`, LAB `432dda9bc7b4ed33997a8cdefe145919bdc880ae`, and the pinned MOD `040866fa00ae96b5dcdcb02bae1fdc4ffdfdf5b1`. The following local results include the LAB continuation changes based on that LAB revision. Publication and hosted results are recorded separately below.

Independent review identified two corrected defects:

- A rehashed retained packet could contain an answered visual check with no camera evidence, duplicate checks/views, blank questions or altered semantics. `validatePacket` now enforces the compiler's bounded check contract at the human presentation and export boundary. `NOT_RUN` without evidence remains valid; answers remain INFERRED and never establish acceptance.
- On Windows/JDK17, directory `fileKey()` can be null. Ignoring directory size/mtime then allowed a different world at the same path to retain the original stamp. Creation time was rejected as a substitute after independent probes found natural collisions (11/64 replacements) and a writable timestamp bypass. The initial fix rejected null `fileKey` with `OWNER_DIRECTORY_IDENTITY_UNAVAILABLE`, before installing the scoped owner. The reviewed Windows native identity continuation below supersedes that platform limitation without a timestamp fallback or authorization bypass.

The owner adapter test also uses a platform-native expected export path. Its production behavior is unchanged.

The X4 review additionally reproduced post-finalization substitution: new unrelated SVG/PNG bytes and a self-consistently rehashed packet could be added without changing raw images, canonical observations or the existing seal. Finalization now seals hash-addressed derived files into its existing artifact inventory, using bounded streaming reads with safe-path/symlink/hash checks. Export requires the packet and every derived reference to match that sealed inventory. This closes the reproduced post-seal attack without changing schema fields or the 27-module control registry.

Inventory is bounded to the exporter's existing 1024-entry limit, including runs without a derived directory; a review-found early-return bypass was reproduced and corrected. Each derived file remains subject to the existing persistence limit of 32 MiB. Legacy seals that did not inventory derived files cannot certify a visual export, but nonvisual export remains available. Historical seals are never rewritten to invent earlier coverage.

Sealing proves that bytes were retained before finalization, not that a particular compiler generated them. The filesystem writer and finalization owner before the seal remain trusted. Producer attestation or byte-for-byte rederivation against hostile pre-seal writers is not established and is not claimed by this source review. No definitive visual/gameplay acceptance is inferred from sealing.

Local verification used Windows, Node 26.1.0, Python 3.12 and JDK17. Hosted source CI uses Linux/Node20, so these environments are not equivalent.

| Gate | Result and scope |
|---|---|
| Presentation, owner adapter and result export regression | `node --test debug-workspace/evidence/tests/visual-presentation.test.mjs debug-workspace/bridge/tests/owner-action-adapter.test.mjs debug-workspace/bridge/tests/result-export.test.mjs`: 44 passed, no skips. Invalid packet cases were reproduced before the fix. |
| Paired scoped control and private export | `KNEEKURA_LAB_SOURCE=<absolute LAB checkout> python -m pytest -q tests/test_minecraft_scoped_control_interop.py` from TECH: 1 passed. Actual CLI/export/import ran with the fixed LAB source; execution/cleanup stayed UNKNOWN and assertions INCONCLUSIVE. |
| Genuine Forge API source check | `node debug-workspace/bridge/runtime-api-selftest.mjs` with an official mapped Forge `1.20.1-47.4.20` classpath: writer 3, image 6, registered-world 6 checks passed. Windows world checks verify rejection when stable identity is unavailable, not successful owner execution. The new rejection regression failed before the fix. |
| LAB complete source aggregate | `npm run test:ci` stopped at two bridge symlink fixtures with `EPERM`. Separately run visual evidence had 62 passed and one symlink fixture failure; owner prelaunch had 24 passed and one symlink fixture failure. No fixtures were removed or weakened. |
| Java portable contracts | Runtime self-test passed. Owner and capture suites stopped at Windows symlink creation permission failures; they are incomplete, not passes. |
| TECH complete local suite | 2,745 passed, 562 skipped, 120 failed and 48 errors. Observed Windows failures include symlink privilege, path separators/length and oversized environment variables; all failures have not been classified. This is not a replacement for the recorded hosted 3,140 passed / 332 skipped result. |
| Post-seal continuation regression | Export, finalization, presentation and owner adapter tests: 75/75 passed, no skips. The post-seal packet attack and absent-derived-directory inventory bypass failed before their fixes; legacy visual refusal and normal export are covered. The paired scoped-control fixture also passed with the seal change. |

The pinned MOD's whole `gradlew.bat kneekuraDebugClasses --no-daemon --offline -Dorg.gradle.jvmargs=-Xmx4G` compilation, including the final fixed LAB Java source and Forge `1.20.1-47.2.0`, succeeded in 54 seconds. This is separate from the standalone API classpath. Neither command launches Minecraft.

Hosted integration CI previously failed before LAB tests because the default TECH-repository `GITHUB_TOKEN` could not checkout the private LAB repository. Run `36833052724`, job `110273859317`, reported `Repository not found`. With the user's continuation authorization, TECH now uses two separate repository-scoped read-only deploy keys via encrypted Actions secrets. Personal broad-access credentials were not copied into CI. `contents: read`, `persist-credentials: false`, exact source pins, and the prohibition on game/self-hosted execution remain. The workflow test permits only the two named checkout secrets.

TECH head `97513a4f371c15386663af1fb0eb1c09d36cc742` pins the published fixed LAB head `39893cd432fec58c3e4567f8c7d5630deadbc522`. [Hosted source run 36840268482](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36840268482) succeeded: complete LAB source aggregate, portable Java owner/camera contracts, both paired fixtures, whole pinned MOD/Forge `1.20.1-47.2.0` compilation and genuine API checks. Visual evidence passed 63/63; Linux registered-world checks passed 7/7, including normal-save stability and replacement rejection. [Standalone TECH run 36840268400](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36840268400) recorded 3,140 passed, 332 skipped and 8 warnings. These source successes do not erase the separate Windows failures above or establish runtime acceptance.

The initial isolated checkouts had no configured runtime or registered debug-world save. The disposable-copy preflight below supersedes that prerequisite check. Actual owner mutation, reset/cleanup, camera restoration, event timing, matched repair and the format benchmark remain unperformed. Both existing PRs remain Draft.

## Windows directory identity and disposable client startup

The current Windows/JDK17 directory provider returns null `fileKey()`. The fallback now uses Forge's existing JNA 5.12.1 dependency to read volume serial plus the 128-bit `FILE_ID_INFO` object ID. A read-only handle validates directory and non-reparse attributes before reading its ID, and closes on every path. Native lookup, attributes, ID, close or linkage failure still rejects owner authority with `OWNER_DIRECTORY_IDENTITY_UNAVAILABLE`. Non-null provider keys and regular-file checks keep their existing paths. No timestamp fallback, new dependency, public evidence schema or 27-module registry change is introduced.

The actual pinned MOD/Forge 47.2.0 compile classpath contains both JNA libraries. TDD first failed at the old null-key rejection; final genuine API checks passed writer 3, image 6 and registered-world 73, including creation-time replay across 64 retained directory replacements and rejection of regular/missing paths. Whole pinned MOD `kneekuraDebugClasses` compiled successfully in 34 seconds. Related Node regression passed 75/75. Independent review separately passed world 71 before the two additional negative tests, rejected file/missing/junction inputs across 4096 calls, and observed stable process handle count in nine samples. No remaining source finding was reported.

Stable IDs do not prevent a path replacement race after the read handle closes, or object-ID reuse after the original directory is deleted. The trusted local filesystem assumption remains; this is not full runtime attestation. Linux execution is verified separately by hosted CI, and native close-failure fault injection was not performed locally.

The supplied `.minecraft-simlab-golden` is a production game directory, not a registered source workspace. Its profile selects Forge 47.4.0 and MOD `2a1284f4be37f52e08d57dd26570990b612705a0`; its only save is `simworld-golden-v1`, and its MOD JAR contains none of the three inspected LAB debug bootstrap/owner classes. It was not used in place. A separate 34-file world copy was created under the pinned MOD worktree's `run/client_a/saves/KNEEKURA_DEBUG_WORLD`; only the copy's `LevelName` was changed and read back through Minecraft NBT APIs. All 34 original world file hashes remained unchanged. A separate local G1 profile passed every doctor check.

The first real client attempt at MOD `040866fa00ae96b5dcdcb02bae1fdc4ffdfdf5b1` failed before READY because the floor texture and four sound references contained illegal uppercase resource paths. A minimal MOD fix at `6cf8a87251e68265a411c4adb99b741264379d0a` normalized the five references/file names, preserved all asset bytes and sound event IDs, and passed existing 9 plus new 2 JUnit tests. Its independent review found no issue. The second attempt reached `DEBUG_READY` for the exact dedicated world on Minecraft 1.20.1 / Forge 47.2.0 / Java 17.0.12, then crashed about 1.6 seconds later: the ordinary `SimNetworkProbeBridge` helper was directly loaded from a Mixin-owned package. Reconciled state was `STALE_NOT_RUNNING`, not healthy live acceptance. No scoped owner actions or captures were armed. MOD follow-up work is tracked in [Draft PR18](https://github.com/genkimorimori252525-oss/reimu-mod/pull/18).

The Mixin helper follow-up at MOD `f9502df842fc5f7103217217d7a327babe452843` moved the ordinary helper outside the reserved package and updated five callers. Send/receive methods must be public for their transformed Forge-package callers; the optional scenario gate, reflection, payloads and failure handling are unchanged. A reserved-package regression first failed; all 13 JUnit tests then passed, also in independent review. An independent separate-package probe verified idle behavior and send/receive/semantic reflection without changing payload identity.

The third real attempt used LAB `1264fddd0e5c00acfb47b81958c39d69fdfb3ef0` and that MOD SHA. Existing `g2-smoke` completed with exit 0, `ok: true`, and separate G1/G2 manifests reporting `PASS` for `run-20261001103410-4ebcac939518`. READY remained live before the controlled stop. The subject UUID `6dc89198-fbdd-43f9-b379-380b71a58e9c` came from the original retained Golden `capture.json`, not an entity scan. Client/server heartbeat and the nine required exact-UUID lanes passed identity, revision, freshness and source-side checks. `requireReimu` was false; this is not Reimu-specific behavior acceptance or pixel capture. The retained one-second observation pre-roll was not truncated; four evicted buffer records were outside its requested window. Shutdown ACK reported zero writer drops, empty queue and `CLEAN_EVIDENCE_SHUTDOWN`; finalization was `EVIDENCE_COMPLETE`, and reconciled runtime was stopped. All 34 original Golden world file hashes still matched after this trial.

These are short G1/G2 startup, observation and safe-stop gates. They do not establish production endurance, scoped owner installation/actions, Arena reset/cleanup, Cardinal-4 pixels/restoration, event timing, matched repair/resume, the visual-format benchmark or full target/transformed-class/config/resource equivalence.

Local records are under `C:/temp/kneekura-live-acceptance-20261001` and `C:/temp/kneekura-native-directory-*-20261001*.log`. Separate failed startup records, successful actual API/compilation logs, raw/canonical evidence, finalization and acceptance manifests remain retained. The two failed attempts are not relabeled as passes.

## Bounded native owner, camera and TECH round trip

At LAB `59ae068144a36fdaa6b6b6ef2e27c1ebd02de400` / MOD `f9502df842fc5f7103217217d7a327babe452843`, fresh disposable-copy run `run-20261001115242-5bb8ac6edb07` completed the private operator scenario with exit 0 and no driver failures. The exact registered Reimu UUID passed the Reimu-specific evidence gate. Actual TECH profile/index/CAS inputs and its pinned 27-module registry were used; no synthetic build, pixels or runtime receipts were substituted.

- Two Cardinal-4 captures each retained four 640x480 PNG frames, reported `COMPLETE` with no gaps, and established `RESTORED` by exact Minecraft API readback of camera, screen, pause, FOV, GUI and mouse state. Captures remain sequential (`sameFrame: false`), perturb observation and invalidate the retained `alive` assertion.
- Native `wait_ticks` (2 ticks) and same-position `teleport_subject` (yaw -90) reported `VERIFIED` with matching observed postconditions. One-use cleanup reported `VERIFIED`; `ARENA_RESET` confirmed the measured baseline `d23cbe766c5c2184d4e4ad6cc4523e6ca9caa9c7d944ef000fadb7dd298437f4` for **BOUNDED_BLOCKS_AND_SUBJECT_POSE** only. Arena epoch advanced 0 to 1; this does not establish reset of effects, scheduled ticks, external entities or every world state.
- Both real capture manifests, raw image lineage, AI packets and HTML reviews were retained before sealing. Comparison executed and correctly returned `NON_COMPARABLE` / `NOT_EVALUATED` with `CAPTURE_CONDITIONS_MISMATCH:frames`; the subject-turn trial is not matched MOD-repair acceptance. No visual assertion was promoted to PASS.
- Shutdown received clean writer ACK, zero drops/empty queue and safe process stop. All 69 canonical records have continuous physical writer sequence across the Arena epoch change. Finalization is `EVIDENCE_COMPLETE`.
- Finalized visual export manifest `997391b76326fd0ddaff505b0bbc5288c5034a2e527c1bdddca94f01c08c06fa` was imported into TECH as `IMPORTED_LAB_REPORT`, result `b0707284a4201ea03f6aebc9485eee5795e349400f21dd5dd4d0358946c001c4`. The conservative projection remains execution `COMPLETED`, cleanup `UNKNOWN`, assertions `INCONCLUSIVE`, runtime attestation `NOT_ESTABLISHED`, even though the bounded native reset receipt is verified.

Real execution exposed two additional LAB defects. Minecraft's camera reads LivingEntity head yaw, while the former ArmorStand `moveTo` set only body yaw; capture now sets both current and previous head yaw. On abort, restoration now waits for existing bounded exact API readback rather than immediately marking the asynchronously cleared pause state UNKNOWN. Diagnostic capture failures are logged without weakening tolerance or deadlines. The physical producer's sequence spans Arena/resource epochs; its gap/replay tracking now uses writer/process identity, while nonproducer epoch keys and real-gap detection remain. Four regressions cover epoch continuity, actual gaps, process restart and replay; the normal G2/CI aggregate includes them.

Verification: portable related Node tests **79/79**, G2 aggregate including the new regressions passed, genuine Forge API writer **3**, image **6**, registered-world **73**, whole pinned MOD compile **32 seconds**, and paired TECH/LAB fixture **1/1**. Independent review confirmed actual head-yaw API semantics, bounded restoration and sequence behavior without a new source finding. Hosted verification for the newly published pin is separate from these local results.

Earlier records remain immutable: r3/r5 failed camera/restoration; r4 verified nonvisual actions/reset/export/import but retained a false 48-record gap in its old PARTIAL seal; r6 captured eight images but did not establish cleanup/export because the private driver lacked post-capture owner-idle readback and referenced the packet artifact incorrectly. The idle explanation is a hypothesis for r6, not a retained proof of its precise CLI failure. The corrected private driver and a fresh world copy produced r7; old seals were not rewritten. Original Golden save hashes still match **34/34**.

Remaining gates: a real matched MOD repair/resume cycle, event-trigger/pre-roll timing, visual-format benchmark, in-game holding appearance, production endurance, full target/transformed-class/loaded-config/resource equivalence, and classification of the separate Windows aggregate failures. `use_item` remains explicitly unsupported. Source-review completion and this bounded native round trip do not establish general operational acceptance. All three related PRs remain Draft.

Private run artifacts: `C:/temp/kneekura-live-acceptance-20261001/owner-r7`; failed earlier runs and the r6 world copy remain retained. Logs contain local runtime identities and are not uploaded wholesale.

## Related source records

- [Bounded Arena and action scope](KNEEKURA_BOUNDED_ARENA_SOURCE_SLICE.md)
- [Cardinal capture and trigger contracts](KNEEKURA_CARDINAL_CAPTURE_SOURCE_20261001.md)
- [Visual compiler and comparison source handoff](KNEEKURA_VISUAL_EVIDENCE_COMPILER_SOURCE_20261001.md)
- [Finalized result export](KNEEKURA_EXPERIMENT_RESULT_EXPORT_SOURCE_20261001.md)
- TECH `departments/minecraft/mod-ai/LAB-SCOPED-CONTROL.md` and `POST-COMPLETION-SOURCE-2026-10-01.md`
