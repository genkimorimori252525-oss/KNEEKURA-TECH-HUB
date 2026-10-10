# Spore G09〜G13 — ランタイム証拠受け入れゲート

**2026-10-11：検証プログラムと15件の自作合成テストは実装・実行済み。** 原作Forge observer、GameTest Java、実サーバー稼働・TPS測定はまだ NOT_IMPLEMENTED / NOT_RUN。

## 何を実装したか

- [観測ログ検査器](tools/evaluate_spore_trace.py) は、1実験runごとの独立Spore JSONL companionを読み、JAR SHA、Minecraft/Forge版、run/scenario/world/dimension、server側、先頭meta・末尾end、seq/tick、行数整合を確認する。
- 入力は8MB未満 / 5万行以内、イベント本文にも上限を置く。別run混入や欠落を静的に拒否。
- [単体テスト](tests/test_gates.py) は15件すべてPASS。違うJARハッシュ・run・world、未終端、重複seq、必要な比較群欠如などを検査する。すべて合成入力。
- [G09の合成fixture](verification/fixtures/g09.synthetic.jsonl)と[検査結果](verification/g09.synthetic.review.json)。結果は SYNTHETIC_FIXTURE_ONLY、runtime_pass=false。

## 先頭meta・イベント・終了行の契約

先頭 ch=spore_meta、schema=kneekura.spore.observation.v1、run_id、scenario=G09〜G13、固定jar_sha256、minecraft=1.20.1、loader=Forge、seed、world_id、dimension、world_disposable=true、origin、physical_side=DEDICATED_SERVER、observer_identity。

中間 ch=spore_observation、同じrun/scenario/world/dimension、厳密増加する整数seq、減少しないtick、kind/data。末尾 ch=spore_end、同じrun/scenario、reason=completed|aborted|timeout|error、observation_countの一致。

originは synthetic_fixture と runtime_claim_unattested に限定。**自己申告されたrunやworld_disposableは真正性・実行権限の証明にはならない。** KNEEKURA-LABの認証済みsession/epoch/world/cleanupと別途照合が必要。既存[LAB main schema](../../lab/simlab/schema.json)は変更しない。

## シナリオ別の最低カバレッジ

| ID | 必要なkindと観測フィールド | 何が保留になるか |
| --- | --- | --- |
| G09 | signal_dispatch: recipient_uuid、列挙順candidatesのuuid/distance_sq | 最初の候補と最近の候補が同じで比較できなければ保留 |
| G10 | signal_resolution: eligible=0/1/2/4、decision=redirectまたはwomb_attempt、任意でspawn_success | 4条件がそろわないと保留。試行と成功は別 |
| G11 | wave_award → wave_spawn_attempt → wave_spawn_result → vigil_retire → vigil_penalty、同一vigil_uuid | 一連の観測・順序が欠ければ保留 |
| G12 | search_goal_stepのdistance_to_block_centerとsearch_pos_cleared、follow_goal_stepのdistance_sqとnavigation_stopped | SearchArea半径9の内外、Follower距離二乗9の内外を採れなければ保留 |
| G13 | server_tick_sampleのproto_count/signal_count/infected_count/tick_ms | 1/4/16体それぞれ信号0・感染0条件を200サンプル以上採れなければ保留 |

**結果ステータス:** BLOCKED_INVALID_TRACE、SYNTHETIC_FIXTURE_ONLY、INCONCLUSIVE_*、IMPORTED_UNATTESTED_OBSERVATIONS。**runtime_passは常にfalse**。有効なJSONLでも真正なForge GameTest PASSには自動昇格させない。G13の平均/p95/p99も計測条件・許可・性能閾値なしにTPS合格としない。

## ローカル再実行

Windows PowerShellで TECH-HUB ルートから：

~~~powershell
py -3 .\departments\minecraft\mods\fungal-infection-spore\tools\evaluate_spore_trace.py C:\Temp\spore-g09.jsonl --out C:\Temp\spore-review.json
py -3 -m unittest discover -s departments/minecraft/mods/fungal-infection-spore/tests -v
~~~

**テスト環境:** Python 3.13.5で15/15 PASS。G09は実行済み合成fixtureで不正な最短距離ルーティングではなく「列挙順の最初が採用されたという観測値」を出力するが、これ自体を原作Minecraftの挙動とは呼ばない。

**残る実装:** Forge observer本体、GameTest・依存class pathのビルド、実ゲームG09〜G13、TPS/forced chunks/cleanupの認証、原作問題の修復史。次の工程は[LAB受け入れ計画](LAB-GAMETEST-ACCEPTANCE-2026-10-11.md)を参照。
