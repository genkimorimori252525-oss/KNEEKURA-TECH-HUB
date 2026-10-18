# YSM 再利用ハンドオフ：Entity state → Molang → Controller → Bone → Renderer

2026-10-18 時点。目的は、別の実装・調査で必要な境界だけを再開できること。全資料の再読、全体監査、対象実行を前提にしない。リンクは本資料を YSM 調査ディレクトリに置いた場合の相対パス。既存資料の古い「次の課題」より、この時点の契約と限定を優先する。

## 1. 固定する入力と確度

- 対象：Modrinth `Zqooxsd2`、YSM `2.6.5`、Forge `1.20.1` release、元の Linux x86-64 ライブラリ。
- JAR：63,269,843 bytes、SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`。
- `META-INF/native/libysm-core.so`：SHA-256 `15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22`。
- 比較元ソース：[公式 candidate `f184edabd1b5115ce5a24cb6d155ba5a669f5ba6`](https://github.com/YesSteveModel/YesSteveModel/tree/f184edabd1b5115ce5a24cb6d155ba5a669f5ba6)。全体の `SOURCE_ARTIFACT_DIVERGENCE` と source/artifact equivalence `NOT_ESTABLISHED` は維持。読みやすいクラス名は意味対応であり、元の非難読名の保証ではない。正確な同定は owner + name + JVM descriptor で行う。
- 中央マップは **669 件（405 CONFIRMED + 264 HIGH）から変更なし**。SHA-256 `dc7abc78b1db9401b89ded2e97e2d8341179ccb62d69aa67698c87d8a7174e30`。件数、命令数、テスト数を完成率に換算しない。全体 semantic review は `NOT_RUN`。
- 原本、ソース、raw trace、checkpoint、依存物は Git 外で保持する。環境が変わったら存在・hash・receipt を確認する。元アセットの読出しやデコードは本資料の作成範囲に含めない。

総合入口：[Native reuse guide](NATIVE-REUSE-GUIDE-2026-10-18.md)、[Current handoff](NATIVE-CURRENT-HANDOFF-2026-10-18.md)。

## 2. 層ごとの最短ルート

| 層 | 最初に読む資料（必要なら補助1本） | 再利用で保持する確定契約 | 明示的に残る仮定・未確定点 |
|---|---|---|---|
| Entity state → query input | [State tracker](STATE-TRACKER-INPUT-RECOVERY-2026-10-17.md)、[Movement queries](MOVEMENT-QUERY-RECOVERY-2026-10-17.md) | entity tick と render tick は別の strict-increase gate。`positionDelta` は採用された補間位置の差。位置差を速度・入力と同一視しない。`setEntity` 自体は履歴を reset しない。 | 実際の tick 呼出し、外部 entity 状態、callback の正常復帰は未観測。primary static review の範囲であり、ゲーム内挙動を認証しない。 |
| Molang → evaluation | [Concrete evaluator](MOLANG-EVALUATOR-RECOVERY-2026-10-05.md)、[Java pipeline index §2](JAVA-PIPELINE-INDEX-2026-10-17.md#2-parsing-variables-and-function-execution) | entity-bound evaluator → `Expression.visit` → function dispatch。unsafe entry の return/control cleanup と safe wrapper の `Exception` catch/null を分離。multi entry の pending return は nonnull sentinel。storage/frame/loop は対応する狭い資料へ進む。 | safe wrapper は全 Throwable の保証ではない。全 AST/全 function の意味、全体 work budget、temp storage の per-expression 所有をこの入口から推定しない。入口資料中の282件等は歴史値。 |
| Controller discovery → state/player | [Player assembly](PLAYER-CONTROLLER-ASSEMBLY-RECOVERY-2026-10-17.md)、[Bedrock controller](BEDROCK-CONTROLLER-RECOVERY-2026-10-17.md) | resource discovery と per-entity factory 実行を分離。順序・文字列順 dedup・preview gate を保持。Bedrock は state selection 後に condition refresh。false condition でも player processing は進み、emission/output filtering と時計を分離する。 | list 順序は視覚優先度の証明ではない。外部 transition 実装、callback、副作用、再入、全 controller 種別の等価性は未確定。 |
| Bedrock point producer → blend queue | [Producer invariant](BEDROCK-QUEUE-PRODUCER-INVARIANT-2026-10-18.md)、[Queue consumer](BONE-COMMIT-QUEUE-RECOVERY-2026-10-17.md) | 下記の限定条件で built-in linear/segmented の beginning subtype が同質となる。consumer は condition → active → nonnull を順に採用し、poll は point を除去しない。 | 外部 transition、途中観測、任意の public field 書換えを除外した条件付き証明。新しい producer join の独立 semantic review は `NOT_RUN`。 |
| Frame processing → commit ownership | [AnimationProcessor](ANIMATION-PROCESSOR-RECOVERY-2026-10-16.md)、[Async ownership/wait](ASYNC-ANIMATION-RECOVERY-2026-10-17.md) | `shouldTick` が止めるのは controller advancement であり、queue visitation/commit 等すべてではない。task 実行後に remove。async submit、`Future.get`、再評価を区別する。 | processor の tail cleanup は finally ではない。interrupted wait が stored future を消しても job 完了証明にはならない。静的な例外可能性を再現済み race/bug と呼ばない。 |
| Bone → Java array | [Bone state](BONE-STATE-RECOVERY-2026-10-17.md)、[Commit/queue](BONE-COMMIT-QUEUE-RECOVERY-2026-10-17.md) | input は各 bone 12 floats：rotation XYZ、position XYZ、scale XYZ、ownHidden、childrenHidden、tracking。output stride は4。commit は flags→初期回転+offset→position→scale→cache reset の順で、atomic ではない。fresh array path はゼロ初期化。 | backing arrays/参照は共有される。constructor 単体の保証と fresh allocator の保証を分離。4番目の output slot の意味、concurrency は未確定。 |
| Java Renderer → native affine/output | [Java handoff](JAVA-RENDER-BOUNDARY-RECOVERY-2026-10-17.md)、[Native reuse guide: contracts](NATIVE-REUSE-GUIDE-2026-10-18.md#contracts-to-preserve) | input/output backing arrays を渡す。geometry handle は registry key。reached affine は `P·T((-x,y,z)/16)·T(p)·Rz·Ry·Rx·S·T(-p)`、`p` は Java-visible pivot/16。legacy code6 は12 floats +2 ints/vertex。output writer はXYZだけ、scratch 再利用時の selected-range copy は stale 値を含み得る。 | 対象 float32/trig、全 hierarchy 入力、全 renderer/backend、GPU 結果は未証明。normal arithmetic は単純な inverse-transpose へ置換しない。code1 の36-byte vertex と code6 を混同しない。 |

## 3. Bedrock の新しい限定証明を適用する条件

consumer が必要とする最小条件は「各軸の最初の採用 point が beginning で、その progress が `<= -1e-5f` または `>= +1e-5f` の場合、後続の採用 point も読出し時に beginning」である。完全同質性はこれを満たす十分条件。near-zero/NaN の early return だけでは producer 同質性を証明しない。

元 JAR と一致する **94 method records / 9 owners** の構造照合と既存資料を使った条件付き静的結論：

- 正常完了した controller-managed cohort、同期した初期化、有限 render time/duration、不変の state data、独立した player/queue mutation・再入なしを前提とする。
- exact built-in linear は保存 duration を返す。segmented は clone ごとに独立 cursor を持つが、同じ変更されない segment list の終端を cached right-bound に保持する。cursor 更新では duration は変わらない。
- この条件下で beginning phase 中の全採用 point は `BeginningTransitionPoint`。全 player の処理を終えてから訪問すれば、同一の controller processing call で全員が境界を越える。scale beginning の無効化も subtype を変えない。
- empty axis は null のまま除外。false holder condition は processing を止めない。beginning 後の running/ending/absent の混在は、最初が beginning となる cast 要求を発生させない。
- **missing animation の除外には `nextAnim` が既に null という普通の consumed/reset pending-state 条件が必要。`resetToIdle` 自体は `nextAnim` を消さない。** process 前の複数の直接 selection、途中例外、再入へ一般化しない。

94件は構造一致件数であり、94件の独立 semantic review や対象実行ではない。外部 `startNew()/length()` は等しい安定した境界を強制しない。再実装で上記条件を保証できなければ mixed-type consumer policy を別途設計する必要がある。本資料は元コードの変更を提案しない。

## 4. 混ぜてはいけない4種類の証拠

1. **Main guarded JNI continuation**：explicit absent-environment fixture の後、`UNMODELED_STAT_PATH_OR_ABI`、`__xstat` ABI1、path `/tmp`、caller `0x31122e` で停止。checkpoint SHA-256 `52bfa6d4103ec1ded965474d4151466cbb2b215118c73a3901b148d688a77b6a`。2つの virtual workers は双方未実行。Path state unchanged、新規 JNI calls/pending Java exception なし。78 scoped tests +26 independent checks と654-instruction continuation はこの限定記録であり、filesystem success を補わない。
2. **Isolated metadata callbacks / read-only metadata proofs**：[52 selected member slots](NATIVE-JAVA-MEMBER-INDEX-2026-10-18.md) は13 receipts、47 original-YSM +1 commons dependency +4 JDK。48 callback-derived identities と4 zero-instruction metadata/pointer proofs。index は `manager-global+offset` で引く。access 等の receipt 欠落を他実験から埋めない。constructor/parser 実行、main JNI 進行、runtime registration の証明ではない。
3. **Authored reference tests**：[Geometry classifier reference](NATIVE-GEOMETRY-CLASSIFIER-REFERENCE-2026-10-18.md) は13 focused +4 independent tests。数学的に作成した6 recordsを入力し、演算順序・binary32 rounding・provider provenance を追う。RN-even、FTZ=False、DAZ=False の非trappingモデル。target MXCSR と dynamically resolved `acosf` は未確定。host `math.acos` は比較用であり、対象互換性・モデル分類の視覚的意味を保証しない。
4. **対象を動かさない静的証明**：Java classfile/元 native bytes、pinned candidate source と限定 receipt の照合。上記 Bedrock invariant や native affine/header proof が含まれる。原本構造、source-range/hash/link checks、数学的 fixture が一致しても JNI/JVM/game/GPU execution へ昇格させない。

[17 original native entry identities](NATIVE-ENTRY-CONTRACT-INDEX-2026-10-18.json) は8 original-YSM classesの宣言対応。別の **5 LWJGL wrappers** は Minecraft1.20.1が宣言する lwjgl-opengl3.3.1 の対象で、17に加算して original-YSM 宣言数と呼ばない。52 member slots とも別集計。実際の `RegisterNatives` 成功、完全な `JNI_OnLoad`、real worker scheduling、実モデル load、描画成功は未証明。

## 5. 必要な1つだけ再確認する

以下は再開時の任意コマンド。本資料作成では実行していない。`JAR`/`SRC` は上記固定入力の外部絶対パス、`OUT` は Git 外の書込み先。YSM 調査ディレクトリから実行する。これらは静的 Python auditor または authored test であり、対象 JAR/native を実行しない。

```sh
# Entity state の証拠回帰
python tools/state_tracker_input_ysm_265.py --jar "$JAR" --source-root "$SRC" --evidence STATE-TRACKER-INPUT-EVIDENCE-2026-10-17.json --out "$OUT/state-tracker.json"

# Bone 配列境界だけ
python tools/bone_state_ysm_265.py --jar "$JAR" --source-root "$SRC" --evidence BONE-STATE-EVIDENCE-2026-10-17.json --out "$OUT/bone-state.json"

# Blend consumer / ordered commit だけ
python tools/bone_commit_queue_ysm_265.py --jar "$JAR" --source-root "$SRC" --evidence BONE-COMMIT-QUEUE-EVIDENCE-2026-10-17.json --out "$OUT/bone-commit-queue.json"

# Authored classifier reference の13テスト。別receiptの独立4テストを含めた再実行とは呼ばない
(cd tools && python -m unittest test_native_geometry_classifier_reference_ysm_265 -v)
```

最初の3コマンドは evidence regression であり、新しい Bedrock producer proof の独立 semantic review を代替しない。入力がなければ既存 receipt を参照し、無断のダウンロード、全体スキャン、成功stubによる guarded continuation は行わない。

## 6. 次の作業を選ぶ基準

Entity input の再利用なら最上段、Molang 実装なら evaluator と必要な storage/AST の1資料、blend 実装なら上記 subtype 条件と consumer を読む。renderer 実装なら array契約→affine/output→必要な backend だけへ進む。各作業で「固定入力」「保持する契約」「残る仮定」「限定された確認方法」を先に宣言する。

未実証事項を実装済み・動作済みと書かず、歴史的 receipt の古い停止位置を最新の `/tmp` frontier と取り違えない。元の未知状態を successful stub に置換して進めることは、この再利用ハンドオフには含まれない。

追加の独立確認： [Bedrock producer invariant の限定意味レビュー](BEDROCK-QUEUE-INDEPENDENT-REVIEW-2026-10-18.md)は条件付き証明を支持。閾値は binary32 の正確値、共通の遷移終了は境界到達時の条件付きであり、時計の進行自体は保証しない。全体の意味レビューや実動作確認が完了した意味ではない。

呼出順序の追加確認：[Controller visitation order](CONTROLLER-VISITATION-ORDER-2026-10-18.md)。原本は controller A の process→visit、B の process→visit、最後に共通 bone commit。全controllerのprocessを一括先行する順序へ変更しない。shouldTick=false でも visit と dirty更新は行われ、前回の処理完了を保証する旗ではない。

制御命令の有効期間：[coded control capability](CODED-CONTROL-CAPABILITY-LIFETIME-2026-10-18.md)。通常は predicate 中だけイベントに制御先を設定し、その後の点計算前に消去する。子contextは同じイベントを共有。例外・再入は別扱い。[非同期イベントの受渡し](ASYNC-EVENT-CAPABILITY-PUBLICATION-2026-10-18.md)では、正常結果を描画側が新たなMolang contextへ入れ直す経路は見つからず、描画補助は主にメタデータ・脚の数値を利用する。Futureの消去やnull結果を、共有配列の安全・処理完了の証拠にしない。両節は限定独立レビュー済み。

パーサー再利用時の注意：[failed parse → temp address](PARSER-FAILURE-TEMP-ADDRESS-2026-10-18.md)。一時変数の割当後に失敗し、同じparserを次に再利用すると、成功した次の式にもずれた番地が残り得る。成功後のresetは既存ASTを再採番しない。観測差には現在frameの論理サイズ・offset・残存値などの条件が必要で、実物の不具合再現ではない。限定独立レビュー済み。
