# 元のBrain private経路計算と実際のPath格納

既存のdefault-OFF brain_navigationで、固定Minecraft 1.20.1 Forgeのexact MoveToTargetSinkを選択した場合だけ取得します。元checkExtraStartConditions／tickのprivate tryComputePath呼出しをexact Mixin Invokerで1回実行し、try/finallyで例外、再選択、未知のnested呼出し後のframeを解放します。元private methodのpublic化、predicateの再実行、元field writeの置換は行いません。

元のbooleanはcanReachや到着と異なります。初回createPathが非nullならcanReach=falseでもtrueです。元reachedTargetがtrueならPath非nullでもfalseです。元WT tracker／speed／closeEnough getter、Brain query／erase／write、Path.canReachとDefaultRandomPosを観測のために呼び直しません。初回nullで未到達の場合だけ元getPosTowardsが実行され、vector非nullの場合に元final createPath(DDDI)がvirtual BlockPos overloadへ委譲します。内部RNG回数や全fallback分岐のnative受入は別途必要です。

4種の証拠を分けます。

- BRAIN_PATH_FINDER_RETURN: 元base Navigation.createPath内の実際のpublic virtual Finder.findPath正常return。正しいcached Finderと選択ownerだけをdirect source scopeへ接続します。
- BRAIN_PATH_CREATE_RETURN: 元private computeが呼んだ初回virtual BlockPos/Iまたはfallback final DDD/Iの正常return。実際の引数と返されたPath、cached Navigation Pathとの生の参照一致を保持します。
- BRAIN_PATH_COMPUTE_PATH_WRITE_CHECKPOINT: 2つの元Sink.path PUTFIELDのAFTER。代入自体は元の処理で、取得されたcreate returnとの生の参照一致を保持します。
- BRAIN_PATH_COMPUTE_RETURN: 元private computeの最終boolean。Path.canReach、Navigation採用、到着成功へ変換しません。

各compute ID内のcreate ID／Finder IDは実際の呼出し範囲で生成します。Sink／tick-stopのIDは既に取得されている同じowner／Brain／Navigationの外側scopeに限り保持し、直近時刻から親子を補いません。既存path系channelも明示ONの場合だけ、同じ実際のFinder source call内で取得したsearch IDをpathEnd前に保持します。空のFinder ID listは取得がないという意味で、search未実行の証明ではありません。返されたPath、Sink.path格納、後続Brain PATH write／Navigation moveToは別々の処理です。base Nav.createPathには直接Nav.path writeがなく、cached reuse／早期null／custom overrideもあるため、座標の一致から採用やsearch起源を推定しません。

create／compute／Finder returnはEVALUATION、実際のfield writeはEXECUTION、brain_navigation coverageはPARTIALです。candidate／selection／到着RESULTは生成しません。未知のPath subclassの内部はNOT_EXPOSEDです。base-known BlockPosの引数はcached Vec3i fields、DDD引数は渡されたprimitiveだけを保持します。非finiteはunknown、custom target Setの内容を反復・queryしません。観測時点のPath事実はdetachしたcopyで、返却後の変更とは区別します。

selected UUID／server thread／cached Brain・NavとNav owner、全run／session／snapshot／process／Arena／revision／時間／event／byte／writerを制限します。compute256 IDs／depth8、source create8とFinder8の有限list、component128、既存Snapshot Path参照256を維持します。取得できない後のcreateは以前のreturn relationを消し、誤接続を防ぎます。既存200 ticks／256 events／524,288 bytesを広げません。observerCostNanosは従来どおりrecordのbuildと最初のbyte checkのみで、frame／引数の事前取得やwriterを含む総費用ではありません。

[追加ledger](BRAIN-PATH-COMPUTE-BYTECODE-LEDGER-2026-10-04.json)はsame mapped artifactの3 owners／18 methods／9 fieldsをJDK、class、disassembly、27 member sliceのhashとdescriptorで保持します。ledger SHA **f553c2d246f5480a38ba4e83b4abb595020687ba0ecea5103aa916b9ac9c36fb**。旧ledgerは保持します。private tryComputePathの2 source calls、2create calls、2PUTFIELD、base NavigationのFinder source callが対象です。

元private methodでnonnull-unreachable=true／already-reached=falseとgetter・query回数を確認した後、未実装return receiptのREDを再現しました。genuine private bytecode fixtureではprivate access、観測source delegateとAFTER writeだけを試験用に置換し、元のbooleanと短絡評価を保ちます。productionのreflection writeやinstalled native証明には置き換えません。scripted Nav/Finder、synthetic fallback primitive／cap fixtureは内部RNGや本物の経路探索の完了証明ではありません。

## 次の検証

Motion／Decision169件、actual Gson59件と全bridge／combined APIを最終確認してから、frozen producer／private自然進行Villager／installed Mixin・直接caller-result／JFR ack・parse／canonical／clean stop／各85hash不変／exact HEAD CIを取得します。このsource段階ではnative未検証です。完全Path候補・拒否・malus・cost、全Brain理由／採用／到着、全Vanilla・FRONTIER・community、広いBoss戦、matched OFF／GPU・pixels、live Tank resize、section21全受入、最後のwhole-diff独立レビューは残ります。Draftと全体goalを継続します。
