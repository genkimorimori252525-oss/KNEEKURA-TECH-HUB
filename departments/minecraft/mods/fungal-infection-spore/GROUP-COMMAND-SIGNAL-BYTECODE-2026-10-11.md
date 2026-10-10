# Spore 2.2.0j — Signal / Vigil / Unit集団AIの追加Bytecode解析

**2026-10-11。Minecraft 1.20.1 Forge原作JAR。DIRECT_BINARY / SELECTED-MAPPED。ゲーム実機・TPS・バグ再現NOT_RUN。**

原本: spore_1.20.1_2.2.0j.jar、SHA-256 d20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489。ユーザー提供。All Rights Reserved。公式配布原本と同一バイトであること、最新1.21.1 NeoForge版との挙動同一性は未確認。詳細は [原本証拠](ARTIFACT-RECEIPT-2026-10-11.json)。原JAR・Bytecode本文・音声・モデルを公共Gitへアップロードしない。調査は [ANALYSIS-WORKFLOW](../../ANALYSIS-WORKFLOW.md)と[仕様](../../ANALYSIS-SPEC-v1.md)に従う。

## 1. 通信・追従AIの実装経路と発動条件

| 原作のクラス / メソッド | 確認したBytecodeの条件 | 狙い |
| --- | --- | --- |
| AI/NeuralProcessing/ProtoAIs/ProtoTargeting#m_8036_ | Protoに標的あり、0〜5一様乱数=3のときだけcanUse。**評価ごと1/6** | Protoの標的をproto_range内の無標的Infectedへ広める |
| AI/LocHiv/LocalTargettingGoal#m_8036_ | Linked、標的かSearchPosあり、nextInt(10)=0。**評価ごと1/10** | Infected同士で標的・SearchPos共有 |
| AI/CalamitiesAI/CalamityInfectedCommand#m_8036_ | nextInt(100)=0、Calamityが有効な標的またはSearchAreaあり。**評価ごと1/100** | Calamityから半径相当32 AABBのInfectedへ命令 |
| CalamityInfectedCommand#Targeting | 標的共有は受信側が無標的の場合。探索地点共有は**受信側に既存SearchPosがある場合のみ上書き** | SearchPos=nullの兵士にはこの分岐で新規探索先を渡さない |
| AI/CalamitiesAI/CalamityVigilCall#m_8036_ | 生存・**HPが最大HPの半分未満**・標的あり・nextInt(200)=0。**評価ごと1/200** | 緊急Vigil生成。Goal開始時、Calamityを親として設定しX/Z±20の位置へ配置 |

**重要:** 1/6等はそれぞれのGoalがcanUse評価を受けた際の乱数ゲートであり、毎tickの発動率、秒間発動回数や実際の命令成功率ではない。GoalSelectorによるスケジューリング・占有Goal・サーバー状況は未測定。

## 2. Vigil → Proto → Calamity または Womb

今回確認した原作クラスの呼び出し連鎖：

1. **Vigil.TimeToLeave**：TRIGGER=1または2ならScent。TRIGGER>=3ならproto_range AABB内のProtoを探してSignal(true, Vigilの座標)を渡す。このメソッドは**最初に列挙されたProto**にSignalを渡した直後にループを抜ける。距離でソートする処理はこの経路にはない。別のSignal作成経路も同じと断定しない。
2. **Proto.m_8119_**：有効なSignalがあるとcheckForCalamities(signal.pos)を実行し、同関数がtrueならSummonConstructorへ渡す。この分岐は特定の200/1200tick moduloの内側ではないので、Signalが残る間は毎server entity tick検討され得る。
3. **Proto.checkForCalamities**：周囲のCalamityでSearchAreaがBlockPos.ZERO（待機）と見なせるものについて、各候補にMath.random()<0.5を試す。成功した最初の個体へ目的地を設定し、Signalをクリア、falseを返す。
4. **派遣しなかった場合**：Calamityが存在していても、全ての50%判定に外れた場合や任務中で使えない場合はcheckForCalamitiesがtrueとなり、Wombの生成を試みる。
5. **Proto.SummonConstructor**：ServerLevelで配置条件を満たした場合、Womb（RECONSTRUCTOR）を生成し、関連した通知を送ってSignalをクリア。条件未達ならSignalが残り得る。Entity追加の戻り値を呼び出し元で使わない点にも注意。生産成功率・繰り返し負荷は実機未確認。
6. **Vigil.SummonInfected**：Vigilのwave番号に応じてbase/middle/max-wave構成から候補を選び、**実際のMob生成や標的確認より前にawardHivemindを呼ぶ**。
7. **Vigil.TimeToLeave**：退場時の処理にpunishHivemindがある。加点・減点は必ずしも作戦全体の成功/失敗と一致しない。
8. **Vigil.m_8107_**：WAVE_SIZE>0なら内部counterを進め、20を超えてからSummonInfectedを実行してwave_sizeを減らす。実機での正確な呼び出し頻度は未計測。

Wikiの[Linking & Signals](https://www.fungalinfectionspore.wiki/systems/linking-signals)ではSignalが「最も近いProto」へ届くとあるが、**ここで直接調べたVigil.TimeToLeaveの一経路にはnearest計算がない**。他の発信元まで一般化しない。WikiはVersionを固定できないBehaviorHintで、今回のBytecode観測を優先する。

### 乱数配備の数学的帰結と独立シミュレーション

条件を満たすCalamityがn体、各個体に対する判定0.5が独立と仮定する**一回のSignal処理**では、誰も派遣されずWombを**試みる**確率は 2^(-n)。実際のWomb生成成功率ではない。

| 空きCalamity数 n | 理論上のWomb試行率 | 自作30,000回比較 |
| ---: | ---: | ---: |
| 0 | 100% | 100% |
| 1 | 50% | 50.2267% |
| 2 | 25% | 25.43% |
| 3 | 12.5% | 12.6133% |
| 4 | 6.25% | 6.2133% |
| 5 | 3.125% | 3.0567% |

[Pythonの独立テスト](../../../ai/evaluation/experiments/spore-signal-routing-2026-10-11/probe.py)と[結果JSON](../../../ai/evaluation/experiments/spore-signal-routing-2026-10-11/results.json)。比較対象の「待機部隊が1体でもいれば優先派遣する」方式はKNEEKURAの独立改良仮説であり原作の挙動ではない。

## 3. Unitがどう行動するか：Goalの責任分離

- **AI/LocHiv/FollowOthersGoal**：canUseの内部searchCooldown=20を使い、既存の相手が有効でないときにAABB拡張32の候補から3D距離二乗最短のPartnerを選ぶ。Mob.tickCount%20で再経路計算。距離二乗<=9でナビゲーションを停止、>4096ならcanContinueToUse側で追従先を解除。
- **追従の相反するブランチ候補**：同Goalのtickには距離二乗>4096ならPartner座標へ即移動する経路もある。Goal継続判定はその距離ですでにPartnerを無効化するため、通常のGoal評価順でテレポート経路が到達可能か未確認。単に「64ブロック超でワープする」と主張しない。
- **AI/LocHiv/SearchAreaGoal**：攻撃対象なし、SearchPosありでGoalを開始。tryTicks%40で位置の再経路計算、到着位置への距離二乗<=9でSearchPosをクリア。他Goalから目標変更されないまま到達不能なときの扱いは追加検証待ち。
- **LocalTargettingGoal**：知覚範囲はmin(MobのFOLLOW_RANGE,32)。標的共有とSearchPos共有が異なる分岐であり、全員が常時同じ目標を持つわけではない。

## 4. 原作の複数指揮官を動かす際の性能監査候補

ProtoのSignal保持中のCalamity周辺検索、Vigil.TimeToLeaveのProto周辺検索、LinkedのLocalTargettingGoalのInfected検索、FollowOthersGoalの最寄り候補走査はそれぞれ**別のエンティティAABBクエリ**。多頭Protoや大規模軍勢では検索回数の上限、適切な指令TTL・イベント駆動化・分散させる頻度などを実機で検証するべき。今回の作業にはMinecraft TPSの測定値はない。

## 5. 再現検査・エビデンス

- [自作 Bytecode group gate](tools/verify_spore_group_ai.py) — 実JARの指定11クラス SHA-256を確認、**19/19 Bytecode構造検査 PASS**。
- [静的検査結果JSON](verification/GROUP-COMMAND-STATIC-RESULT-2026-10-11.json) — 同じJARで2回の出力がバイト一致。別のSRParasites JARではBLOCKED_HASH_MISMATCHとして拒否。
- 認定対象はJARの選定メソッド/クラスのみ。実ゲームのSignal配送、Vigil生成、mob spawnの成否、スケーラビリティはNOT_RUN。
- 原作者の問題修正Issue/PRは修正差分まで調べておらず、Failure/Repair史の完了や改修完了は主張しない。

## 6. 次の実機GameTest課題（まだ未実施）

G09：複数Proto配置でVigil由来Signalの宛先がEntity列挙順か距離かを観測。  
G10：未任務Calamityを0/1/2/4体にして、派遣数・Womb試行と実Spawn・Signal存続を測定。  
G11：Vigilの援軍試行と実Spawn成功・awardHivemind、退場時のpunishHivemindの差を計測。  
G12：到達不能SearchPos、Partner死亡・unload・64ブロック距離、チャンク境界で目標が失効するか。  
G13：N=1/4/16 Proto＋複数SignalでAABB検索・chunk ticket・server tick CPUを計測。

既存[隔離Forge LAB契約](LAB-GAMETEST-ACCEPTANCE-2026-10-11.md)を使う場合も事前の権限・依存・安全なworld・cleanupを維持する。**この文書はゲーム起動した証拠ではない。**