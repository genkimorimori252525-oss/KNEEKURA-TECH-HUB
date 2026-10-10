# Spore 2.2.0j — G12 Goalフラグ競合候補の観測データ評価基盤

**2026-10-11 / Minecraft 1.20.1 Forge / 研究用自作ツール**  
**状態:** Forge観測MODソースのコンパイル確認済み。Java→PythonのG12合成結合試験PASS。**原作Spore実ゲーム、Goal割り込み、AI負荷、GameTest/G12受け入れは NOT_RUN / INCONCLUSIVE。**

## 原作Bytecodeの調査と観測器の分担

- [実JARから86登録元・372 GoalSelector.addGoal呼出を固定した調査](GOAL-REGISTRATION-PRIORITY-AUDIT-2026-10-11.md) は原作の**登録コード上の呼び出し箇所**を示す。全呼出が同時に実行されるという意味ではない。
- [Forge 1.20.1向け GoalRuntimeSampler.java](observer/src/main/java/org/kneekura/sporeobserver/GoalRuntimeSampler.java) は**読み取り専用**。ForgeのSRG field mappingからMobのaction/target GoalSelectorを読み、WrappedGoalのpriority、実Goalクラス、Flags、isRunningをコピー。サーバー側G12観測中のWitch・Brute・Leaper・Busserを各最大2体優先するInfected計8体に対し、登録状態を20tick毎・稼働状態差分をtick終了毎に採る。各Mobは研究対象/稼働中Goalを優先して最大12項目を表示する。
- [G12 evidence interpreter](tools/analyze_spore_goal_snapshots.py) は既存の[JSONL実験行のfail-closed検証](tools/evaluate_spore_trace.py)を通した後で、goal_registry_snapshotを確認する。実観測ログに擬似Goalや異なるrunが混入すれば分類し、**実ゲームのGoal衝突が起きたというPASSを返さない**。

## 収集できるもの、できないもの

| 観測フィールド | 直接取得したときの意味 | 制約 |
| --- | --- | --- |
| priority、goal_class、flags | 特定のロード中Mobに、その時点で登録されていたGoal | static JARに存在するだけのGoalより狭い集合 |
| running | GoalSelectorがその時点でrunningとした状態 | canUseの回数、割り込み理由、継続時間を意味しない |
| registered_goal_count、registered_running_count | 所属Mobの両Selectorの登録/実行中合計 | 記録上限12の外にもGoalが存在し得る |
| truncated | 記録12件よりGoal登録数が多い | 偽の「見つからない」と扱わない |
| potential_shared_flag_pairs | **同じSelector**でMOVE/LOOK等を共有するGoalの組合せ | すべてが同時実行可能・衝突済みとは言わない |
| same_priority_shared_flag_pairs | 上の組合せのうち、同じ数値priority | 同順位ではGoalSelector側の選択/登録順の影響もあり得る |
| co_running_shared_flag_pairs | 単発snapshot中で両方runningかつ同一Flagがあった場合 | ログの真正性と実ゲームの状態推移・他MODの介入未確認 |

**安全の要点:** Target SelectorとAction SelectorのGOAL同士は異なるSelectorとして扱い、同じMOVE/LOOKを設定しても無条件で互いの直接競合候補へ算入しない。制御フラグが共通しないGoalは数値priorityが同じでも競合候補に加えない。

## 再現可能な独立テスト

- [Java G12SyntheticProducer](observer/tests/G12SyntheticProducer.java) はTECH-HUB自作の二体分の登録情報を生成。Witchの priority4 の支援系3 Goal + SearchAreaGoal (MOVE/LOOK) と、BruteのTransportInfected TARGET-onlyとMelee MOVE/LOOKを**合成データ**として使う。
- [PythonのG12 GOAL reviewer](tools/analyze_spore_goal_snapshots.py) はWitchの4Goalから共有Flagかつ同priorityの**6組**を検出。BruteのTARGETとMOVE/LOOKは共有Flagがない。
- [既存G12テストゲート](tools/evaluate_spore_trace.py) は同じ合成JSONLを実験未実施／境界未検証としてINCONCLUSIVEに保持。
- Pythonで追加6件の回帰テスト（既存合計31件）を追加。wrong scenario、invalid flags、ターゲットSelector混同、終了不完全、偽のruntime originなどをfail-closed処理。
- GitHub Actionsの \`portable-observer-core\` に Java→JSONL→両Python reviewerの一致をチェックするステップを追加。[対象CI](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/38085740754)。**「6組の競合をSpore実機で再現した」という意味ではない**。

### ローカル実行例

~~~powershell
py -3 .\departments\minecraft\mods\fungal-infection-spore\tools\analyze_spore_goal_snapshots.py C:\Temp\registered-lab-g12.spore.jsonl --out C:\Temp\g12-goal-review.json
py -3 -m unittest discover -s departments/minecraft/mods/fungal-infection-spore/tests -v
~~~

独自JSONLを示すだけではLABのrun/owner/world/cleanupの証拠にならない。ゲーム観測の真正性とGoalの実際の競合・タイミングを裏付けるには、LABの実験登録と認証済みrun、必要に応じて特定GoalのcanUse/start/stop/interruptの read-only eventフック、対照試験が必要。

## 原作の将軍AI技術として扱うときの境界

- **候補A:** InfectedWitchの同priority4支援Goalが同じMOVE/LOOKを持ち、基底SearchAreaGoalと競合し得る。
- **候補B:** BruteのTransportInfectedは移動経路/注視を更新しているが、TARGETしか宣言していないため他のMOVE/LOOK Goalが排他できない可能性。
- **候補C:** InfectedConsumeFromRemainsはcanUse内で地形を変更し得るのにFlagが空で、EligibilityとMutationの分離が弱い可能性。

**どれも STATICALLY_SUPPORTED_DESIGN_RISK であって、実機で競合やTPS低下を証明したものではない。** 将軍AIでの設計候補はResourceLock(MOVE/LOOK/TARGET/WORLD_MUTATION)とTaskPriorityの分離、現在実行中の注文の期限管理、失敗・中断のイベント記録を扱う。

**残作業:** G12実Minecraftでのrunning差分取得とGoal.start/stopの真の呼出時刻の識別、バニラGoalSelectorの実行制御周期、他MODのMixinとGoal登録副作用、G09〜G13の認証済みLAB GameTest。厳密なFPS/TPS、FRONTIER NeoForge、whole-target解析もNOT_RUN。

## 継続仕様：Goalの状態差分は直接callbackではない

[後続の実装・偽陽性防止の詳細](G12-GOAL-STATE-TRANSITIONS-2026-10-11.md)を参照。observerが各tick終了時にisRunningを比較し、false→true・true→falseとなったGoalだけを記録する。**同じtick内の複数変化を保証できず、Goal.start/stop呼出は直接測定していない。** Java17の選定/差分単体テストと、合成G12ログのPython判定をCIで分離して実行する。
