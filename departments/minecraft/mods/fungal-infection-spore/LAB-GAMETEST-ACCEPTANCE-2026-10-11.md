# Spore 2.2.0j — 隔離Forge GameTest / LAB受け入れ契約案

**2026-10-11。状態：DESIGNED_NOT_RUN。** 原作の動作や負荷を実際に計測したものではない。MODのJARを無許可のサーバー・既存worldで起動しない。

## 検証基盤の整合

- ANCHOR：Minecraft 1.20.1 Forge + Spore 2.2.0j。原本SHA-256 d20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489。依存MOD・Forge・Java・設定・ワールドseed・サイド・run IDを実行前に固定する。
- [TECH-HUBのLAB契約](../../lab/README.md)および[現行Minecraft引き継ぎ](../../CURRENT-HANDOFF-2026-10-02.md)の隔離world/owner/session/cleanupを守る。GameTest sourceが存在するだけでは実行権限にならない。
- [Forge 1.20.x GameTest公式手順](https://docs.minecraftforge.net/en/1.20.x/misc/gametest/) は @GameTestHolder / RegisterGameTestsEvent、隔離構造、成功・失敗・timeoutを規定。実験側の新規JUnit/Javaコードは**まだForge classpathでbuildしていない**。ここでは受け入れ契約のみ設計する。
- 原作者のJARを変更せず、第三者ソースや資産を公開リポへアップロードしない。追加の観測器を作る場合は別の独立した研究用MODに限定する。

## シナリオと明示的assertion

| ID | 初期条件 | 実測すること | PASSに必要な観測 |
| --- | --- | --- | --- |
| G01 | Proto 1体、配下の固有4種の候補、標的を固定 | 実際に抽選されたMobの種類/配列index k とpersistent NBTのdecision/member | NBTが指す個体と実際の選択位置を突き合わせて一致/不一致を観測、失敗経路のログも保存する |
| G02 | 同種別の装備/HPの標的、与ダメージを1回/10回、総ダメージを揃える | Proto weightsの前後差、発生したLivingDamageEvent件数、被害個体 | 加点/減点の件数を実測し、重み変化をイベント数・ダメージ量で分類。二重イベントは除外せず記録 |
| G03 | 攻撃者を同条件にして学習あり/なしのProtoを複数シード比較 | 学習された重み、部隊選択、攻撃回数、指揮成功率 | 「勝率」以外の戦術的成果、失敗率、部隊ごとの資源消費、統計区間を記録 |
| G04 | Proto A/B、別々の標的、両方同ディメンション→save/reload | 2体のweights/NBT・帰属元Entity ID/UUID・軍の戦果ルーティング | 混線や喪失の有無、所有者不在時の動作が再現できる |
| G05 | Overworld 2体 + Nether 1体、対照群はOverworld 2体のみ | getAmountOfHivemindsによる各ディメンションの強化判定とjoin/leaveイベント | 全体カウント3の時に閾値到達するか、実際の強化が各ディメンションでどう変わるか |
| G06 | D1にProto由来ChunkLoadRequest、D2読込、後にowner削除 | 各dimensionのforced chunk/Forge ticket、request map、TTL、unforceの実行 | D2に誤チケットが入るか／cleanup後の残留がゼロかをログで示す |
| G07 | 同じ隔離worldでProto 1 / 4 / 16体と複数Infectedの負荷比較 | 平均/p95/p99 server tick ms、TPS、loaded/forced chunk数、Mob数、server heap/GC、packet量 | 計測条件・run/seed・取得失敗やクラッシュも残す。基準値未設定なら判定はUNKNOWN |
| G08 | Biomass=3から最大5召喚試行を誘導 | 成功spawn数・各成功直前と直後のBiomass・召喚ブロック状態 | 負数になるかを観測、地形や既存Mob上限が何回成功を妨げるか記録 |

**ゲート**：GameTestが完了しても、対象の判定コードを一度も実行していない場合はINCONCLUSIVE（0実行をPASSにしない）。クラッシュ、同期不良、時間切れ、Mobが候補条件を満たさない等は成功判定に含めない。負荷測定と機能PASSは別ドメインの受け入れを使う。

## 観測器の実装時の責務

- 観測するのはServerLevelのEntity UUID/ID、dimension、SpawnType、Proto UUID、配下Mob persistent NBT（hivemind/decision/member）、damage source/被害Mob、実ダメージ量とtick、weightsのダンプ差分、BioMass、request IDとdimensionとChunkPos、chunk ticket数、TPS。
- 原作BytecodeのEntity IDは再起動後に同じ値であると仮定しない。必要なら観測器側でEntity IDとUUIDの関係をrunごとに保持する。
- 試験コードはデータ取得だけを基本とし、プレイヤー所有のworld/保存データには作用しない。強制spawn/攻撃などは実験契約で宣言し、専用テンプレート内だけで実行。
- 失敗・不確実な結果も保存し、元のJAR/ワールド/生ログを公開Gitへ直接載せない。必要ならハッシュ・集計・元保存場所のロケータだけを残す。

## 次の実装入口

**未実装:** 隔離研究用Forge observer、G01〜G08のJava実装、forgeGradleビルド、依存関係取得、GameTest実行、負荷統計の分析とcleanup報告。実行主体は既存Minecraft/LABの登録済み権限ルートに従う。

**先に使える静的検査器:** [Bytecode gate](BYTECODE-CONTRACT-GATE-2026-10-11.md) は原JARが手元にあればJava環境だけで再実行可能だが、これ自体にForge実行の権限はない。

## G09〜G13 追加計測案（2026-10-11 / DESIGNED_NOT_RUN）

原作の [Signal/群体GoalのBytecode根拠](GROUP-COMMAND-SIGNAL-BYTECODE-2026-10-11.md) と [19静的検査結果](verification/GROUP-COMMAND-STATIC-RESULT-2026-10-11.json) を参照。旧G01〜G08の試験は実施済みにしない。

| ID | 隔離worldの入力条件 | 取得する証拠 | 注意事項 |
| --- | --- | --- | --- |
| G09 | Vigilが3回目の波を終え、複数Protoがproto_range内でそれぞれ異なる距離とEntity走査順にいる | Signalが届いたProto UUID、距離・列挙順、Signal位置、イベントtick | 近いProtoへ常に届くと前提化しない |
| G10 | 待機Calamityが0、1、2、4体、条件・地形・敵を固定 | Redirectの成否、Womb生成**試行**と実成功、Signal残存tick、资源消費 | 原作の50%判定と生成成功率は別 |
| G11 | Vigilのwave_sizeを制御し、召喚候補が有効/無効の2条件を準備 | SummonInfected実行、awardHivemind回数、実Spawn件数、退場時punishHivemind | 「加点=成功」は禁止 |
| G12 | SearchPosが到達不能、リーダー64ブロック超、死亡・unload・再接続 | PathNavigation更新、SearchPosの失効、Partner交換とtick負荷 | 旧tickの仮説と実動作を区別 |
| G13 | Proto 1/4/16体、Signal 0/1/10、Infected 0/100/1000の条件差 | Goal評価回数、エンティティAABBクエリ、平均/p95/p99 tick ms、chunk ticket、loaded chunks | Forge依存とLAB権限を固定。TPS・性能PASSは未報告 |

**現在:** この5シナリオのForge GameTest Javaコード/Observer未実装、Minecraft実行NOT_RUN。別の独立の数学テストPASSを本受け入れの合格へ転用しない。

### G12 判定条件の精密化（Bytecode/mapping訂正）

SearchAreaGoalの目的地判定は**中心から9ブロック未満**（Minecraft 1.20.1 `Vec3i.closerToCenterThan(Position,9.0)`）であり、Follower側の距離二乗9（3ブロック）とは異なる。G12ではSearchPosに対し9.1/8.9ブロック付近の境界を観測し、測距対象がBlockPosの中心であることも記録する。ゲーム未実施。

## G09〜G13 の検証器実装状況（2026-10-11更新）

[ランタイム観測ログのfail-closed検証器](RUN-EVIDENCE-GATE-2026-10-11.md) と [実装](tools/evaluate_spore_trace.py) が利用可能。Python 3.13.5で[15の合成テスト](tests/test_gates.py) PASS、[GitHub Actions](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/38081259925) もSUCCESS。

**限定的な進捗:** 観測されたイベントのrun・world・original JAR・行順序・最低限のシナリオカバレッジを判定できる。G09〜G13のForge実機用observer/Goal内フックはまだ存在しない。実ゲームからのデータがないため、全てのruntime assertionはNOT_RUNのまま。観測ファイルのorigin欄は自己申告であり、本来のLABの認証済み実行・cleanupの代わりにはならない。

原作JARの起動メタデータにも[依存テーブルの不整合候補](METADATA-AUDIT-2026-10-11.md)を発見。正式GameTest前にFMLの依存解釈・Forge実行条件を隔離環境で確認する必要がある。

## 2026-10-11 — 実装状態の更新

[Spore専用の独立Forge Observer](observer/README.md) はソース実装され、[GitHub ActionsでForge 1.20.1 APIのcompileJavaに成功](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/38082379417)。既存LABの実験契約に依存し、起動時にはロード済みSpore JARのhashとsession/world/seedを確認する。無許可のworldへ生成/攻撃/ブロック破壊を行わない。読み取り専用G13計測の観測コードとG09〜G12の状態snapshotコードがある。

新しい [G13 Java→JSONL→Pythonの合成600件テスト](observer/tests/G13SyntheticProducer.java) はローカルで出力判定がSYNTHETIC_FIXTURE_ONLY、runtime_pass=falseとなった。これはゲームの試験ではない。

従来の「Forge observer未実装」は上記実装に関する**過去の記載**として残す。**今なお未達**なのはSpore実ロードのForge専用サーバー起動、LABの承認済みsession/experiment、GameTestシナリオの実行、G09〜G12のメソッド単位の正確な観測、チケット/TPS/cleanupの認証である。

## 2026-10-11 — Goal登録・競合とG12実行中Goal観測

G12の実装補強として、[GoalRuntimeSampler](observer/src/main/java/org/kneekura/sporeobserver/GoalRuntimeSampler.java)で読み取り専用の`goal_registry_snapshot`（goal/target selector、priority、flags、isRunning、総件数と省略有無）を取得するコードを追加。

**新しい観測目的:** 同じMinecraftバージョン・条件・Mobごとに、静的372登録呼出から実際に有効化されたGoal集合を照合する。特にWitchの同priority4のMOVE/LOOK支援Goal、BruteのTARGET-only輸送Goalと交戦Goal、Infectedの優先度4のSearchArea/BufferAIを測る。

**不変の限界:** G12の`goal_registry_snapshot`はGoalSelectorの瞬間的な公開状態であり、canUseの実際の呼出、割り込み、衝突、故障時の経路更新を観測するイベントではない。G12の`search_goal_step`/`follow_goal_step`の境界証拠が揃わなければ結果はINCONCLUSIVE。Spore原作の実機ロード、registry/session権限、cleanupと負荷測定はいずれもNOT_RUNのまま。
