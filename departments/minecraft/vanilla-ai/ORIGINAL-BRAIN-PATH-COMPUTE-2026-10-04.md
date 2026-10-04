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

## Frozen native R55

producer **430ae2aa1fac73243cbc5629fbbf3a7b98c2f448**、run-20261004142827-8dfe72c3d237／sess-20261004142827-220fbcf9d7bf／snapshot-20261004142827-dd268907f224、process epoch1／Arena epoch0、private adult Villager UUID55555555-6666-7777-8888-000000000001です。元control85ファイルのcopyで同じfloor／照明／playerと自然day11850から進行し、desired result／Brain memory／navigationをseedしません。

2 complete compute groupsで**8新規events**（Finder／create／元field write／private compute各2）を取得しました。いずれもCHECK_EXTRA_START／INITIAL、返されたexact Pathは**canReach=false**ですが元private booleanは**true**でした。Finder→create return→元Sink.path代入→compute returnを、同じcompute/create/Finder ID、exact UUID、全run／session／snapshot／process／Arena／revision、gameTimeArgument、instanceIdentity、eventIndexと生のPath参照で照合しました。create時とcompute時のcached Navigation Pathはabsent、返されたPathとSink.pathは同じ参照です。座標からの同一性推定ではありません。

| compute invocation | game tick | source observation ID末尾（obs:forge-runtime:37948:）: Finder→create→write→compute | Path参照 | node count |
| --- | ---: | --- | --- | ---: |
| compute:1:1 | 40501 | 44 → 45 → 46 → 47 | path:1:4 | 10 |
| compute:2:1 | 41106 | 614 → 615 → 616 → 617 | path:2:5 | 14 |

private computeは開始条件内の呼出しのため、この2組に外側Sink／tick-stop IDは取得されていません。後続PATH write／Navigation moveTo各2件は別scopeの証拠として保持し、時刻や参照だけで新たな直接caller因果を作りません。brain_navigation単独のためgeneric search IDもNOT_CAPTUREDですが、実際のdirect Finder source正常returnは取得済みです。false private boolean／null／fallback RNG／TICK_RECOMPUTE／cached reuse／custom override／exceptions／各cap／rearmは今回のnativeで証明していません。

| revision | valid snapshots | 新規4種events | 全callbacks／payload bytes | Motion実サンプル | same-snapshot参照一致 |
| --- | ---: | ---: | --- | ---: | ---: |
| 1 | 124 | 4 | 256／333100 | 52 | 45 |
| 2 | 120 | 4 | 256／335192 | 83 | 75 |

全512callback／244snapshot、canonical **1,239 unique observations**はEVIDENCE_COMPLETE、SHA **af5ecb7ee1fa5ed6ce92cfba1a1ac237e86bef9e31ad707b00116e4f45b4a126**、finalization SHA **a0ae4e1c388eae36478e6a3b6ab8d3dd1f6930b7472fe627143c8c85a995ebef**。200 ticks／256 events／524,288 bytes／32 nodesの既存上限を維持し、両窓はEVENT_BUDGETで閉じました（local101..301／721..921 exclusive）。実際の全callback prefixはrevision1: 40501..40563、revision2: 41106..41168です。snapshotの取得期間を全callback windowの完全観測として扱いません。135 Motion実サンプル／120 same-snapshot PATH・Navigation参照一致は別の事実です。新しいcompute4種のpartial groupは0ですが、件数上限以後の全種類の未取得tailを正常／失敗や未呼出しと補いません。

clean ACK／drop0／queue0／finalWriterSeq1239、owned launcher41028／runtime37948のOS上の終了、元／control／predecessor R54／baseline各85ファイルのhash不変を確認しました。MOD53a84の8,444 precompiled filesと149 compile artifacts＋2 output roots／TFのhashを保全しました。元save、JAR、source body、private runtime dataはGitHubに追加しません。

JFR設定34,835 bytes／SHA d4d74f3594bfe342397f53aaa75a7551e7b2d9ac6f86c7ca2bc016690501b37dを起動前に照合し、actual start／stop ACKと保存fileのJDK parseを確認しました。JFR **3996462 bytes**／SHA **5f19f6ac0cc94520ce5a29557df9512bc0d50d133f712701b7d43dbf3d0b0b32**、63秒／ExecutionSample350／CPULoad60／ThreadCPULoad437です。単独記録であり、matched OFF／GPU・pixels／observer-effect受入ではありません。以前のR51未取得を含む記録を保全します。

## Source／fixture／hosted CI

最終sourceでMotion／Decision **169件成功**、allbridge／Mixin／combined API、実際のproduction Gson→strict JavaScript **59ケース成功**を確認しました。null初回＋reached短絡、Finder／create元例外の同一性、OFF／thread／selectedowner／cachedNavowner／revision／時間／event／byte／writer、8depth／256compute IDs／8create tail／128components／256shared Path参照、unknown subclass、nonfinite fallback primitive、detachとrearmを検査しました。compiled exact7 boundaryのdescriptor／target／require1、2AFTER PUTFIELDのordinal0/1／opcode181、1private Invokerと2single delegatesを検査しました。旧17条件／dispatch、39stop、24Brain Navigation、11Nav、14activityのGsonを維持しました。

producer CI push **37209374193**／PR source **37209377556**／pytest **37209377557**はSUCCESS。actual PR checkout merge **ed2e09d9f12896b973ae07b3afaff1e835370a77** の親は57e52f9ef44c082daf7abbb0b0f5ada3a258a406、430ae2aa1fac73243cbc5629fbbf3a7b98c2f448。169 focused／59 actual Gson markers、完全LAB source suite／portable Java／pinned MOD compile／dependency／resource／unit gatesを確認しました。hosted pytest最終行は **2026-10-04T14:33:50.4787411Z 3149 passed, 332 skipped, 8 warnings in 292.31s (0:04:52)**。document publication HEADのCIは別に確認します。

## 残る検証

元private reachedTarget／canReachの実際の呼出しbooleanと内部operand、開始条件→compute→後続PATH write／Nav採用のdirect outer scope、完全fallback RNG／false／cached reuse／TICK_RECOMPUTE、全Path候補・拒否・cost・malus、完全Brain理由／到着、全Vanilla・FRONTIER・community、広いBoss戦、matched observer-effect／GPU・pixels、live Tank resize、section21全受入、最後のwhole-diff独立レビューは残ります。Draftと全体goalを継続します。
