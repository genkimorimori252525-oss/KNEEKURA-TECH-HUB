# Spore Gargoyl × Dynamic Trees — 地形破壊時のBlockState / 座標の不整合

**2026-10-11 / バイナリ＆ソース照合。** 実ゲームでのクラッシュ再現ではない。**Spore ANCHOR:** Minecraft 1.20.1 Forge 2.2.0j、ユーザー提供原本JAR SHA-256 d20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489。Dynamic Treesは比較対象の別MOD、他MC/Loaderトラックへ証拠を混ぜない。

## 報告と調査対象

- [Dynamic Trees Issue #1201](https://github.com/DynamicTreesTeam/DynamicTrees/issues/1201) は **2026-07-09** 投稿、確認時 **OPEN**。報告環境：Minecraft **1.20.1**、Forge **47.4.20**、Dynamic Trees **1.20.1-1.4.11**、Spore **1.20.1_2.2.0j**。GargoylのSmashStomp攻撃とTrunkShellBlockのcoredirプロパティ欠如の例外が、**報告者のログ**に含まれる。実際にこちらの環境で再現したわけではない。
- レポータがSporeのJARファイル名を指定していても、**当方のJARと報告者のJARの同一SHA-256は不明**。MOD構成が多数含まれるため、報告内の全条件・他MODの影響は未検証。
- 原本Sporeクラス：com/Harbinger/Spore/Sentities/EvolvedInfected/Gargoyl.class、SHA-256 **ff93579d0247e45fc2ca075ff55a5db6184fb47f4eee459c0e395e8a206c5780**。
- Dynamic Trees 1.20.1ソースを **release/1.20.1 @ eb7f75e9f0f021503349893cf6ecb8ee864a3053** に固定。[gradle.properties](https://github.com/DynamicTreesTeam/DynamicTrees/blob/eb7f75e9f0f021503349893cf6ecb8ee864a3053/gradle.properties) は **modVersion=1.4.11**、mcVersion=1.20.1。対象[TrunkShellBlock.java](https://github.com/DynamicTreesTeam/DynamicTrees/blob/eb7f75e9f0f021503349893cf6ecb8ee864a3053/src/main/java/com/ferreusveritas/dynamictrees/block/branch/TrunkShellBlock.java) のblob SHAは ae5cc16b2a0f972ce1b4a9197a8c7bcbc2905384。

## 両原典を結んだ原因候補（実行未確認）

**Spore Gargoyl.SmashStomp(Level,BlockPos center,double radius,double hardnessLimit) のBytecode：**

1. 攻撃対象のcandidatePosを計算しローカル変数13へ置く。
2. Level.getBlockState(candidatePos)で候補位置のBlockStateを取得し、ローカル変数14へ保管する。
3. そのBlockStateのgetDestroySpeed（SRG BlockState.m_60800_）を**2回**呼ぶが、両方とも引数のBlockPosには **candidatePos(13)ではなく元のcenterPos(2)**を渡している。
4. 条件次第でFallingBlockEntityを作り、candidatePosでブロックを破壊する。

**Dynamic Trees 1.20.1 TrunkShellBlockの公開ソース：**

1. getHardness(state, world, pos)が getMuse(world,pos) を呼ぶ。
2. getMuseはworld.getBlockState(pos)を読んでgetMuseUncheckedへ渡す。
3. getMuseUncheckedがgetMuseDir(state,pos)を呼び、1.4.11ではcoredir属性の有無を確認せずそのstateからgetValue(CORE_DIR)を呼ぶ。
4. candidatePosはTrunkShellBlockでも、centerPosのBlockStateが空気等でcoredirを持たない場合、**異なる位置の状態をgetHardnessへ渡したことが例外を誘発する**という説明が、報告Issueのstack traceと整合する。

**証拠レベルの切り分け：**

| 事実または仮説 | 根拠・状態 |
| --- | --- |
| SporeがcandidatePosのBlockStateにcenterPosの硬さ問合せを2回行う | **DIRECT_BINARY**: 上記SHA固定のGargoyl.class |
| Dynamic Trees 1.4.11が渡されたposでBlockStateを引き直し、coredirを無条件参照する | **DIRECT_SOURCE**: release/1.20.1 @ eb7f75e、TrunkShellBlock.java |
| Gargoyl/TrunkShellの組合せでIllegalArgumentExceptionが報告された | **THIRD_PARTY_REPORTED**: Issue #1201のクラッシュログ |
| 上記2つのコード経路が報告クラッシュの原因だった | **HIGH_CONFIDENCE_INFERENCE / BUG_CANDIDATE**。機序は整合、当方は未再現 |
| 原作者がすでに原因を承認し修正した | **UNKNOWN**。issueはOPENで、修復PR・正確なbefore/after diff未取得 |

### 原本検証プログラム

- [TECH-HUB自作の静的検査器](tools/check_gargoyl_hardness.py) はJAR SHA・該当.class SHAを照合し、BlockState取得位置と硬さ照会位置が一致しないことを、**別のレジスタを使った2回の呼出**として再検査する。
- [結果JSON](verification/GARGOYL-HARDNESS-STATIC-2026-10-11.json)：**4/4選定Bytecode構造PASS**、原作JARで実行済み。別のSRParasites JARならhash段階で拒否する。Minecraft・Dynamic Treesの実機起動はNOT_RUN。
- 出力に著作権のある原作のbytecode全文・スタックトレース全文を保存せず、derivative explanation/ID/SHAだけ公開。

## 再利用できる技術上の教訓（設計案）

- **呼出側の契約:** BlockStateをworld.getBlockState(candidatePos)で取得した場合、そのBlockStateに問い合わせる座標も原則としてcandidatePosにする。別の座標を使うなら明確な目的・一致確認・例外境界を設ける。
- **受け側の堅牢化:** Dynamic Treeの別トラックである[1.21.1側ソース](https://github.com/DynamicTreesTeam/DynamicTrees/blob/8bf66d83ac3a707fe482782fe21d2cb732527c66/common/src/main/java/com/dtteam/dynamictrees/block/branch/TrunkShellBlock.java)ではgetMuseDirがプロパティ存在チェックを行う。これは別バージョンで見つけた保護例であって、**1.20.1の修正が提供された、Issue #1201が解決済みという証拠ではない**。
- 独立した侵略MODや将軍AIの地形破壊は、BreakPermission、対象BlockStateとBlockPosの整合性、競合MODの動的硬さ、残骸/BlockEntity NBT、変更後のRollback Journalを独立に試験する。

## 研究状態・修復史の残工程

- **ANCHOR:** 1.20.1 Forge Spore 2.2.0jの該当Method MAPPED/DIRECT_BINARY。
- **COMPARATIVE:** Dynamic Trees 1.20.1-1.4.11ブランチの公開ソースを確認。1.21.1ソースは参考のみ。
- **未実施:** 作者の該当修正diff/issue closureの確証、報告環境の再現、実体FallingBlockEntityとDynTrees World/BlockState条件、最新FRONTIER Sporeの元JAR、TPS測定。
- 正式なTECH-HUB [Failure/Repair手順](../../FAILURE-REPAIR-HISTORY-v1.md) は、SourceSnapshot・Issue原文のcaptureと修正前後のhashが揃っていないため **PARTIAL / 未import**。報告Issueを修復済みケースやGameTest PASSに昇格させない。
