# AI評価・最適化

**状態:** 評価指標の入口のみ。数値ベンチマーク・実測は NOT_RUN。

| 対象 | 検証すべき指標 | 注意 |
| --- | --- | --- |
| 個体ゲームAI | 到達率、攻撃成功、停滞、CPU時間 | 強い敵 ≠ 賢いAI |
| 群体AI | 目標達成率、部隊損失、役割分担、命令遅延 | 集団での改善を単体性能から分離 |
| 学習 | 未見条件での変化、忘却、サンプル効率 | 設定変更 ≠ 学習 |
| LLM・エージェント | 結果の検証、費用、無許可実行、反復成功率 | 流暢な文章 ≠ 正確性 |
| 実行資源 | サーバーtick、CPU、メモリ、GPU/VRAM、I/O | 静的解析 ≠ 性能実測 |

同一シナリオ・乱数シード・戦力条件と複数試行でベースライン比較を行う。成功例だけでなく反例や停止理由も残す。Minecraftに適用する際は実際のGameTest/LAB結果が必要で、この文書は許可やPASSを意味しない。

最初の評価対象：[階層型指揮・群体知能](../multi-agent/HIERARCHICAL-COMMAND-AI-v0.md)  
[共通調査手順](../RESEARCH-WORKFLOW.md)

## 実行された小規模な研究実験

- [Spore Protoの16重み算術モデル](experiments/spore-proto-policy-2026-10-11/README.md) — 部隊選択方式を独立した合成課題で比較、Minecraft実機ではない。
- [SporeのSignal→Calamity/Womb選択の確率分岐](experiments/spore-signal-routing-2026-10-11/README.md) — 30,000判断×6、シード固定。実際のゲームでの派遣成功・負荷値はNOT_RUN。

両者をAIの学習済み実ゲーム性能の証拠として扱わない。原作のバイトコードはMinecraft部門が別トラックで保有する。

### Minecraft実機向けの証拠収集契約（実機はNOT_RUN）

[Spore G09〜G13 observation validation gate](../../minecraft/mods/fungal-infection-spore/RUN-EVIDENCE-GATE-2026-10-11.md) はrun/scenario/artifact/worldを照合し、記録が不足する場合はINCONCLUSIVEのままにする。研究用観測器の受け入れ検証であり、正規LAB session/owner/cleanupや実ゲーム結果を代替しない。Python 3.13の合成テスト15件と[CI](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/38081259925)は成功したがForge runtimeは未実行。

### Spore G12 GoalSelector登録競合候補の検証

[原作JARの登録表とread-only GoalSelector snapshotの整合性を検証する方法](../../minecraft/mods/fungal-infection-spore/GOAL-SNAPSHOT-EVALUATION-2026-10-11.md)と[所有するPython判定器](../../minecraft/mods/fungal-infection-spore/tools/analyze_spore_goal_snapshots.py)を追加。G12 Java合成ログではpriority4のMOVE共有候補6組を数え、runtime_pass=falseを保証。**原作Spore実機、GameTest、Goal中断や性能の確認ではない**。
