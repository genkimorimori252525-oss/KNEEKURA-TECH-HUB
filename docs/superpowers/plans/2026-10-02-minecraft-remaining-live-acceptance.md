# Minecraft Remaining Live Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to execute this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 実装済みのTECH/LAB連携で実際のMOD不具合を1件修復し、妥当なBefore/After証拠、再開、人間向け表示まで確認する。残る実運用条件は別々に判定する。

**Architecture:** TECHが実験意図、ソース・資材の固定、修復履歴を保持し、LABが専用Minecraft、操作、撮影、原証拠、停止を担当する。新しいdaemon・Evidence DB・一般コマンド実行は追加しない。既存の厳密比較とUNKNOWNを維持して受入記録を作る。

**Tech Stack:** Minecraft 1.20.1 / Forge 47.2.0 / JDK17、既存LAB Node ESM、TECH Python/Store/CAS、既存Blockbench連携。

**Spec:** `docs/superpowers/specs/2026-10-01-minecraft-mod-ai-experimental-runtime-bridge-design.md`。直近の根拠は `departments/minecraft/mod-ai/POST-COMPLETION-SOURCE-2026-10-01.md` とLAB `docs/KNEEKURA_EXPERIMENT_SOURCE_SCOPE_20261001.md`。

## Baseline

- TECH `2fb2e0eda62b2c132d53dc9d33c2fe1730475347`、LAB `4e834dcf1252ece7f7953a58a57ff6e8bcafc3a5`、MOD `f9502df842fc5f7103217217d7a327babe452843`。実行前にremoteとローカルの差を確認する。
- 最新hosted source/standalone CI成功。TECH 3,140 passed / 332 skipped / 8 warnings。
- r7は撮影2回・8画像、2操作、限定復元、画像packet輸送、停止を実機で確認済み。69 records、zero drops、EVIDENCE_COMPLETE。これをやり直すだけでは新しい受入証拠にならない。
- 比較条件差は全4viewの `partialTick` のみ（before 0.81999993 / after 0.24000001）。現contractの `NON_COMPARABLE` は正しい。MATCHEDや修復PASSは未成立。
- 現export/resumeはcleanup UNKNOWN、assertions INCONCLUSIVE、runtime NOT_ESTABLISHEDを保持する設計。受入を通すために書き換えない。

## Global Constraints

- no production world / no new Evidence database / no caller-supplied executable path / no arbitrary Blockbench/Minecraft script。
- no automatic retry after uncertain mutation / no automatic launch-budget increase / no automatic canonical Claim promotion。
- no interpretation of action completion as gameplay PASS / no interpretation of image existence as visual PASS / no same-frame claim for sequential capture。
- 新しいrun・worldコピーを使い、旧sealを変更しない。元Golden、元Blockbench project、資格情報を保持する。
- 実験は既存上限内（time budget最大120000ms、actions最大32、captures最大16）。予算を延長して成功扱いにしない。
- 生の `partialTick` やcamera metadataを加工して比較を通さない。許容差の変更や同期方式の追加は、計測と回帰条件を定義した別の小変更として扱う。
- コード修正が必要なら対象を読んで再現テスト→最小修正→関連検証→独立レビュー。ソース変更後だけ必要なCIを再実行する。
- raw logs/worlds/credentialsは公開しない。全PRはDraftを維持し、計画実行にmerge/deployを含めない。

## Review Focus

- 異なる補間時刻・camera条件を、同じ条件の画像として比較しない（Task 1）。
- build/resource/config変更後に古い結果をcurrent扱いにしない（Task 2）。
- triggerの後で得た画像をpre-rollに充当しない。unloaded/UNKNOWNから架空のexitを作らない（Task 3）。
- AIの見落としや画像差分を、そのまま改善・ゲームプレイPASSに昇格させない（Task 4）。
- 中断・stale owner・symlink不可・未実行を成功へ分類しない（Task 5）。

## Files and outputs

- 新規TECH受入記録：`departments/minecraft/mod-ai/LIVE-REPAIR-ACCEPTANCE-2026-10-02.md`。run/request/source/material IDs、原証拠hash、合格・未解決を集約する。
- 新規TECH視覚評価記録：`departments/minecraft/mod-ai/VISUAL-FORMAT-BENCHMARK-2026-10-02.md`。ケースの独立した正解と形式別の結果を保持する。
- 新規LAB運用確認記録：`docs/KNEEKURA_LIVE_ACCEPTANCE_REMAINDER_20261002.md`。trigger、停止/再開、Windows分類を記録する。
- private runtime artifactsは新規runの既存EvidenceRuntimeに保持する。実験用スクリプトは既存の固定されたoperator手順を使用し、汎用public APIを追加しない。
- 以下の既存実装ファイルは調査対象。必要性が確認されるまで変更しない。

## Task 1: 実画像の比較条件を成立させる

**Files:** LAB `debug-workspace/evidence/visual-comparison.mjs`、`debug-workspace/evidence/tests/visual-comparison.test.mjs`、`debug-workspace/forge-bridge/src/main/java/com/github/tartaricacid/touhoulittlemaid/sim/debug/KneekuraDebugCardinalCapture.java`。出力はTECH受入記録。

**Interfaces:** `compareVisualRuns({before, after, intendedDifferences=[]})`。各側は実canonical Store、sourceObservationId、登録requestBytesを渡す。成立時もstatusは `MATCHED_EVIDENCE_ONLY`、acceptanceは `NOT_EVALUATED`。

- [x] r7の2captureを入力に、他条件一致・partialTick相違・NON_COMPARABLEを再確認し、既存比較テストの補間時刻拒否条件を確認する。
- [x] native `RenderLevelStageEvent.getPartialTick()` とpause中の実レンダリング経路を調べ、実際の補間条件を揃えられるか決定する。raw metadataの上書きや偶然の同値が出るまでの反復は採用しない。
- [x] 有限の同条件・無修復control trialを最大2回行う。条件が揃えば4view/viewport/FOV/matrices/perturbationsとraw lineageを検証し、MATCHED_EVIDENCE_ONLYを記録する。揃わなければ根拠と必要な最小同期変更を記録し、修復比較の未成立を維持する。
- [x] コード変更が必要な場合は、実レンダリング条件を揃える方法・対象・失敗時UNKNOWNを確定してから局所的な実装計画を追加する。比較側の一致検査を削除する解決は採用しない。
- [x] `node --test debug-workspace/evidence/tests/visual-comparison.test.mjs debug-workspace/evidence/tests/visual-capture.test.mjs` と、変更があればgenuine Forge compileを実行する。

**完了条件:** 無修復controlで実際の同条件比較が成立する。未成立ならTask 2の修復比較をPASSにしない。X8 multipassはここで具体的な必要性が確認された場合だけ検討する。

## Task 2: 実際のMOD修復・再開を1件通す

**Files:** TECH `src/kneekura_tech_hub/minecraft/experiment_bridge.py`、`experiment_control.py`、`tests/test_minecraft_experiment_resume.py`、`tests/test_minecraft_scoped_control_interop.py`。既存Blockbench修復経路とTECH受入記録。

**Interfaces:** `prepare_experiment(store, request)`、`export_result(store, registry, request_hash, visual_packet_hash=...)`、`import_experiment_result(store, request_hash, result)`、`resume_experiment(store, result_hash, current_target)`。Task 1の比較を使用する。

- [x] 撮影前に再現可能な実不具合を1件選び、独立した期待状態とvisual/structured checkを固定する。候補は局所部品・UV・texture。現Reimuに該当する未修復不具合があるかは未確認なので、存在を仮定して修正しない。
- [x] disposable project/worldでbeforeを撮影し、AIの原因仮説と根拠画像を保持する。AIの判断はINFERREDとして扱う。
- [x] 既存の局所修復機能で最小変更を作り、変更外の部品/UV/texture/display値が保持されたことを検証する。
- [x] afterの実build/resource/configを固定し、同じsetup/actions/assertionsで新generationを実行する。変更したtarget fieldsのみ `intendedDifferences` に正確なbefore/after値として指定する。
- [x] 妥当な4view比較、独立した期待状態、無関係な回帰の有無を確認し、raw→packet→export→TECH履歴へ保持する。pixel差分だけで改善扱いにしない。
- [x] 別プロセス/新Storeから保持済み結果をresumeし、参照できる証拠とUNKNOWNを確認する。current_targetのhashを変えたnegative checkでは `REVERIFY_REQUIRED`、`CURRENT_TARGET_CHANGED`、`can_replay: false` を確認する。
- [x] `python -m pytest -q tests/test_minecraft_experiment_resume.py tests/test_minecraft_scoped_control_interop.py` を実行し、受入記録を更新する。

**完了条件:** 1件の再現→原因特定→局所修復→妥当比較→履歴/再開を、人間が同じ原証拠から確認できる。exportの保守的projectionは保持する。撮影前に起動が失敗するresource-path修正だけでは、この視覚修復gateの代わりにならない。

## Task 3: native ARENA_EXIT・pre/post timing

**Files:** LAB `debug-workspace/bridge/owner-trigger-config.mjs`、`owner-trigger-source.mjs`、`debug-workspace/evidence/trigger-capture.mjs`、`debug-workspace/evidence/tests/trigger-retention.test.mjs`。LAB運用確認記録。

**Interfaces:** TECH `watch_triggers(store, registry, request_hash)`。明示的sealed opt-in、ARENA_EXITのみ、既存の予約capture slotと非更新leaseを使用する。

- [x] 実際に境界を自然に通過する専用fixtureを準備し、UUID/初期状態/loaded範囲を固定する。r7のReimuはNoAIだったため、そのまま歩くと仮定しない。範囲外teleportや偽triggerの注入でnativeイベントを代用しない。
- [x] watch前のstatus/planningがtriggerをarmしないことを確認する。offsets、tolerance、cooldown、timeout、slotを登録してから有限watchを明示的に開始する。
- [x] 1回のinside→outsideの実観測とpre/postの実timestampを照合する。負offsetに間に合わなかった画像はMISSINGのまま保持する。
- [x] 2回目の同じwatch意図、期限切れ、UNKNOWN/unloaded境界を検査し、再送・架空イベント・slot増加がないことを確認する。
- [x] `node --test debug-workspace/evidence/tests/trigger-capture.test.mjs debug-workspace/evidence/tests/trigger-retention.test.mjs debug-workspace/bridge/tests/owner-trigger-source.test.mjs` を実行し、実イベント記録と区別して保存する。

**完了条件:** 1件のnativeイベントと実pre/post coverage、欠落・タイミング・再送拒否を説明できる。画像が揃わない場合はPARTIALとして記録する。

## Task 4: 視覚形式のbenchmarkとゲーム内の持ち方

**Files:** LAB `debug-workspace/evidence/visual-compiler.mjs`、`visual-presentation.mjs`、`visual-geometry.mjs`。TECH視覚評価記録と受入記録。

**Interfaces:** 同じraw画像を単一RGB、raw4方向、contact sheet、labels+top-down、structured/timeline追加、必要時diagnosticのA〜F形式へ提示する。原証拠は共通とする。

- [x] 独立した正解を先に固定した8ケース（正常、地面埋まり、clipping、texture欠損、部品向き/変位、障害物とprojectile、遮蔽、RGB曖昧性）を揃える。未対応の診断viewは未実行として明記する。
- [x] 各ケースをA〜Fで評価し、YES/NO/NOT_VISIBLE/AMBIGUOUS、参照view、誤判定、読む情報量を記録する。総合点1つで優劣を決めない。
- [x] Task 2の実修復で手動操作・画像探しが減るか確認し、必要な精度を保つ最も簡潔な既定packetを選ぶ。
- [x] 対象itemとdisplay slotを事前に固定し、既存Blockbench holding変更を実ゲームで撮影する。slot値の検証と実際の見え方を別々に判定する。unsupported use_itemは使用しない。
- [x] `node --test debug-workspace/evidence/tests/visual-compiler.test.mjs debug-workspace/evidence/tests/visual-presentation.test.mjs` を実行し、表示が原証拠を変更しないことも確認する。

**完了条件:** ケースごとの失敗傾向と既定形式の選定理由がある。holding appearanceの実画像があり、数値検査だけの受入を解消できる。

## Task 5: Windows・中断・運用境界を整理する

**Files:** LAB運用確認記録、TECH受入記録。LAB既存doctor/G1/G2/stop/finalize経路とCI workflowは最初に調査する。

- [x] 既存Windows full suite失敗を環境不足・製品不具合・fixture移植性に分類する。symlink権限、path/長さ、環境サイズの証拠を残し、skipをpassとして数えない。
- [x] 対応する隔離環境でfull suiteと延期中のThin Viewerを実行する。runner設定を変える場合は必要な変更範囲を別記する。失敗原因を隠すexcludeは追加しない。
- [x] 予算内の正常停止/再開を新しいrunで3回、操作中断を1回確認する。新ownerを作る場合も旧leaseを延長せず、UNKNOWN後は履歴の確認前に自動再送しない。
- [x] 非所有・観測のみの専用runtimeで30分の安定観測を1回行い、heartbeat、PID、writer queue/drop、停止ACKを保持する。有限operatorの120秒予算を延長して実現しない。30分の結果を長期production enduranceの保証にしない。
- [x] 実loaded target/transformed class/config/resourceの証明範囲を表にする。現在のclass-resource/container linkage・ON_DISK_NOT_LOADEDで証明できない項目は未確立として残す。
- [x] 各ソース修正後だけ、関連テスト・独立レビュー・固定SHAのhosted CIを確認する。最終受入表とPR説明を整え、Draft解除/mergeの可否を判断できる材料を作る。

**完了条件:** 対応環境の結果、未対応条件、中断後の安全状態、一般運用を保証できない境界が明確。残るFAIL/UNKNOWNは消さない。

## Order and stop condition

Task 1 → Task 2を最優先。Task 3と4は独立した受入結果として追加し、Task 5で環境・運用条件を集約する。新しい機能を広げる前にこの範囲を終える。

中核の完成条件は設計§24どおり、実際のMOD修復1件を同じ実験・妥当Before/After・人間/AI共通証拠・保持した不確実性で検証できること。production相当の運用準備にはTask 3〜5の未解決事項も判定する。full target equivalenceが未確立なら一般的な実運用検証済みとは記載しない。

この計画の作成時点では新たな試験・変更・公開は未実行だった。実行結果は次の照合表と受入記録を参照。チェックは結果の判定・記録を表し、すべての条件のPASSを意味しない。


## 実行結果の照合

| Task | 結果と境界 |
|---|---|
|1|両方の実partial-tickを保持したnative4方向比較が成立。時計38・比較43・実API検証を実行。OS全体の入力復元は未証明。|
|2|実際のdebug_force_takeoffモデル欠落を原texture保持の6行修正で解消。同条件Before/After、TECH保持、新Store/別プロセスresume、resource driftによる再検証要求を確認。|
|3|自然落下ArmorStandによるnative ARENA_EXITを確認。pre-roll MISSING、0msは+304ms、postは同captureの再利用でwindow PARTIAL。unloaded実機exitは未実行、cleanup UNKNOWNを保持。|
|4|真のTankコピーでholding6→4、埋まり、頭部遮蔽、南側遮蔽、static arrowを撮影。8ケース40A–E判定、8F NOT_RUN。非blind探索評価と独立qualitativeレビューを区別。exact頭mesh clippingはAMBIGUOUS、production既定は未変更。|
|5|Windows全失敗分類、actualThin Viewer、正常3停止、非所有30分観測、loaded境界、独立レビューと修正、Draft公開、固定SHA hostedCIを記録。r9のnative wait pending中断、UNKNOWN保持、closed owner拒否、ACK31/drop0/queue0、export/importが成立。標準WinPS5.1と全Windows成功は未成立。|

詳細: [LIVE-REPAIR-ACCEPTANCE-2026-10-02.md](../../../departments/minecraft/mod-ai/LIVE-REPAIR-ACCEPTANCE-2026-10-02.md)、[VISUAL-FORMAT-BENCHMARK-2026-10-02.md](../../../departments/minecraft/mod-ai/VISUAL-FORMAT-BENCHMARK-2026-10-02.md)、[FINAL-REVIEW-2026-10-02.md](../../../departments/minecraft/mod-ai/FINAL-REVIEW-2026-10-02.md)。Draft維持。一般運用・全Windowsテスト・full loaded target equivalenceは未成立。

最終判断: 計画の実行・結果判定・記録は完了。中断したwaitはUNKNOWNのまま保持し、Draft解除/merge/一般運用受入は実施しない。固定コードCIはpin commit eb68b2dで成功し、最終資料headの結果は受入記録/PR説明の公開チェックで別途確認する。
