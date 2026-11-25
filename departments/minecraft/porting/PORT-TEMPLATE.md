# AI向け移植作業テンプレート
対象MODの作業ノートへ必要な節だけコピー。文書の肥大化や全チェック強制を目的にしない。
## 入力
- 元 repository/SHA/JAR hash（該当する場合）、Minecraft/loader/Java/mappings/build
- 先 Minecraft/loader/Java/mappings/build/依存MODの対応版
- 変更許可、ライセンス、配布条件、原本保持、別worktree
- 元の機能・元環境の再現性（未確認は明記）
## 方針
- 保持すべき挙動・ID・データ・外部連携：
- loader差 / vanilla版差 / dependency差：
- 参照規則ID・原典・適用条件：
- 対象外・不可能・未解決：
- 保存互換要求（旧worldの更新/逆更新は別検証。既存worldで試さない）：
## 実装
独立ロジックを維持し接続部を修正。公式MDKは参考、既存buildを不要に再構築しない。対象APIの実ソース・signature・mappingを確認。変更箇所を小単位にして、コンパイル失敗と修正を記録。機能削除や例外握り潰しを成功としない。自動変換ツール、常駐サービス、追加フレームワークは不要。
## 受け入れ
| 項目 | 元 | 先 | 証拠/結果 |
|---|---|---|---|
| ビルド・JAR metadata | | | NOT_RUN |
| client / dedicated server 起動 | | | NOT_RUN |
| 主要機能・GameTest | | | NOT_RUN |
| 保存/再読込・データ移行 | | | NOT_RUN |
| networking / side | | | NOT_RUN |
| Mixin・描画・依存互換 | | | NOT_RUN |
| 性能（対象に必要な場合） | | | NOT_RUN |
N/Aには理由。実行許可、固定source/環境、使い捨てworld、LABの現行契約を守る。配布JARはソースプロジェクトとは別検証。PASS/FAIL/NOT_RUN/UNKNOWNを区別する。
## 知識還元
再利用可能な差分だけRECIPESへ。before/after・方向・guard・反例・根拠・検証版を添える。機械的に逆規則を作らない。製品固有コードは製品側、公開リポへの私的データ/第三者素材の転載なし。既存Hubの人間レビューを尊重。
