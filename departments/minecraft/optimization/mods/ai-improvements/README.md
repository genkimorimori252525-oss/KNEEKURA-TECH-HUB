# AI Improvements: Performance Tuning — 軽量化技術研究

- **研究保存先**: `departments/minecraft/optimization/mods/ai-improvements/`
- **登録日**: 2026-10-11
- **対象**: [BuiltBrokenModding / AI-Improvements](https://github.com/BuiltBrokenModding/AI-Improvements)
- **分類**: `TICK_SIMULATION`, `ENTITY_BLOCKENTITY`, `CACHE_DATA_STRUCTURE`
- **機構の証拠**: あり（限定した公開ソース、コミット/Issue）
- **性能の測定結果**: **PERFORMANCE_NOT_VERIFIED / NOT_RUN**
- **互換性と正しさの実機試験**: **NOT_RUN**

## SourceSnapshot / 1.20.1 Forgeへの適用境界

| Role | Native version and loader | Immutable source identity | What is established |
|---|---|---|---|
| **ANCHOR destination** | Minecraft **1.20.1 Forge 47**, Java 17 | source/release parity **UNESTABLISHED** | 明確な1.20.1向け実JARの比較・ビルド・性能確認は未実施 |
| **ANCHOR-adjacent source** | Minecraft **1.20 Forge 46.0.12**, mod 0.5.2 | [`89c89590d8160f332bd2740acd0a67c96f37f00d`](https://github.com/BuiltBrokenModding/AI-Improvements/tree/89c89590d8160f332bd2740acd0a67c96f37f00d) | `gradle.properties` と `mods.toml`、以下の静的技術調査 |
| **COMPARATIVE** | Minecraft 1.20.2 NeoForge | [`6568bc1343f81c19056b09fada82761fedcbd4d8`](https://github.com/BuiltBrokenModding/AI-Improvements/tree/6568bc1343f81c19056b09fada82761fedcbd4d8) | `1.20` ブランチの現在HEADは1.20.1 Forgeと別 |
| **FRONTIER** | Minecraft 26.3 NeoForge | [`a51cab76acf89099ea3c41393d858f9e061dbe4b`](https://github.com/BuiltBrokenModding/AI-Improvements/tree/a51cab76acf89099ea3c41393d858f9e061dbe4b) | source path inventoryのみ、全面的な差分解析は未実施 |

元の横断調査メモ: [NESM/旧Epic Siege比較時のAI Improvements研究](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/research/nesm-jar-and-ai-perf-2026-10-11/departments/minecraft/mods/ai-improvements/README.md)（[PR #110](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/pull/110)）。この軽量化レーンの文書が**性能面の分類・受入条件の正式な入口**。元の研究本文を複製しない。

## Source-confirmed mechanisms

1. **EntityJoinLevelEventでの選択的Goal除去** — `ModifierSystem` → `ModifierLevel` → `ModifierLayer` → `GenericRemove / FilteredRemove`。対象Mob/Goalを設定で限定できる。削除はGoalを先に収集し、列挙後に適用する。
2. **視線角計算の置換** — `FixedLookControl` は通常の`LookControl`を、`FastTrig` の**256×256=65,536個のfloat atan2テーブル**を使う実装へ置換する。状態`wantedX/Y/Z`・回転速度・クールダウンを引き継ぐ。元から独自`LookControl`を持つMobには置換しない。
3. **フィルタ順序をヒット頻度に合わせる処理** — `FilterLayer`/ `ModifierLayer` の成功回数と局所移動。繰り返し生成されるMobでの探索候補だが、順序変更の意味的安全性は未測定。設定`enableCallBubbling`が宣言されていても、選択したソース断面でこの値の参照は確認できていない（機能の有効性は未確定）。
4. **イベント重複呼び出しの削除** — Issue #31に対応する修正コミットでは不要な`LivingSpawnEvent`のサブスクライブを取り除き、`EntityJoinLevelEvent`を残した。インストール時処理の重複実行を減らす設計。

これは**一般的なA*経路探索の高速化**でも、一定割合のTPS改善を保証する方式でもない。既定設定では主なlook/idle Goal削除はfalseで、通常LookControlの置換はtrue。

## 何を省くか / 何を維持するか

Goal除去の最大の利点は対象の不要な処理そのものを停止できる点。その代わり首振り、索敵、回避、繁殖、移動、水泳などゲームプレイが変化する。目的が演出や敵行動のあるMODで一律に無効化するのは不適切。

FastTrigは反復`atan2`計算を表参照にする候補で、`float`約256 KiBの基礎配列を確保する（その他の実装メモリは含まない）。精度とCPU速度が元と等価だという証拠ではない。特殊な多砲塔ボスなどの照準・回転演出は別途検証が必要。

## 元資料 / ライセンス

- [ConfigMain.java](https://github.com/BuiltBrokenModding/AI-Improvements/blob/89c89590d8160f332bd2740acd0a67c96f37f00d/src/main/java/com/builtbroken/ai/improvements/ConfigMain.java)
- [ModifierSystem.java](https://github.com/BuiltBrokenModding/AI-Improvements/blob/89c89590d8160f332bd2740acd0a67c96f37f00d/src/main/java/com/builtbroken/ai/improvements/modifier/ModifierSystem.java)
- [ModifierLayer.java](https://github.com/BuiltBrokenModding/AI-Improvements/blob/89c89590d8160f332bd2740acd0a67c96f37f00d/src/main/java/com/builtbroken/ai/improvements/modifier/editor/ModifierLayer.java)
- [FilterLayer.java](https://github.com/BuiltBrokenModding/AI-Improvements/blob/89c89590d8160f332bd2740acd0a67c96f37f00d/src/main/java/com/builtbroken/ai/improvements/modifier/filters/FilterLayer.java)
- [FixedLookControl.java](https://github.com/BuiltBrokenModding/AI-Improvements/blob/89c89590d8160f332bd2740acd0a67c96f37f00d/src/main/java/com/builtbroken/ai/improvements/FixedLookControl.java)
- [FastTrig.java](https://github.com/BuiltBrokenModding/AI-Improvements/blob/89c89590d8160f332bd2740acd0a67c96f37f00d/src/main/java/com/builtbroken/ai/improvements/FastTrig.java)
- [History: Issue #31](https://github.com/BuiltBrokenModding/AI-Improvements/issues/31) / [repair diff](https://github.com/BuiltBrokenModding/AI-Improvements/commit/2e95e6e62edeea7cfd86a06865d5cebaf190ab39)
- 旧時点のソース[LICENSE](https://github.com/BuiltBrokenModding/AI-Improvements/blob/89c89590d8160f332bd2740acd0a67c96f37f00d/LICENSE) は**MIT、適用対象はコードのみ**と記載。配布ページの表記とは区別し、原作のJAR・画像・その他資産を移さない。

## 添付技術記録

- [OPTIMIZATIONS.md](OPTIMIZATIONS.md) — 軽量化のguard、fast path、fallback、意味的リスク
- [BENCHMARKS.md](BENCHMARKS.md) — A/B受入仕様、現状NOT_RUN
- [SOURCE-RECEIPT.json](SOURCE-RECEIPT.json) — 証拠境界と未実施事項
- [FAILURE-REPAIR-HISTORY.md](FAILURE-REPAIR-HISTORY.md) — 選択した修正履歴
