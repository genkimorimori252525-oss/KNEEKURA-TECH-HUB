# Fungal Infection: Spore — Minecraft AI technology analysis

**Target:** Fungal Infection: Spore 2.2.0j / Minecraft 1.20.1 Forge, Harbinger  
**Research snapshot:** 2026-10-11  
**Status:** IN_PROGRESS — important Proto/Womb/Mound/Group/Volley bytecode methods MAPPED; 1,350 classes total, selected 183 classes dumped; runtime NOT_RUN; not whole-target COMPLETE.

## Read here

- [Hivemind / group AI / ecology / volley technical findings](HIVEMIND-AI-BYTECODE-2026-10-11.md) — exact selected original class-method evidence, 4×4 policy, weight updates, feedback call path, target sharing, resource circulation, performance hypotheses, negative claims.
- [JAR evidence and verification limits](ARTIFACT-RECEIPT-2026-10-11.json) — exact uploaded artifact byte size and SHA-256, mods.toml metadata, source/release/version boundaries.
- [AI department — hierarchical command plan](../../../ai/multi-agent/HIERARCHICAL-COMMAND-AI-v0.md) — independent KNEEKURA design proposal, not proven to exist in original Spore.
- [Original MOD shortlist](../../../ai/multi-agent/MINECRAFT-MOD-SCOUT-2026-10-11.md) — historical reconnaissance performed before JAR acquisition.


## 最新の調査追加（2026-10-11）

- [Hivemind学習・複数Proto・リソース・負荷の追加Bytecode監査](HIVEMIND-LEARNING-LIFECYCLE-AUDIT-2026-10-11.md) — 選定個体と報酬帰属の不整合候補、moraleBoostのclamp例外、全ゼロ入力時の決定、活動中Protoのregistry、負Biomass、チケット再要求。
- [追加監査の原本内11クラスSHA-256と限定的なFinding](BYTECODE-CONTINUATION-RECEIPT-2026-10-11.json) — 不変エビデンスロケータ、実機NOT_RUN。

個体の評価の不整合は**Bytecodeに基づくBUG_CANDIDATE**であり、実際の戦果への影響と修正前後の確認は未実施。過去の研究成果を「完全解析」へ昇格させるものではない。

## Key findings

1. The original Proto Hivemind really uses a 4-input / 4-output linear scoring system. It updates the selected action row by +0.05 on attributed positive damage feedback and -0.10 on attributed negative damage feedback, with bounds [-1,1]. It persists its own weights to NBT. **Not proof of deep neural learning or a global learned model shared among all hiveminds.**
2. The surrounding organisms split work: Proto for conditional summon/target selection, Womb for gathering and assimilating infected Mob resources, Mound for expanding infestation, HiveTumor for producing Proto, and upper-order AIs for propagating targets/search positions.
3. ScatterShotRangedGoal implements a variable number of same-update ranged calls. Projectile spreading angles and specific resulting in-game bullet patterns are yet to be verified.
4. Experimental ExpPathFinder delegates to the vanilla PathFinder and wraps Path. Its path name does not by itself establish neural-pathfinding machinery.

## Provenance

Original JAR: spore_1.20.1_2.2.0j.jar, SHA-256 **d20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489**, size **116,439,461 bytes**. Author/loader and license from mods.toml (All Rights Reserved). Binary equivalence to downloaded official release is not established; raw JAR/decompiled source/assets/sounds are deliberately not committed to public TECH-HUB.

- ANCHOR: MC 1.20.1 Forge, original uploaded JAR.
- FRONTIER: public MC 1.21.1 NeoForge release is separately known; binary NOT_ACQUIRED/NOT_REVIEWED.
- EVIDENCE: targeted static reads; game execution, multiplayer, TPS, visual performance and server correctness are **NOT_RUN**.

All further MOD research follows [Minecraft analysis workflow](../../ANALYSIS-WORKFLOW.md) and [specification](../../ANALYSIS-SPEC-v1.md) and keeps previous historical findings intact.

## 2026-10-11: Policy simulation and cross-dimension audit

- [Synthetic Proto policy experiment](../../../ai/evaluation/experiments/spore-proto-policy-2026-10-11/README.md) — 256 seeded synthetic trials, NOT Minecraft. Source and output committed separately from the original JAR.
- [Cross-dimension Proto/chunk-ticket audit](CROSS-DIMENSION-AI-BOUNDARY-AUDIT-2026-10-11.md) — original bytecode shows a global Proto registration count and world-load chunk-ticket dimension-scoping risk, runtime NOT_RUN.


**新しいエビデンス:** [複数ディメンションの条件とChunkTicket再生の9クラスSHA記録](BYTECODE-CROSS-DIMENSION-RECEIPT-2026-10-11.json)。従来の活動中Proto数はstaticな全体件数であり、Wikiの「ディメンション内3体」と一致しない可能性がある。原作Minecraft実機での再現はNOT_RUN。



## 新しい再検証ゲートとGameTest計画（2026-10-11）

- [固定JARのBytecode契約13件を機械検査する方法と結果](BYTECODE-CONTRACT-GATE-2026-10-11.md)（9 class hashes / 13 static contracts PASS、Minecraft実機NOT_RUN）。
- [実際に動作する独立Python検査器](tools/verify_spore_bytecode.py) と [実際のJSON結果](verification/bytecode-gate-2026-10-11.json)。別のJARを投入するとBLOCKED_HASH_MISMATCH。
- [隔離Forge1.20.1 GameTest / LABの8シナリオ受け入れ契約](LAB-GAMETEST-ACCEPTANCE-2026-10-11.md)。設計のみでGameTestのJava実装/ゲーム起動はNOT_RUN。

新たな着目点：Forge LivingDamageEventでの**ダメージ発生回数**に基づく報酬は、個体の総与ダメージや指揮作戦の勝利と同義ではない。初期4候補の「番号不一致75%」はindexの組合せ確率であり、Mob種の違いとは限らない。

## 2026-10-11 — Signal指揮・群体Goalの追加回収

- [原作Spore Vigil→Proto→Calamity/WombのSignalとUnit追従・探索のBytecode解析](GROUP-COMMAND-SIGNAL-BYTECODE-2026-10-11.md) — 39クラス調査のうち選定11クラス・19構造契約固定。実機NOT_RUN。
- [19契約の再現可能な自作Bytecode検査器](tools/verify_spore_group_ai.py) と [実JARの静的検査結果JSON](verification/GROUP-COMMAND-STATIC-RESULT-2026-10-11.json) — 11/11クラスハッシュ、19/19静的条件PASS。異なるJARは拒否。
- [AI部門のSignal派遣分岐の合成確率比較](../../../ai/evaluation/experiments/spore-signal-routing-2026-10-11/README.md) — 条件を固定した30,000回×6シナリオの数理テスト。Minecraftの勝率ではない。
- [将軍AIの独立Signal Router設計](../../../ai/multi-agent/SIGNAL-ROUTING-CASE-STUDY-2026-10-11.md) — 原作Bytecodeからの知見と別製品への設計提案を分離。

**新たな限定所見:** Vigilの退場時TRIGGER>=3のSignalは、当該メソッドでは列挙順の最初のProtoへ送られる。ProtoのCalamity派遣は待機個体ごとに50%抽選し、不成立ならWomb生成を試みる。Vigilの援軍試行前の加点と退場時の減点は、作戦の勝敗を直接評価していない。ゲーム内の再現・TPSはNOT_RUN。

### 解析精度の訂正（2026-10-11）

[Signal/Group AI研究](GROUP-COMMAND-SIGNAL-BYTECODE-2026-10-11.md) の初版にあった「SearchAreaGoalが目標まで3ブロック以内でSearchPos解除」は誤読。実際は **BlockPos.closerToCenterThan(Position,9.0)**、つまり半径9ブロック未満で解除。**FollowOthersGoalの距離二乗9＝半径3ブロック**とは異なる。対応する19契約の検査器とJSON結果を更新し、再実行して静的PASS 19/19を再確認した。旧コミットは歴史的証拠として残す。

## 2026-10-11 実行可能な検証への進捗（G09〜G13用ゲート）

- [元JAR mods.tomlに残ったexamplemod依存と、1.20.1を含まないバージョン範囲の直接監査](METADATA-AUDIT-2026-10-11.md)。TOMLを元JARからparseして直接確認。実Forge起動の成否はUNKNOWN。
- [G09〜G13の別run/別world/別原本のログを拒否する観測結果検証器](RUN-EVIDENCE-GATE-2026-10-11.md)。[実装](tools/evaluate_spore_trace.py)、[15の単体テスト](tests/test_gates.py)、[原本メタ検査コード](tools/audit_spore_metadata.py)。
- [元JARのメタデータ監査JSON](verification/mods_toml_audit_result.json)と[G09合成ログの検査結果](verification/g09.synthetic.review.json)を保存。G09実ゲーム観測ではない。
- [GitHub Actionsで15/15単体試験PASS](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/38081259925)。このCIは合成fixture + Python構文のみを検証し、Spore本体を取得・起動しない。

**進捗を厳密に区別:** G09〜G13の**ログ判定器はIMPLEMENTED/TESTED_SYNTHETIC**。G09〜G13のForge観測器・GameTest Java・実機測定は**NOT_IMPLEMENTED/NOT_RUN**。前回の静的Bytecode契約19/19 PASSとは別の試験。

## 2026-10-11 — Forge観測MODのソース実装とコンパイル

[observer/README.md](observer/README.md) — 実行権限が固定されたLABセッション内でだけ有効になる、Forge 1.20.1研究用の読み取り専用補助MODを新設した。Spore原作を変更せず、既存session.json・world・run ID・world seedと、ロード済み原作JARのSHA-256を検査。ログは別のSpore JSONL companionとして出力する。

[GitHub Actions 38082379417](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/38082379417) でForgeGradle 6＋Minecraft 1.20.1ソースコンパイル、Java17のportable JSONLテスト、Pythonゲート15件が成功。後続には[G13の600件合成ログのJava→Python結合テスト](observer/tests/G13SyntheticProducer.java)も追加した。

**G13に直接観測できる範囲:** ロード中のProto・active Signal・Infected件数、ServerTick START〜END未校正時間、読み込み済みチャンク、バニラの強制ロードチャンク。Forge ticketの全件・正式MSPT・TPS・ゲームの勝率は未測定。

**G09〜G12に残る範囲:** Signal呼出の実際の候補列挙、Calamity再配置・Womb試行メソッド、Vigilの報酬呼出、Goal tickそのものは受動イベントでは直接取れない。現状はsnapshotイベントのみでGameTest成功とはしない。LAB登録済みworld・Spore実ロード・観測・cleanupの認証はまだNOT_RUN。


## 最新の確定ビルド証拠（2026-10-11）

[原作Sporeではない、TECH-HUB自作ObserverのForgeGradleビルド検証レシート](verification/OBSERVER-FORGE-CI-2026-10-11.json) を作成。[GitHub Actions #38082851629](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/38082851629) で、**Forge 1.20.1専用Observer JARのビルド、packaged class・META-INF/mods.toml検査、原作Spore class混入防止、Java17とPython15件、Java→Python合成G13の3ジョブがSUCCESS**。このジョブには原作Spore JAR、実Minecraft world、GameTest実行は含まれない。

その後、[Observerソース](observer/src/main/java/org/kneekura/sporeobserver/SporeEvents.java)へG11用の Proto公開weights[16] / Vigil wave_size / Forge LivingDamageEventの**スナップショット観測**を追加。メソッドaward/punishの実呼出と強く結び付いた証拠ではないため、G11は依然INCONCLUSIVE。観測器の[最新構成](observer/README.md)は原作JARとLAB sessionの一致を要求する。
