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

## Frozen native R61

producer **b0fe4a139c35ca93b8873f90e096afcb3784c5f9**、run-20261004185828-836dd9851481／sess-20261004185828-ca47dc952f37／snapshot-20261004185828-0b3560019ec4、process1／Arena0、adult Villager UUID55555555-6666-7777-8888-000000000001です。正式control85filesのfresh privateコピー、自然day11850から進めました。desired memory/path/resultをseedしていません。既存brain_navigationだけをopt-inしています。

**132正常base-source receipts**（revision1=21／revision2=111）を、元R58の**44要求receipts内の132checks**へdirect requirement ID/checkIndex/tryStart ID/全context/UUID/元virtual boolean/実source順序で照合しました。全44取得済み要求prefixは3checksでnontruncatedです。new sourceのBrain componentと旧要求のSink componentは別のidentityです。前者を後者に偽装せず、直接frame IDsとcontextを使います。

| 元module / requested status | Map.get結果 | 元presence | base正常boolean / virtual正常boolean | 件数 |
| --- | --- | --- | --- | ---: |
| CANT_REACH_WALK_TARGET_SINCE / REGISTERED | NON_NULL | NOT_CALLED | true / true | 44 |
| PATH / VALUE_ABSENT | NON_NULL | false（VALUE_ABSENT site） | true / true | 44 |
| WALK_TARGET / VALUE_PRESENT | NON_NULL | false（VALUE_PRESENT site） | false / false | 43 |
| WALK_TARGET / VALUE_PRESENT | NON_NULL | true（VALUE_PRESENT site） | true / true | 1 |

REGISTEREDのslotが空かpresentかは再照会せず**NOT_QUERIED**です。null returned slot、unknown/null operands、custom override/baseなし/複数base、source caps/例外/rearmはfixtureで検証していますが、今回のnativeで受入済みにはしません。Activity要求のbase-source channelは今回armedにしておらず、R60の空要求Setとは別の試験です。

**43要求→HAS_REQUIRED_MEMORIES条件→元tryStart正常return groups**を照合しました。条件false/tryStartfalse42、条件true/tryStarttrue1です。後者はmemory-requirement:1:7／try-start:1:7、tick40415/runtime40356、source61→62→63→64→65→77で、3元base-source→要求→条件→tryStartreturnを直接リンクします。中間のextra/compute等をこの6点だけで説明済みにはしません。

**最後の要求1件では条件・tryStartreturnがNOT_CAPTURED**です。source3点と要求receiptは取得済みでも、その後のevent budget終了を未呼出し・失敗・完全start chainへ変換しません。132 source→要求linksにpartial0であることと、要求→上位start groupsにpartial1であることは別の範囲です。

| revision | valid snapshots | 新source / 元要求 | 全callbacks / payload bytes | Motion実サンプル | same-snapshot PATH/Nav一致 | 終了理由 |
| --- | ---: | --- | --- | ---: | ---: | --- |
| 1 | 120 | 21／7 | 256／440993 | 59 | 46 | EVENT_BUDGET |
| 2 | 120 | 111／37 | 256／358768 | 82 | 74 | EVENT_BUDGET |

全512callbacks/240valid snapshots/**1,251 unique canonical observations**、EVIDENCE_COMPLETE、SHA **ee19c57e77dbfc5c90bbbad786bc095ba0cc564eaa6ce2df44aac4b16c9e0aa6**、finalization SHA **5aba906ab397335b16b3a46d16f5113bb0371016c860061638e4e92bec5762f4**です。既存200ticks/256events/524288bytes/32nodes、revision1 local101..301 exclusive／revision2 local701..901 exclusive、両256 EVENT_BUDGETを維持しました。141Motion実サンプルと120same-snapshot参照一致は独立した事実です。

cleanACK/drop0/queue0/finalWriterSeq1251、owned launcher31944/runtime40356のOS終了、元/control/predecessorR60/baseline各85filesのhash不変、MOD53a84の8444precompiled files/149compile artifacts/TF hash不変を確認しました。正式save/source body/mapped JAR/private runtime dataは公開しません。

JFR34835bytes preflight、actual start-stop ACK、JDK parseを確認しました。**4273365bytes／SHA 32f86dcd3b579e3a95a581ab46fa5931deeb258ad922573d7f0d6eaba7f8e776**、63秒/ExecutionSample377/CPULoad60/ThreadCPULoad436です。単独記録でmatched OFF/observer-effect/GPU/pixels受入ではありません。observerCostNanosはsource収集を含む全CPU費用ではありません。

## Hosted producer CI

[source PR37226327243](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/37226327243)、[pytest37226327041](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/37226327041)、[push37226323327](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/37226323327)はSUCCESSです。actual PR checkout merge **6fc07035f8010628505db5462166c901fa6e7823**、親は57e52f9ef44c082daf7abbb0b0f5ada3a258a406／b0fe4a139c35ca93b8873f90e096afcb3784c5f9。205focused/26newactualGsonと旧17/16/16/42/35/59/17/39/24/11/14、complete LAB source/portable Java/pinned MOD compile/dependency/resource/unit gatesを確認しました。hosted pytest: **2026-10-04T19:01:12.5828988Z 3149 passed, 332 skipped, 8 warnings in 273.17s (0:04:33)**。R59 Windows bridge119pass/4既存platformfail/1skipを保全し、R61で再実行していません。publication HEAD CIは別途確認します。

## 残る検証

native Activity/nonempty/custom/null/caps/例外/rearm、全priority/Activity/内部memory eligibility、duration/fallback RNG/cachedreuse/TICK_RECOMPUTE/実到着、全Path候補/拒否/malus/effectivecost、全Vanilla/FRONTIER/community、広いBoss戦/coordination、matched OFF/GPU/pixels、live Tank resize、section21全受入と最後のwhole-diff独立レビューは未完了です。Draftと元の全体goalを継続します。
