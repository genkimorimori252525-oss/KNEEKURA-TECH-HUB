# 元Brain memory slot・presence判定の直接source

[R58の元Behavior要求](ORIGINAL-BRAIN-MEMORY-REQUIREMENT-2026-10-05.md)と[R60の元Activity要求](ORIGINAL-ACTIVITY-REQUIREMENT-2026-10-05.md)が実際に行うvirtual Brain.checkMemoryの中で、base methodの元Map.get/Optional.isPresent/正常returnを捕捉します。元virtual call・Map.get・該当presence callはそれぞれ元の回数だけ実行します。slot/presence/value/expiration/registry/AI/getterの再照会は追加しません。

元Map.get結果がnullならfalseで戻り、presenceを呼びません。非null slotでREGISTEREDならtrueでpresenceを呼びません。VALUE_PRESENTはoffset35/ordinal0、VALUE_ABSENTは49/ordinal1の元isPresent callを使い、元bodyでは最大1か所だけ実行します。未知/null requested statusで非null slotならidentity比較を通りfalse、presenceは呼びません。元Object→Optional castとnull branchを維持し、不正なMap値のClassCastExceptionを補正しません。

base正常booleanと外側virtual正常booleanは独立して記録します。custom Brainがbaseを呼ばずに返す場合や複数のbase traversalを混ぜる場合は、単一base sourceのpacketを作りません。外側booleanをcached slotから再計算せず、custom/Mixinの結果の違いを理由に元の戻り値を変えません。static source evidenceはinstalled transformed class attestationではありません。

新しいBRAIN_PATH_MEMORY_SOURCE_RETURN／BRAIN_ACTIVITY_MEMORY_SOURCE_RETURNはEVALUATION／対応するbrain_navigation・brain_activity／PARTIALです。共通source IDに、元requirement ID、元tryStart／Activity ID、元checkIndex1..8を直接frameから付けます。Map結果のNULL/NON_NULL、presence NOT_CALLED/NORMAL_RETURNと該当site/正常boolean、baseResult/resultを保持します。NOT_CALLEDは正常base returnまで捕捉できた一つのbase traversalに限る事実で、未知の独自AI全体への主張ではありません。完全候補、全memory原因、選択成功、移動結果を作りません。

source IDs256/depth8/component128、旧requirementのcheckprefix8+実9件目tail、既存200ticks/256events/524288bytes/32nodes/default OFFを維持します。exact選択cached Brain/memories Map/module/status/raw Optional/parent/context/threadが一致しなければ抑止します。R58のNav/raw owner gateは維持し、R60に追加のNav条件は付けません。元Map/presence delegate中はsource frameを一時抑止し、arbitrary callbacksを混ぜません。正しいnested直接scopeは別IDで、復元は同じactive sessionだけです。元例外、cast、再設定・clear・time/context交換・Map交換・budget/writer failureとfinally cleanupを維持します。

新eventも既存event budgetを使うため、取得済みchildの親receiptが窓の末尾で未取得になる場合があります。直接IDによる部分リンクとして残し、時刻の近さで完全chainへ補いません。旧R50/R57/R58/R59/R60/compute/Sinkのpayload形式は変更しません。observerCostNanosは既存summary build/first-byte-checkの範囲で、source収集全体のCPU費用ではありません。

[追加source ledger](BRAIN-MEMORY-SOURCE-BYTECODE-LEDGER-2026-10-05.json)はsame artifactの3owners/3methods/6fields/9member slices、SHA **53221de4e34dfb5ee33118bdedf47518b04ab036c960295a9bfdc3174109df95**です。元class/disassembly/member descriptors・hashesとJDK対応を照合しました。JAR/source body/save/private runtime dataは公開しません。

## Fixture検証

genuine base checkMemory bytecodeをcloneし、private field試験アクセス、元Map.get/presence delegatesと正常return callbackだけを置換しました。元cast/null branch/identity比較/2RETURN sitesを保持し、未変更baseのvirtual/get回数・booleanと照合するRED→GREENです。null slot、registered empty/present、VALUE_PRESENT/ABSENT×empty/present、null status、未知/null module、custom virtual反転/baseなし/複数base、元get exception identity/不正cast/null presence、両直接parent、Activity無Nav、arbitrary callback/nested分離、mixed module/Map交換、context8fields/OFF/channel/thread/time/Brain/Navowner/clear/rearm/IDs256/depth8/component128/event1/byte1/writer/cleanupを検査しました。9元checksがすべて実行され、新source8packetと旧prefix8+tailが一致します。raw synthetic maps/unsafe subject/reflection writesはfixtureだけです。

compiled ASMでexact3mandatory Redirect、元method selector/target/append args/ordinal0+1/require1、base RETURN require2、OFF/observedの元Map/get/presence delegate各1回を検査しました。production Gson→strict consumer26新ケースと旧17/16/16/42/35/59/17/39/24/11/14、新6JSケースを共通APIと回帰へ接続しています。Motion/Decision205件は成功、genuinecombinedAPIは成功しました。旧Windows platform失敗は保全し、無関係なOS変更や同じ全suiteの再実行はしません。

## 次の検証

frozen producerのfresh private85control copy/predecessorR60/baselineから、自然進行Villagerのbrain_navigation窓で元R58要求とsource childを直接ID/context/checkIndex/module/status/正常boolean/source順序で照合します。R60で実機取得できたRESTは登録済み空要求Setだけで、source childは未取得でした。今世代の非空要求・各presence枝の実機証拠はまだありません。synthetic26ケースをnative成功へ読み替えません。

actual JFR start-stop ACK/parse、canonical/cleanstop/drop0/ownedOSexit/元保存対象各85hash/MOD8444+149+TF、producer3CI、追加3docsとpublication HEAD2CI/Draftreadbackを確認します。全custom/null/caps/例外/rearm、全priority/Activity/内部memory eligibility、duration/fallback RNG/cachedreuse/TICK_RECOMPUTE/実到着、全Path候補/拒否/malus/effectivecost、全Vanilla/FRONTIER/community、広いBoss戦/coordination、matched OFF/GPU/pixels、live Tank resize、section21全受入と最後のwhole-diff独立レビューは引き続き未完了です。Draftと元の全体goalを継続します。
