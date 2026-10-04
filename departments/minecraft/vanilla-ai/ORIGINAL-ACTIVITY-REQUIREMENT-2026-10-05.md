# 元Activity要求Map・メモリチェックの直接source

[R50の元Activity更新scope](ORIGINAL-ACTIVITY-CALL-2026-10-04.md)内で、Brain.activityRequirementsAreMetが元activityRequirements Map.containsKey(Activity)とvirtual Brain.checkMemoryに実際に渡した引数・正常戻り値を記録します。private predicateへの元callはsetActiveActivityIfPossibleとsetActiveActivityToFirstValidの2か所にあり、各source-specific RedirectからInvokerで元private methodを1回実行します。元Map.get/Set iterator/Pair.getFirst/getSecond/first-falseとfirst-valid list short circuitを維持し、Map/Pair/slot/presence/getter/AIを再実行しません。新しいpredicate捕捉は直接のR50 ActivityFrameがある場合に限ります。

元MapにActivityがなければbase bodyはfalse、登録済みで要求Setが空ならtrueです。要求がある場合は最初の元checkMemory falseで止まります。Map membership、実際のcheckMemory boolean、private predicateの正常booleanは別々の事実で、custom virtual/Mixin結果をcached slotから再計算しません。数値priority/全候補/選択原因/internal slot理由を取得済みとはしません。

新しいBRAIN_ACTIVITY_REQUIREMENT_CHECKS_RETURNはEVALUATION/brain_activity/PARTIALです。既存ActivityFrame IDと新requirement IDは直接frameからリンクします。IF_POSSIBLE/FIRST_VALIDは実call siteです。元Map membershipと正常predicate boolean、最大8件の元checkMemory passed module/status/returned booleanを保持し、実9件目の正常returnでchecksTruncated=trueです。missing/empty mapはchecks空で正常receiptを持てます。Activity/moduleは有限raw identityだけをlabelし、未知/nullはNOT_EXPOSED。新しいgameTime queryや引数を作りません。旧R50/R57/R58/R59/compute/Sink payloadは不変です。

requirement IDs256/depth8/component128、既存200ticks/256events/524288bytes/32nodes、default OFFを維持します。現在のexact選択cached Brain/直接R50 parent/frame/requirements Map/reference/thread/contextが一致しなければ抑止します。source delegate中は古いrequirement frameを一時抑止し、任意callbackのcheckを元prefixへ混ぜません。正しいnested predicateは別ID、Map交換/clear/rearm/context変更/例外/budget/writer failureでは旧receiptを新sessionへ付けません。finally cleanupと元例外同一性を維持します。source取得の欠落を圧縮したindexや失敗/未呼出しへ補いません。observerCostNanosは既存summary build/first-byte-check範囲で、収集全体のCPU費用ではありません。

[追加source ledger](ACTIVITY-REQUIREMENT-BYTECODE-LEDGER-2026-10-05.json)はsame mapped Brainの1owner/4methods/2fields/6member slices、SHA **b43fed8307aed454bee85cb6120a12877bd06ac84a28a165ba109f4bab452e35**です。2つの元private predicate callersを含むexact descriptorsとclass/disassembly/member hashesを照合しました。JDK/artifact対応は既存同一世代のproofへ接続します。静的sourceはinstalled transformed class attestationではなく、source body/JARを公開しません。

## Fixture検証

元private predicateと両public callerのgenuine bytecodeをcloneし、private field/setter試験アクセスと元source delegateだけを置換しました。Map.get/Pair getters/iteration/first-false/first-valid branchを保持し、未変更private predicate baselineとcontains/get/check回数・順序・booleanを照合するRED→GREENです。missing/registered empty/firstfalse/customtrue、未知/null module/status/Activity、9checks-prefix8、nested predicateとarbitrary callback抑止、元Map/get-null/virtual例外、requirements Map交換、exactcached Brain/context6fields/time/clear/rearm/close/OFF/channel/thread/event1/byte1/ID256/depth8/component128/writerとframe cleanupを検査しました。synthetic maps/unsafe subject/reflection writesはfixtureのみです。

compiled ASMで4mandatory Redirect（2callers+contains/check）、exact selector/target/handler引数/require1、一つのprivate Invoker/各callerの元delegate1回、各OFF/observed branchの元contains/check1回を検査します。production Gson→strictJS17新規ケース、旧16/16/42/35/59/17/39/24/11/14と新5JSケースを関連回帰へ接続しました。Motion/Decision199件は成功、genuinecombinedAPIは成功しました。既存Windows bridge119pass/4platformfail/1skipやfullpytest失敗を再実行せず保全します。

## Frozen native R60

producer **6b11ff5d70846069016d112c211d809a739a6eff**、run-20261004181617-aab815691917／sess-20261004181617-9dff8eddbc8f／snapshot-20261004181617-59e79bd7669f、process1／Arena0、adult Villager UUID55555555-6666-7777-8888-000000000001です。正式control85filesのfresh privateコピー、自然day11850から進めました。desired Brain memory/path/resultをseedしていません。

2窓で元Activity更新正常return **400件**、元schedule query正常return **19件**を取得しました。revision1に、新要求receipt **1件**と旧requirements/setter各1件があります。revision2では新要求receiptを取得しておらず、未呼出しや失敗には読み替えません。

**RESTへの切替1件**は、元query→旧requirements正常return→新要求summary→元setter正常return→元update正常returnの5点を、直接ActivityFrame ID／全run/session/snapshot/process/Arena/revision／UUID／Brain component／実source orderで照合しました。旧condition receiptは新summaryの前に出ます。

| direct Activity / requirement ID | game tick / day argument | caller / Activity | 元Map.containsKey / private predicate | 元checkMemory returns | source ID末尾 |
| --- | --- | --- | --- | --- | --- |
| activity:1:67／activity-requirement:1:1 | 40475／12018 | IF_POSSIBLE／REST | true／true | 0（空prefix、truncated=false） | 105→106→107→108→109 |

このnativeケースは**登録済みの空要求Setでtrueになる枝**です。checkMemoryの内部Map.get/Optional presence、非空要求Set、missing Activity、FIRST_VALID、custom/null/例外/caps/rearmは今回のnativeで未検証です。fixtureの17ケースとは分けます。cached activeActivitiesはCORE+IDLEからCORE+RESTへ変わりました。選択原因の全解析や移動結果には広げません。

| revision | valid snapshots | 全callbacks / payload bytes | Motion実サンプル | same-snapshot PATH/Nav一致 | 終了理由 |
| --- | ---: | --- | ---: | ---: | --- |
| 1 | 120 | 213／337717 | 39 | 35 | WINDOW_ENDED |
| 2 | 120 | 209／332890 | 80 | 70 | WINDOW_ENDED |

全**422callbacks／240valid snapshots／1,118 unique canonical observations**、EVIDENCE_COMPLETE、SHA **c0fcf83193d4044bfc0c6ed05c2323981a2e007ac92de66d988898139f1e8449**、finalization SHA **b3e9ccac1e2f1620f4ec776c621abde6b2e91b281b5dcaccbffb74d1a165dce4**です。既存200ticks/256events/524288bytes/32nodes、revision1 local101..301 exclusive／revision2 local701..901 exclusive、両WINDOW_ENDEDを維持しました。119Motion実サンプルと105same-snapshot参照一致は独立した事実です。

cleanACK/drop0/queue0/finalWriterSeq1118、owned launcher57444/runtime31052のOS終了、元/control/predecessorR59/baseline各85filesのhash不変、MOD53a84の8444precompiled files/149compile artifacts/TF hash不変を確認しました。正式save/private runtime data/mapped JAR/source bodyは公開しません。

JFR34835bytes preflight、actual start-stop ACK、JDK parseを確認しました。**3852503bytes／SHA 4df7078b051b6d40ea651c5fcc22796e0950ed7ed30e93a9e35be84fed3b0754**、63秒/ExecutionSample341/CPULoad60/ThreadCPULoad453です。単独記録でmatched OFF/observer-effect/GPU/pixels受入ではありません。observerCostNanosはprefix収集を含む全CPU費用ではありません。

## Hosted producer CI

[source PR37223648256](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/37223648256)、[pytest37223648230](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/37223648230)、[push37223643997](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/37223643997)はSUCCESSです。actual PR checkout merge **10540a95f2e5e7d7f71637b9c88b1f8631499eb4**、親は57e52f9ef44c082daf7abbb0b0f5ada3a258a406／6b11ff5d70846069016d112c211d809a739a6eff。199focused/17newactualGsonと旧16/16/42/35/59/17/39/24/11/14、complete LAB source/portable Java/pinned MOD compile/dependency/resource/unit gatesを確認しました。hosted pytest: **2026-10-04T18:18:49.9941324Z 3149 passed, 332 skipped, 8 warnings in 235.83s (0:03:55)**。以前のWindows bridge119成功/4既存platform失敗/1skipはR59の記録を保持し、R60で再実行していません。publication HEAD CIは別途確認します。

## 残る検証

全priority/Activity/internalmemory eligibility、base checkMemoryの元Map.get/Optional presence枝、非空要求の実機判定、FIRST_VALID/nativecustom/null/例外/caps/rearm、全compute枝/duration/fallback RNG/cachedreuse/TICK_RECOMPUTE/実到着、全Path候補/拒否/malus/effectivecost、全Vanilla/FRONTIER/community、広いBoss戦/coordination、matched OFF/GPU/pixels、live Tank resize、section21全受入と最後のwhole-diff独立レビューは未完了です。Draftと元の全体goalを継続します。
