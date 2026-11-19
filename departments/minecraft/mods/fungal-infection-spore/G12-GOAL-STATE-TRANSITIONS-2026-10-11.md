# Spore 2.2.0j — G12 Goal実行状態差分の受動観測

**2026-10-11 / ANCHOR = Minecraft 1.20.1 Forge, Spore 2.2.0j**
**原本JAR SHA-256:** d20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489
**状態:** Owned Forge Observerのソース実装・合成試験。原作Sporeの実ゲーム・G12 GameTest・TPSは **NOT_RUN**。

## 1. 以前の「先頭12件」サンプリングの弱点を改善

旧[GoalRuntimeSampler](observer/src/main/java/org/kneekura/sporeobserver/GoalRuntimeSampler.java)はpriority番号順に登録Goalを並べて先頭12件だけを出力する。Infected Witchの支援3Goalはpriority4であり、継承した目標等があると観測上欠落する可能性がある。

このため、[GoalSnapshotSelection.java](observer/src/main/java/org/kneekura/sporeobserver/core/GoalSnapshotSelection.java)を独立Java17の選定器として作成。

1. InfectedWitchの支援Goal、TransportInfected、SearchAreaGoal、FollowOthersGoal、LocalTargettingGoal、InfectedConsumeFromRemains、BufferAI、BuffAlliesGoalを優先。
2. 次にその時点でrunningのGoalを優先。
3. 最後に数値priorityが小さいGoalを優先。selector、クラス名、観測器内の一時instance IDで順序を安定化。
4. 最大12件。全登録件数/全実行中件数、truncated、selection_policyを明記。**省略されたGoalが存在しないという結論に使わない。**

[GoalSnapshotSelectionTest.java](observer/tests/GoalSnapshotSelectionTest.java)は、priority0の通常Goalが16件あっても、priority4のWitch支援3Goal＋SearchAreaGoalと稼働中Goalを選び取る合成回帰試験。実ゲームのGoal数や稼働を測ったものではない。

## 2. Tick間のrunning変化（Goal callbackそのものではない）

[GoalRunningStateDiff.java](observer/src/main/java/org/kneekura/sporeobserver/core/GoalRunningStateDiff.java)を追加。

- [GoalRuntimeSampler](observer/src/main/java/org/kneekura/sporeobserver/GoalRuntimeSampler.java)は、GoalSelectorのWrappedGoalをIdentityHashMapで識別し、**同じrunでだけ有効な正のGoal ID**を割り当てる（最大2,048）。永続的なMinecraft Goal IDではない。
- [SporeEvents.java](observer/src/main/java/org/kneekura/sporeobserver/SporeEvents.java)はG12の受動サーバーtick終了時に観測対象8体のGoal登録/running状態をサンプルし、同一Mob・同一Goal IDについて前回とrunning値が異なるときのみ goal_running_state_delta_snapshot を記録する。
- Goal登録状態の通常snapshotは20tickごと。runningの変化差分は1tickごとのサンプルから検出する。
- 未観測・truncated・Mob選出漏れのあるGoalについて、停止と推測しない。サンプリングから外れたMobの以前のrunning情報は破棄し、復帰時は新しい基準サンプルにする。
- **Goal.start/stop/canUse/tickの実呼び出しを記録するのではない。** 同じtick内の複数回の切り替え、変化の真の原因や制御資源のロック競合は、この方式では証明できない。

## 3. 各Mobを偏らず観測する

G12での観測対象は、ロードされているInfectedをUUID順に整列後、Witch・Brute・Leaper・Busserそれぞれ最大2体を優先し、余りを別Infectedで補う**合計最大8体**。旧「エンティティ登録順で先頭8体」から改善した。

これも一つの選定サンプルであり、全MobのAI履歴や全ディメンションでの観測とは呼ばない。

## 4. 記録を検証するときの偽陽性防止

[analyze_spore_goal_snapshots.py](tools/analyze_spore_goal_snapshots.py)は既存のrun ID・world ID・原本JAR SHA・event順序検査を経たG12ログにのみ適用。

- goal_running_state_delta_snapshot は capture_scope = END_TICK_RUNNING_STATE_DIFF_NOT_GOAL_CALLBACK のみ認める。
- 数値Goal IDの重複、同じrunning真偽を変化と偽るデータ、不正selector/priority、truncated件数の不一致、偽の「Goal.start直接観測」印を拒否/INCONCLUSIVE。
- delta_changes_false_to_true/true_to_false は、**Goal開始回数/停止回数ではなく、隣接するtick終了時のrunning値差分数**として記録。
- いかなるJSONLでも、この検査器はruntime_passをtrueへ昇格させない。認証済みLABの実験・world・build・cleanupと原作ゲーム内の観測が必要。

## 5. テスト・出典・未完了

- [GoalRunningStateDiffTest.java](observer/tests/GoalRunningStateDiffTest.java)：初回基準、running変化、前回にないGoal、途中でサンプルされなかったMob、重複Goal IDの回帰検査。
- [GoalSnapshotSelectionTest.java](observer/tests/GoalSnapshotSelectionTest.java)：研究対象の支援Goalを、12件の表示上限でも残す合成検査。
- [G12SyntheticProducer.java](observer/tests/G12SyntheticProducer.java)：Witch/Bruteの独立合成登録状態と、Witchのrunning差分1件を生成。Java→JSONL→両Python検証器で検査。
- [test_gates.py](tests/test_gates.py)：不正なrunning差分、未完了run、偽のGoal callback証拠、異なる原本を拒否する回帰検査。
- [原作372件の登録呼出とその制御Flag分析](GOAL-REGISTRATION-PRIORITY-AUDIT-2026-10-11.md)。
- [Yarn Minecraft 1.20.1 GoalSelector API説明](https://maven.fabricmc.net/docs/yarn-1.20.1%2Bbuild.9/net/minecraft/entity/ai/goal/GoalSelector.html)では、同じFlagを共有する同priorityの実行中Goalを後続Goalが同priorityで置き換えないと説明。これはMinecraft APIの説明で、Sporeの具体的な実ゲーム競合の観測結果ではない。

**残るG12実証:** LABで承認された隔離Forge 1.20.1サーバーへSpore固定JARとOwned Observerを配置し、Witch/Brute/Leaper等を制御した独立シナリオで実行。Goal callbackの正確な開始/中断理由を得るには、別途read-only内部フックまたは元MODの計測点を設計・検証する必要がある。

**FACET:** ANCHOR Goal登録STATIC_MAPPED、OWN_OBSERVER_SOURCE_IMPLEMENTED、CI_BUILD_TEST（runごとに別照合）、ACTUAL_SPORE_RUNTIME=NOT_RUN、TPS=NOT_MEASURED、WHOLE_TARGET=NOT_COMPLETE、FRONTIER 1.21.1 NeoForge=NOT_ACQUIRED。
