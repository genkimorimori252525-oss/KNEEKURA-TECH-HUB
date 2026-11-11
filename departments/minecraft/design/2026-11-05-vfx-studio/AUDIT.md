# KNEEKURA VFX Studio v1.1 — 軽量・敵対監査記録

- 実施日: 2026-11-05 JST
- 対象: PLAN.md / 計画基準 main@4866d7d7bbfe42a668437ebf38f8a13d6a3d59e7
- 監査方式: 既存ソース・検証報告・公開 upstream の静的調査による設計監査。**独立レビューや新規実クライアントテストではない**。
- 総合判定: **DESIGN READY WITH GATES**。方針の重大な論理破綻は見つからなかったが、実装・実機・権利・互換性の合格は未確認。導入済み/動作済みとは記載しない。

## A. 現行の真偽区分

| 主張 | 確認した根拠 | 判定 |
| --- | --- | --- |
| 既存水槽は実 Minecraft を正本にしている | lab/docs/KNEEKURA_LAB_HISTORY.md / 現行統合ハンドオフ | CONFIRMED_DESIGN |
| registered UUID の XYZ, velocity, yaw/pitch, AABB | KneekuraDebugCardinalCapture.java の entityFact/serverFacts、KneekuraDebugServerObserver.java の SERVER_ENTITY_STATE | IMPLEMENTED; 各ランの鮮度は別途 |
| XZ の俯瞰地図と人/AIの画像資料 | lab/debug-workspace/evidence/visual-geometry.mjs, visual-compiler.mjs | IMPLEMENTED |
| Cardinal-4 が実画面を撮影し復元する | 同名 Java 実装、KNEEKURA_LIVE_ACCEPTANCE_REMAINDER_20261002.md | REAL_CLIENT_VERIFIED_FOR_PRIOR_SCOPE |
| 全モブリアルタイム地図 | 現行は明示 UUID と bounded subjects | NOT_ESTABLISHED |
| VFX の一時停止/巻き戻し/四方向同時瞬間 | Photon provider API と client time を含む実機テストなし | NOT_ESTABLISHED |
| 武器ボーン、FX emitter、画面全体シェーダーの空間記録 | 現行 raw subject snapshots の外 | NOT_IMPLEMENTED_IN_THIS_PLAN |
| AIによるVFX自動編集・リテイク | 現行 Blockbench 静的アイテム guard とは別 | NOT_IMPLEMENTED |
| Photon Forge 1.20.1 版 | https://modrinth.com/mod/photon-editor/version/mc1.20.1-1.1.17-forge および upstream 1.20.1 branch | RELEASE_EXISTS; RUNTIME_COMPATIBILITY_NOT_TESTED |

## B. 失敗を想定したレビュー

| ID / 優先度 | 不具合になり得る点 | 計画に反映した防止策 | 実装前/受入時のゲート |
| --- | --- | --- | --- |
| A01 / HIGH | Cardinal-4は4つの別render frame。粒子が動くのに「同一瞬間の4視点」と誤記する | 1視点 RECORD_REPLAY を先行。四方向は VFX clock freeze の証拠がなければ sequential time skew を表示 | 実 tick/render frame/FX clock 差が一致するかを実測 |
| A02 / HIGH | 既存 capture stage は AFTER_LEVEL_BEFORE_HAND_HUD で post-effect を拒否。画面の歪み・手元演出が撮れない | P6 で別 opt-in capture stage。既存ガードを緩めない | stage別 PNG と原画維持、カメラ/画面状態復元 |
| A03 / HIGH | XZ 地図が全モブ/全ブロック地図と誤解される | 対象UUID限定の地図を保持。必要範囲だけ bounded block query と Y elevation を追加 | 未登録 mob は描かない。欠損/未捕捉は明示 |
| A04 / HIGH | ボーンの client pose、server XYZ、VFX emitter の時間・座標系の違い | SOURCE_KIND と座標系、profile/model/bone layout hash、tick+partialTick を結び付ける | 既知の武器動作で位置誤差を独立検証 |
| A05 / HIGH | Photon の版/依存/API/ライセンスを想像で統合する | P0 で配布版、対応するLDLib、ライセンス条件を固定。コード移植・転載は保留 | upstream の適用条件確認、隔離環境実動作、第三者資産なし |
| A06 / HIGH | AI の操作が一般コマンド/任意 script を許し、ワールドやローカルファイルを破壊する | opt-in disposable world、既存owner/lease/CAS、schema限定操作、無断自動install無し | target mismatch / stale generation / unknown outcome / path traversal 負例 |
| A07 / MEDIUM | モブの映像と構造化座標を同じ瞬間として扱う | 観測時刻/発生源/鮮度を別々に保存。描画上の推測と直接数値を分離 | 不一致時は UNKNOWN / INCONCLUSIVE、見かけ上一致で PASSにしない |
| A08 / MEDIUM | GPU粒子やシェーダーの巻戻しを seed のみで保証する | RECORD_REPLAY で原フレームをコマ送り、CONTROLLED_SEEK は別の実証ゲート | 再実行時の差を測定。seek不可は UNAVAILABLE |
| A09 / MEDIUM | 常時全フレーム高解像度撮影でストレージ・描画負荷が増大 | 有限の ROI・秒数・fps・バイト数・対象数・書込キュー予算。通常時OFF | drop/queue/frame timeと停止後の回復を測定 |
| A10 / MEDIUM | 既存 LAB/Viewer/Score Mode と機能が重複、正本が分裂 | 統合LAB+既存EvidenceStore。Score Mode(PR#97)やMotion Traceの最新ソースと照合 | 新 DB/runner/standalone LAB を作っていないこと |
| A11 / MEDIUM | aestheticな好みを画像差分だけで PASSとする | 数値・視覚・ゲームプレイ・性能を分離。AI評価は根拠付きだが推論として残す | 実際に不自然な斬撃例と正常例を比較 |
| A12 / MEDIUM | cancel/世界再読込でクライアントに粒子/音/残像が残る | lifecycleに CANCEL/END/UNLOADを持たせ、有限寿命とidempotent stop | 早期キャンセル/死亡/アンロード/遅延packetの負例 |

## C. 実装を始める前の「止める条件」

1. 1.20.1 Forge / Photon / LDLib / 他必須依存の同居と出典が確認できない。
2. 該当 upstream ライセンスの条件が明らかでないまま、第三者コード/資産のコピーや未許可の移植が必要になる。
3. 使用する水槽が作業用ワールドではなく本番ワールドを指している、または owner/lease/RunSnapshot が不一致。
4. キャプチャ中に実ゲームのプレゼンテーション状態を復元できない。
5. 完了UNKNOWN後に同一の副作用命令を再送しないと先に進めない。
6. 現行受入記録・権限境界・別作業の成果を壊さないという証拠がない。

「止める条件」に遭遇したら、その phase の結果を BLOCKED/UNKNOWN と記録し、必要な **最小修正の提案**を出す。安全制約を外して通したことにはしない。

## D. あえて採用しなかったもの

- 新しい第二の水槽、Web側の独自 Minecraft レンダラー、独自Evidence DB、常駐AIエージェント。
- 最新 Photon 2.x の1.20.1への無許可直接移植、商用/配布条件を無視した upstream 統合。
- 任意スクリプト/GLSLのAIによる無制限実行。
- 全世界のモブ/ブロック/粒子を無制限にスキャンする「完全地図」。
- GeckoLib と EpicFight の同時必須化。
- 一次実証時点での動画編集、HDR/ポストエフェクト全面制作、フォトリアル演出の自動採点。
- 単にソース試験が通ったことを、実Minecraftや演出品質の合格へ昇格させること。

## E. 最終評価・次の条件

設計は軽量で、既存の verified Tank / 4方向 raw capture / 構造化位置 / XYZ / Evidence を維持しながら VFX の新しい責務だけ追加する方向に整っている。

**Plan = READY（対象範囲とゲートを確定） / Runtime = NOT_RUN / FX Provider Compatibility = NOT_RUN / AI VFX Editor = NOT_IMPLEMENTED / License Gate = OPEN.**

次の作業は PLAN.md の P0 から始める。P0の権利・API・実機確認結果により Photon との接続方式は修正できるが、ここに記載した根本原則、既存水槽の再利用、真偽と証拠の区分は変更しない。

レビューはこの branch に書類だけを提案する。merge/公開範囲/Actions/runner/設定/秘密の変更は行わない。

## F. 2026-11-11 統合改訂の追加監査 — 制作方式・アニメ・検証選択・人間協業

**対象:** [VFX PLAN §8](PLAN.md) のModel/Animation Production lane、および [共通デバッグ計画 §8–14](../2026-10-09-shared-mod-debug-roadmap.md) のVerification Router/Decision Observatory/Human Review。従来A01–A12と停止条件を保存し、以下は追加の問題・受入条件である。コード、外部プラグイン、CI、実機、設定を変更したという記述ではない。

### F1. 真偽分類の追加

| 主張 | 判定 | 論点 |
| --- | --- | --- |
| 既存Blockbenchで静的杖モデルを作成・パーツ/UV/texture/displayを修正 | SCOPED_LIVE_EDITOR_VERIFIED | 2026-09-30のstaff、2026-10-01の部分修復受入に限定。完全なanimated mobは未証明 |
| 既存の水槽/Forgeは実描画・UUID・時刻・限定的な動作証拠を扱える | IMPLEMENTED_SCOPED | source/owner/world/epoch/renderer identityは個別に照合。4方向は逐次 |
| img2blockbenchの3ルート、Mosaicary GLB/glTF→GeckoLib、BlockSmith text-to-3D | UPSTREAM_ADVERTISED_OR_BENCHMARKED | KNEEKURA連携/Windows/Forge 1.20.1互換/品質はNOT_RUN |
| sosadly上流と他のMCPにGeckoLib/clip生成機能が存在 | UPSTREAM_ADVERTISED | 現在のTECH HUBのguardと同一ではない。新MCPの安全な共存はNOT_RUN |
| Animation Method Registry、動的な制作方式切替、最終bundle | PROPOSED_NOT_IMPLEMENTED | manifest、互換性無効化、clip別route、immutable CAS連鎖の実装と負例が必要 |
| Verification Routerの省略理由・最小手段選択、Debug Wand、人間のワンクリック確認 | PROPOSED_NOT_IMPLEMENTED | 既存TaskContext/Owner権限の読み替え禁止 |
| GeckoLib 4を使用した既存Kirbyのgeometry/animation | EXISTING_PRODUCT_ASSETS | 汎用制作・汎用controller/animation品質の受入ではない |
| 新案で人間作業が短縮し、水槽起動が減る | HYPOTHESIS_NOT_MEASURED | 同じ課題をbaseline比較するまで効果を断言しない |

### F2. 敵対監査（A13–A29）

| ID | 重要度 | 危険・失敗例 | 防御・実装ゲート |
| --- | --- | --- | --- |
| A13 | HIGH | 「検証最小化」が、必要な実ゲーム判定の省略と偽PASSにつながる | assertion domainと未証明の残件を保存。実機依存のclaimはlive未実行ならNOT_RUN。source testだけで合格としない |
| A14 | HIGH | agentが水槽実行を繰り返し、時間・CPU・diskを消費する | 起動前に主張/既存証拠不足/新取得ログと対象を記述。等価実行の再利用・skip理由。確率的検証だけ有限試行契約 |
| A15 | HIGH | img2blockbenchの1枚画像から不明な背面・深度・正確なboneを推定し「再現成功」と偽る | multi-view/不明領域記録、人間の好みと形状構造の結論を分離、未知箇所をUNKNOWN |
| A16 | HIGH | MosaicaryのURL pluginが再起動時に自動更新され再現性がなくなる | 固定commitからローカルpluginをハッシュ検証して使用、更新は別々にレビュー |
| A17 | HIGH | 外部3D/画像providerへ第三者の素材/ローカル秘密・契約のない有料API呼び出し | 送信先/対象/license/budgetを可視化して明示opt-in。providerを選んでも権限を取得しない |
| A18 | HIGH | 新しいMCPを複数接続し、別AI/別pluginが同じBlockbench projectへ同時編集 | 中核sosadlyの現行guardを保持し、排他的なeditable session・project identityを強制。新MCPはまずoffline参照 |
| A19 | HIGH | bone名が同じでpivot・階層・bind poseが違うのに旧アニメを無検証流用 | rig layout hash、coordinate mapping、clip参照、expected generationでinvalidate。retarget実証までUNKNOWN |
| A20 | HIGH | glTF→cubesで材質・UV/透明度・easing・effect keyframe・IK constraintが失われる | 損失項目を明示した LOSSY_CONVERSION、各format出力とsourceからの意味保存を独立検査 |
| A21 | HIGH | animation clipの一括replaceにより、人間の手修正や他clipが消える | expected-old readback、指定clip/part単位、pre/post diff、無関係ファイルのhash不変、未知完了のblind retry禁止 |
| A22 | HIGH | Mob AIのfailure reasonを時間的な並びから創作してしまう | Decision ObservatoryのDIRECT/INSTRUMENTED/DERIVED/UNKNOWNと因果分類を維持。Goal selected≠実行成功 |
| A23 | HIGH | 実クライアントで取得したVFXだけでserver HITや同期が成立したと断言 | server authoritative eventとclient animation/FXを別clock・side・packetで観測。未確定の因果はUNKNOWN |
| A24 | MEDIUM | Animation previewだけで実ゲームのcontroller/Molang/rendererの成功と誤認 | clip structure / editor screenshot / runtime renderを別判定列にして各証拠を要求 |
| A25 | MEDIUM | 解決済みの静的問題も毎回水槽へ持ち込み、human reviewも毎度求める | VerificationDecisionに低コスト選択/skip理由、予算と重複抑制、短いまとめレビュー |
| A26 | MEDIUM | Debug Wandで任意のモブや本番worldを変更・操作できる | debug-only、既存owner+lease+allowedArena、定義済み有限scenarioだけ。通常モードでは機能なし |
| A27 | MEDIUM | 確率的モブ挙動の1成功だけで動作保証、または省略ポリシーで再現性調査を禁止 | seed/試行分布/試行予算/停止基準を定義。ログ欠損/observer負荷を報告 |
| A28 | MEDIUM | human reviewが未回答なのにAIが審美品質を自分でPASSへ昇格 | 省略/未回答/人間選択を別状態保存、好みの判定は本人、AIは根拠付きの補助推定のみ |
| A29 | MEDIUM | 複数planが正本化し、既存VFX・shared debug/Entity Decision Observatory/モデル設計の権限とAPIが矛盾 | 本PRで既存3文書のみ増補。横断的検証はshared、制作方法はVFX、監査はAUDIT、意思決定の観測契約は既存Decision Observatoryを引用 |

### F3. 受入と停止条件（追加）

**静的・低コスト試験**: (1) 規則で水槽不要と判定したUV/json修正がコード/Editorのみで完結し、未実機領域がNOT_RUNのまま残る (2) 実機が必要なMobAI/Controller/同期は誤って省略しない (3) stale evidence/誤ったasset・bone/UUID/runが再利用不可 (4) 人間の審美確認を未回答のまま完了扱いにしない。

**route/animation試験**: (1) 2方式以上を比較、意図的な切替と旧候補保全 (2) model/rig/animation/FXの参照が一本のfinal manifestで追える (3) 同名bone別pivot、欠損texture、古いclipの混入、変換で失われたeffect、任意上書き、未知完了を必ず負例で拒否 (4) export構造/Editor外観/実ゲーム結果を独立保持。

**ゲーム内実証**: (1) 1体のUUID/一定のarenaでAI行動とclip/FXを限定観測 (2) 戦闘のserver stateとclient render/timeの対応を分けて記録 (3) 異時刻Cardinal-4を同一瞬間と誤記しない (4) camera、input、world、session、FX全ての停止と復元を確認 (5) 人間レビューを必要時だけ最少操作で実施し、実際の手数を計測。

**停止条件**: plugin権限の拡大、無断課金/外部送信、競合MCPのeditor乗っ取り、旧候補/人の編集の破壊、既存本番worldへの副作用、ライセンス不明のコード取り込み、再試行不能なUNKNOWN状態、実ゲーム検証が不可なのにPASSが必要なとき。無理にPASSにせずBLOCKED/NOT_RUNとして終了する。

**今回の監査判定**: DESIGN EXPANSION READY FOR REVIEW WITH GATES / IMPLEMENTATION NOT_RUN / PROVIDER INTEGRATION NOT_RUN / WINDOWS RUNTIME NOT_RUN / QUALITY IMPROVEMENT NOT_MEASURED。旧A01–A12の結論・既存の権利ゲート・製品本番制限・未マージ境界は変更しない。

## G. 2026-11-11 Animation Provider 計画の追加監査

**監査対象:** VFX PLAN §9. 元の A01–A29 を削除しない追加の不具合・安全・品質チェック。不採用の Kimodo、video2mocap は導入候補/自動fallback/依存の全てから除外する。今回の計画更新ではコードやプラグインは実行していない。

### G1. 実装/宣伝/実機を混同しない

| 対象 | 現時点の証拠区分 | 実装時に確かめること |
| --- | --- | --- |
| sosadlyのcreate_rig / generate_animation / add_keyframe(s) / analyze_animation / preview_animation | UPSTREAM_DOCUMENTED; KNEEKURAの現在のbounded adapter内はPARTIAL/NOT_ESTABLISHED | 固定sourceに実在するか、読み書き/戻り値/失敗時権限、before/after roundtrip |
| adhi-jp GeckoLib validator / animation upsert / still frame | UPSTREAM_DOCUMENTED; KNEEKURA統合NOT_RUN | 4.2.5等のテスト対象版と現行形式差、手修正消失、easing/effects/pose readback |
| jasonjgardner animation skill / timeline / graph editor / GeckoLib easing | UPSTREAM_DOCUMENTED; KNEEKURA統合NOT_RUN | Bezier等のGeckoLib変換不可、export後の意味保存、bounded edit |
| RenasDemirbas rig/IK/動作検査 | UPSTREAM_DOCUMENTED; KNEEKURA統合NOT_RUN | 実アルゴリズム/API、GPLと再配布、sosadlyとの機能の重複/衝突 |
| EL4CTEO Blender animation skill | UPSTREAM_DOCUMENTED; KNEEKURA統合NOT_RUN | Blender依存、bakeとglTFのloss report、GeckoLib形式との独立受入 |
| AI自己改善・routeの自動選択・失敗の知識化 | DESIGN ONLY | モデルの提案と実験結果・永続正本の区分、誤改善のrollback、human oversight |

### G2. 追加の敵対監査 A30–A42

| ID | 危険 | 最小防御・反例試験 |
| --- | --- | --- |
| A30 | 新しいMCPを無条件で増やし、同一Blockbench projectへ2つのwriterが同時変更 | editor ownerは1つ。二重writer要求/別plugin変更を拒否し既存保存状態が維持される |
| A31 | sosadly上流のREADME機能を現在のTECH HUBで実行可能と仮定 | 固定版APIと現在のguardに対するcapability probe。READ-ONLY/NOT_CONFIGURED/NOT_IMPLEMENTEDを分ける |
| A32 | 任意execute_scriptやplugin installを「animation作成に必要」として開放 | hard deny、proxy clientから迂回不能なplugin側拒否、明示的なバージョン・権限・所有地の検査 |
| A33 | 人が修正したclipをreplace:true等のwhole clip updateで消してしまう | expected old clip/full project hash、target bone/time span限定、非対象部の不変性、rollback snapshot |
| A34 | Bezier/step/easingがGeckoLibへ無変換で反映されると仮定 | target GeckoLib4のeasing/restrictions・export→readback。lossはLOSSY_CONVERSION/UNKNOWN、未証明PASSなし |
| A35 | 同名bone、異なるUUID/pivot/親子で旧アニメ/FXだけ持越し | rig hash/transform tree/clip bindingsとdependency invalidate。古い材を許可なく使わない |
| A36 | IK/Procedural/Blender motionをエクスポートでそのまま再現できると仮定 | finite keyframe bake、sampling、root motion、Euler/Quaternion、axis、floor contactの変換検証 |
| A37 | アニメ生成数を増やすため、同じモデルを毎回実機起動 | offline schema/editor優先、Verification Routerのclaim単位決定、source/conditions同一の理由なき反復はskip理由 |
| A38 | 「実機起動しない」が硬直し、ランダムAI/ネットワーク/rendererの必要な反復まで禁止 | 合理的な新しい証拠とscope/予算がある試行は複数回許可。固定回数上限を品質の代わりにしない |
| A39 | AI自己改善が要求や安全境界・不採用の変更を勝手に行う | 最適化可能なのは方法/アルゴリズム/局所fixtureのみ。権限・課金・出版・不採用解除にはuserの別同意 |
| A40 | AIが1回の成功例を根拠に、推奨アルゴリズムを普遍的な正解として固定 | 版本・モデルtype・動作type・試験datasetと失敗例を保持。baseline比較の効果とconfidenceを分離 |
| A41 | Auto review/request_reviewが応答を待ち続け、ユーザーに頻繁な操作を要求 | AIが必要な比較を準備。人間の嗜好判断のみ必要時にまとめて提示。未回答=NOT_REVIEWED、他領域の合格と混同しない |
| A42 | Specialist repoを取り込んだ後に、その機能が既存sosadlyへ追加され重複したまま残る | capability inventoryの定期的な差分検査、同等なら重複実装を廃止候補として比較。削除/切替はreplay試験と移行条件でのみ実施 |

### G3. AIの改善余地を保証する監査基準

**自律性の確認:** あらかじめ指定した正解の方法を単純実行するだけでなく、(1) アニメーションの不自然さを検出 (2) 分かっている構造/予算下でclip編集または別routeを選択 (3) 旧candidateを保存 (4) before/after static/pose比較 (5) 必要な場合のみ実機/人間へ問い合わせ (6) 妥当な範囲で方法を改良して記録できるか評価。実装AIがどのルートを選んだかを人間に簡潔に知らせる一方、内部の全試行を都度承認させない。

**自己改善は科学的な仮説の比較:** 新規repo、何らかのIK手法、モデル変換ルート、独自validatorの提案は許す。採用には同じ課題の前後比較、費用/遅延/劣化・権利/依存の記録、旧環境へのrollback性が必要。ライセンス/安全ゲートを破った最短経路や幻覚的な改善は棄却する。

**検証する失敗例:** lossのあるクリップ変換、boneピボット不整合、変換済みと見せかけて再生しないcontroller、古いrouteのCAS参照混入、権限外書込、editor二重起動、実機の必要性を明示できない反復、限定実機/静的/人間審美の混同。テストで改善不能だった場合は例外を隠さず、未達として止める。

**最終監査判定:** 設計としての採否・実装順序は明確だが、S0–S6の実装、GeckoLib/Blockbenchの増設権限、Windows実機、改善効果は全てNOT_RUN。未検証の外部repoはライブラリを丸ごと導入しない。既存 VFX/A0–A6、共通デバッグ・人間レビュー計画を維持する。
