# Fungal Infection: Spore — Hivemind AI / Group / Combat bytecode 2026-10-11

**状態：選択メソッドの静的解析（MAPPED / DIRECT_BINARY）。実機NOT_RUN、全1,350クラス解析COMPLETEではない。**

## Artifact とトラック

- 原本：ユーザー提供 spore_1.20.1_2.2.0j.jar（116,439,461バイト）。
- SHA-256：d20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489。
- META-INF/mods.toml：Spore 2.2.0j、Harbinger、javafml [47,)、Minecraft 1.20.1、All Rights Reserved。
- ZIP総entry 3,850、非directory 3,692、class 1,350、JSON 1,130、PNG 809、OGG 346。JDK javap -p -c -constants で関連183クラスのdumpを取得し、そのうち下記の主要処理を詳読。
- ANCHOR：1.20.1 Forge（当該アップロードのバイナリ）。FRONTIER：1.21.1 NeoForge公開版はメタ情報のみで未調査。アップロードJARと作者配布ファイルのbyte-equivalenceは未確認。
- 原JAR・Java decompile全文・画像・音声をGitHub公開履歴へ保存しない。詳細は [ARTIFACT-RECEIPT-2026-10-11.json](ARTIFACT-RECEIPT-2026-10-11.json)。
- 分析原則：[ANALYSIS-WORKFLOW](../../ANALYSIS-WORKFLOW.md)、[ANALYSIS-SPEC](../../ANALYSIS-SPEC-v1.md)、[AI研究手順](../../../ai/RESEARCH-WORKFLOW.md)。技術の確認とゲームでの実行を混同しない。


### 2026-10-11 継続監査の入口と訂正

[最新追補：複数Proto、学習の誤帰属、moraleBoost、Biomass、chunk tickets](HIVEMIND-LEARNING-LIFECYCLE-AUDIT-2026-10-11.md) および[選定11クラスの原本内SHA-256](BYTECODE-CONTINUATION-RECEIPT-2026-10-11.json) を参照。

この文書のProtoTargetingのクラス所在を修正：実JARの正確なパスは Sentities/AI/NeuralProcessing/ProtoAIs/ProtoTargeting.class であり、LocHiv配下ではない。またProtoの学習時 [-1,1] clampには、別の moraleBoost メソッドからの**非clamp加算**という例外がある。更新則の限界と異なるMob候補への誤評価の可能性は上記追補が優先。

## 1. 真の「軽量に学習するHivemind」：Proto

**ソースの同定**：com/Harbinger/Spore/Sentities/Organoids/Proto.class。
原作2.2.0jの実Bytecodeから、単なる紹介文ではなく4入力×4出力の**線形部隊選択器と報酬・罰則更新処理**を確認した。

| メソッド | Bytecodeで確認した動作 |
| --- | --- |
| initializeValues | weights double[16] に RandomSource.nextDouble で初期値設定。team_1～team_4 は SConfig.SERVER.proto_summonable_troops の候補から準備。別にteam_5も保持 |
| inputs(LivingEntity) | 4つの0/1入力：1.標的とProtoの**距離の二乗 < 200**、2.onGround、3.**最大HP >= 20**、4.armor >= 20。標的null時は全て1 |
| decide(double[]) | 各j=0..3について score_j = Σ(i=0..3) x_i * w_(4*j+i)。最高得点のjをargmaxで選択 |
| getDecisionList | j=0,1,2,3 をteam_1,team_2,team_3,team_4へ対応づける |
| summonMob | 決定したリストからMobをspawnし、個体のpersistent NBTに hivemind（元Protoの**実行時Entity ID**）、decision、member を保存するコード経路 |
| adjustWeightsForDecision | 選択したjの4要素を同じdeltaだけ加減、各値を[-1,1]に制限（clamp） |
| praisedForDecision | +0.05で重み更新、確率0.2でawardMember。 |
| punishForDecision | -0.10で重み更新、確率0.05でpunishMember。 |
| NBT save/load | m_7380_ / m_7378_ でweightsと5つのteamリストを保存・復元 |
| entity tick | m_8119_ には200tick単位の条件付きinputs → decide → summonMob経路、他にも40/1200/3000/6000tickごとの拠点・菌類処理 |

**重要な境界**：
- 4入力は独立の2値特徴。体力の入力は現在HPではなく**最大HP**である。距離条件の200は距離そのものではなく二乗値。
- 各重みの更新は**選ばれた出力行に対する一律オフセット**であり、特徴ごとに別の誤差逆伝播をするわけではない。重みの選好を適応させる軽量ルールである。
- 重みはProto個体にNBT保存される。全てのHive同士の重み共有や、子Protoへ重みを「遺伝」させることは確認できていない。
- Protoから発行された数値Entity IDの参照がチャンクunload/reloadやserver再起動後に正確に続くかは未検証。最適化案としてUUID+dim+epoch参照を別設計とするのは有用だが、原作コードの実装事実ではない。

### 1.1 実際の戦闘フィードバック経路

**com/Harbinger/Spore/sEvents/HandlerEvents.class — DefenseBypass(LivingDamageEvent)** では：
- ダメージ加害側のTagged Mobが参照するEntity IDを解決し、Protoなら praisedForDecision(decision, member) を呼ぶ。
- 被害側がHivemindタグを持ち、対応するProtoを解決できるなら punishForDecision(decision, member) を呼ぶ。

さらに **Sentities/BaseEntities/Organoid.class — awardHivemind / punishHivemind** からもProtoの該当メソッドを呼ぶ経路が存在する。sEvents/Infection.classにはawardHivemindを使う経路がある。

従って「部隊を選んでspawnする → 与ダメージ/被ダメージの結果で重みを更新 → 次回の部隊選択に影響」というデータ経路が**元のJARの中で確認できる**。ただし「戦争に勝利した/占領に成功した」の報酬ではない。Forge eventの全場面実行回数、ゲームでの学習速度、勝率はNOT_RUN。

## 2. 群れ・上位個体のターゲット配布

| クラス・メソッド | 原作JARからの確認 |
| --- | --- |
| Sentities/AI/NeuralProcessing/ProtoAIs/ProtoTargeting | Protoの標的を近くの Infected へ渡す。config proto_rangeに依存する |
| Sentities/AI/LocHiv/LocalTargettingGoal | 近くの未ターゲットInfectedへ現在の標的やSearchPosを伝播。AABB拡張距離最大32。確率条件あり |
| Sentities/AI/CalamitiesAI/CalamityInfectedCommand | Calamityを中心にAABB拡張32で感染Mobを列挙し、標的やSearchPosを渡す。起動には乱数0/100と標的/探索位置条件を使う |
| Sentities/AI/LocHiv/FollowOthersGoal | SEARCH_INTERVAL 20、FOLLOW_DISTANCE 32、STOP_FOLLOWING_DISTANCE 3、TELEPORT_DISTANCE 64等を含む。全分岐・到達率の詳細は未検証 |
| Sentities/AI/LocHiv/BufferAI | 個体のkills値等を参照し支援状態の付与/ポイント消費する。全軍共有学習を示すものではない |

**学習する上位個体、索敵を共有する上位Mob、単純な実行Mob、局地拠点が異なるコード面に存在。** ただしTECH-HUBのDirector→Commander→Unit 3層構造と完全一致すると主張しない。単なる同名Hivemindを外部LLM/APIで動かしている証拠もない。

## 3. 生産・資源と感染の循環

**Womb: Sentities/Organoids/Womb.class**
- tick m_8119_：BIOMASS >= SConfig.SERVER.reconstructor_biomass ならsummon。recontructor_clock*20 tickの内部カウンタを経てbiomass +1。
- nextInt(100)==0 で CallNearbyInfected、nextInt(40)==0 で AssimilateNearbyInfected を**試行**する。必ず100/40tickに一度とは言えない。
- CallNearbyInfected（server側）：自身のAABBを50拡張し、周辺 Infectedの setSearchPos をWombの座標へ設定。
- AssimilateNearbyInfected（server側）：AABB 0.1拡張のInfectedを見つけ、biomass += calculateAssimilation(mob) + mob.getKills()。対応レシピの有無を処理し、対象Mobをremove、血液パーティクル・音・eatingTicksを更新。
- **結論：仲間の再集合＋接触した個体を消費して資源回収＋閾値で新個体を生産**するコード経路を確認。

**Mound: Sentities/Organoids/Mound.class**
- AGE/COUNTER、SConfigのmound_age等で成長・SpreadInfectionを制御。SpreadKinにInfectionTendrilの生成経路。これは拠点の成長・範囲拡張であり、機械学習ではない。

**HiveTumor: Sentities/Organoids/HiveTumor.class**
- SummonProto(ServerLevel) に Proto entity生成経路、MobSpawnType.CONVERSION での配置、HiveTumorの退場処理。生成条件/閾値・頻度・実動作は未評価。

**Protoの広域コスト仮説**
- m_8119_ は他にも scanForHosts、moraleBoost、griefBlocks、loadChunks、Signalなどを別周期で呼ぶ。特にチャンクロード、広域のEntity走査、感染改変のTPS・ネットワーク費用は別途実機測定が必要。

## 4. 砲撃・群射・経路探索

**ScatterShotRangedGoal: Sentities/AI/CalamitiesAI/ScatterShotRangedGoal.class**
- m_8037_ は射程とLine-of-Sightを確認し、RandomSource.nextIntBetweenInclusive(minShots, maxShots+getExtraShots()) で発射数を決め、同じ攻撃更新内で RangedAttackMob.performRangedAttack(target, scale) を繰り返し呼ぶ。
- getExtraShots: SAttributes.BALLISTICが1以上なら(int)(3*attributeValue)、1未満または未設定なら0。
- これは**多発弾の発射タイミングのscheduler**。角度を扇状/円状にする処理をこのGoalで確認したわけではない。個体のperformRangedAttack/弾体クラスごとに軌道の追加調査が要る。

**経路探索**
- HybridPathNavigationやCalamityPathNavigation、ClimberNodeNavigatorなど移動様式別のサブシステムが存在。実際の移動費用や到達率はNOT_RUN。
- Sentities/AI/NeuralProcessing/Experimental/ExpPathFinder.class の m_77427_ は、実際にはvanilla PathFinder.m_77427_を呼び、非nullのPathをPatchedPathで包むコード。**パッケージ名NeuralProcessingだけでニューラル経路探索が稼働中と断定しない。**
- 原作JARにはProjectileパッケージにAcidBall、BileProjectile、ThrownTumor、FleshBomb等があるが、各軌道、角度、命中後の効果を全件回収・検証したわけではない。

## 5. 失敗履歴・専門コミュニティの手掛かり

公式：
- [原作者のSpore CurseForge](https://www.curseforge.com/minecraft/mc-mods/fungal-infection-spore)
- [コミュニティWiki](https://www.fungalinfectionspore.wiki/home)
- [Help Center](https://www.fungalinfectionspore.wiki/home/help-center) — griefing関連設定の探索ヒント

Issue：
- [Dynamic Trees Issue #1201](https://github.com/DynamicTreesTeam/DynamicTrees/issues/1201) はSpore 2.2.0j × Dynamic TreesのGargoyl関連クラッシュを2026-07-09に報告。**他プロジェクト側の報告であり、報告原因/修正/再現は未確定**。修正diffやランタイム検証を経ていないので本研究のFAILURE-REPAIR-HISTORY完成を主張しない。

Reddit上の感染進行・ラグ・ゲームバランス談はBehaviorHintとし、正確な版・投稿内容・実機プロファイラがない限り、JARの性能や動作を証明しない。

## 6. Parasites・Sculk Hordeとの比較（概念のみ）

| 原典 | 内部で確認済みの知能単位 | 持ち帰る独立技術 |
| --- | --- | --- |
| Spore 2.2.0j | Protoごとの小規模な4入力4出力の召喚選好、与被ダメージに基づく重み更新、周辺への標的配布 | ルールベースのTacticalPolicyとそのイベント配線 |
| [Scape and Run: Parasites 1.9.21](../scape-and-run-parasites/COMBAT-AI-BYTECODE-2026-10-11.md) | 攻撃種別の個体耐性と死亡時の群体メモリ集積・次世代への適用 | AdaptationMemory（ダメージ耐性） |
| [Sculk Horde公開ソース候補](../../../ai/multi-agent/MINECRAFT-MOD-SCOUT-2026-10-11.md) | GravemindがCombat/Infectorなどを選ぶ増援判断（元ソースの一部） | ReinforcementPolicy（敵の役割・資源配分） |

同じ「賢い群れ」でも**部隊の選び方、受けた攻撃への耐性、軍のリソース配分**は別機能。今は独立研究として保存する。コピー混合や製品移植が完了したと扱わない。

## 7. 未調査・次の証拠ゲート

| 面 | 状態 | 次に必要なもの |
| --- | --- | --- |
| 不変原本識別 | SHA/ZIP/metadata照合済 | 公式配布JAR SHAとの一致・依存関係の閉包 |
| Proto | 重要メソッドMAPPED | イベント呼出の全経路、保存/読込時のLink ID、複数Protoの学習分離を実機検証 |
| Womb/Mound/HiveTumor | 選定メソッドMAPPED | 植生変換/生成/死亡による連鎖、効果範囲、戦術的有用性 |
| Combat | ScatterShot schedulerの直接読取 | 各Mobの弾幕形状・攻撃時間・誘導性・被害・視覚効果のメソッド全回収 |
| AI navigation | クラスと選定メソッドの一部 | 目標更新、PathNode計算、チャンク境界、経路コスト |
| Release history | 1件の第三者Issue候補のみ | upstream Issue/PR・修正差分、正式なFAILURE-REPAIR-HISTORY |
| Runtime/Performance | **NOT_RUN** | 隔離されたForge1.20.1/LABで検証、TPS/メモリ/通信計測 |
| 全MOD | **IN_PROGRESS/NOT_COMPLETE** | 1,350クラスの必須facetと資産/モデル/パーティクル/音の証拠付き分析 |
| 1.21.1 NeoForge FRONTIER | **未調査** | 別原本の取得と互換性/差分分析 |

**証拠区分：** ここで列挙したメソッド経路は固定JARのDIRECT_BINARY。実際のゲーム行動/速度/性能はNOT_RUN。移植や一般化はDESIGN_PROPOSAL。AIは自分でCANONICAL VALIDATEDへ昇格しない。

## 8. 追補：HowitzerとFleshBombの標的依存攻撃

**直接確認した原作Bytecode：** Sentities/Calamities/Howitzer.class の m_6504_(LivingEntity,float)、compareEntity(LivingEntity,int) と Sentities/Projectile/FleshBomb.class の m_5790_ / m_8060_ / SummonInfected、FleshBomb$BombType enum。

| 対象 | 解析結果 |
| --- | --- |
| Howitzer.compareEntity | BASIC、FLAME、BILE、ACID、NUCLEARの5種から弾種を判断。入力はisRadioactive / hasNuke、標的の最大HP、armor、周囲4ブロック拡張AABB内の対象数、SConfigのcorrosionリストなど。 |
| Howitzer.m_6504_ | howit_ranged_damage × global_damageを計算し、選択したBombTypeと4..7の乱数を用いてFleshBombを生成。20%の確率でCarrierフラグを立て、発射速度の上下補正と投下音を設定。 |
| FleshBombのEntityHit | explodeCircleで範囲効果を起動。FLAMEなら着火系処理とブロック置換、BILEならBILEブロック変換、NUCLEARならNukeEntity作成などの分岐。 |
| FleshBombのBlockHit | 爆発処理、FLAME/BILEの地形置換、ACIDのsummonAcid、NUCLEARのNukeEntity分岐。Carrier=trueならSummonInfectedを呼ぶ。 |
| SummonInfected | SConfig.SERVER.howit_summmonsリストからランダム選択したEntityTypeを生成しServerLevelへ配置。 |
| FleshBomb.aimForTarget | 保持しているVec3位置への進行ベクトル補正。リアルタイムの生きた標的追尾と同義ではない。 |
| AcidBall | ブロック命中からplace_acidを呼び、条件に応じてSblocks.ACIDを配置。 |
| ThrownTumor | 着弾時、爆発・AreaEffectCloud・poison/bile/freeze/damageの分岐を持つ。 |

**到達可能性の留保：** Howitzer.compareEntityにはint引数が8を超える場合の弾種切替があるが、m_6504_はfloat引数をintへcastして渡している。通常の正規化距離値ならこの条件を満たさない可能性があり、実際に全弾種が使われるかは別検証。bomb種ごとの攻撃力・破壊範囲・連射密度・描画演出・TPSはNOT_RUN。
