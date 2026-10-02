# Minecraft live repair acceptance — 2026-10-02

This is the execution record for `docs/superpowers/plans/2026-10-02-minecraft-remaining-live-acceptance.md`. The full acceptance plan remains in progress. All PRs remain Draft; no merge or deployment is included.

## Matched native control

- MOD source: `f9502df842fc5f7103217217d7a327babe452843`.
- LAB source: `7160b0a8ea9cf2ec83dfad9277486398c97cf5cd` (local, not yet published).
- TECH source: `2fb2e0eda62b2c132d53dc9d33c2fe1730475347`.
- Request: `e642637abc4724d1008cae7103db85f807b73353df7e65cc994fb47f2a04210b`.
- Run: `run-20261001165920-0fed04502a79`, process epoch 1.
- Selected UUID: `6dc89198-fbdd-43f9-b379-380b71a58e9c`, `touhou_little_maid:reimu`, NoAI, fixed pose.

Both native cardinal captures are COMPLETE/RESTORED. All eight raw `RenderLevelStageEvent.getPartialTick()` values are 0. The existing strict comparator returned **MATCHED_EVIDENCE_ONLY**, with no reasons, and **NOT_EVALUATED** acceptance. Camera poses, actual matrices, viewport, FOV, human restoration state and perturbation conditions matched. Sequential captures still have `sameFrame: false`.

| Retained artifact | SHA-256 / identity |
|---|---|
| Before canonical observation | `obs:forge-runtime:5624:34` |
| After canonical observation | `obs:forge-runtime:5624:58` |
| Before packet | `fac370704ed2f011ec5dc457aebe951f6a916cad913924f1e025fcee91c5ca08` |
| After packet | `ee509ea8ee0876c097263114ecba2c3ec32e13baa4873604a6ed9002e7fb7dc4` |
| Before/after sheet | `852ff6ac27e884e82279cd1fcf402e71c753eee888a8e25502c08888028b5d7a` |
| Export manifest | `52a51ffdb69836849c22d55fe7f95d0f9e9a5cc075636d05fa9b0431d8de9256` |
| TECH imported result | `786bb33474173bc89811580179568dca572e42a396780e37443daa04da31d9fa` |

Two bounded wait actions and the Arena cleanup have VERIFIED receipts. Actual camera/input/settings restoration has equal expected and observed Minecraft API state. The run stopped with CLEAN_EVIDENCE_SHUTDOWN, finalWriterSeq 67, zero drops and zero remaining queue; canonical evidence contains 67 records and seals as EVIDENCE_COMPLETE. Driver exit code is 0 with no failures. Raw runtime evidence stays private under the dedicated `owner-r11` run.

The sheet was visually inspected: selected Reimu is visible in all four directions. Nearby unselected entities can animate between captures; matching selected capture conditions does not establish whole-scene equality or pixel identity. This control is neither a repaired MOD nor a gameplay acceptance result. Exported cleanup UNKNOWN, assertions INCONCLUSIVE and runtime NOT_ESTABLISHED remain unchanged.

### Clock fix and retained failures

The original r7 pair was correctly NON_COMPARABLE because raw partialTick differed. Actual Minecraft bytecode reads `pausePartialTick` after RenderTick.START for GameRenderer, while ForgeHooksClient.dispatchRenderStage obtains the earlier cached `realPartialTick` through Minecraft.getPartialTick(). The capture owner now holds both real clocks at 0 only inside the existing pause/server barrier and restores both exact original float values. Frame metadata still records the actual event; comparison tolerances and guards are unchanged.

- r8: preparation failed closed before launch on grant/action scope mismatch; private driver scope corrected.
- r9: first native control attempt, PARTIAL/RESTORED, no images; RENDER_INTERPOLATION_NOT_ESTABLISHED demonstrated the separate Forge cache. Cleanup and clean stop succeeded. Evidence retained.
- r10: JVM native malloc failed before READY, no owner installation or action dispatch. Default JVM heap maximum was 8116 MiB. Crash log retained. Offline preflight verified the original selected UUID, pose, NoAI and two air cells. This startup failure did not provide a second capture control.
- r11: fresh private launch with JavaExec heap capped at 3 GiB; unchanged owner lease/capture budgets; successful second native control above. No original Golden files or production settings were changed.

Verification: clock CPU contract 38 checks; comparison/capture Node tests 43/43; genuine Forge API compilation and writer 3/image 6/world source 73 checks passed. The native run compiled the actual bridge and launched Forge. Final whole-branch review and source publication are recorded in FINAL-REVIEW-2026-10-02.md and the exact-source CI section below.

## Real missing-item-model repair

The actual MOD registered `touhou_little_maid:debug_force_takeoff` without `models/item/debug_force_takeoff.json`. Native startup independently reported this missing model. Before image acquisition, the expected repair was fixed to the exact existing sibling debug-item convention: `item/generated`, layer0 `touhou_little_maid:item/spell_reimucheat`. The existing PNG and all other tracked files were to remain unchanged.

The dedicated offline fixture equipped the selected Reimu's right hand with this item, count 1, under the world session lock. Complete chunk NBT comparison/readback established that only `HandItems[0]` changed. Model ID, NoAI, pose, other equipment and nearby entities remained unchanged; the earlier world copy was retained. No unsupported `use_item` was invoked.

Before run `run-20261001171003-719bc391f9d5` visibly rendered a large black/magenta missing-model cube in all four directions. MOD commit `53a84d06578632b5d123e3c2bb631b611bf830d7` adds only the six-line missing model file, identical to the existing sibling document. After run `run-20261001171449-a7ae83fe8000` visibly renders the shared debug-item icon in north/east/west; the thin icon is occluded in south (**NOT_VISIBLE**). These view findings are **INFERRED** from retained raw images. They establish the selected visual symptom and repair, not general gameplay correctness.

The strict cross-generation comparison is **MATCHED_EVIDENCE_ONLY / NOT_EVALUATED**, with no reasons. Only generation, profile ID, index snapshot ID, source revision and the actual selected-resource hash are declared differences. Build class members, config, request setup/actions/assertions and real capture conditions remain equal. All sixteen frames across the two runs report raw partialTick 0 and both runs seal EVIDENCE_COMPLETE after clean STOPPED, zero drops/queue and VERIFIED bounded cleanup. Writer final sequences are 80 and 63 respectively.

| Evidence | Before | After |
|---|---|---|
| Generation | 1 | 2 |
| Request | `00297cbab47733d65d5ac4dabcd76a4e253b7003a0c1d1127cf0650326dfaeb2` | `1ab639f0d41d161dc25dfcf602de1bf763ea2ef98cd0cc1e6c0477e72b70837e` |
| First packet | `b061430f742a9a8954a41f5334b1698ad82bb49446918cf36bbc62803e40337a` | `448c45499cd8910cc25824144ea8147c96ea6ea320aff6bda0b9779c570f17d6` |
| Selected resource artifact | `bfccef9f76c6336074a2574114aa6175eb89713d8038de08d7db0818b8aeffaa` | `ea2fac30fca2aa55a90a179b99c7e8986f92f69d9c72ddb7d7df14f15ff40726` |
| Export manifest | `42ee995370e8bd58b3e054266a75250d2c2bb0b84a58f489648dd1fc1a5d9f1e` | `9c0068ad2dc7115595f221b6561e39c9a6ffff115e0346b700fb02013314cb47` |
| TECH result | `c94856b697fda659f136a3ae45881fd23deb39d78527ce2d9a633ab151019894` | `5361e54564c3b2c4fe6564b5a9d95779ecf998ca2bf3a83277c1bc498face858` |

Node comparison JSON hash: `962aabdd4f5defb87909d792ae70238416cf3bdcb88e8131a9460d8ee30c6107`; paired sheet: `f817382f14882f9254bbac317ee12ead96cd002900f9c7d3343471a047b18b6f`. The private fresh TECH Store retains the original comparison bytes and its separately canonicalized JSON projection `ebc5f18cac9376b9c0aa0c0c33d27acae7e5c215cd4495cf2354d3c1d93aad07`; neither changes either native seal. Review projection: `769286884831a61ab6a64370b189ff65577d5ff45c5353aaca3a0a609a5a3681`. Unchanged texture SHA-256: `ff7fc56b2207ec43b2dd31ff9fe5f788fbdabd4ccd442162126cef84cef2f347`.

A separate Python process opened a fresh Store containing 24,077,413 verified source blob bytes. Both results resumed with MATCHING_DECLARED_TARGET, 21/20 retained evidence entries, `can_replay: false`, `execution_authority: NONE`; process execution was explicitly forbidden and not invoked. Changing resource_hash returned REVERIFY_REQUIRED, CURRENT_TARGET_CHANGED and no replay. Cleanup UNKNOWN, assertions INCONCLUSIVE, runtime NOT_ESTABLISHED and the generic LIVE_REPAIR_ACCEPTANCE_NOT_RUN resume gate remain preserved; this manual bounded acceptance record does not promote those exporter projections. Related Python tests: 9 passed / 4 Windows skips, no exclusions.

The selected-resource ZIP binds this item texture and model presence/absence. It is not a proof of all loaded resources, transformed classes or whole production runtime equivalence. Nearby unselected scene animation is outside the selected repair assertion. This real missing-model repair is separate from the previously injected Blockbench staff repairs; in-game staff holding is recorded separately below. Final independent review and Draft source publication are recorded separately below.

## Remaining acceptance

Native ARENA_EXIT and its PARTIAL timing window, Windows failure classification, Thin Viewer and finite 30-minute observation are recorded in the LAB remainder record. Eight-case exploratory visual comparison and native Blockbench staff holding have separate true-Tank evidence below. Intentional interruption, final independent branch review and exact-source CI are recorded only after completion. None is implied by the selected item repair.


## 検証ワールド訂正（後続試験の対象）

ユーザー指定の真の水槽は `g3-real-machine-acceptance/reimu-mod/run/client_a/saves/KNEEKURA_DEBUG_WORLD`。上記の完了したcontrol/修復比較、後続のgravityイベントと30分観測は旧Golden fixtureで実行した証拠であり、この水槽での受入へ読み替えない。

真の水槽原本から、`session.lock` のread-only共有ロック下で85ファイル・11,613,055 bytesを新規コピーし、コピーSHA-256と原本のコピー前後SHA-256を照合した。全一致、原本変更なし。manifest: `K:/kneekura-live-acceptance-20261002/true-tank-source/snapshot-sha256.txt`。

後続試験は隔離MOD workspace内のコピーで行う。元の19×11×19外周を維持し、中央4セルの床をblack_concreteからstoneに変更して既存owner paletteに合わせた。既存bedrock霊夢 `11111111-2222-2222-3333-333344444444` を `[9.5,224,9.5]` へ配置し、NoAI/NoGravity/Invulnerableと対象itemを固定した。observerは制御領域外へ配置。NBT全chunkの読み戻し一致。これらは実験fixtureの準備であり、元Tankのfull-state resetやYSM検証を証明しない。

最初に調べたDownloads LABの `simlab/tank-v2/schema/dry-tank-size.mjs` は別の実装（4096セル、既定floorY64）だった。真の水槽と対応するソースは、同じg3 worktreeの **KNEEKURA-LAB `8e36ea8b1c8634bb1422c965b0e5f179d54f1cdf`** にある。`KneekuraDebugTankCoordinator` / `KneekuraTankGeometry` と `actions/tank-recipe.mjs` は9×9×7、17×17×11、19×19×11およびcustom寸法1..64、inner volume65536、origin可変の機能を持つ。今回の保存済みrecipeはorigin `[0,224,0]`、19×11×19、`OBSERVATION_BRIGHT`。元branchのresize/reset操作は未実行で、今回の局所owner制御の実装と混在させていない。

暗い表示の原因は、元の `KneekuraDebugTankView`（client grid/full-bright lightmap）が現在のLAB bridgeに含まれていなかったこと。resource pack欠損と推測して照明ブロックを追加していない。この描画部分を移植し、登録resource ZIP内の任意 `kneekura/tank-presentation.json`、保存済みrecipeとの一致、現owner/run identity・有限leaseで明示的に有効化する。recipeのcanonical hashは `e9ed87f3b512cf59dac3ce6eb0c08654d047657be1e383dc6df580a5582bcac3`。server light、entity effect、physicsは変更しない。両側のresource hashへ同じcapsuleを固定する。元g3 branch全体の統合やYSM renderer受入ではない。

K側のMOD workspace `K:/kneekura-mod-goal-20261001` はprivate Cコピーの13,122ファイルを全SHA-256照合して作成した。Cコピーも保持している。原本g3ワールド/両repoは変更しない。旧Goldenの五つの停止済みworld backupは `K:/kneekura-live-acceptance-20261002/retained-old-golden-worlds/` に照合付きで保持している。

### True Tank native presentation and retained attempts

LAB `135563fd8790a07fd0b07042cedeaa68b0137fe5` / MOD `53a84d06578632b5d123e3c2bb631b611bf830d7`, `tank-a-r7` run `run-20261001203333-ffcbef65c4af`: native raw RGB visibly restores the one-block grid and bright selected bedrock Reimu/staff. All four Cardinal-4 sets are COMPLETE/RESTORED, all16raw partialTick values0; six declared actions and scoped cleanup VERIFIED. Clean STOPPED,169canonical records, zero writer drops/queue, EVIDENCE_COMPLETE, driver0/no failures. Export `40aa3f7e0580d9444c05b33f6325555b2addc64802cf140093135d0408b381bb`, TECH result `743ee69ffb534c806348e8af891894b9340b6d93024bd87c837ee81d453ad83c`. This is the first successful full scenario on the true-Tank copy, separate from all old-Golden results.

Request `fdd176f9b132dc99d5b2ad0fe43d14c82eb0ba82b84a912e29ea8091be1b0498`; resource `5ec7e5bfe395e81d653e8bfbcaa7fa085f1e8d3c74c9294cff790f48394cc007`; typed bounded baseline `e654fe6dd4610937e88769e4159c26c3f184ff2f2ae76d989a2ec0601793a8ab`. Stopped a7 fixture world is retained at `K:/kneekura-live-acceptance-20261002/tank-a-r7/world-retained`.

| Slot | Scenario | Native packet SHA256 |
|---|---|---|
|0|Normal, holdingy6|`e9630f1ebd6e6733cd82ec60e789db7ebaef267cdb56f775f7a751d1d0bb638d`|
|1|Burialy223.4|`0f711ed0e76c1e14ad08703631b8ca50b7063ffe905056a534dcffc77f355b2a`|
|2|Head-covering stone|`d4a177a81a1d6f68c75dc06a256d19d40cc06c16e84edc507de216970508ddd3`|
|3|South occluder|`8a912d05b7b8233c0389a44b1e35a8c85f16363c142b23099b5ef6446f9ca9b9`|

Earlier attempts remain separate failures: tank-a obtained only slot0 before a native pause; r2 private preparation failed; r3 native4MB direct-buffer allocation crashed without shutdownACK, sealed PARTIAL/cleanupUNKNOWN. r4/r5 exceeded240s startup, no READY/actions, sealed PARTIAL. K relocation required a normal prewarm (passed4m45s) and finite READY600s; owner remains120s. r6 reachedREADY but correctly rejected staleC registration against actualK world, no owner/captures, clean stop. The private registration was corrected for r7. After attempt `tank-b` correctly rejected observer drift caused by a record file added during startup; `tank-b-r2` stopped before actions because a private script substitution corrupted its helper path. Those private mistakes are retained; no product guard was bypassed. New trials use fixed LAB files and exact-token/path preflight. None of these failures counts as a visual comparison success.


### Holding After, strict comparison and static projectile

`tank-b-r3`, run `run-20261001205029-c43fd3e6d6ba`, request `b9b955aa47cf5544240ad1a29fe522ca0abec47a0e2a55a8c516d943137b0a37`: same four scenarios, sixteen native frames, six VERIFIED actions, VERIFIED scoped cleanup, clean stop/zero writer drops and queue, EVIDENCE_COMPLETE, driver0/no failures. First packet `31132dcbec0445665ced652554eeac7c6abe4b1459c47a3b6a73cae74ebcb984`; export `121ebe7abcd8e57b119cf66b273e8919e2fb50e07c6ac14ec8d37896c915e546`; TECH result `8f1a66df060d37557961c29f6fd687513afd03e57138a4bf8b773db3e1ea0b76`. LAB135563f/MOD53a84d are the native source pair, not the later documentation/review commit. Stopped fixture world retained separately.

The slot0 holding comparison is MATCHED_EVIDENCE_ONLY / NOT_EVALUATED, no reasons, only generation and selected-resource changes declared. Registered Blockbench `thirdperson_righthand.translation.y` changes6→4, other model fields and texture binding unchanged. Actual gold/purple staff is visible north/east/west in both runs with a small displacement; south remains partially occluded. Comparison `1340e21bc0c60a120cad62af0b77b73e6733f9fcecafcad87c3c5f16edde8532`, paired sheet `25f88736223c4cd6aebd1f69a597e252d3781f8645bce8903343914962f9c62e`. Speech-bubble animation differs. Exact effective numeric transform, whole-scene equality and subjective improvement are not established.

`tank-projectile`, run `run-20261001205645-d86ad19b987d`, request `e8eac5fdfeabd23d5d062820955fe719a844453d8f1d992ba9dd039d4fae1fe3`: two COMPLETE/RESTORED sets/eight native frames, stone obstacle and clear-air actions VERIFIED, cleanup VERIFIED, clean stop85records/drop0/queue0, EVIDENCE_COMPLETE, driver0/no failures. Typed projectile baseline `0fffdbcf75d3e40407383da8046308905e73024bd32cba836a79f5c9d4e4729a`. Packets `a4cfcd92a6b28952ad093a569dcae5521a18ddd3992a32bde81588925f9486cc` and `8060bca91bf5380c08f2c6b04cafb191e64bf6d5bc4529f61d819a3f0f04f622`. Export `1367bd51a44f4494309c6a9e0d08326a7ca4197ad7917e0cd239e6e7e3c79c2c`; TECH result `8850dd492bb3d6b0c14bc1a10a96cab9a1c8897ca73377425333ba888cdbc3d9`. The registered arrow is static, NoGravity/Invulnerable, velocity0; this does not test combat, collision response or projectile flight.

### Eight-case exploratory result

See [VISUAL-FORMAT-BENCHMARK-2026-10-02.md](VISUAL-FORMAT-BENCHMARK-2026-10-02.md) for40A–E judgments,8F NOT_RUN results, source references and input amounts. Private derived export `K:/kneekura-live-acceptance-20261002/visual-format-export-r3/manifest.json` preserves immutable native canonical/seal hashes and original raw image bytes. Judgments are unblinded implementer evaluation, not independent accuracy statistics. C is the local recommended starting format, with raw detail and E for exact identity/artifact values; production default remains provisional and unchanged. Exact head-mesh clipping remains AMBIGUOUS. No outcome is promoted into generic gameplay PASS or full runtime equivalence.

### Post-review startup refinement

Final LAB source pin f2d6165b16587672ac56f83c001c65bc2fa6d06a / MOD53a84d06578632b5d123e3c2bb631b611bf830d7 are published as Draft. Renderer lifecycle code is6ed4831; source-only Gradle prewarm succeeded7m12s. A private manifest SHA-binds8444main source/classes/resources/refmap entries before/after use; only verified main compilation is skipped in the private launch, actual LAB bridge and handshake still required. Normal MOD build.gradle forced-rebuild behavior is unchanged.

Interruption-r4 reached six native server/client tick records but failed closed before owner installation on runtime PID attestation (PowerShell inspection failed). No owner/action/wait/capture was authorized. EVIDENCE_PARTIAL and complete error record retained; actual native and launcher PID absence was separately confirmed before moving its fixture world. A thread sample identified TacZ generated-gun-pack deletion/re-extraction as the startup delay, not lack of physical RAM (sample available about7.6GiB). The private generated pack was moved intact to the stopped-r4 evidence area, with no source/config/registered resource or original-world change; fresh-r5 uses the identical SHA-verified request/CAS, new finite grant and fresh world. No uncertain mutation is replayed.


### Exact-source CI after the review fix

TECH pin commit `eb68b2d371136db1f90af6d0693f775fa621fea5` fixes LAB `f2d6165b16587672ac56f83c001c65bc2fa6d06a` and MOD `53a84d06578632b5d123e3c2bb631b611bf830d7`. Both push and PR hosted source runs succeeded: [36934722014](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36934722014) / [36934727261](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36934727261). The latter compiled the actual LAB bridge against pinned MOD, passed portable owner/camera/registration/control/export contracts, actual dependency contracts (Tank30), and MOD resource/unit regressions. This is SOURCE_ONLY evidence, not a native acceptance run.

Hosted TECH complete suite [36934727193](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36934727193) passed **3141 / skipped332 / warnings8** in280.88s; push run36934722089 also succeeded. The extra test belongs to concurrent preserved TECH work; old3140 is historical. These runs test the pin commit above; later acceptance-document commits do not retroactively change that SHA.

LAB standalone Windows CI [36932200240](https://github.com/genkimorimori252525-oss/KNEEKURA-LAB/actions/runs/36932200240) at f2d6165 **failed**: genuine Forge bridge compilation and preceding gates passed; Node aggregate:51pass/3fail/1skip (55tests); Thin Viewer step was skipped. Two material/symlink fixtures fail `EPERM` creating links without Windows privilege. The inherited-descendant-pipe fixture receives a successful drained close in about57ms, while its POSIX-oriented expectation requires a100ms timeout; a focused local seven-case rerun reproduces6pass/1fail. The bounded-output implementation waits for `close` and its separate timeout/output-limit/forced-stop checks pass. Neither failed fixture nor skipped viewer is counted as pass. Windows runner permissions and these fixture assumptions were not silently changed; hosted Linux source suite succeeds on the same LAB SHA. The separate actual Edge/WARP Thin Viewer result remains labelled separately. Push Windows run36932193468 also failed; GitHub did not provide its job log at initial inspection. No unsupported claim about its precise cause is made.

Interruption-r5 ended before READY, with0records/no owner/action/capture and EVIDENCE_PARTIAL. The associated Gradle daemon22292 and JVM24452 report native allocation failure mapping356515840bytes for G1 virtual space. This is a startup memory failure, not an accepted interruption. Actual known JVM/launcher/helper absence was checked before retaining its private world and generated TacZ pack. r6 uses the identical request/CAS with a fresh grant/world after CI finished; no uncertain action is replayed and all previous failed trials remain retained.


Interruption-r6 reached READY and `INSTALLED_SCOPED_CONTROL`, then `readCurrent` classified OWNERSHIP_UNKNOWN (`live:null`); the driver refused all captures/actions. Stop closed the owner with `OWNER_SHUTDOWN_REQUESTED`, clean ACK17records/0drops/0queue, EVIDENCE_COMPLETE, driver1. A complete evidence seal describes retained evidence, **not successful intended interruption**. Subsequent stop inspection attested both launcher/runtime identity; it does not prove the earlier transient inspection's precise cause. A separate read-only twelve-sample CIM collector probe against the existing private Gradle daemon returned parseable complete JSON12/12 in531–735ms. The failed r6 state was not repaired or reused. r7 preserves fresh request/grant/world isolation and now records redacted ownership/error scalars before any operation; no inspection guard or finite lease changed.


Interruption-r7 confirms the Windows inspection failure under memory pressure: launcher identity matches, but native PID inspection returns a PowerShell thread-start error, with system free virtual memory about0.55GiB and native JVM private bytes later5.92GiB despite a verified2GiB heap. No captures/actions were submitted. The normal stop correctly refused uncertain inspection. A diagnostic GC request against this failed runtime did not materially release committed memory. The existing `stopCurrent` process-operations interface was then supplied an **actual PowerShell7 Get-CimInstance backend** (not assumed PID/time/command). Both original ownership checks matched; clean ACK406/drop0/queue0 and VERIFIED_EXIT followed. The owner status retains OUTCOME_UNKNOWN/LEASE_EXPIRED_OR_CLOCK_CHANGED; no outcome was rewritten as verified. A subsequent real absent-PID check allowed immutable EVIDENCE_COMPLETE sealing of406records/no operation. This is failed-trial retention, not accepted intentional wait interruption.

For r8, the existing bundled PowerShell7.6.5 runtime is copied to a private K directory; all658source files SHA-match the original. A private `powershell.exe` alias has exact `pwsh.exe` bytes, resolves its own copied support files and executes real CIM. Twelve bounded collector probes return complete parseable identity JSON12/12. Only the private launcher process PATH is prepended; machine/user PATH, OS/pagefile, credentials, LAB/MOD source, registered request/config/resource and finite budgets are unchanged. Default WindowsPowerShell5.1 acceptance is **not** established by this alternate local inspector procedure. The initial private r8 preparation assumed OWNER_CLOSED, failed before preparing a driver, and a helper was launched with a missing script; no native runtime/action was launched. Preparation was corrected to require actual VERIFIED_EXIT/no operation and retain the original lease-expired UNKNOWN, then a fresh r8 grant/world was launched only after the helper/script/PID preflight. No same-run authority recovery or action replay occurred.


Interruption-r8 failed before READY with5native tick rows/no owner/action/capture, PARTIAL/driver1. The associated JVM45092 fatal error is native malloc1115616bytes `Chunk::new`; actual heap total2GiB/used about1.6GiB and metaspace about219MiB. Concurrent REI recipe-plugin NPE is retained but not asserted to cause the fatal JVM allocation error. Inspector substitution did not fix this separate total-commit exhaustion. The exact private prewarm Gradle daemon22292 was verified by PID/start-time/command and log order (last private build finished after last start); only this idle daemon was stopped. Free virtual memory increased to about6.88GiB. r9 uses a fresh grant/world/identical request with private Gradle heap512MiB instead of1GiB, keeping native Minecraft2GiB, graphics, lease120s, READY600s, capture4 and wait1200 unchanged. This saves private operator memory; it is not a source change or general OS memory guarantee.


### Final post-review native capture and intentional interruption: r9

Final LAB **f2d6165b16587672ac56f83c001c65bc2fa6d06a** / MOD **53a84d06578632b5d123e3c2bb631b611bf830d7**, original request `de0b776b970fa4192eb5e04fffb8559cbef51b0421f078af1ac93e7755da91ff`, resource `b161675b3aa5bca5bd732c19edf8e9363d3ff0dc75856ce627b420c5a1068165`. Run `run-20261001230455-708a8146a93d`, session `sess-20261001230455-58d87b6401d2`. Driver **exit0/no failures**. Native READY, actual PID/start-time/command ownership and scoped owner installation passed with the private real PowerShell7 inspector and512MiB Gradle procedure described above.

One declared CARDINAL4 capture completed: four PRESENT native frames781–784, no gaps, actual partial-tick zero and exact Minecraft API restoration. Contact sheet was visually inspected: black/grey grid, bright native character and gold/purple staff in north/east/west; south holds normal character occlusion. This establishes active registered presentation with the final review fix; native expiry/disconnect image sequences were not separately filmed. CPU lifecycle/dirty-transition30checks provide that separate contract evidence.

The declared `long-wait`1200tick operation reached its native dispatch reservation, owner idle=false/unsafe=false/nextActionId=long-wait. Inspection before stop reported OUTCOME_UNKNOWN with recorded ACCEPTED and dispatchAllowed=false. Intentional stop occurred while the wait was pending. After stop both reported/recorded statuses remain **OUTCOME_UNKNOWN**, dispatchAllowed=false; read-only inspection has execution NOT_RUN. This is not completed1200tick acceptance or a mutating-action rollback test. Closed owner inspection refused `OWNER_NOT_CURRENT_IDLE_CONTROL`; no resend, new owner after stop, lease extension or extra capture was attempted. Native shutdown closes owner (`OWNER_CLOSED`, `OWNER_SHUTDOWN_REQUESTED`), clean ACK **31records / dropped0 / queue0**, both launcher23712/runtime56960 plus helper37180 absent and VERIFIED_EXIT. EVIDENCE_COMPLETE describes clean retained evidence, not verification of the interrupted action.

Visual source observation `obs:forge-runtime:56960:22`; packet `3ae6fa38276436813c870010b8912ae8c366042a046196d4d474cd93b38ce3b2`; contact sheet `37290f1076a28f585b3989e2142df27e35650f6059934884bbdf586070b7aee0`. Export `b392f9c86c6d8d9eec346dccf423121614c61e2883a00d09ae4da5ffe0d8f428`, TECH imported result `2a54027c26274c65b184dc0f77506d8485143b5548260b750c36fff1e8240869` (OK). Export preserves runtime_attestation NOT_ESTABLISHED and can_replay=false. Precompiled MOD main hashes matched again after stop. Prior failed runs/seals and original85Tank/34Golden source hashes remain retained/unchanged.

### Final acceptance disposition

All five planned tasks have executed results and explicit boundaries. The actual selected missing-model repair, strict Before/After, material/result retention and separate-process resume are established. True-Tank normal native cycles a-r7/b-r3/projectile plus final r9 pending-wait stop supplement the earlier old-Golden cycles; neither cohort is relabelled. Eight-case40A–E exploratory judgments,8F NOT_RUN, independent qualitative review, actualThin Viewer, native PARTIAL trigger and finite30minute non-owner observation are recorded. The single Important reviewer finding was fixed; no Critical or Minor finding was left by that review. Final r9/operator refinement was verified by the implementer, not independently rerun by the reviewer.

Draft remains the disposition for TECH PR74, LAB PR35 and MOD PR18. Windows aggregate3fail/1skip and alternate local inspector, pre-trigger gaps/reused post image, failed cleanup/UNKNOWN cases, untested original resize/reset/YSM, exact mesh clipping and full loaded target equivalence remain limitations. No general operational readiness, independent blind accuracy estimate, production endurance, merge or deployment is claimed. Raw logs/worlds/operator files/credentials remain private; source/tests/minimized records are published.
