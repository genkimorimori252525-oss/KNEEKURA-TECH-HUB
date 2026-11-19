# Spore 2.2.0j — AI Goal登録元・優先度・制御フラグの接続図（2026-10-11）

**ANCHOR:** Minecraft **1.20.1 Forge**、Spore **2.2.0j**、ユーザー提供原JAR SHA-256 **d20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489**。  
**調査状態:** 直接GoalSelector.addGoal呼出全件のBytecodeを抽出し **86登録所有クラス・372呼出・27静的契約 PASS**。**Minecraft実ゲームでのGoal競合やTPSは NOT_RUN。** 著作権のある元クラス・decompile全文・資産はGitへ保存していない。

[原本JAR receipt](ARTIFACT-RECEIPT-2026-10-11.json)、[48 AI型の索引](AI-GOAL-LAYER-2026-10-11.md)、[Signal/局地命令の既存解析](GROUP-COMMAND-SIGNAL-BYTECODE-2026-10-11.md)、[Minecraft ANALYSIS-WORKFLOW](../../ANALYSIS-WORKFLOW.md)、[SPEC v1.2](../../ANALYSIS-SPEC-v1.md)に従う。AI部門での将軍型への応用は本研究と別設計。

## 1. 直接の登録箇所を漏れなく数えた

**Binary locator:** 実JAR中の \`net/minecraft/world/entity/ai/goal/GoalSelector.m_25352_(int,Goal)\` へのinvoke。Minecraft 1.20.1 mappingsで **GoalSelector.addGoal(int,Goal)** に対応。

| 項目 | 直接呼出の件数 |
| --- | ---: |
| 呼出のある元JARクラス | **86** |
| 呼出合計 | **372** |
| \`Mob.f_21345_\`（通常 goalSelector） | **356** |
| \`Mob.f_21346_\`（targetSelector） | **16** |
| \`m_8099_\`（registerGoals） | **241** |
| \`addRegularGoals\` | **106** |
| \`addTargettingGoals\` | **12** |
| \`HandlerEvents.onLivingSpawned\` | **10** |
| \`addVariantGoals\` | **3** |

**重要:** 372はJavaメソッド内の**呼出箇所数**。個々のMobに入る有効Goalの個数でも、全てが毎tick開始されるという意味でもない。継承元の登録メソッドが呼ばれる場合、基底クラスのGoalは具体Mobの実際のGoalにも加わる。variant選択やイベント条件を満たさない呼出は実行されない。

[機械可読の限定サマリー・代表クラスSHAと27契約](verification/GOAL-REGISTRATION-MAP-2026-10-11.json) と [全件を再生成する自作Pythonスクリプト](tools/audit_spore_goal_registrations.py)。

**再実行:** Python 3.13、JDK javap（本研究ではJDK 21を用い、解析対象MODはJava 17環境のForge1.20.1）。

~~~powershell
py -3 .\departments\minecraft\mods\fungal-infection-spore\tools\audit_spore_goal_registrations.py "C:\MyJars\spore_1.20.1_2.2.0j.jar" --out "C:\Temp\spore-goal-registration.json"
~~~

- 実際の原本JARで**86/372/356/16** と27契約を検出。
- 同一JARへの2回実行は**出力バイト一致**。全登録クラスのshaと372呼出(owner, method, bytecode-PC, selector, priority, allocated Goal class)を含むローカルの派生JSON SHA-256は **e2d20388fb07e97d2a8b31bdb05cca4ddc52e885df06abaf936095fad4d65492**。
- SRParasitesの別JARを与えると内容を読まず **BLOCKED_HASH_MISMATCH** になる。
- サマリーJSONに契約検査とサンプルSHAを残し、必要になったとき上記コマンドから全派生JSONを復元する。原作のクラスバイト本文は再配布しない。

## 2. 各Mobに登録された役割別Goal

| 登録を行うクラス | Selector | 優先度 | 登録するGoal | 読み取れる役割 |
| --- | --- | ---: | --- | --- |
| \`BaseEntities/Infected\` | goal | 3 | \`LocHiv/LocalTargettingGoal\` | 近距離の標的・SearchPos共有 |
| 同上 | goal | 4 | \`LocHiv/BufferAI\` | 個体の支援効果 |
| 同上 | goal | 4 | \`LocHiv/SearchAreaGoal\` | 指定地点への移動 |
| 同上 | goal | 7 | \`InfectedConsumeFromRemains\` | 飢餓・残骸の消費 |
| 同上 | goal | 10 | \`LocHiv/FollowOthersGoal\` **2件** | 仲間の追従。二重登録の対象Class/Predicateは別途確認が必要 |
| \`EvolvedInfected/Brute\` | goal | **1** | \`TransportInfected\` | 兵員輸送 |
| \`EvolvedInfected/Leaper\` | goal | **3** | \`TransportInfected\` | 兵員輸送 |
| \`EvolvedInfected/Busser\` | goal | **6** | \`Busser$4\` → \`TransportInfected\`継承 | 条件付き輸送 |
| \`BasicInfected/InfectedWitch\` | goal | **4、4、4** | \`InfectedWitch$3,$4,$5\` → \`BuffAlliesGoal\`継承 | 異なる条件の支援Goal3件 |
| \`Organoids/Proto\` | goal | 3 | \`ProtoTargeting\` | 上位の標的配信 |
| \`BaseEntities/Calamity\` | goal | 7 | \`CalamityVigilCall\` | Vigil援軍の開始条件 |
| \`8種のCalamities具体Mob\` | goal | **7** | \`SummonScentInCombat\` | Scentの追加 |
| 同上 | goal | **8** | \`SporeBurstSupport\` | 広域支援・CDU干渉 |

**固定したコード経路:** InfectedWitch.m_8099_はsuper.m_8099_を先に呼び、その後に3種類のBuffAlliesGoal派生を登録する。基底Infected.m_8099_はaddTargettingGoals/addRegularGoalsを呼ぶ。継承されたSearchAreaGoal（priority 4, MOVE）は、WitchのBuffAlliesGoal（priority 4, MOVE/LOOK）と**同じGoalSelectorでMOVE競合**を起こす配置となる。各GoalのcanUse/goal instanceの状態によって勝敗は異なり、Witchの支援が必ず停止するという意味ではない。

**別の登録主体:** HandlerEvents.onLivingSpawnedは、Configの \`attack\` / \`flee\` リストとPathfinderMob型の条件によって、**NeareastAttackableTargetGoal 6箇所(priority 3)＋AvoidEntityGoal 4箇所(priority 4)** の直接登録呼出を持つ。**これはSporeのMob内部だけでなく他Mobへ対Sporeの索敵・回避行動を追加できる設計面**。configに一致するMobでその分岐が実行される。通常の全Mob登録として数えない。

## 3. 制御Flagが示す「優先度だけでは決まらない競合」

Minecraft 1.20.1 \`Goal.m_7021_\` は \`setFlags(EnumSet<Goal.Flag>)\`。バニラ\`GoalSelector\`の優先度（**小さい番号ほど優先**）は、**同じ制御Flagを共有するGoal間**で重要になる。参考：[Forge GoalSelector API](https://mcstreetguy.github.io/ForgeJavaDocs/1.20.1-latest/net/minecraft/world/entity/ai/goal/GoalSelector.html) / [1.20.1 mappings.dev Goal](https://mappings.dev/1.20.1/net/minecraft/world/entity/ai/goal/Goal.html) / [Goal Selectorの同優先度とFlag説明（Yarn 1.20.1）](https://maven.fabricmc.net/docs/yarn-1.20.1%2Bbuild.9/net/minecraft/entity/ai/goal/GoalSelector.html)。

| 元JAR Goalのconstructor | 明示的なflags | 研究上の含意 |
| --- | --- | --- |
| \`TransportInfected\` | **TARGET** のみ | 自身はPathNavigation/LookControlを操作するが、MOVE/LOOKの占有を宣言していない。Brute等の別Goalとの競合防止が不十分な**候補**。canUseで攻撃目標なし条件もあるため、必ず衝突するとは未確認 |
| \`BuffAlliesGoal\` | **MOVE + LOOK** | 3つのWitch支援Goalが優先度4で同一制御を要求し、基底SearchAreaGoal（MOVE）とも競合する |
| \`SearchAreaGoal\` | **MOVE** | 目的地移動を占有 |
| \`FollowOthersGoal\` | **MOVE + LOOK** | 探索/交戦中の移動Goalと競合し、優先度10の追従は一般に低い |
| \`LocalTargettingGoal\` | 設定なし | 他のMOVE系Goalと制御フラグ上は競合しない |
| \`InfectedConsumeFromRemains\` | 設定なし | **canUse内でblockを破壊する可能性**があり、Goal優先度7でも他MOVE Goalとの排他は保証されない |
| \`SporeBurstSupport\` | 設定なし | 広域効果を利用するがMOVE/LOOKを占有しない |
| \`SummonScentInCombat\` | 設定なし | 同じCalamityの広域支援・戦闘Goalと並行実行可能な構造 |
| \`ProtoTargeting\` | 設定なし | 標的配信と主戦闘Goalを区別可能 |

**「設定なし」の正確な範囲:** 今回の元JAR内の該当Goalクラスで、constructorからGoal.setFlagsが呼ばれていない。実行時のflag改変・GoalSelectorのdisabledFlag・別MODのMixinによる変更は未調査。Flag配列が空でも無条件で実際にGoalが動くわけではない（canUse/GoalSelector更新間隔を通る）。

## 4. なぜ将軍AIに直接関係するか

中央指揮官は命令（役割・目標・期限）だけ決め、各UnitにGoalを配布する方式なら、**内部のMOVE/LOOK/ATTACK/RESOURCE_MUTATIONの権限契約**を持つ必要がある。特に：

1. **一つのユニットに重なったMove命令を送らない。** 役割切替時の取消・タイムアウト・最低限の停止処理を用意。
2. **同優先度の支援Goalは選択規則を明示。** 所要時間、優先条件、既に実行中か、ターゲットの危険度などを記録し、初期登録順へ暗黙に依存しない。
3. **Worldを変更するGoalはcanUseから分離。** 読取のみの可否判定→MutationJournalに記録された変更→有効性検査→責任者ごとrollbackを分離。
4. **動的に他Mobへ加える行動も分離。** \`onLivingSpawned\`から追加された行動とMob既定のGoalが干渉しないか、依存MODの組合せで確認する。

これらは**新規の設計案**で、原作Spore自体が上記契約を搭載していることや、既存挙動より高速・賢いことを示さない。

## 5. 到達点と明示した未調査

- ANCHOR 1.20.1 Forge / Spore 2.2.0j：**直接登録呼出372件をINVENTORIED/MAPPED**。全Goalの実行時状態・すべての継承順序やGoal.Flagの動的更新は未収集。
- \`G01〜G13\` Forge実ゲーム/GameTest：**NOT_RUN**。別の[読み取り専用Observer](observer/README.md)はJARビルド済みだが、GoalSelectorの状態とGoalクラス別の実行フラグの直接観測は実装していない。
- 原作JAR以外のMOD・Mixin変換、正確なnewGoalRate/flag disabled変更、複数チャンク・ワールド間連携は引き続きUNKNOWN。
- AI/配下48クラスの存在を調査済み、今回Goalの**登録呼出所有クラスは86**。これは別の集合。全1,350クラスのwhole-targetはNOT_COMPLETE。
- FRONTIER Spore 1.21.1 NeoForge、作者ソース・修復差分・runtime/TPSは別タスクで未検証。

この研究はTECH-HUBの知識基盤へ自動VALIDATED昇格させない。元JARの実バイナリと、再現スクリプト・ハッシュで人間/後続AIがレビュー可能な段階に留める。
