# Minecraft AI MOD — Source/JAR 候補調査 (2026-10-11)

**状態:** DISCOVERY / SELECTED-SOURCE-READ / 未解析全体 / NOT_RUN。特定のMODを「完全解析」「学習AI搭載確定」「1.20.1で統合動作確認済み」として扱わない。

調査入口：
- [Minecraft ANALYSIS-WORKFLOW.md](../../minecraft/ANALYSIS-WORKFLOW.md)
- [Minecraft ANALYSIS-SPEC-v1.md](../../minecraft/ANALYSIS-SPEC-v1.md)
- [AI部門 RESEARCH-WORKFLOW.md](../RESEARCH-WORKFLOW.md)
- [階層型指揮・群体知能 v0](HIERARCHICAL-COMMAND-AI-v0.md)
- [既存のScape and Run: Parasitesの実JAR解析](../../minecraft/mods/scape-and-run-parasites/README.md)

**目的:** 研究分野ごとに公開ソースの候補を発掘し、将軍→部隊→兵士の階層化、仕事の委譲、地域・世界レベルの勢力、行動と適応、経路探索、地形復元の技術源を見つける。原典・作者文書・コミュニティ・選択した実Javaコードを混同しない。

## 公開ソースを確認した研究候補

GitHubの下記SHAは **2026-10-11 時点の実際のリモートブランチ先端**。作者の配布JARとのバイト一致は別途検証が必要。ソースの存在は解析完了ではない。

| 優先 | 名称 / 主な関心 | Minecraftトラック | ソースと固定したcommit | 初回の実コード証拠 / 状態 |
| ---: | --- | --- | --- | --- |
| 1 | **Sculk Horde** / 中枢AI・感染・群れの増援 | 1.20.1 Forge | [TeamPeril/Sculk-Horde 1.20@c954020](https://github.com/TeamPeril/Sculk-Horde/tree/c9540207cfbc6cd4a42ba14f5a09b7f8b58b41fd) | [Gravemind.java](https://github.com/TeamPeril/Sculk-Horde/blob/c9540207cfbc6cd4a42ba14f5a09b7f8b58b41fd/src/main/java/com/github/sculkhorde/systems/gravemind_system/Gravemind.java): 3状態進化、ReinforcementRequestでCombat/Infector選別・個体数制限。**コメントは現在「増援制御が主、Raid/Defense統括はFuture plans」**。 marketing の「全軍を賢く指揮」は未証明。 |
| 2 | **Recruits** / 部隊命令・隊形・司令官・分隊 | 1.20.1 Forge | [talhanation/recruits main@cff03e0](https://github.com/talhanation/recruits/tree/cff03e085d65653406a8b6ddcdd0ebff615c3e48) | [RecruitCommanderUtil.java](https://github.com/talhanation/recruits/blob/cff03e085d65653406a8b6ddcdd0ebff615c3e48/src/main/java/com/talhanation/recruits/util/RecruitCommanderUtil.java): Follow/Hold/Move/Shield/Formation/Upkeep命令を各兵士の状態へ反映。[CommanderEntity.java](https://github.com/talhanation/recruits/blob/cff03e085d65653406a8b6ddcdd0ebff615c3e48/src/main/java/com/talhanation/recruits/entities/CommanderEntity.java) は指揮官個体とPatrolLeaderAttackControllerを持つ。**1.15.2配布JARと同じコードか不明**; Gradleのmod_versionは1.10.7と記載。 |
| 3 | **MineColonies** / 多職種NPC・役割分担・都市AI | 1.20.1 Forge | [ldtteam/minecolonies version/main@4eb1b87](https://github.com/ldtteam/minecolonies/tree/4eb1b870b7cb2339b79f231033df5bbef27b2646) | [AbstractEntityAIGuard.java](https://github.com/ldtteam/minecolonies/blob/4eb1b870b7cb2339b79f231033df5bbef27b2646/src/main/java/com/minecolonies/core/entity/ai/workers/guard/AbstractEntityAIGuard.java) のGuard AIs、警戒・巡回・脅威テーブル、コロニーのJob/RequestSystemへ繋がる責任分担。巨大なソース; whole targetが簡単という意味ではない。 |
| 4 | **Improved Mobs** / 対人経路・破壊・修復・乗騎 | 1.20.1 Forge & Fabric | [Flemmli97/ImprovedMobs 1.20.1@029b8c2](https://github.com/Flemmli97/ImprovedMobs/tree/029b8c20302a76bac1af9f5140e2abb6f73fea5c) | [BlockBreakGoal.java](https://github.com/Flemmli97/ImprovedMobs/blob/029b8c20302a76bac1af9f5140e2abb6f73fea5c/common/src/main/java/io/github/flemmli97/improvedmobs/ai/BlockBreakGoal.java), [BlockRestorationData.java](https://github.com/Flemmli97/ImprovedMobs/blob/029b8c20302a76bac1af9f5140e2abb6f73fea5c/common/src/main/java/io/github/flemmli97/improvedmobs/utils/BlockRestorationData.java) を直接確認。障害時ブロック破壊→SavedDataにBlockState・位置・破壊時間・ドロップ→指定時間後に**空気状態のみ復元**。BlockEntity NBTの完全原状復帰ではない。[FlyRidingGoal.java](https://github.com/Flemmli97/ImprovedMobs/blob/029b8c20302a76bac1af9f5140e2abb6f73fea5c/common/src/main/java/io/github/flemmli97/improvedmobs/ai/FlyRidingGoal.java) に地上経路と飛行経路の比較。 |
| 5 | **Ancient Warfare 2** / 古典的軍隊・命令・城攻め | 1.12.2 Forge; 1.20.1 は移植先案 | [P3pp3rF1y/AncientWarfare2 1.12.x@446b7db](https://github.com/P3pp3rF1y/AncientWarfare2/tree/446b7db2cc28f52dc1d9292db87ef1bdd7538ac6) | [NpcAIPlayerOwnedFollowCommand.java](https://github.com/P3pp3rF1y/AncientWarfare2/blob/446b7db2cc28f52dc1d9292db87ef1bdd7538ac6/src/main/java/net/shadowmage/ancientwarfare/npc/ai/owned/NpcAIPlayerOwnedFollowCommand.java) MOVE/GUARD/ATTACK_AREA、永続/単発命令。[NpcSiegeEngineer.java](https://github.com/P3pp3rF1y/AncientWarfare2/blob/446b7db2cc28f52dc1d9292db87ef1bdd7538ac6/src/main/java/net/shadowmage/ancientwarfare/npc/entity/vehicle/NpcSiegeEngineer.java) は兵器の探索・乗機・照準・発射タスク。**NpcAIPlayerOwnedCommander自体は近くの仲間にStrengthを付与するGoal**で、戦略的将軍AIそのものではない。 |
| 6 | **Alex's Mobs** / 群れ・追従・動物行動 | 1.20.1 Forge | [AlexModGuy/AlexsMobs 1.20@09755da](https://github.com/AlexModGuy/AlexsMobs/tree/09755dade2cfbdf14839e026d3af446f9d3ff843) | [ElephantAIFollowCaravan.java](https://github.com/AlexModGuy/AlexsMobs/blob/09755dade2cfbdf14839e026d3af446f9d3ff843/src/main/java/com/github/alexthe666/alexsmobs/entity/ai/ElephantAIFollowCaravan.java) は隊列の先頭選択・追従・離脱・距離で速度増を扱う。多数の動物専用Goalもある。動物全体の本当の生態系シミュレーション/進化学習を確認したわけではない。 |
| 7 | **Zombie Awareness** / 音・血液の匂い・群れの知覚 | 1.20.1 Forge | [Corosauce/ZombieAwareness 1.20@3b15771](https://github.com/Corosauce/ZombieAwareness/tree/3b15771a2cdf72dc61aeadf644e0ee16e18345a7) | [EnumSenseType.java](https://github.com/Corosauce/ZombieAwareness/blob/3b15771a2cdf72dc61aeadf644e0ee16e18345a7/src/main/java/com/corosus/zombieawareness/EnumSenseType.java) に `SCENT_BLOOD`, `SOUND`, `WAYPOINT` が明示。低コスト知覚の調査が有望。 |
| 8 | **The Hordes** / 侵略イベント・Mob集団のライフサイクル | 1.20.1 Forge | [SmileycorpMC/The-Hordes 1.20@8fd3f48](https://github.com/SmileycorpMC/The-Hordes/tree/8fd3f481ec3c501a3bb893ed3c23fb97e3a825db) | [HordeEventHandler.java](https://github.com/SmileycorpMC/The-Hordes/blob/8fd3f481ec3c501a3bb893ed3c23fb97e3a825db/src/main/java/net/smileycorp/hordes/hordeevent/HordeEventHandler.java): プレイヤー・日数・時刻から侵略開始、攻撃目標変更、despawn制御。**知能/学習エンジンというより波状襲撃を管理するDirector候補**。 |
| 9 | **Baritone** / 高度な経路探索、採掘・設置を考慮した経路費用 | 1.20.1 Forge・Fabricのソースあり | [cabaletta/baritone 1.20.1@efed17c](https://github.com/cabaletta/baritone/tree/efed17c8804252f14bc5ba5b647d91863c5c7e7d) | READMEと1.20.1 `gradle.properties` はpathfinderと1.20.1 Forge47.0.1のターゲットを宣言。**クライアント操作ボット向け**、そのままサーバー側のMobのGoalに組み込めるわけではない。 |
| 10 | **Guard Villagers** / 护衛・巡回・追従・役割交代 | 1.20.1 Forge の旧branchあり | [seymourimadeit/guardvillagers 1.20.1@b067d53](https://github.com/seymourimadeit/guardvillagers/tree/b067d5340fdae162e933fd77bec0a2bc330eef05) | READMEに護衛の職務、近隣村民との関係、Follow/Patrol指令。**default mainはMC26.3 NeoForge** なので1.20.1へ移植時の出典には旧branchを使う。 |

## 元MODの完全な実装ソースが確認できなかった候補

| 優先 | 名称 / 入手先 | 配布artifact（1.20.1 Forge） | 調査目的 / 境界 |
| --- | --- | --- | --- |
| J1 | [Fungal Infection: Spore（the_harbinger69）](https://www.curseforge.com/minecraft/mc-mods/fungal-infection-spore) | **`spore_1.20.1_2.2.0j.jar`** / 2026-06-29 / 約111 MB | 原作者説明にHivemindの再構築、感染者の群れ化、援軍要求、階層形成、バイオマスによる進化。公式ページはWikiリンクを提供するが、原作対応Java GitHubソースは今回確認できず。実JARでAI/進化/通信/発生源の依存関係を追うのが有用。**All Rights Reserved。** |
| J2 (別件) | [Fungal Infection: Spore AI（sx666）](https://www.curseforge.com/minecraft/mc-mods/fungal-infection-spore-ai) | **`spore_ai-2.8.0-beta.2+mc1.20.1-forge.jar`** / CurseForge file ID **9007186** / 2026-09-29 / 約4.9 MB | 別作者によるSporeアドオン。作者はMindごとの会話・関係/個性、斥候派遣、地形・養分による部隊配置を説明。**外部AI endpoint/API設定が必要**、呼び出し費用あり得る。CurseForge「Source」は**Spore AI Model CommunityというYSMモデル/外観配布repoであり、ページ自身が『MODプログラムソースは公開していない』と明記**。作者のAIアルゴリズム/JARの内部実装は未検証。**All Rights Reserved。** |
| J3 (補助) | [SporeAI（ByteChen）](https://www.curseforge.com/minecraft/mc-mods/sporeai) | `sporeai-1.6.0.jar` / 2026-08-20 / 1.20.1 Forge | 上記sx666のアドオンとは**別物**。DeepSeek/OpenAI-compatible endpointを用いるLLM狩猟/会話の実験候補。APIキーが必要で、MinecraftMobの軽量ルールAIの直接基盤には向かない。プロジェクトはMITと表示しているが、公開ソース本体の有無は未確認。 |

ユーザーにJAR提供を依頼するなら、**最初はJ1の原作Sporeのみ**が一番新しい情報を回収できる。J2のLLM制御に重点を置くなら追加し、API必須・モデル費用・個人情報送信の条件を別途確認する。GitHubモデル素材リポはMODソースの代用ではない。バイト一致・sha256・依存物は実物を受領してから固定。

## プレイヤー/コミュニティの手掛かり（実装事実ではない）

- [Reddit 2026-10-03 — army/civilization](https://www.reddit.com/r/feedthebeast/comments/1wwwo2f/any_mods_that_allow_me_and_my_friends_to_make_our/) にMineColonies・Recruits・AW2の実使用者コメント。戦術の調査先を選ぶ参考。個体AIの設計事実を証明しない。
- [Reddit 2025-07-07 — mob block breaking](https://www.reddit.com/r/feedthebeast/comments/1lu7xju) にはImproved MobsやEpic Siegeの設定とブロック破壊の問題報告。原因/修正を断定しない。検証シナリオの候補。
- [Reddit 2025-02-28 — simultaneous Sculk/Spore infection](https://www.reddit.com/r/feedthebeast/comments/1j0lxs8) に1.19.2で両勢力間の大量感染/ラグ報告。他版に一般化はできないが、敵対勢力の多重シミュレーション負荷を測定する手掛かり。
- [Reddit 2022-05-04 — Ancient Warfare army control](https://www.reddit.com/r/feedthebeast/comments/uigcqy) に、命令を聞かず個体が勝手に敵へ突撃するという報告。優先順位と命令上書きの研究案に繋げる。

## 技術回収を混ぜない分類

- **A：指揮官/集団指示**: Recruits → AW2 → Sculk Horde（Sculkは増援役割優先中心）。
- **B：大規模職務・資源要求**: MineColonies。
- **C：戦術による環境変更 / 原状復元**: Improved Mobs（保存対象はBlockState主体）。
- **D：生物群れ・社会的行動**: Alex's Mobs、Zombie Awareness。
- **E：軍勢出現・戦闘スケジュール**: The Hordes。
- **F：複雑な経路最適化**: Baritone（クライアント用設計を1.20.1 ServerGoalへ機械的コピー不可）。
- **G：感染勢力・階層・進化**: Scape and Run: Parasites（既存）とSpore（JAR待ち）。
- **H：LLM/自然言語での指示**: Spore AI addonはAPI/外部モデルの比較資料であり、API非依存の階層型指揮AIとは独立テーマ。

## 未完了・次の工程

1. 決定した各ソースについてGit commit固定から full-tree inventory、ライセンス、issue/PR失敗修正履歴、該当サブシステムの呼び出し経路を取得。**今回のクラス抜粋をwhole-target completeにしない。**
2. SourceSnapshot/メタ情報は実JARのhash/依存関係/実行結果とは別。配布JARを検証したら初めて原作バイナリのbytecodeと照合する。
3. A/B/Cの階層型指揮実験（指揮なし・指揮あり・共有記憶追加）のため、各MODから独立したアルゴリズム契約のみ回収。既存MODを一つのテンプレートに融合しない。
4. 1.20.1 Forge / 最新上流は別トラック。旧AW2 1.12.2と新しいバージョン/ローダーのAPI差を明記する。
5. Minecraft起動、実機・TPS・ネットワーク・Mob振る舞い・JAR完全同一性検証は **NOT_RUN**。Source/JARの著作権・資産の再配布境界を保持。

**ここにある優先順位は研究価値の暫定順位であり、賢さを測定・順位付けしたものではない。**


## 追記：Spore原作JAR取得・解析着手（2026-10-11）

上記の「J1はJAR待ち」は**当初の発掘時点の履歴**。同日にユーザーから Spore 2.2.0j / Minecraft 1.20.1 Forge の実JAR提供があり、SHA-256を固定してBytecode解析を開始した。旧記録は書き換えず、新しい正本を参照する。

- [Minecraft部門 Spore研究入口](../../minecraft/mods/fungal-infection-spore/README.md)
- [実JARのProto指揮AI・重み更新・戦術砲撃の調査](../../minecraft/mods/fungal-infection-spore/HIVEMIND-AI-BYTECODE-2026-10-11.md)
- [AI部門への再利用課題](PROTO-HIVEMIND-CASE-STUDY-2026-10-11.md)

本体2.2.0jの実バイナリには4入力×4出力の部隊選択・ダメージに基づく重み更新がある。静的調査の限定的な進捗であって本MOD/学習性能のCOMPLETEやPASSではない。
