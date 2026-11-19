# Spore 2.2.0j — 輸送・支援・飢餓・広域制圧AIの原作Bytecode解析

**日付:** 2026-10-11 / **ANCHOR:** Minecraft 1.20.1 Forge 2.2.0j  
**固定原本:** spore_1.20.1_2.2.0j.jar、SHA-256 d20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489。  
**状態:** AI配下のクラス48件をすべて列挙・SHA算出（INVENTORIED）。うち**重点7クラス**のメソッドをJDK javap -p -c -constantsで読み、20件の限定Bytecode契約を照合PASS（MAPPED）。残り41クラスのメソッド意味解析・Forge実機・TPS/勝率は NOT_COMPLETE/NOT_RUN。

優先手順：[ANALYSIS-WORKFLOW](../../ANALYSIS-WORKFLOW.md) / [ANALYSIS-SPEC](../../ANALYSIS-SPEC-v1.md)。既存の[Hivemind学習](HIVEMIND-AI-BYTECODE-2026-10-11.md)と[Signal指揮](GROUP-COMMAND-SIGNAL-BYTECODE-2026-10-11.md)を保持する。原作All Rights ReservedのJAR・class本文・画像・音声は公開Gitへ複製しない。

## 1. AIディレクトリの実数と境界

原本 com/Harbinger/Spore/Sentities/AI/ 配下には**48の.class**がある（内側クラスも数える）。そのうちNeuralProcessing/配下は**4件**：Experimental/ExpAirPathNavigation、Experimental/ExpPathFinder、ExpPathFinder$PatchedPath、ProtoAIs/ProtoTargeting。

この数は「AIの全機構が48クラスで完結する」という意味ではない。Proto・Vigil・WombなどのEntity本体やEventHandler側にも知能・生産/進化処理がある。NeuralProcessingという名前だけで多層ニューラル学習が実行されると断定できない。

[AI層48クラスの不変クラスSHAと限定検査結果](verification/AI-GOAL-LAYER-2026-10-11.json) / [再実行用の自作Python解析器](tools/audit_ai_goal_layer.py)。

## 2. TransportInfected — 輸送と騎乗

**原本:** Sentities/AI/TransportInfected.class、SHA-256 8a7cc28be43269c748b7d8fb7b76f705b3ce431118ccbeec03aa6e1607e086a7。

- constructorではTargetingConditionsのrange=**16.0**。getFreePartnerはAABBを**32.0**膨張させ候補を列挙し、距離の二乗が最小の個体を選ぶ。AABB32だけを最終的な実効探索距離と解釈しない。
- canUseはMob.tickCount%20==0で候補を再検索し、Mob自身が騎乗中でなく、攻撃目標がなく、候補があるときに行動候補になる。
- tickはLookControlとPathNavigationで相手へ接近。**距離二乗が9未満（半径約3未満）**でequip()を呼ぶ。
- equipは元Bytecodeで partner.startRiding(mob) を呼ぶ。**パートナーが輸送側Mobに乗る**のであり、単なる追従ではない。
- tick内でPathNavigation.moveToを呼ぶが、内部キャッシュを含め実際に毎tick経路の再構築が生じるかは未検証。

**再利用候補:** 個体AIから輸送任務を切り分け、待機/騎乗枠の予約・リーダー死亡やchunk unload時の撤退/再割当を明示する。

## 3. BuffAlliesGoal — 後衛支援

**原本:** Sentities/AI/BuffAlliesGoal.class、SHA-256 94fe50ffbc82eac3a038d0481b9835b70aba14ebc4d2b370ab97dccf54a3d4b0。

- canUseはMobに攻撃目標がないとき、**getFreePartner()を連続して2回呼び出す**。それぞれはLevel.getNearbyEntitiesを呼ぶ経路であり、静的には冗長な周辺検索の候補。実性能低下は未測定。
- getFreePartnerはAttributes.FOLLOW_RANGEに合わせAABBを広げ、Class/Predicate/TargetingConditionsで絞り距離の二乗最小の候補を選択。
- tickはLine-of-Sight、距離、attackTimeを条件に、RangedBuff.performRangedBuff(partner, normalizedDistance)へ委譲。支援の中身は各Mobの実装を読むまで未確定。

**再利用候補:** 支援ユニットのローカルGoalと上位の支援命令を分け、探索/支援の最適な周期は実測で決める。

## 4. InfectedConsumeFromRemains — 飢餓と成長

**原本:** Sentities/AI/InfectedConsumeFromRemains.class、SHA-256 587fddabc788d6adfab3412f1a2641486dbb458175ad2107268911bd9deec0ef。

- canUse=m_8036_はisStarving()を確認し、RandomSource.nextIntBetweenInclusive(0,10)==0、**Goal評価当たり1/11**の確率ゲートを通るとisCorpseを呼ぶ。
- isCorpseはMobのAABBを**2.0**拡張してBlockPosを順に走査。REM AINS/WALL_REMAINS系やBIOMASS_BULBへ**Math.random()<0.1**の独立した条件を試す。
- 成立時はWorld側のblock破壊API（SRG m_7471_）とsetHunger(0)を呼び、REM AINS系では**EvoPoints+1**、BIOMASS_BULBでは**Kills+1**へ進む。
- **重要な設計上の副作用:** canUse()が呼び出したisCorpse内に**地形破壊と進化値の変更**がある。「行動可能か問い合わせるだけの純粋な関数」と誤認すると問題になる。ブロック候補が存在しても0.1抽選に当たらず実際には消費しないケースがある。
- tick負荷やブロックの復元は未観測。このGoal自体が破壊前のBlockEntity NBTを全て記録して復元するとは証明できない。

**再利用候補:** 資源回収/飢餓を独立Goalとし、条件確認とworld mutationを分離、MutationJournalによるundoとプレイヤー編集保護を検証する。

## 5. Calamityの広域支援

### SporeBurstSupport

**原本:** Sentities/AI/CalamitiesAI/SporeBurstSupport.class、SHA-256 11b3a441f33429b8e9a2273f3c593bfca5642292f377e16d293f87d00c7f8f79。

- canUseは生存・RandomSource.nextInt(300)==0・有効な標的・**距離二乗<200**等を検査する（半径200ブロックではない）。
- startはCalamityをsetStun(60)に設定。TrueCalamityならchemicalRange()・buffs()・debuffs()を参照し、sporeBurstとkillCDUsを実行する。
- killCDUsはAABB全体のBlockPosを走査し、Sblocks.CDUならCDUBlock.replaceCDUを呼ぶ。chemicalRangeが大きければ、探索の体積に比例する費用候補になる。**本当に遅い・どの範囲を破壊したというゲーム実測ではない**。

### SummonScentInCombat

**原本:** Sentities/AI/CalamitiesAI/SummonScentInCombat.class、SHA-256 f529908ca2742d2b92ff38ec18212c272891141721895dfbe76ee3a23fe49b71。

- config scent_spawn、生存、RandomSource.nextInt(400)==0と他のMob条件を検査。
- checkForScentは自分のAABBを**8.0**膨張させた範囲のScentEntityを数えて**2件未満**なら可とする。
- startはScentEntityを生成しsetStun(80)。1/400はGoal評価あたりの乱数判定であり、毎400tickで確実に召喚とはいえない。

## 6. 戦闘と航法の補助Goal（選定解析）

- HurtTargetGoal は攻撃を受けた個体のalertOthers経由で近傍の他Mobへ標的を伝える。Proto由来の指揮・命令とは別の**局地反応アラート**。
- AerialRangedGoal はScatterShotRangedGoalを継承し、PathNavigationとOrbit(target)で飛行位置を変える。Hinderburg向け専用Goalで、Vec3回転・移動と弾幕スケジューラをつなぐ経路がある。正確な飛翔弾道・命中率・CPUはNOT_RUN。
- CalamityPathNavigation、HybridPathNavigation、ClimberNodeNavigator、Experimental/ExpAirPathNavigationは個別のナビゲーション技術を持つ。今回の48件インベントリは**全移動メソッドの解析が完了した意味ではない**。

## 7. 将軍AIへの独立の技術回収（DESIGN_PROPOSAL）

**Director:** 攻撃目標/資源予算。**Commander:** 輸送・支援・攻撃・回収のタスク割当。**Unit:** 局所Goalと移動、実際の成功/失敗報告。回収時のblock変更は独立のmutation journalで記録し、元ゲームやプレイヤーのworldを直接改造する原作コードのコピーペーストは行わない。

計測すべき対象は、二重getNearbyEntities、飢餓Goalによる範囲BlockPos全走査、Calamityの広域CDU置換、Aerialの再経路決定。リーダーが各Unitの経路を毎tick代わりに計算すると中央処理がボトルネックになる可能性がある。いずれも**負荷仮説であり測定済みではない**。

**全体:** ANCHOR selected source Bytecode MAPPED、original JAR SHA VERIFIED、game runtime NOT_RUN、FPS/TPS NOT_MEASURED、frontier 1.21.1 NeoForge 未取得、Failure-Repair-historyの元修正diff未分析、Whole-target NOT_COMPLETE。
