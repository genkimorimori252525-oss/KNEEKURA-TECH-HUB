# 実装計画 — mcbuild完成建築のバージョン別移植（2026-11-14）

**Status: APPROVED_DIRECTION / PLAN_ONLY / NO_CONVERTER_CODE_YET**  
起点：[PR #115](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/pull/115) の建築ジャンル。  
事前監査：[AUDIT-2026-11-14.md](AUDIT-2026-11-14.md)。  
技術ソース：mcbuild固定 `34ce86372d4c23f4d83d4e24fc256cb399d6c3e3`、WorldEdit 7.2.15 `5ca4dffd1208846a24c9462b855690f835c9eadf`。

## 目標と非目標

**目標**：mcbuildで完成した**同一の建築物**を、ブロックID＋ブロック状態＋XYZ座標を維持しながら、まず **Minecraft Java 1.20.1 + Forge（WorldEdit 7.2.15）** に持ち込める形式へ変換する。その後、必要に応じて対象バージョンを増やせる構造とする。建築AI・視覚的再設計は現在のmcbuildのまま利用する。

**非目標**：mcbuildのNeoForge MODをForgeへ移植すること、ビルダーを常駐サービス化すること、毎回AIに再評価やリライトを義務付けること、見た目や創造性に一律の点数をつけること、ワールドを無承認で更新すること。ブロックエンティティの中身・エンティティ・バイオームの完全な再現は今回の対象外。

## 設計する経路

```text
mcbuild LLM/DSL → VoxelGrid（疎な完成配置データ）
                       │
                       ├─ v3 .schem 原本（不変保存、SHA-256）
                       │
                       ▼
              Building IR（ブロックID/状態/XYZ・origin・意図情報）
                       │
             Target Profile（1.20.1/Forge）
                       ▼
             ID/状態検証 + 代替表の明示適用
                       ▼
              Sponge Schematic v2生成
                       │
                独立Readerでread-back + 差分検証
                       ▼
             適用方法レポート（air policyを含む）
                       │
               **人間の選択 / バックアップ**
                       ▼
                 1.20.1 WorldEditへ手動配置
```

**重要**：最初は別のCLI／ライブラリとして実装し、既存`runner.py`へ自動変換・自動ペーストを挿し込まない。運用を確認してから任意の`convert`サブコマンドとして接続してよい。

## 作業順序と合格条件

### P0 — 形式／実装面の再現可能なベースライン

- [ ] 既存のmcbuildオフラインFakeLLMを pinned checkout で実行し、原本`final.schem`と生成物SHA・プロンプト・commit・実行環境を記録（この段階でAPI課金は不要）。
- [ ] mcbuild v3 NBTを読み取り、Version=3、DataVersion=3953、`Schematic.Blocks`階層、ブロック寸法、palette、VarInt、Offsetを解析したfixtureを保存。1.21.1の本来のDataVersionは3955と別記。
- [ ] WorldEdit 7.2.15のv2 Reader/Writerソース（監査のリンク）と、Sponge仕様v2/v3を参照して最小テストケースを確定。

**Gate P0**：静的説明だけでPASSにせず、ピン留め原本と読み取り結果が一致する。テスト環境がない場合はNOT_RUNを明記して次へ進む条件を残す。

### P1 — 中間表現（Building IR）の定義

- [ ] 実際に配置されたブロックのXYZ整数座標、完全修飾block ID、stateプロパティ、source version、原点／貼り付け基準、寸法を保存。情報を失う座標丸めは禁止。
- [ ] **未配置セル（ABSENT）／明示されたair（EXPLICIT_AIR）／通常ブロック（SOLID_OR_OTHER）を区別**。`VoxelGrid.items()`から直接取得できる場合だけ完全区別。v3`.schem`のみの入力は`AIR_INTENT_UNKNOWN`。
- [ ] 絶対座標と相対座標、origin/Offsetの関係を明示し、boundsは実際に残った配置情報から再算出。不要な空白による巨大外接領域の確保を防ぐ。
- [ ] 元データ／生成原本を上書きせず、固定SHAと変換履歴を残す。ローカル成果物のGit管理は行わない。

**Gate P1**：座標の負値、非ゼロorigin、軸（X/Y/Z）・向き、ABSENTとAIRの違い、消去後boundsのテストが通る。

### P2 — 対象バージョンの厳密な互換検査

- [ ] `target=minecraft-java-1.20.1-forge` の設定を、**データ形式**（Sponge v2）、**データバージョン**（3465）、**使用ブロックレジストリ／stateの定義**で分離管理。
- [ ] 対象1.20.1の正式なBlockState一覧と合法なproperty/valueを照合する（ブロック名だけでは足りない）。MODブロックは必要なMOD ID・版も指定し、存在確認できない場合はUNKNOWNとして拒否。
- [ ] 1.21で追加されたブロック、無効なstate、未登録MODブロックを**無断でairに置換しない**。失敗箇所の座標・原ID・理由・代替候補をまとめて返す。
- [ ] 代替マッピングは**明示的なオプション**。元→置換先・位置・個数を報告し、同じ定義なら同じ結果になることを確認。

**Gate P2**：全ブロックが可搬ならlossless／非対応があればfail-closedまたは承認済み置換のみ。WorldEdit Reader側の`unknown→air`が発動しない入力になるまで出力を認めない。

### P3 — Sponge v2ライタと読み戻し検証

- [ ] `Schematic`を**v2のルート**としてGZip NBT化し、`Version=2`・`DataVersion=3465`・Width/Height/Length・Offset・PaletteMax・Palette・BlockData（VarInt）等を仕様どおり配置。v3のネストした`Schematic.Blocks`を流用しない。
- [ ] 順序 `x + z*width + y*width*length`、NBT Shortの寸法、PaletteMax、VarIntの上限とエントリ数、負のOffset、0/非原点のoriginをテストする。
- [ ] デフォルトは**非破壊的なairスキップ貼り付けを推奨**（WorldEdit`//paste -a`相当）。`full_region_replace`（空気も使って領域を消す）は別途明確な利用者選択を要する。v2単体では「明示airだけ貼る」ことを表せないため、その場合はsidecarマスク／別配置機構が必要であり、実装なしに可能とは言わない。
- [ ] ガードは配置ブロック数に加え、`width*height*length`と見込みメモリ・出力サイズに適用して**大容量確保前に失敗**させる。破損NBT、過大入力、余剰／途中で切れたVarInt、重複・不正paletteを拒否する。
- [ ] v2を**独立したリーダー**で再解析してIRとの内容・座標・状態・空気扱いを比較する。

**Gate P3**：v2形式解析が成功するだけでなく、全保存対象セルと位置の差分が0である。出力先で存在しないブロックを見落とさない。既存の`final.schem`を破壊しない。

### P4 — 1.20.1 Forge実機受入

- [ ] 正しいForge 1.20.1＋WorldEdit 7.2.15の**隔離ワールド**を用意し、先にバックアップ。
- [ ] **手動**で`.schem`を読み込み、貼り付け前のclipboard内の種類・配置・Offsetを確認する。
- [ ] 小さなfixtureを配置して、同一ブロック、階段／ドア／フェンス／ガラス／水等のstate、複数階、負座標、離れた配置、空気のスキップによる地形の保持を観測する。
- [ ] 無効IDや対象外ブロックで**危険なair置換がない**こと、想定外の既存ブロック破壊がないこと、ワールドの復元が可能なことを確認。失敗時には実測結果と原本を保全する。

**Gate P4**：`READABLE_BY_WORLDEDIT`、`PASTE_IN_TEST_WORLD`、`VISUALLY_CHECKED` は別々に認定する。Forge実機が手元に無ければ静的・ファイルレベルの受入だけ記録し、最後をPASSにしない。

### P5 — 使い勝手・保守と拡張

- [ ] `validate`／`convert`（名前は実装時確定）の1コマンド導線と、初めて使うAIが誤認しない短いCLIヘルプを追加する。オンライン建築APIの起動やワールド変更はデフォルトで起こさない。
- [ ] レポートに`source_commit`、`source_schem_sha256`、`target_profile`、`block_count`、`dimensions`、`warnings`、`substitutions`、`air_policy`、`validation_level`、`out_schem_sha256`を残す。秘密情報・ユーザーワールド全体をGitに含めない。
- [ ] 成功した1.20.1の検証契約を**他版向けTarget Profileを追加できる形**に整えるが、未検証版を対応済みにしない。

**Gate P5**：既存MOD-AI/Knowledge Core/LABが常時依存せず、Forge 1.20.1で再現可能な成果物とread-back記録が取得できる。

## 必須fixture（少数でも識別力のあるもの）

| ID | 入力 | 期待 |
|---|---|---|
| T01 | 石・樫材の直方体とガラス | 1.20.1で差分ゼロ |
| T02 | `oak_stairs[facing=east,half=top]`・ドア・フェンス | state値と向きが保持される |
| T03 | 負座標・非ゼロorigin・L字型 | 空間位置ずれなし／未配置領域を区別 |
| T04 | 明示airと未配置セルを含む建築 | スキップと全置換の差、意図不明は警告 |
| T05 | Minecraft 1.21のみに存在する素材（例：`trial_spawner`） | 代替未指定なら**拒否**。勝手にairにしない |
| T06 | 不正state・不正ID・未登録mod ID | **拒否**＋具体的な位置と理由 |
| T07 | 異常な寸法、overlong VarInt、破損NBT、bounds縮小 | 大容量確保前／不正解釈前に失敗 |
| T08 | 原本と変換結果の再読込 | 対応可能範囲で位置・種類・状態の同一性を検証 |

## 開発ルール・判断の自由度

- **既存の良さを壊さない**：mcbuildの設計・レンダリング・AIによる自由な改善を規制しない。目的は完成後の**移植レイヤー**だけ。
- **必要な道具だけ使う**：既に採用済みのPython環境とNBTライブラリを優先。過剰なMCP、複数エージェント、常駐サーバー、巨大な共通基盤を追加しない。
- **同等以上の実装を認める**：パス／型名／中間表現は設計上の提案。実装担当がより単純かつ損失・安全面で同等以上の方法を見つけたら採用し、理由とテストを残せばよい。
- **テストは観測範囲を正直に**：単体テスト／独立Reader／Forge実機／視覚品質の結果を混ぜない。検査完了を人間の好みに対する保証にしない。
- **公開範囲を維持**：MITのコードと第三者のMinecraft画像/ブロック状態アセットを混同しない。upstreamフルソース・JAR・ワールド・秘密情報はGitに入れない。
- **PR #115はDraftのまま**：mainへのマージ、ワールド編集、オンラインAPI課金は別の明示操作。完了と認定するのは各Gateの実測後のみ。

## 引継ぎチェック

着手時は[監査](AUDIT-2026-11-14.md) → この計画 → [建築ジャンルREADME](../README.md) → [既存mcbuild bridge](runner.py) → pinned upstreamを順に参照する。まずP0を確認してから、**P1〜P3の純粋な変換処理**を実装する。P4は実機が使用可能な段階まで`NOT_RUN`でよい。作業結果には実行したコマンド、検証対象commit、fixture、エラー、未確認点を添える。
