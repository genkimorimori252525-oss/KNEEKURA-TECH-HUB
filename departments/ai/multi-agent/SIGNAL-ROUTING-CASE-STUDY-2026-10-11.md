# 将軍AI向け：Signal指揮・援軍配分・局地情報伝搬の技術回収

**2026-10-11 / DESIGN_CANDIDATE。** 原作Minecraftの実装証拠は [Sporeの11クラス原JAR追跡](../../minecraft/mods/fungal-infection-spore/GROUP-COMMAND-SIGNAL-BYTECODE-2026-10-11.md)。このファイルは独立した汎用設計案であり、Sporeと同じコードを使う計画ではない。

## 再利用する知能階層

| 層 | 機能 | 何を配布するか |
| --- | --- | --- |
| Scout / Vigil型 | 脅威の発見、通報、危機報告 | Signal（脅威座標、発見者、発見時刻） |
| Commander / Proto型 | 出動可能な部隊の検索、派遣と増援生産の判断 | Order（目標、役割、期限、優先度、資源費） |
| Unit / Infected型 | 共有された標的やSearchPosを実行 | 目的地へ経路探索し、交戦・到達・失敗を報告 |
| Faction Director | 複数指揮官の目標競合解消、記憶・資源を集計 | 地域・勢力の方針と有限予算 |

**命令伝達と個体行動は分離する。** 個体が毎tick中央AIへ問い合わせる方式をデフォルトにせず、命令変更イベントとローカル継続Goalを使う。更新間隔の最適値は推定ではなく計測で決める。

## 原作コードから得た反例と独立候補

1. **Signalの宛先:** 原作Vigil.TimeToLeaveの経路では最初に列挙されたProtoへSignalをセットする。距離順位/負荷順位での選別は未確認。独立設計はdimension+UUID+load+実行中命令を比較して宛先を決める候補。
2. **部隊再配分の確率:** Proto.checkForCalamitiesは空きCalamity1体でも50%で派遣せずWomb生成を試みる。[独立の合成実験](../evaluation/experiments/spore-signal-routing-2026-10-11/README.md)では n=1の生成**試行**率が50.2267%（理論50%）。これは原作Minecraft内の成功率ではない。
3. **命令の失効:** 原作SearchAreaGoalは3ブロック圏内でSearchPosを解除するが、到達不能や信号重複での適切な失効は未検証。独立Order案は発行時刻、期限、世代、失敗理由、再割当条件を持つべき。
4. **通信のスコープ:** 原作にはProto→Infected、Calamity→Infected、Infected→Infected、Vigil→Protoという異なる経路がある。独立案ではdimension/owner/factionを境界とし、無関係な群れへ報酬や作戦を送らない。
5. **報酬の整合:** Vigilは生成を試みる段階でawardHivemind、退場でpunishHivemindを呼ぶ経路がある。独立設計では召喚**試行**、実Spawn**成功**、援軍の戦果、資源効率を別イベントで記録する。
6. **処理費用:** AABB探索やランダムGoal試行の繰り返しは人数依存である。Directorは必要時のみ区域・目標を更新し、各Unitはローカルの移動/攻撃に専念する。

## 将来の命令スキーマ候補（未実装）

```text
Signal: signal_uuid, world_epoch, dimension, faction_id, source_uuid,
        found_tick, expires_tick, target_pos, severity, seen_target
Order:  order_uuid, signal_uuid, commander_uuid, unit_uuid, dimension,
        issued_tick, expiry_tick, objective, priority, max_spawn_cost
Report: order_uuid, actual_unit_uuid, spawn_member_index, event_kind,
        observed_tick, measured_effect, failure_reason
```

同一Signalは任務中のOrderへ二重発行しない。実召喚の部隊IDと候補indexを取り違えない。自軍の資源がゼロになるときのWomb生産停止、依存チャンクのunload時の命令停止と再割当を契約化し、実機測定で採否判断する。

## 最低限必要な評価比較（NOT_RUN）

- T1：既存部隊0/1/2/4体 → 再配分/新兵站拠点生成と成功率。
- T2：Signalの発生元が別dimension、発見場所が未ロード、指揮官喪失 → 誤配送を起こさないか。
- T3：敵城への移動中に異なるSignalが来たとき、既存Orderの有効期間・優先度・再計画・撤退。
- T4：同じ敵を10回小ダメージと1回大ダメージで攻撃 → 報酬と戦略目標は区別されるか。
- T5：1/4/16体のProto相当Commander、N=100/1000体の軽量Unitでサーバーtick負荷比較。

現状の成果は**原作の静的Bytecode解読と独立合成試験**。この計画はMinecraft MODの実装完了、性能改善証明、実ゲームでの学習・生態系形成を示すものではない。

### 2026-10-11 距離判定の知見

原作SearchAreaGoalは探索目標まで**9ブロック未満**になるとSearchPosをクリアする。原本JARの `BlockPos.m_203195_(Position,9.0)` がMinecraft 1.20.1の `Vec3i.closerToCenterThan` に対応するため、以前の「距離二乗9なので半径3」という解釈を訂正した。Followerのナビ停止判定は距離二乗9（約3ブロック）で異なる。将軍AIでの指示は、到達の半径・目標消失条件・任務終了のイベントを混ぜずに設計する。
