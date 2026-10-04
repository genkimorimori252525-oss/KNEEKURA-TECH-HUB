# 元Activity要求Map・メモリチェックの直接source

[R50の元Activity更新scope](ORIGINAL-ACTIVITY-CALL-2026-10-04.md)内で、Brain.activityRequirementsAreMetが元activityRequirements Map.containsKey(Activity)とvirtual Brain.checkMemoryに実際に渡した引数・正常戻り値を記録します。private predicateへの元callはsetActiveActivityIfPossibleとsetActiveActivityToFirstValidの2か所にあり、各source-specific RedirectからInvokerで元private methodを1回実行します。元Map.get/Set iterator/Pair.getFirst/getSecond/first-falseとfirst-valid list short circuitを維持し、Map/Pair/slot/presence/getter/AIを再実行しません。新しいpredicate捕捉は直接のR50 ActivityFrameがある場合に限ります。

元MapにActivityがなければbase bodyはfalse、登録済みで要求Setが空ならtrueです。要求がある場合は最初の元checkMemory falseで止まります。Map membership、実際のcheckMemory boolean、private predicateの正常booleanは別々の事実で、custom virtual/Mixin結果をcached slotから再計算しません。数値priority/全候補/選択原因/internal slot理由を取得済みとはしません。

新しいBRAIN_ACTIVITY_REQUIREMENT_CHECKS_RETURNはEVALUATION/brain_activity/PARTIALです。既存ActivityFrame IDと新requirement IDは直接frameからリンクします。IF_POSSIBLE/FIRST_VALIDは実call siteです。元Map membershipと正常predicate boolean、最大8件の元checkMemory passed module/status/returned booleanを保持し、実9件目の正常returnでchecksTruncated=trueです。missing/empty mapはchecks空で正常receiptを持てます。Activity/moduleは有限raw identityだけをlabelし、未知/nullはNOT_EXPOSED。新しいgameTime queryや引数を作りません。旧R50/R57/R58/R59/compute/Sink payloadは不変です。

requirement IDs256/depth8/component128、既存200ticks/256events/524288bytes/32nodes、default OFFを維持します。現在のexact選択cached Brain/直接R50 parent/frame/requirements Map/reference/thread/contextが一致しなければ抑止します。source delegate中は古いrequirement frameを一時抑止し、任意callbackのcheckを元prefixへ混ぜません。正しいnested predicateは別ID、Map交換/clear/rearm/context変更/例外/budget/writer failureでは旧receiptを新sessionへ付けません。finally cleanupと元例外同一性を維持します。source取得の欠落を圧縮したindexや失敗/未呼出しへ補いません。observerCostNanosは既存summary build/first-byte-check範囲で、収集全体のCPU費用ではありません。

[追加source ledger](ACTIVITY-REQUIREMENT-BYTECODE-LEDGER-2026-10-05.json)はsame mapped Brainの1owner/4methods/2fields/6member slices、SHA **b43fed8307aed454bee85cb6120a12877bd06ac84a28a165ba109f4bab452e35**です。2つの元private predicate callersを含むexact descriptorsとclass/disassembly/member hashesを照合しました。JDK/artifact対応は既存同一世代のproofへ接続します。静的sourceはinstalled transformed class attestationではなく、source body/JARを公開しません。

## Fixture検証

元private predicateと両public callerのgenuine bytecodeをcloneし、private field/setter試験アクセスと元source delegateだけを置換しました。Map.get/Pair getters/iteration/first-false/first-valid branchを保持し、未変更private predicate baselineとcontains/get/check回数・順序・booleanを照合するRED→GREENです。missing/registered empty/firstfalse/customtrue、未知/null module/status/Activity、9checks-prefix8、nested predicateとarbitrary callback抑止、元Map/get-null/virtual例外、requirements Map交換、exactcached Brain/context6fields/time/clear/rearm/close/OFF/channel/thread/event1/byte1/ID256/depth8/component128/writerとframe cleanupを検査しました。synthetic maps/unsafe subject/reflection writesはfixtureのみです。

compiled ASMで4mandatory Redirect（2callers+contains/check）、exact selector/target/handler引数/require1、一つのprivate Invoker/各callerの元delegate1回、各OFF/observed branchの元contains/check1回を検査します。production Gson→strictJS17新規ケース、旧16/16/42/35/59/17/39/24/11/14と新5JSケースを関連回帰へ接続しました。Motion/Decision199件は成功、genuinecombinedAPIは成功しました。既存Windows bridge119pass/4platformfail/1skipやfullpytest失敗を再実行せず保全します。

## 次の検証

frozen producerのfresh private85control copy/predecessorR59/baseline、自然進行Villagerのbrain_activity opt-in windowから取得できた元要求Map/checksと旧R50 query/set/updateを直接ID/context/source順序で照合します。全caller/custom/null/例外/上限/内部slot理由をnative受入済みとは扱いません。actual JFR ACK/parse、canonical/cleanstop/drop0/ownedexit/元保存対象各85hash/MOD8444+149+TF、producer3CIとpublication HEAD2CI/Draftreadbackを確認するまで新sourceの実機受入は主張しません。

全priority/Activity/internalmemory eligibility、base checkMemoryの元Map.get/Optional presence枝、全compute枝/duration/fallback RNG/cachedreuse/TICK_RECOMPUTE/実到着、全Path候補/拒否/malus/effectivecost、全Vanilla/FRONTIER/community、広いBoss戦/coordination、matched OFF/GPU/pixels、live Tank resize、section21全受入と最後のwhole-diff独立レビューは引き続き未完了です。Draftと元の全体goalを継続します。
