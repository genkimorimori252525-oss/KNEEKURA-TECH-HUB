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

## 次の検証

Frozen producerのprivate自然進行Villagerによるinstalled条件／dispatch／direct child取得、JFRのactual ack、canonical／clean shutdown／各85ファイル不変、producer・公開HEAD CIはこのsource checkpointでは未検証です。元ワールドへmemoryや望む停止結果を書き込みません。完全Path／Boss戦／Vanilla・FRONTIER・community／matched observer-effect／GPU・pixels／live Tank resize／section21全受入／最後のwhole-diff独立レビューは残っています。Draftと全体goalを継続します。
