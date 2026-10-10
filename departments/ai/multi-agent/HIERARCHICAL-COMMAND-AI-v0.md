# 階層型指揮・群体知能 — 設計候補 v0

**発案:** 2026-10-11 / AI部門最初のテーマ  
**状態:** DESIGN_CANDIDATE。**実装なし、AI学習なし、シミュレーションなし、実機評価なし。**

## 発想

**すべてのモブに高度な知能を持たせる代わりに、少数の「将軍」が作戦を決め、部隊指揮官が割り当て、各兵士が単純なAIで行動する。** 必要に応じて、成功/失敗の統計や攻撃への適応を群れに共有する。

この3階層は**TECH-HUB独自の将来設計案**であって、参考MODに同じ司令塔構造が実装されているという主張ではない。

## 候補アーキテクチャ

```text
Director（勢力・全体戦略）
   目標選定 / 資源配分 / 失敗からの方針変更 / 勢力記憶
        │
        ├── Regional Commander（局地指揮）
        │       部隊編成 / 側面攻撃 / 目標優先度 / 撤退
        │           ├── Unit A（軽量FSM/Goal）
        │           └── Unit B（軽量FSM/Goal）
        │
        └── Regional Commander（別地域）
                    ├── Unit C
                    └── Unit D

記憶は Unit / Squad / Faction を別スコープで管理
```

| 層 | 判断内容 | 更新原則 |
| --- | --- | --- |
| Director | どこを攻めるか、兵力・資源をどこへ配分するか | イベントや低頻度の更新。全Mobの毎tick経路は処理しない |
| Commander | どの兵士に迂回・攻撃・破壊・支援を割り当てるか | 局所状態・優先度・命令期限を処理 |
| Unit | 索敵、移動、攻撃、回避、破壊、命令失効時の自己防衛 | 既存の軽量AIやゲームtickに委譲 |

DirectorやCommanderを実際のエンティティにするか、サーバー内部の戦術ノードにするかは未決定。指揮官が死亡したら副官継承・自主行動・撤退のどれを選ぶかも戦術として検証する。

## 命令と報告の設計原則（まだスキーマ未確定）

指示には、発行元、部隊/ユニット、優先度、目的地/対象、発行時刻、有効期限、前提条件、実行失敗時の代替を含める。受領・終了・失敗は重複や競合が分かるようにする。

Directorへは全ユニットの生ログでなく、戦果・損失・進路停滞・発見した敵戦術などの**要約**を渡す。細かい経路・衝突回避・飛び道具はUnit側に任せる。適切な更新間隔はベンチマークで決め、現時点で「軽量」と断定しない。

## 学習と生態系の発展案

- **個体記憶:** 直近の攻撃種別、退避先、進路失敗。
- **部隊記憶:** どの侵攻路/役割分担が成功したか。
- **勢力記憶:** 敵勢力の脅威、過去の大きな敗北、資源の推移。
- **将来の生態系:** 縄張り、餌/資源、繁殖、捕食、競争、淘汰を**別の研究課題として**検討。上記の記憶や進化ポイントだけで生態系完成とはしない。

まずは確率やカウンタに基づく軽量な学習を基準にし、強化学習やニューラルネットは利益を測定してから判断する。

### 出典との境界

[Minecraft部門にあるScape and Run: Parasitesの原作JAR調査](../../minecraft/mods/scape-and-run-parasites/COMBAT-AI-BYTECODE-2026-10-11.md)では、ダメージ種別の個体耐性、死亡時の群体への集積、次世代への再適用、個別の仲間追従・光源破壊・侵食Goal等が静的に確認されている。

これは「学習と集団行動を組み合わせられる」という**実装例**であって、Director/Commander/Unitの3階層が原作にある証拠ではない。1.12.2のBytecode証拠を1.20.1 Forgeでの実装完了とも呼ばない。

## 評価計画（すべて未実施）

| 比較群 | 戦術 | 記憶 |
| --- | --- | --- |
| A：基準 | 独立Mobが目標へ突撃 | なし |
| B：指揮型 | Director/Commanderが役割・目標を割り振る | なし |
| C：指揮＋学習 | Bに戦果/失敗/敵攻撃の共有記憶を加える | ルールベース |

同じ戦力、地形、装備、乱数シードで複数試行する。実験候補は平地戦、壁のある拠点攻撃、迂回と光源破壊、将軍喪失/通信遅延、連敗による戦術変更、Mob上限、チャンク読み込み/復帰。

評価：目標達成率、所要時間、兵力損失、停滞回数、命令遅延/競合、戦術の多様性、サーバーtick/CPU/メモリ、プレイヤーの建築への影響。勝率だけを「知能」の指標にしない。

比較すべき対案として、完全中央制御、分散Utility AI、HTN/GOAP、共有Blackboard等を別途調査する。階層型が常に優れるという前提は置かない。

## 担当境界・次の工程

AI部門は抽象的な指揮契約・情報共有・評価方式を研究する。Minecraft部門は具体的なGoal/Brain/PathNavigation、攻撃演出、ワールド変更、Forge依存・LAB/GameTestを担当する。

**次:** 先行実装・論文・専門コミュニティを探して比較し、軽量な最小シミュレータを設計する。動作・性能・原作との一致はすべて UNKNOWN / NOT_RUN。

## 2026-10-11 — 実MODのSignal Router調査からの追加課題

[Spore 2.2.0jのVigil→Proto→Calamity/Womb指揮のBytecode解析](../../minecraft/mods/fungal-infection-spore/GROUP-COMMAND-SIGNAL-BYTECODE-2026-10-11.md) と [AI部門の独立Signal派遣比較](SIGNAL-ROUTING-CASE-STUDY-2026-10-11.md) を参照。

階層型指揮は「目標の決定」だけでは足りず、偵察Signalの**誰へ配送するか**、すでに任務中の部隊の**優先度/空き**、新兵站拠点を作るときの**資源予算**、兵士の**SearchPos失効**、作戦の**成功報酬と行動試行報酬の分離**も必要。原作は選定の確率や条件が違うため、この研究成果を単一テンプレートに強制統合しない。

現状はDESIGN_CANDIDATEで、実Minecraft適用や性能改善を証明していない。

## 2026-10-11 — 役割別Goalの実JAR技術回収

[Spore 2.2.0jの輸送・後衛支援・残骸回収・広域制圧Goal](../../minecraft/mods/fungal-infection-spore/AI-GOAL-LAYER-2026-10-11.md) のBytecode解析から、Commanderが決める任務を Transport / Support / Resource Recovery / Combatへ分ける選択肢が増えた。Unitは独立の局所Goalを実行し、作戦完了・資源消費・地形変更を別イベントとして報告する案。これらを必須の一体化AIテンプレートとするものではない。原作のcanUse相当の内部でblockを破壊する処理は[BlockStateと照会位置の不整合](../../minecraft/mods/fungal-infection-spore/GARGOYL-DYNAMICTREES-HARDNESS-2026-10-11.md)と合わせて、可逆WorldMutationJournalと副作用分離の受け入れテスト候補へ入れる。**DESIGN_CANDIDATE / runtime未検証**。

## 2026-10-11 — Goal登録・競合とG12実行中Goal観測

[Sporeの86クラス・372直接Goal登録呼出、実Goal.FlagとMob継承関係の分析](../../minecraft/mods/fungal-infection-spore/GOAL-REGISTRATION-PRIORITY-AUDIT-2026-10-11.md)を技術候補として追加。

Director/Commanderが任務優先度だけ与えても、Unit側のMOVE/LOOK/TARGET予約が合っていないと競合が起こり得る。InfectedWitchでは同優先度4の複数支援Goalと継承元SearchAreaGoalがMOVEを共有している。Bruteは輸送時に移動するのにTransportInfectedのFlagがTARGETのみ。これらは**Bytecodeで確認した設計上の競合候補**であり、GameTest未実施のため実際の干渉・性能悪化は断定しない。

将来の将軍AIでは、`TaskPriority`とは別の`ResourceLock(MOVE/LOOK/ATTACK/WORLD_MUTATION)`、タイムアウト、タスクの割込理由、失敗→再割当の記録を検討。これは**原作コードの流用ではなく独立の設計候補**。
