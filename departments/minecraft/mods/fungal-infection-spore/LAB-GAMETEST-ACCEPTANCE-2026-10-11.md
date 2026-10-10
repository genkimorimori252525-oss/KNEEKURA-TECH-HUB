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
