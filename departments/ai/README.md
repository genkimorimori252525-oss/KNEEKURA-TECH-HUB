# AI Technology Department — KNEEKURA TECH HUB

**設立日:** 2026-10-11  
**状態:** FOUNDATION / DOCUMENTATION ONLY（研究部門を登録した段階。AIモデル、実行基盤、学習・実機検証は未実装）

## 使命

Minecraftなど個別製品から独立して、人工知能の**意思決定・探索・計画・群体協調・学習・記憶・評価・軽量化**を研究する。ゲームAIとLLM/機械学習のどちらも対象とするが、異なる手法を一つの汎用AIテンプレートへ無理に統合しない。

## 研究カテゴリ

| 分野 | 入口 | 主題 |
| --- | --- | --- |
| 基礎AI | [foundations](foundations/README.md) | FSM、Behavior Tree、GOAP、HTN、Utility、探索・経路計画 |
| 群体・マルチエージェント | [multi-agent](multi-agent/README.md) | 将軍・指揮官・兵士、部隊編成、役割分担、共有記憶 |
| 学習・進化 | [learning](learning/README.md) | 適応ルール、強化学習、進化アルゴリズム、記憶 |
| LLM・自律エージェント | [llm-agents](llm-agents/README.md) | 言語モデル、ツール実行、複数AIの協働、ローカル推論 |
| 評価・最適化 | [evaluation](evaluation/README.md) | 再現可能な比較、性能・資源測定、失敗分析 |

- [AI部門の調査手順](RESEARCH-WORKFLOW.md)
- [研究キュー](RESEARCH-QUEUE.md)
- **最初の設計課題:** [階層型指揮・群体知能 v0](multi-agent/HIERARCHICAL-COMMAND-AI-v0.md)

## 他部門との境界

- [Minecraft技術部門](../minecraft/README.md)は具体的なMob、MOD、JAR/Bytecode、Forge API、実機検証を担当する。AI部門は製品から独立した汎用の知能構造と評価方法を担当する。
- [Minecraft MOD-AI](../minecraft/mod-ai/README.md)は「AIを使ってMODを作るための既存ツール基盤」であり、この「AIそのものを研究する部門」とは別。
- [Scape and Run: Parasites 1.9.21のJAR研究](../minecraft/mods/scape-and-run-parasites/README.md)は個体学習・群体継承・侵略AIのケーススタディとして参照する。そこから今回の将軍AIの存在を断定しない。

## 共通の証拠管理を再利用

[TECH-HUB憲章](../../governance/CONSTITUTION.md) と [Knowledge Core](../../docs/architecture/BASELINE-v1.md) に従う。コミュニティ、Reddit、解説サイトは発見や反例の入口とし、技術的な結論は固定した論文/原典・ソース・Issue/PR・実験に基づける。

研究メモは**候補**。根拠のない推測を事実へ昇格させず、AIによる自動VALIDATEDを行わない。新しいDB、無制限のクローラ、全分野共通ランタイムを作ったことにはしない。

**候補調査:** [Minecraftの指揮・群体・学習・経路探索MOD比較（2026-10-11）](multi-agent/MINECRAFT-MOD-SCOUT-2026-10-11.md)。公開ソースとJAR調査候補を区別した発掘段階。


**原作JARからの新規研究:** [Spore Protoの軽量学習・指揮機構](multi-agent/PROTO-HIVEMIND-CASE-STUDY-2026-10-11.md) を研究候補に登録。実JARのBytecode根拠は [Minecraft部門 Spore解析](../minecraft/mods/fungal-infection-spore/README.md) に固定している。2026-10-11時点で実機性能の検証は未実施。

