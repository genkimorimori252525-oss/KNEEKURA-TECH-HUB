# 元のBrain開始ループのActivity・状態・開始戻り値

[R57の元tryStart](ORIGINAL-BRAIN-TRY-START-CALL-2026-10-05.md)と[R58の元メモリ要求](ORIGINAL-BRAIN-MEMORY-REQUIREMENT-2026-10-05.md)へ、Brain.tickが実際に呼ぶprivate startEachNonRunningBehaviorの直接scopeを追加します。元private methodを既存Brain Mixin内のInvokerから1回実行し、そのsource Set.contains(Activity)／interface BehaviorControl.getStatusを各1回だけ実行します。元Map.values／entrySet／iterator、Level.getGameTime、STOPPEDだけのtryStart分岐を維持し、再走査・AI／getter／registry queryの追加はありません。

元loopは数値priorityキーを読みません。priorityStatus=NOT_EXPOSEDで、Activity/controlの元走査indexを数値priorityや理由へ変換しません。ActivityはCORE／IDLE／REST／WORK／MEET／PLAY／FIGHTのraw identityだけを既知labelにし、その他とnullはNOT_EXPOSEDです。未知のMOD controlも元interfaceの実戻り値を扱いますが、独自AIをVanilla Goalとして説明しません。STOPPED／RUNNING／nullの元statusと、元tryStartの正常booleanを別の事実として保持し、cached statusを読み直して再計算しません。

新しいBRAIN_PATH_START_LOOP_RETURNはEVALUATION／brain_navigation／PARTIALです。正常に完了した元private loopの有限prefixを記録します。Activity8／各control8、実際の9件目正常returnで各truncated=true。inactive Activityはcontrols空、RUNNING/null statusはtryStartStatus=NOT_CALLED、STOPPEDは元正常tryStartResultを持ちます。元tryStartへ実際に渡ったlongがある場合だけsourceGameTimeStatus=AVAILABLEとgameTimeArgumentを保持します。それ以外はNOT_CAPTUREDで、元Level.getGameTime結果を追加取得したりreceipt時刻と同一視しません。R57 frameが実際に割り当てられた場合だけcapturedTryStartInvocationIdを付け、そのIDだけで子の正常完了・record保持を主張しません。旧R57/R58/compute/Sinkのpayloadは変更しません。

loop IDs256／depth8、共有component128と既存200ticks／256events／524,288bytes／32nodesは不変です。exact選択owner／Brain／cached Nav／raw Navowner／cached activeActivities Set／level／thread／contextが必要です。source delegate中は古いloop scopeを一時抑止し、任意callbackを親の元走査へ混ぜません。正しいnested private loopは別IDで捕捉します。mixed source／cached Set変更／rearm／clear／例外／budget終了では正常loop summaryを偽装せず、元例外同一性とfinally cleanupを保ちます。observerCostNanosは既存summary buildとfirst-byte-checkの範囲で、prefix収集や観測全体のCPU費用は含みません。

[追加source ledger](BRAIN-START-LOOP-BYTECODE-LEDGER-2026-10-05.json)はsame mapped artifactの3owners／4methods／3fields／7member slicesです。SHA **5f64ab73c390bd8639e1ef5973d15411c96ba88cb6b11d88a9313e2a5f4e5f65**。artifact/JDK/class/disassembly/member hashesとexact descriptorsを照合しました。静的sourceはinstalled transformed class attestationではなく、source body/JARを公開しません。

元private loopのgenuine bytecodeをcloneし、試験用private field accessorと3source delegateだけを置換しました。未変更private methodとのgetter/values/contains/status/tryStart回数・実順序・分岐を照合するRED→GREENです。inactive、STOPPED/RUNNING/null、unknown/null Activity、virtual true/false、8+tail×2、nested loopとcallback抑止、exact R57 child、元例外、OFF/channel/thread/cached Brain/Nav/Set/Navowner/revision/time/event/byte/rearm/clear/component128/writerとframe解放を検査します。compiled ASMで3mandatory source Redirect/require1/Invokerとsingle original delegateを照合します。synthetic map/reflection writes/unsafe subjectはfixtureのみで、native全branchの受入証拠ではありません。旧tick/stopのlambda検査を元Behaviorクラスへ限定し、旧3protected/1final delegateと5必須Redirect件数を維持しました。

Motion/Decision194件と新16Gsonケース、および旧16/42/35/59/17/39/24/11/14を検査します。genuinecombinedAPIは成功しました。Windowsのbridge全124件は119成功/4失敗/1skipでした。失敗は既存のsymlink権限3件とdescendant pipe終了判定1件で、今回変更範囲の失敗とは扱いません。OS設定や無関係コードは変更せず、hosted Linux CIを別途確認します。

## Frozen native R59

producer **b63c4632eca5b790a6189a0523d5455efbdb50f8**、run-20261004173827-14ff8c000fe3／sess-20261004173827-61420ba24c93／snapshot-20261004173827-f81d642e0b16、process1／Arena0、adult Villager UUID55555555-6666-7777-8888-000000000001です。正式control85filesのfresh privateコピー、自然day11850から進めました。desired Brain memory/path/resultをseedしていません。

**102正常private loop receipts**（revision1=52／revision2=50）に、元Activity contains正常returns **816件**、元interface getStatus正常returns **918件**を含みます。個々の配列要素に別observation IDを付けたのではなく、1receipt内の元走査prefixです。既知raw Activity CORE=true204／未label Activity=false612、元status STOPPED806／RUNNING112、元tryStart正常boolean true139／false667を取得しました。未知Activityの名前・数値priority・独自AI内部理由を推測して補いません。

**全102 loopsでActivity prefix8とcontrol prefix8のtruncationが発生**しました。各tailの元9件目正常returnを観測してtrueにする実装ですが、以後の要素を列挙していません。COREが異なる元priority-mapのentryで複数回判定される事実を保持し、同一Activityのindexを数値priorityや理由へ読み替えません。未取得tailを未呼出し／失敗／完全候補へ補いません。nativeの有限prefix tail取得とsynthetic全cap/custom/null/例外/rearm fixtureは区別します。

**25 exact loop→R57 normal tryStart child links、partial child links0**を照合しました。選択UUID、全run/session/snapshot/process/Arena/revision、元gameTimeArgument、control class/raw component tokenと実返boolean、child source/eventIndex順序が一致します。これらは取得できた子に限る照合で、tail全体の子や未取得loopの完了を主張しません。旧R58 requirement25receipts内に75元check returns、全25 complete requirement→condition→tryStart groupsがあります。WALK_TARGET VALUE_PRESENT=false23／true2、他2要求=true25です。

**2 complete15-event direct chains**で、新しいloop receiptと元14点のmemory→condition→compute6→PATHwrite/Nav/Sink→startdispatch→tryStartreturnを照合しました。source IDsを時刻の近さで結んだのではなく、同じ元control/loop frameの直接IDです。

| loop / tryStart / requirement | game tick | 元Activity / index / control index | 元Path.canReach / compute / Nav / tryStart | distance / closeEnough | source ID末尾 |
| --- | ---: | --- | --- | --- | --- |
| start-loop:1:16／try-start:1:16／memory-requirement:1:16 | 40444 | CORE／6／1 | true／true／true／true | 8／0 | 86→87→88→89→90→91→92→93→94→95→96→97→98→99→100 |
| start-loop:2:9／try-start:2:9／memory-requirement:2:9 | 41037 | CORE／6／1 | false／true／true／true | 29／4 | 644→645→646→647→648→649→650→651→652→653→654→655→656→657→658 |

runtime7060、両chainのmemory=true/extra=true/reached=falseです。1つはPath.canReach=true、もう1つはfalseですが元compute/Nav/tryStartはtrueです。正常boolean、Pathの到達可能flag、実到着を区別します。全compute枝・cachedreuse・duration/fallback RNG・TICK_RECOMPUTEはこれだけで受入済みにはしません。

| revision | valid snapshots | loop receipts | 全callbacks / payload bytes | Motion実サンプル | same-snapshot PATH/Nav一致 | 終了理由 |
| --- | ---: | ---: | --- | ---: | ---: | --- |
| 1 | 120 | 52 | 256／459324 | 61 | 51 | EVENT_BUDGET |
| 2 | 120 | 50 | 256／461730 | 80 | 71 | EVENT_BUDGET |

全512callbacks/240valid snapshots、canonical **1,248 unique observations**、EVIDENCE_COMPLETE、SHA **b726ec5869725a0f3b69517407e221ebb8c28e5db7a860c8f231d9db422154b5**、finalization SHA **3750aa3033084719f2f287c6c49a79f84b580395bb07675c8bfd4f202b01a551**です。既存200ticks/256events/524,288bytes/32nodes、revision1 local121..321 exclusive／revision2 local721..921 exclusiveのEVENT_BUDGETを維持しました。141Motion実サンプル/122same-snapshot参照一致は独立した事実です。

cleanACK/drop0/queue0/finalWriterSeq1248、owned launcher41272/runtime7060のOS終了、元/control/predecessorR58/baseline各85filesのhash不変、MOD53a84の8,444precompiled files/149compile artifacts/TF hash不変を確認しました。正式save/private runtime data/mapped JAR/source bodyは公開しません。

JFR34,835bytes preflight/actual start-stop ACK/JDK parseを確認しました。**4479612bytes／SHA b856b7f1aed14faddcf73d5259e5c82f389fdb20398b05868f43db295a3baf65**、63秒/ExecutionSample382/CPULoad60/ThreadCPULoad469です。単独記録でmatched OFF/observer-effect/GPU/pixels受入ではありません。summary observerCostNanosは収集全体を測定しません。

## Hosted producer CI

[source PR37221204974](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/37221204974)、[pytest37221205047](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/37221205047)、[push37221201344](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/37221201344)はSUCCESSです。actual PR checkout merge **c5c2bf71a838e5ebcadd2de8f395a4f8a53c715f**、親は57e52f9ef44c082daf7abbb0b0f5ada3a258a406／b63c4632eca5b790a6189a0523d5455efbdb50f8。194focused/16newactualGsonと旧16/42/35/59/17/39/24/11/14、complete LAB source/portable Java/pinned MOD compile/dependency/resource/unit gatesを確認しました。hosted pytest: **2026-10-04T17:42:28.9191556Z 3149 passed, 332 skipped, 8 warnings in 283.13s (0:04:43)**。Windows bridge119成功/4既存platform失敗/1skipとhosted Linux成功を区別します。publication HEAD CIは別途確認します。

## 残る検証

全priority/Activity eligibility/internal memory理由、nativecustom/null/例外/rearmや全cap経路、全compute枝/duration/fallback RNG/cachedreuse/TICK_RECOMPUTE/実到着、全Path候補/拒否/malus/effectivecost、全Vanilla/FRONTIER/community、広いBoss戦/coordination、matched OFF/GPU/pixels、live Tank resize、section21全受入、最後のwhole-diff独立レビューは残ります。取得できた102有限loop/25child linksを全候補・全実運用受入に広げず、Draftと全体goalを継続します。
