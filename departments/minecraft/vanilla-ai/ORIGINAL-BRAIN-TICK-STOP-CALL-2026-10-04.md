# 元のBrain tick／stop条件とdispatch

## 実装範囲

既存のdefault-OFF brain_navigationを拡張します。固定Minecraft 1.20.1 ForgeのBrain.tickEachRunningBehavior内の元interface BehaviorControl.tickOrStopを1回実行し、選択したexact MoveToTargetSinkに有限の軽量frameを設けます。未知のcontrol、OneShot、Gate、Sink subclassも元のinterface処理を1回実行しますが、このframeへ取得しません。既定channel集合とMixin登録集合は変更しません。

元のfinal Behavior.tickOrStopが実行したprotected virtual timedOut／canStillUseの正常boolean returnをBRAIN_PATH_CONDITION_RETURNとして保持します。timedOut=trueは元の短絡評価でcanStillUseを呼ばずstopへ進みます。timedOut=falseの後、元canStillUseがtrueならtick、falseならstopです。観測側で条件・query・AIを再実行しません。protected Shadow delegateは元virtual dispatchを1回保ちます。

元protected virtual tick／final doStopの正常void returnはBRAIN_PATH_DISPATCH_RETURNとして別に取得します。元の例外は同一のまま伝播し、失敗したcondition／dispatchの正常returnを作りません。既に完了した条件のreturnは別の事実として残ります。try/finallyはthrow、rearm、unsupported nesting後のframeを残しません。

同じ直接取得したtickOrStopInvocationIdの条件・分岐へ接続します。元dispatch中に実際にcaptureしたconcrete Sink呼出しのIDだけをcapturedSinkInvocationIdsに保持します。最大8件で、その先は明示的なtruncated tailです。時刻の近接から親子を補いません。このlistはconcrete call scopeの取得であり、全child取得や各正常完了を保証しません。[R53停止](ORIGINAL-BRAIN-STOP-CALL-2026-10-04.md)と[R52 tick／start](ORIGINAL-BRAIN-NAVIGATION-CALL-2026-10-04.md)の各returnは独立した事実です。

条件はDecision ModelのEVALUATION、dispatchはEXECUTION、coverageはbrain_navigation: PARTIALです。CANDIDATE／SELECTION／到着RESULTを生成しません。元の最終booleanから個々のoperandの理由を特定しません。完全停止理由、到達、search採用、広いBrain AI解析は未取得です。

## sourceと上限

[追加ledger](BRAIN-TICK-STOP-CALL-BYTECODE-LEDGER-2026-10-04.json)は同じ固定mapped artifactの4 owners／12 methods／4 fieldsをclass、disassembly、member sliceのhashとdescriptorで保持します。SHAはc5db9d9d960a194ebb053c57b6ebf2db1661cfa97d8a173fac226d84537dc478。以前のledgerを維持します。

exact MoveToTargetSinkはBehaviorを直接継承し、timedOut overrideを宣言しません。base methodは元gameTime > endTimestampで、等しい時刻はfalseです。それでも観測は元virtual戻り値を使用し、deadlineから再計算しません。Sink canStillUseはcached path／lastTargetPosで早期returnし、他branchでWALK_TARGET query、spectator、Navigation.isDone、到達条件を短絡評価します。今回のreturnからどのoperandがfalseになったかは補いません。Behavior.doStopはgeneric stopの前にstatusをSTOPPEDへ設定します。

選択Mob、exact cached Brain／NavigationとNavigation owner、server thread、session／run／snapshot／process／Arena／UUID／選択revision、時間／event／byte／writerを制限します。canStillUseのowner／level／timeもframeと一致しなければ取得しません。軽量frame8段階／256 IDs、component128件、direct child8件です。既存Snapshot256 Path参照とconcrete Sink frame256 IDsを別に保ち、各外側callでconcrete Sink IDやfull cached snapshotを追加消費しません。既存200 ticks／256 events／524,288 bytesを広げません。条件取得が増えるため、件数で閉じるprefixと未取得のtailを明示します。

## source／fixture検証

元genuine tickOrStopで、deadlineと等しい時刻のabsent-path branchが正常stopし、getter／query／erase／Navigation stopの回数を維持することを確認してから、条件観測が存在しないREDを再現しました。元Behavior tickOrStop／doStop bytecodeの明示的なfixtureは、protected観測call siteとstatus private writeだけを試験用に置換し、元短絡評価を残します。installed Mixinの実機証明へ置き換えません。

original timeout true／継続false／継続true、条件／dispatch例外の同一性、完了した条件の保持、depth8／9、invocation256、component128、child8件とtail、owner／Navigation owner／level／time／revision、OFF／thread／event／byte／writer／rearmを確認しました。無効な外側ownerでも独立して有効なconcrete Sink callbackは保持し、外側へ誤接続しません。compiled 5 Redirectのexact descriptor／require1／単一delegate、3 protected Shadow delegate、元interface callとfinal doStopの単一delegateを確認しました。

Motion／Decision **164件成功**、hash照合したgenuine依存関係で全bridge／Mixin compileとcombined API／owner／writer／Arena／overlay回帰が成功しました。**17 actual production Gson→JavaScriptケース**（条件12／dispatch5）はstrict consumerを通りました。timedOut trueにcanStillUseを補いません。以前の39 stop／24 Brain Navigation／11 Navigation／14 activityのGsonを維持します。

## Frozen native R54

producer **6c582ed01fec307898c3683a0de1b056e4b7df35**、run-20261004132545-7d81c5b8dfc2／sess-20261004132545-d651b347c317／snapshot-20261004132545-76f54df47009、process epoch1／Arena epoch0です。private adult Villager UUIDは55555555-6666-7777-8888-000000000001。元control85ファイルからcopyし、同じfloor／照明／playerとDayTime11850の自然進行を用いました。memoryや望む停止結果をseedしません。

| revision | valid snapshots | 元条件return／dispatch return | 全callback件数／payload bytes | Motion実サンプル | same-snapshot PATH／Navigation参照一致 |
| --- | ---: | --- | --- | ---: | ---: |
| 1 | 120 | 122／61 | 256／329,606 | 76 | 61 |
| 2 | 120 | 126／62 | 256／323,752 | 84 | 74 |

200 ticks／256 events／524,288 bytes／32 nodesの元上限を維持し、両窓は**EVENT_BUDGET**で閉じました（local101..301／701..901 exclusive）。実際の全callback prefixのgameTime範囲はrevision1: 40409..40499、revision2: 41009..41087です。120 snapshotsずつは選択保持期間の取得であり、条件を200 ticks全て取得したと扱いません。全512 callbacksのうち新規371件は条件248／dispatch123、既存141件はSink return126／Navigation停止3／memory消去6／PATH write3／Navigation moveTo3です。

**123 complete direct groups**はtick120／stop3です。元timedOut=false 124件、canStillUse=true 121件／false3件を取得しました。revision2のtick-stop:2:63はtimedOut=false／canStillUse=trueまでの**1 partial group**で、件数上限の後のdispatchを正常returnや失敗として補いません。timedOut=true／deadline equality／custom override／例外／depth・ID・child・component cap／rearm／nested restart／tick reconciliationはこのnative窓では未取得です。genuine fixtureの成功と区別します。

停止3組は元timedOut=false→元canStillUse=false→doStopの元concrete child→Navigation停止→WALK_TARGET消去→PATH消去→Sink正常終了→dispatch正常終了を、同じ直接取得したinvocation／child IDで照合しました。全source IDのprefixはobs:forge-runtime:45728:です。下表は実際の順序 timedOut／canStillUse／Navigation停止／WALK_TARGET消去／PATH消去／Sink終了／dispatch終了です。

| control invocation / concrete child | game tick | source observation IDの末尾（上記prefix） |
| --- | ---: | --- |
| tick-stop:1:14 / sink:1:14 | 40422 | 80 → 81 → 82 → 83 → 84 → 85 → 86 |
| tick-stop:1:38 / sink:1:39 | 40465 | 212 → 213 → 214 → 215 → 216 → 217 → 218 |
| tick-stop:2:42 / sink:2:42 | 41050 | 838 → 839 → 840 → 841 → 842 → 843 → 844 |

7件ごとのexact UUID、run／session／snapshot／process／Arena／revision、gameTimeArgument、instanceIdentity、source method、eventIndex順序を照合しました。beforeは3箇所のPathとWALK_TARGET Optional slotがpresent、Navigation stop後はcached Navigation PathがabsentでBrain PATHはまだpresent、消去とSink終了後は3PathとWALK_TARGET slotがabsent、speed0.5は保持されました。個々のcanStillUse operand、到達条件、RNG／cooldown、search採用や到着RESULTは証明しません。160 Motion実サンプル／135 same-snapshot参照一致も別の事実です。

canonical **1,297 unique observations**はEVIDENCE_COMPLETE、SHA **3945291eae5050e2c70b722c75e8c2bea5d8290d6a70902550c91ee8f6d6fc9b**、finalization SHA **e8a0c1e92b64b76b43492d46efe577967d1b2e1805eb6feba15a5114cafd3650**。clean ACK／drop0／queue0／finalWriterSeq1297、owned launcher43084／runtime45728のOS上の終了、元／control／predecessor R53／baseline各85ファイルのhash不変を確認しました。EVIDENCE_COMPLETEは保持・flush・finalizationの確認で、未取得tailや全AIの受入ではありません。

JFR設定34,835 bytes／SHA d4d74f3594bfe342397f53aaa75a7551e7b2d9ac6f86c7ca2bc016690501b37dを起動前に照合し、actual start／stop応答を要求しました。保存JFR **4,252,106 bytes**／SHA **1da905dea554e23aad6a64be925f8ad6fbada6f8387cca06e7453a87bd617868**はJDK jfr summaryでparse成功です。63秒／ExecutionSample357／CPULoad60／ThreadCPULoad445を含みます。単独記録であり、matched OFF、GPU／pixels、性能上限やobserver-effect受入ではありません。以前のR51 JFR未取得記録を保全します。

private canonical／installed condition・stop・integrated proof／JFR／post-setup baselineと以前の証拠を保全しています。save、JAR、source body、private runtime dataはGitHubへ追加しません。

## Hosted producer CI

source push **37205538571**／source PR **37205542125**／pytest **37205542126**はSUCCESS。actual PR checkout merge1cf30a00ac792e9b755ca315080c90c7f0ab79b9の親はbase57e52f9ef44c082daf7abbb0b0f5ada3a258a406とproducer6c582ed01fec307898c3683a0de1b056e4b7df35。164 focused／17 actual Brain tick-or-stop Gson markers、完全LAB source suite／portable Java／pinned MOD compile／dependency／resource／unit gatesを確認しました。hosted pytestは**3,149成功／332スキップ／8 warnings（275.30秒）**。documentation publication HEADは別に確認します。

## 残る検証

全条件内部の理由・timeout native branch、complete concrete subclass/caller、tryComputePath／search採用／到着、全Path候補・拒否・cost、広いBoss戦／Vanilla・FRONTIER・community、matched observer-effect／GPU・pixels、live Tank resize、section21全受入、最後のwhole-diff独立レビューは残っています。Draftと全体goalを継続します。
