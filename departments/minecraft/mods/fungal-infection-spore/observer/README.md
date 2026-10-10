# KNEEKURA Spore Observer — Forge 1.20.1

**状態（2026-10-11）：Forge側ソース実装済み。専用サーバーのSpore実JAR起動・GameTest・TPS実測はNOT_RUN。**

これはTECH-HUBが新規作成した読み取り専用の研究用補助MOD。原作Sporeのコードや素材を再配布しない。対象は Minecraft 1.20.1 Forge / Spore 2.2.0j / 原本SHA-256 d20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489。1.21.1 NeoForge版の互換性は未確認。

## 動作する条件

- 初期状態ではイベントを登録しない。明示的なJVMプロパティ kneekura.spore.observe.enabled=true かつ dedicated server の場合のみ有効化する。
- 既存LABのsession.json、.kneekura-run.json、run ID、world ID、seed、session roleとworldの実パスを照合する。自己申告はLABのregistry権限・session attestationの代わりにはならない。
- Forge ModListから**実際にロードされたSpore JARのファイルパス**を得てSHA-256を確認。不一致や読取不能では停止する。
- EntityJoin/Leave、ServerTick START/END、公開getterにより、Sporeのロード中Mob、ProtoのSignal、Calamityの未任務状態、Infectedの探索位置を**受動的に観測**する。
- Mob生成、ブロック編集、AIへの命令、チャンク固定、私有worldへの書き込みを実装しない。LABセッションディレクトリに限り CREATE_NEW でrun IDごとのJSONLを書く。8 MB、最大49,998イベント、最大10,000tick、追跡4,096Entityの上限を設ける。
- 出力は origin=runtime_claim_unattested であり、既存の[観測証拠検証器](../RUN-EVIDENCE-GATE-2026-10-11.md)がruntime PASSを自動認定することはない。

## 実装した観測範囲

| G番号 | 収集するイベント | 未到達の検証 |
| --- | --- | --- |
| G09 | proto_signal_snapshot | Vigilが列挙した正確なProto候補順とSignal発行メソッド内の呼出は未観測 |
| G10 | proto_signal_snapshot、calamity_search_snapshot、entity_join_snapshot | Calamity再配置の抽選とWomb生成**試行**の内部分岐は未観測 |
| G11 | entity_join_snapshot / entity_leave_snapshot、proto_weights_snapshot、vigil_wave_snapshot、damage_event_snapshot | 公開getterの重み16個、残り召喚数、Forge LivingDamageEventを受動観測。**awardHivemind/punishHivemindや実Spawn成功のメソッド呼出は未観測** |
| G12 | search_pos_snapshot / follow_partner_snapshot | Goalの実行・SearchPosクリア・ナビ停止は未観測 |
| G13 | server_tick_sample | Proto、active Signal、Infected数、ロード済みチャンク数、バニラ強制ロードチャンク数とServerTick START〜END時間の**未校正値**を記録。Forge ticket総数・正式MSPTやTPSではない |

G09〜G12はスナップショットだけで十分な証拠にはならないため、Python側のシナリオ判定はINCONCLUSIVEのままにする。G13も実行主体の認証、一定サンプル数、計測条件とcleanup証拠が必要。

## ビルドとテスト

Java 17、ForgeGradle 6、Forge 1.20.1-47.4.10 を宣言。元Spore JARはビルド・GitHub Actionsへ取得しない。TECH-HUBルートから既存Kirby用Gradle 8.8 wrapperを再利用する。

- Windows: departments/minecraft/projects/kirby-mod/gradlew.bat -p departments/minecraft/mods/fungal-infection-spore/observer build --no-daemon
- Linux: bash departments/minecraft/projects/kirby-mod/gradlew -p departments/minecraft/mods/fungal-infection-spore/observer build --no-daemon
- Pythonログ受入: py -3 departments/minecraft/mods/fungal-infection-spore/tools/evaluate_spore_trace.py FILE.jsonl
- Portable writer: [TraceSink.java](src/main/java/org/kneekura/sporeobserver/core/TraceSink.java) / [TraceSinkTest.java](tests/TraceSinkTest.java)。Java17で個別コンパイル・実行可能。

[Spore research gates CI](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/workflows/spore-research-gates.yml) の portable-observer-core と forge-observer-compile は別々のジョブとして判定する。CIでForgeビルドが成功しても実ゲームPASSではない。

## 登録済みLAB runでのみ使用するシステムプロパティ

- kneekura.spore.observe.enabled=true
- kneekura.spore.observe.scenario=G13
- kneekura.spore.observe.runId=登録済みLAB run_id
- kneekura.spore.observe.worldId=登録済みworld_id
- kneekura.spore.observe.seed=登録済みworld_seed
- kneekura.spore.observe.durationTicks=1200
- kneekura.spore.observe.sessionDirectory=既存LAB sessionディレクトリの絶対パス
- kneekura.spore.observe.expectedWorld=準備済み隔離worldの絶対パス

LABの [現行実行権限](../../../CURRENT-HANDOFF-2026-10-02.md) と [元の受入計画](../LAB-GAMETEST-ACCEPTANCE-2026-10-11.md)を必ず満たすこと。セッションの作成とworld制御はこの補助MODが行わない。

**次の不足:** 正式Forgeコンパイル（CIとは別結果）、実LAB registryでのWorld受入、Sporeの依存閉包、実起動、G13計測、G09〜G12のメソッド単位の観測フック、証拠とcleanupの審査。未達をPASSにしない。


## 合成データを使ったJava→Python結合試験（2026-10-11）

[G13SyntheticProducer.java](tests/G13SyntheticProducer.java) は、原作やMinecraftを実行せずに自作JavaのTraceSinkから200件×3条件（Proto 1/4/16体）、計600件の専用JSONLを生成する。

生成結果を既存の[evaluate_spore_trace.py](../tools/evaluate_spore_trace.py)へ渡したローカル試験では、3条件のサンプルを認識しつつ、status=SYNTHETIC_FIXTURE_ONLY、runtime_pass=falseを維持した。CIにも同じ横断テストを追加した（実行結果は別途workflowログで確認）。この結果をG13実サーバー性能PASSと呼ばない。

[G13計測コード](src/main/java/org/kneekura/sporeobserver/SporeEvents.java)の観測時間はForgeのTickEvent START〜ENDで、計測器の介入があり、サーバー本体の正式MSPTと同義ではない。別途計測器OFF/ONで同じ環境のオーバーヘッドを比較する必要がある。


### JARパッケージ検証ゲート

CIでは自作Java17のソースをForgeGradle 6でビルドし、生成JARの中身を検査する。所定の観測器classと META-INF/mods.toml が存在し、**原作com/Harbinger/Sporeのclassが一切含まれない**ことが必要。成果物の公開配布や、原作ゲームでの動作まで自動保証するものではない。

G13の記録には tick_ms に加え、loaded_chunks と vanilla_forced_chunks_only も含む。後者はVanillaの強制ロード範囲であり、Forge独自の全ticket数ではない。tick_msはServerTickEvent START〜ENDの未校正値なので、独立したprofiler計測を行うまではTPSや正式MSPTと同義にしない。

**G11の補助観測について:** 元JARの Proto.getWeights() と Vigil.getWaveSize() は公開getterのため、リフレクション経由で読み、値のコピーをログへ出す。学習や召喚の処理は呼び出さず、ゲーム状態は変更しない。LivingDamageEventのamountはイベント発生時点の値で、ミッション報酬や後続の実ダメージ確定とは同一視しない。既存のPython G11ゲートが要求するwave_award/wave_spawn_result等を**このスナップショットで代用しない**。

## 2026-10-11 — Goal登録・競合とG12実行中Goal観測

[原作Bytecodeから復元した86クラス・372件のGoal登録位置](../GOAL-REGISTRATION-PRIORITY-AUDIT-2026-10-11.md) は**静的な呼出一覧**。有効Goalの実体を直接測るために [GoalRuntimeSampler.java](src/main/java/org/kneekura/sporeobserver/GoalRuntimeSampler.java) を追加した。

- **G12のみ**、20tickごとの受動snapshot中で対象Infectedの先頭8体まで登録済みGoalを観測。各MobのAction/Target両Selectorを合わせ、priority、Goalの実Class名、実際のGoal.Flag、WrappedGoal.isRunningを読み取る。出力kindは`goal_registry_snapshot`。
- Minecraft1.20.1 `Mob.f_21345_`と`f_21346_`へはForge `ObfuscationReflectionHelper.findField` を通じた**読み取り専用のSRG field参照**を行う。実体Goalを止めたり、追加・削除したり、Goal.canUseを実行したりしない。
- 1Mobにつき最大**12 Goal**だけを表示。総登録Goal数、実行中件数、`truncated`を併記。省略されたGoalがないと偽らない。イベント本文上限4KBを超えないことも安全契約。
- これは**ある時刻の現在状態を記録するだけ**で、Flag衝突が実際に発生したとか、別Goalを中断したというGameTest結果ではない。元JAR・LABの承認済み隔離worldとcleanupは未検証。出力を`search_goal_step`等へ勝手に変換しないため既存G12の受け入れ状態はINCONCLUSIVEのまま。

コンパイルは既存のForgeGradle CIで別途確認する。反射fieldの変換/アクセスが失敗した場合は観測を止め、runtime PASSへ昇格しない。
