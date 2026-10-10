# Spore 2.2.0j — Hivemind学習・複数指揮官・資源・性能の追補監査

**日付:** 2026-10-11 (Asia/Tokyo)  
**状態:** IN_PROGRESS / 選定Bytecodeを再読して成立する範囲のみ MAPPED。原作ゲーム実機・FPS/TPS・対戦学習の有効性・公式配布とのバイト一致は NOT_RUN / NOT_VERIFIED。

## 調査範囲と証拠

- 対象: user-provided spore_1.20.1_2.2.0j.jar、Minecraft 1.20.1 Forge、JAR SHA-256 **d20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489**。
- 参照: [研究入口](README.md)、[前回のHivemind静的解析](HIVEMIND-AI-BYTECODE-2026-10-11.md)、[原本receipt](ARTIFACT-RECEIPT-2026-10-11.json)。
- 使用: OpenJDK 21.0.12.1 の javap -p -c -constants、JAR内選定クラスを直接読取。**バージョン固有のSRG/難読化メソッド名を含む**。Minecraft 1.21.1 NeoForge版は未確認。
- 対象クラスハッシュと今回のスコープは [BYTECODE-CONTINUATION-RECEIPT-2026-10-11.json](BYTECODE-CONTINUATION-RECEIPT-2026-10-11.json) に記録。JARやデコンパイルした第三者コードは公開しない。
- 原典探索: [公式系WikiのProto](https://www.fungalinfectionspore.wiki/mobs/organoids/proto-hivemind)、[Linking & Signals](https://www.fungalinfectionspore.wiki/systems/linking-signals)、[Womb](https://www.fungalinfectionspore.wiki/mobs/organoids/womb)、[CurseForge](https://www.curseforge.com/minecraft/mc-mods/fungal-infection-spore)。WikiはBehaviourHintであり、技術的結論はこのJAR側で照合する。2026-10-11閲覧、サイトの原HTTPバイトとSHAは取得していない。

## 1. 重大な静的な不整合候補：メンバー評価の誤帰属

**直接観察**: com/Harbinger/Spore/Sentities/Organoids/Proto.class の summonMob(int,BlockPos)。

1. 入力intは **部隊決定番号 j**、getDecisionList(j) で部隊のMob候補を取得。
2. RandomSource.nextInt(list.size()) で別の局所変数 **実際の抽選位置 k** を選ぶ。
3. entityResourceLocation(k,list) によって選ばれた種類の個体を生成。
4. 生成個体のpersistent NBTに hivemind = Protoの整数Entity ID、decision = **j**、member = **j** と書く。**memberに k は渡されていない**。
5. com/Harbinger/Spore/sEvents/HandlerEvents.class の DefenseBypass(LivingDamageEvent) と BaseEntities/Organoid.class の awardHivemind/punishHivemind はタグ decision/memberをそのままProto.praisedForDecision(j,member) / punishForDecision(j,member) に渡す。
6. Proto.awardMember と punishMember は、memberを **getDecisionList(j) のリストインデックス** として扱う。

**結論**: Mobが実際に選ばれた候補番号 k と、評価に利用される番号 j が一致する保証はない。4候補均等抽選かつ有効な4人部隊という限定条件では、任意のjについて **4通り中3通り (75%) で個体固有の評価先が異なる**。これは「原作コード中のデータフロー不整合＋数学的帰結」であり、実ゲームでの悪影響再現は**未実施**。

部隊行jの重み自体はdecision番号jを受け取るため、その選好更新が違う部隊へ入るわけではない。ずれるのは**部隊内の個体候補の報酬/罰則帰属**。試験時は生成された実Mob種と、報酬を付けた/置換した候補を突き合わせる。

## 2. 学習器の表現力・報酬の偏り・非有界補正

**Proto.inputs(LivingEntity):** 4 binary features = 「targetとの距離二乗 < 200」「接地」「標的の**最大**HP >= 20」「防御力 >= 20」。nullは[1,1,1,1]。これは連続距離や現在HPをそのまま学習するものではない。

**Proto.decide(double[]):** 部隊j（0..3）について score[j] = Σ(i=0..3) weights[4j+i] * inputs[i]。argmaxの同点は先に現れた添字0を保持する。

**Proto.adjustWeightsForDecision(j,delta):** 選択行の4値をそれぞれ delta 加算し、各々 [-1,1] へclamp。praisedForDecisionは +0.05、punishForDecisionは -0.1。clamp前なら負報酬1回は正報酬2回と等量。イベント発火回数に対して重みが動き、命中ダメージ量の大きさが更新値へ掛けられているわけではない。

- clampを踏まない範囲では、部隊jへの評価がその部隊スコアへ与える変化は **Δscore[j] = delta * Σ inputs[i]**。**どの特徴量に対して成果が得られたかを選んで学習する更新ではない**。
- inputs=[0,0,0,0] の場合、全スコアが0で固定となり argmax はj=0。標的が遠い/空中/最大HP20未満/防御20未満など条件がすべて0となる例で、重みの違いはその判断に影響できない。成立条件は個別の全4判定を満たすことであり、この場面のゲーム内頻度は未測定。
- **Proto.moraleBoost() は特別**：16重みのうち **9個以上が負**なら、すべての重みにそれぞれ RandomSource.nextDouble() を加える。**この処理に [-1,1] clampは無い。** 原作の一般的説明「すべての重みは常に-1〜1」は正しくない。Proto.tick(m_8119_) の1200tick条件で呼ばれるため、条件成立時に60秒相当の全体補正が発生し得る（20TPS換算）。通常重み学習とは別の復帰/補正機構と分類する。
- Proto.praisedForDecisionは20%で awardMember（現在の候補をteam_5のfavoritesへ追加）、punishForDecisionは5%で punishMember（候補を除外し、favoritesやconfigから代替を探す）。**どちらも前節のmember位置不整合の影響候補**。

これらの静的な性質は、モデルの学習効果・強さ・FPSを証明しない。長期間の出力の偏り/補正頻度はシードを制御した独立モデル比較やMinecraft実機で確認する。

## 3. 複数Protoの共有データと局地AI

**SporeSavedData.class**:
- static protos: ArrayList<Proto> を持ち、addProto / removeProto / getHivemindsを公開。**この登録リスト自体はSavedData NBTへ保存されない**。
- **HandlerEvents.onLivingSpawned(EntityJoinLevelEvent)** はServerLevelのProtoを上記staticリストに追加。
- **HandlerEvents.DiscardProto(EntityLeaveLevelEvent)** は離脱したServerLevelのProtoを除外。
- SporeSavedDataの実際の保存対象は別の ChunkRequests であり、Proto.weights はProto個体の NBTで別保存される。

**結論**: 活動中Protoの共通登録と、各Protoの学習重みは別の状態。リストのstatic宣言はディメンション横断の活動個体参照を示すが、**すべてのProtoが一個の重み行列を共有することは示さない**。チャンクunload/reload時の追加・削除順序、別ディメンション、クライアント/サーバーでの同期挙動は実機未検証。

**命令:** 実際のProtoTargeting.classの正確なパスは **com/Harbinger/Spore/Sentities/AI/NeuralProcessing/ProtoAIs/ProtoTargeting.class**。旧解析メモの「AI/LocHiv/ProtoTargeting」は誤ったパスであり、ここで訂正。LocalTargettingGoalはAI/LocHiv/LocalTargettingGoal.class。ProtoTargetingはProtoの生存標的をproto_rangeで囲むAABB内のターゲット未設定Infectedへ渡す。LocalTargettingGoalはInfected同士で目標とSearchPosを移す。

**帰属ID:** Proto.summonMobは数値のEntity IDをpersistent NBTに書き、HandlerEventsは元MobのLevel.getEntity(int)でProtoを解決する。Protoがunloadされた場合や再起動後のID再割当での帰属成功/誤帰属は**未検証**。将来の独立設計ならdimension＋UUID＋generation/epoch＋保存時刻＋失効処理を比較候補にする（原作に搭載されているという意味ではない）。

## 4. 戦場の資源収支：バイオマスが負数になり得る

**Proto.m_8119_ の200tick毎の分岐**：有効ターゲット、周辺Organoid数 <=4、biomass >2 等の条件が通ると、ランダムに **1〜5回** summonMob を呼ぶ。**資源の閾値をチェックするのはループ前**で、各回の入口に再チェックがない。

**Proto.summonMob** で位置/地形条件が通るごとに eatBiomass(2) を呼び、個体生成へ進む。**Proto.eatBiomass は現在値から引くだけで0下限へのclampはない**。

例：ループ開始時にbiomass=3で5回の召喚が成功したと仮定すると、3-5×2 = **-7**。これはコード上の可能性で、出現状況・確率・地形条件に制限される。公式系[Wikiでも負のBiomassに関する同様の挙動を記述](https://www.fungalinfectionspore.wiki/mobs/organoids/proto-hivemind)しているが、論拠はJAR自身。ゲーム内の頻度は未測定。

## 5. 推定負荷面の監査：サーバー処理をtick頻度で整理

**Proto.m_8119_ のSERVER側条件別呼び出し**（ModuloはEntity tick counter、必要なconfig/ターゲット/ノード/信号条件を満たす場合のみ）。

| 呼出周期 | 候補操作 | 負荷上の観点 |
| --- | --- | --- |
| 40 ticks（20TPSで2秒） | griefBlocks、ターゲットとScentチェック | ブロック読書き/エンティティ更新、設定に依存 |
| 200 ticks（10秒） | addBiomass(1)、generateCasing(config)、攻撃対象がいる場合の召喚波 | ブロック設置、1〜5体の条件付spawn、負資源 |
| 1200 ticks（60秒） | scanForHosts、moraleBoost | proto_rangeのAABB周辺Entity走査と16重み補正 |
| 3000 ticks（150秒） | giveMadness(config) | Entityステータス適用 |
| 6000 ticks（300秒） | SpreadInfection(config/node)、loadChunks | 地形改変/チャンク固定 |
| **Signal.activeの間は毎SERVER tick検討** | checkForCalamities → 条件次第でSummonConstructor（Womb） | proto_rangeのEntity走査; 必要な信号消費処理まで追跡。実コスト未測定 |

**ChunkLoaderHelper/ChunkLoadRequest**:
- Proto.onAddedToWorldからloadChunks、周期6000tickで同処理。proto_chunk設定で有効/無効が変わる。
- Proto.lambda$loadChunks$2 は UUID、現在のChunkPos、寿命12000tickを持つ **新しいChunkLoadRequest** を作る。
- 新しいrequestに対して ChunkLoaderHelper.ACTIVE_REQUESTS.containsValue(newRequest) を実行する。**ChunkLoadRequest.classはequals(Object)をoverrideしていない**ため、既存requestと値が同じでも通常のObject参照同一性でのみ一致する。毎回新規のオブジェクトなので、**この重複排除チェックは既存の同一内容requestを防止しない**。
- その後addRequestはrequest IDでMap.putし、forceChunkでticketを要求、SporeSavedDataへ保存。キーの重複が上書きされるため「メモリが無制限に増える」「確実にチャンクリーク」は未証明。**冗長な再要求処理の可能性**を性能監査候補にする。
- HandlerEvents.onServerTick(END)はChunkLoaderHelper.tickを**毎tick**呼び出し、活動中requestを走査してTTLを更新する。期限時は ownerUUID に基づく getEntity(UUID) が現在のchunkにいる場合に更新し、いなければunforce。World Load時にはSavedDataからrequestを復元してforceする処理が存在する。
- Proto死亡時はcleanupChunkLoadingでrequest削除を試みるが、死亡・通常despawn・ディメンション移動・サーバー停止の全ケースのcleanup完了はNOT_RUN。

**示したのは呼出密度/データ構造の監査でありTPS、メモリ、ネットワークのベンチマークではない。**

## 6. 次に検証するGameTest・限定シミュレーション

1. **個体評価の対応:** 4候補の部隊を固定し、j≠kとなる召喚を観測。帰属タグ、表彰/入替対象、選ばれたMob IDが一致するか。期待値の75%は4通り均等の静的数学であり、ゲーム実測ではない。
2. **学習の表現:** 输入[0,0,0,0]で必ずj=0か、各出力行を±更新したときの選択変化、9個負の場合のmoraleBoostとclamp逸脱。複数の初期シードで調査。
3. **複数Proto:** Proto A/Bが異なる攻撃を経験→重みが個体ごとに独立か、chunk unload/reload後のNBT保存、片方の死亡後の貢献タグが正しいか。
4. **資源の整合:** biomass=3など制御し、5候補waveと召喚成功/失敗を区別。negative資源・回復・保存を観測。
5. **負荷:** N=1,4,16 Proto、信号頻度/大量Infected/1200tickスキャン/チャンクチケットを変え、server tick cost、forced chunks、Entity数、network bytesとGCを測る。
6. **修正/履歴:** 原作者の2.2.0jに対応する公開ソースは確認できていない。配布版間JAR差分や作者Issue/PRは未固定。今は**BUG_CANDIDATE**であって修正済み、不具合再現済みとはしない。

## 7. 技術回収候補（独立設計）

- TacticalPolicyは特徴ベクトルを受けて部隊を選ぶだけ、Unit Controllerは経路/射撃を担当、Report Routerは単位ID・部隊ID・実個体ID・発行世代に対する戦果を検証して戻す。
- 目的別Reward（命中回数・有効ダメージ・資源消費・戦略目標達成）を別の重み付けで研究。Sporeの+0.05/-0.1を一般的な正解として採用しない。
- 任務予算（生産上限・資源非負・チケット件数・tickコスト）を指揮系と分離。1体の責任範囲を有限にし、ディメンション/チャンクの境界に強いUUID参照と失効を使う。
- 世界規模のDirectorと各局地Proto相当のCommanderを分離。複数指揮官の学習を共有するかはアブレーションで決定し、原作に既にあると主張しない。

**Facet状態:** 原作ANCHOR選定クラスのBytecodeは DIRECT_BINARY/MAPPED。モデルの勝率・マルチプレイ・FPS/TPS・チャンク復元・全クラスの意味解析は NOT_RUN/NOT_COMPLETE。TECH-HUB CoreへのCANONICAL/VALIDATED昇格はしていない。
