# AI部門 — 研究キュー（2026-10-11）

これは研究計画の候補であり、**AI実装の完了一覧ではない**。Minecraft部門の既存キューは変更しない。

| 順位 | テーマ | 状態 | 次の作業 |
| --- | --- | --- | --- |
| A0 | AI部門の入口・手順・分野分類 | DOCUMENTATION_CREATED | リンク・差分・役割境界の確認 |
| A1 | [階層型指揮・群体知能](multi-agent/HIERARCHICAL-COMMAND-AI-v0.md) | DESIGN_CANDIDATE | 先行実装の調査と最小シミュレーション |
| A2 | FSM / Behavior Tree / GOAP / HTN / Utility比較 | NOT_ANALYZED | 原典・実コード・失敗/修正例を比較 |
| A3 | 個体/群体の共有記憶、強化学習と進化 | CASE_STUDY_LINKED | SRP原作の学習と独立の学習手法を比較 |
| A4 | LLM・複数AI・ツール実行 | NOT_ANALYZED | API方式と非API方式の費用、権限、検証 |
| A5 | 軽量なローカルAI | NOT_ANALYZED | CPU/GPU、VRAM、レイテンシ、測定環境を固定 |
| A6 | 評価・可視化の共通テスト | DOCUMENTATION_ONLY | 指標・アブレーション・失敗記録を設計 |

最初の評価候補は「独立Mob」「階層型指揮」「階層型指揮＋共有記憶」の3群比較。環境/乱数/戦力をそろえ、勝敗だけでなく目標到達率、指示遅延、停滞、CPU時間、メモリ消費を測る。**いずれも未実施。**

既存の根拠となるケースは [SRP原作の戦闘・共有適応Bytecode解析](../minecraft/mods/scape-and-run-parasites/COMBAT-AI-BYTECODE-2026-10-11.md)。こちらは1.12.2での静的証拠であって、群体指揮AIの完成品ではない。


### 継続解析：Protoの学習帰属・群体運用の静的監査

[Sporeの複数Proto・戦果帰属・資源/TPS面の原作Bytecode監査](../minecraft/mods/fungal-infection-spore/HIVEMIND-LEARNING-LIFECYCLE-AUDIT-2026-10-11.md) を追加。特に「実際に選択した兵士を正しく報酬評価できるか」と「指揮官が増えた際の計算・チャンク固定コスト」をA1の最初の受け入れテスト候補とする。ゲーム内測定はNOT_RUN。

## Minecraft群体AI MOD候補（2026-10-11）

[調査対象MODの発掘一覧と固定Git SHA/JAR入手候補](multi-agent/MINECRAFT-MOD-SCOUT-2026-10-11.md) を参照。これは **発見・初期ソース確認** であり、A1〜A6の実装や性能検証を完了したものではない。既存のMinecraft解析キューを置き換えない。


### 実JARの一次解析から進んだ項目（2026-10-11）

[Spore Proto Hivemindの4×4指揮・軽量学習、部隊連携の比較](multi-agent/PROTO-HIVEMIND-CASE-STUDY-2026-10-11.md) を新規登録。原作[JAR解析と証拠](../minecraft/mods/fungal-infection-spore/README.md)はMinecraft部門が所有。A1/A3の設計材料が増えたが、シミュレーション・実測はNOT_RUN。


### 2026-10-11 独立の実行済み数理シミュレーション

[Spore Proto 4×4学習式の合成ベンチマーク](evaluation/experiments/spore-proto-policy-2026-10-11/README.md) を追加。256シード×1,200判断で学習なし / 原作算術 / 特徴ごとの独立更新案 / 士気補正を比較。成功は SYNTHETIC のみ、Minecraft 1.20.1 ForgeランタイムはNOT_RUN。[別の原作Bytecodeに基づくディメンション境界リスク](../minecraft/mods/fungal-infection-spore/CROSS-DIMENSION-AI-BOUNDARY-AUDIT-2026-10-11.md)も発見した。

### Signal指揮と軽量Unitの新しい研究成果（2026-10-11）

[Spore原作のSignal→Proto→Calamity/WombとGoal周期の原本Bytecode解析](../minecraft/mods/fungal-infection-spore/GROUP-COMMAND-SIGNAL-BYTECODE-2026-10-11.md)、[AI部門Signalルーティングの独立設計](multi-agent/SIGNAL-ROUTING-CASE-STUDY-2026-10-11.md)、[確率分岐の再現コードと結果](evaluation/experiments/spore-signal-routing-2026-10-11/README.md) を追加。19項目のBytecode構造チェックがPASS。実機G09〜G13はNOT_RUN。

### G09〜G13のデータ証拠ゲート（2026-10-11）

Spore 2.2.0jの[指揮・Signal・Goal受け入れテストのrunログ検証器](../minecraft/mods/fungal-infection-spore/RUN-EVIDENCE-GATE-2026-10-11.md) を実装し、合成データの15/15単体テストとGitHub Actionsを通した。別run・world・artifact・途中欠損を受け入れず、偽造可能なJSONLにruntime PASSを付けない。**Forge observer・GameTest稼働・TPS測定は未実施**。原作者の[mods.toml依存設定不整合](../minecraft/mods/fungal-infection-spore/METADATA-AUDIT-2026-10-11.md)も別facetへ記録した。

### Spore Forgeの読み取り専用観測器（2026-10-11）

[observer README](../minecraft/mods/fungal-infection-spore/observer/README.md) と [ソース](../minecraft/mods/fungal-infection-spore/observer/src/main/java/org/kneekura/sporeobserver/SporeEvents.java)をTECH-HUB Minecraft研究領域に追加。原作を改変せずSpore 2.2.0j SHAを起動時検査、Proto/Signal/Infectedと未校正ServerTickの状態を記録する。ForgeGradleの[ソースビルドCI](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/38082379417)はPASS。Forgeを用いたSpore原作実ゲーム観測は依然NOT_RUN。JSONLだけで成功を断定せずLABの認証とcleanupを待つ。


### Observerの実装とスコープ付きCI根拠（2026-10-11）

[Spore研究用の読み取り専用Forge Observer](../minecraft/mods/fungal-infection-spore/observer/README.md) に、G13の未校正server tick時間・Proto/Signal/Infected・loaded chunk数、G11の公開重み/波数/damage snapshotを実装。自作Jarは[Actions #38082851629](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/38082851629) で **ForgeGradle 1.20.1 packaged source build成功**、[不変buildレシート](../minecraft/mods/fungal-infection-spore/verification/OBSERVER-FORGE-CI-2026-10-11.json)あり。原作Sporeと実LAB worldは起動していないのでruntime/GameTest/TPSはNOT_RUN。G09〜G12の実装内メソッドの正確な命令タイミングはまだ未観測。
