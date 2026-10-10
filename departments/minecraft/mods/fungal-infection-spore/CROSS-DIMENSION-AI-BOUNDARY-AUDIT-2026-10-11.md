# Spore 2.2.0j — ディメンション境界と群体指揮・チケット管理の静的監査

**2026-10-11 | ANCHOR: Minecraft 1.20.1 Forge / 原作Spore 2.2.0j | DIRECT_BINARY/MAPPED + BUG_CANDIDATES | Runtime NOT_RUN**

## 0. 原本と変更禁止の境界

原本 JAR SHA-256: d20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489（ユーザー提供、配布版とのbyte-equivalenceは未確認）。[ARTIFACT-RECEIPT](ARTIFACT-RECEIPT-2026-10-11.json)、[選定クラスのハッシュ記録](BYTECODE-CONTINUATION-RECEIPT-2026-10-11.json)。JDK javapでoriginalのclass bytecodeを直接読む。原JAR/音声/PNG/decompile全文を公開Gitへ保存しない。1.21.1 NeoForge版FRONTIERは今回対象外。

## 1. Proto World Modifier — 原作コードとWikiのディメンション境界が異なる可能性

[コミュニティWiki: Proto Hivemind](https://www.fungalinfectionspore.wiki/mobs/organoids/proto-hivemind) §Proto World Modifier は「任意のディメンションで最低3体」と説明する（2026-10-11閲覧の**探索ヒント**）。

**Bytecodeで確認した経路:**

1. com/Harbinger/Spore/ExtremelySusThings/SporeSavedData.class は **static final List<Proto> protos** という**レベル別でない静的リスト**を持つ。addProto(proto)はこのリストに無条件追加、removeProto(proto)は削除。getAmountOfHiveminds()は protos.size() を返す。パラメータにレベル/ディメンションがない。
2. com/Harbinger/Spore/sEvents/HandlerEvents.class の onLivingSpawned(EntityJoinLevelEvent) は、ProtoかつServerLevelであれば addProto を呼ぶが、levelのディメンションはリストの区分キーへ格納していない。DiscardProto(EntityLeaveLevelEvent)も同じ一括リストから削除する。
3. com/Harbinger/Spore/Core/SConfig$Server.class の proto_spawn_world_mod デフォルト値は **3**。
4. com/Harbinger/Spore/Sentities/BaseEntities/Infected.class の setDefaultLinkage(ServerLevelAccessor)、Sentities/Organoids/Mound.class の setDefaultLinkage(Level)、Sentities/BaseEntities/Calamity.class の setDefaultAdaptation(ServerLevelAccessor)、Sentities/BaseEntities/Hyper.class の m_6785_(double) が、各自のServerLevelのSporeSavedData.getDataLocation(level)を取り、非nullならその **getAmountOfHiveminds()** を上記設定値と比較。実際のカウントはinstanceとは独立のstatic global listの.size()である。

**静的な帰結:** Aディメンション2体 + Bディメンション1体が同時に有効なら、静的リスト数は3。各レベルのSavedDataが存在し適切なタイミングで評価すれば、**同じディメンションには3体いなくても** 上記の閾値判定を通過できる。これはバージョン2.2.0jのコードの条件から導けるもので、実際の現象の再現はまだない。

**明記する制約:** 全server tick/異次元移動でいつjoin/leaveイベントが発火しリストが何体になるか、WorldSavedDataが非nullか、具体的なMob/防具/チャンク条件などで結果は異なる。これを「確実に全ディメンションが常時強化される」と表現しない。Wikiの説明は版・実測が未特定で、コードを優先しつつ不一致を記録する。

## 2. チャンク復元ループにディメンション照合が無い

**Bytecodeの独立した連結した経路:**
- SporeSavedData.classの **static Map<String,ChunkLoadRequest> activeRequests** は全レベルで共通。getRequests()は static map.values()、m_7176_ (NBT save) はこのstatic mapの全エントリを列挙して書く（レベル単位filter無し）。load(CompoundTag)はそのファイルにある要求を同じstatic Mapへput。
- HandlerEvents.class **onWorldLoad(LevelEvent.Load)** は、**現在読み込み中のServerLevel**をローカル変数に保持し、SporeSavedData.get(currentLevel).getRequests()の**全件**を巡る。
- 各要求のChunkPosから、**ChunkLoaderHelper.forceChunk(currentLevel, pos)** を呼ぶ。request.getDimension() / request.dimensionの照合・フィルターはこのループにない。
- もっともChunkLoadRequest.class自身はResourceKey dimensionを保持し、NBTにDimension文字列を書き込む。request.getDimension()はcurrent serverを参照し、dimごとのLevelを解決できる。つまりディメンション情報は存在するがworld-loadループで使用されていない。

**静的帰結（要実機検証）:** ChunkLoadRequestのstatic表に複数ディメンションの要求がある場合、あるディメンションがロードされた際に**別ディメンションから来たChunkPosの座標を、現在のレベルでもforceする**可能性がある。複数ディメンションのSavedDataに同じ要求が混在保存される可能性もある。どのようなタイミングで重複が発生し、実チケットが長期間残るかは未測定。

## 3. 既存のrequest重複排除問題と結合した負荷の計測候補

- [前回の静的監査](HIVEMIND-LEARNING-LIFECYCLE-AUDIT-2026-10-11.md)で、Protoが新規に生成するChunkLoadRequestに対し Map.containsValue(newRequest) を使っているが、ChunkLoadRequestにはequals/hashCodeのoverrideがなく、実値同等の旧要求が見つからない可能性を記録済み。
- ChunkLoaderHelper.addRequestはIDをキーにMap.putしforceChunkを呼ぶ。キーの上書きがあるため、件数の無制限増加は**静的コードだけでは主張不可**。
- ChunkLoaderHelper.tickは ACTIVE_REQUESTS の全エントリをサーバーtickごとに走査し、期限を減らし、更新または削除する。コードパスの仕事量はエントリ数に対してO(N)だが、**実TPS・チケット過剰・不要読み込みの有無は未計測**。

## 4. 実際に検証するべきシナリオ

1. D1=OverworldにProtoを2体、D2=Netherに1体配置。各ディメンションでInfected/Mound/Calamityのspawn直後のLinked/Adaptationフラグを観測し、D2のProtoがいない1+2以外の対照群と比較する。
2. D1にProto由来チャンク固定要求を作り、D2 level loadを発生させる。SporeSavedDataのrequest ID/dimension/chunk、ChunkLoaderHelper.ACTIVE_REQUESTS、各ServerChunkCacheのticket数、D1/D2のloaded chunkを比較する。
3. 自動リクエスト更新・owner消滅・死亡・reloadで、チケットが解放されたかを実際のServerLevelごとに測る。
4. 試験はTECH-HUBの隔離LAB/ダミーworldに限り、テスト終了時にforce-chunk/AI/ワールドのcleanupを確認。**今回は実行していない。**

## 5. より良い独立指揮設計への回収

- FactionDirectorとCommanderPoolは **Dimension/Server/Owner UUID**を明示的に区分して、部隊ごとの学習、指令・生息地・観測範囲を分離する。
- WorldSavedDataは保存対象のdimensionだけを書き、要求キーにdimension+owner+chunk+epochを含める。データのロード時は保存済みdimensionを照合する。
- 指揮官不在・ディメンション移動・ロード/アンロード・World保存/復旧で命令とchunk ticketsを原子的/冪等に扱う。設定されたresource budgetとload expiryを毎tick監査する。
- これは**原作Sporeからコピーした実装ではない独立設計案**。Mono-runtime性能や効用は未実証。

**証拠状態:** DIRECT_BINARYはJAR内の実クラス構造と呼び出し条件。矛盾するWikiはBehaviorHint。複数ディメンションでのゲーム挙動は NOT_RUN / BUG_CANDIDATE。公式配布とのバイト同一性、FPS/TPS、外部Issueでの修正履歴はNOT_VERIFIED。旧版と最新FRONTIERを混同しない。
