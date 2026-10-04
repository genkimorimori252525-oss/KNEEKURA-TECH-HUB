# 元のBrain開始条件と直接の経路計算・start scope

既存のdefault-OFF brain_navigationを使い、Brain.startEachNonRunningBehavior内で実際に呼ばれたBehaviorControl.tryStartの正常booleanを保持します。exact選択MoveToTargetSink、cached Brain／Navigationとraw Navigation ownerが一致した場合だけ、有限try-start frameを開きます。元interface callはOFF／unknown subclass／未対応owner／例外の場合も1回だけ実行します。優先度・active Activity／getStatusの全候補選択理由を取得済みとはしません。

元Behavior.tryStartはfinalで、protected virtual hasRequiredMemories→trueの場合だけcheckExtraStartConditions→両方trueの場合だけstatus RUNNING・元duration RNG・endTimestamp・virtual start→true return、その他false returnの順です。source-specific Redirectと3 protected Shadow delegateで、元条件の実際のboolean、元startの正常void、元interfaceの正常booleanを別の事実にします。memory／AI／getter／RNGを再実行せず、元例外とshort circuit、status／endTimestamp／duration RNGの元bodyを維持します。hasRequiredMemoriesはprotectedであり、privateと誤認したpublic化／Invokerを加えません。個々のMemoryStatus／entryCondition内部理由はNOT_EXPOSEDです。

元checkExtraStartConditionsはcooldown decrementでfalseになる場合があります。WALK_TARGET取得後のprivate reachedTarget→未到達の場合だけ[R55の元compute](ORIGINAL-BRAIN-PATH-COMPUTE-2026-10-04.md)と[R56のpredicate／operand](ORIGINAL-BRAIN-PATH-COMPUTE-CONDITION-2026-10-05.md)が実際に実行されたとき、その現在のcompute frame IDを追加条件receiptへ保持します。元virtual startのdispatch receiptは、実際のSTART_FROM_BRIDGEのSink frame IDを保持し、既存のPATH write／Navigation moveTo／Sink returnへ接続できます。old compute／Sink payloadは変更しません。

新しいBRAIN_PATH_START_CONDITION_RETURNとBRAIN_PATH_TRY_START_RETURNはEVALUATION、BRAIN_PATH_START_DISPATCH_RETURNはEXECUTION、すべてbrain_navigation／PARTIALです。direct source-call scopeの有限child IDを保持しますが、IDだけではchild completion／全children／Navigation採用・到着を証明しません。native verifierでは実際のchild receipt、raw参照、全UUID／run／session／snapshot／process／Arena／revision、source順序を別途照合します。時間・座標の近さから因果を作りません。

frame256／depth8、条件内compute ID8／start内Sink ID8に明示的tailを設け、既存component128／Snapshot Path256、200ticks／256events／524,288bytesを維持します。exact selected／current cached Brain・Nav owner／server thread／context／時間／event／byte／writerを照合します。callbackでowner／level／kind／gameTimeが不一致ならそのsource scopeを抑止し、古いparentへ子を帰属させません。tryfinally、clear／rearm／detachでframeを解放し、元呼出し中のrearmから旧returnを新parentへ接続しません。

[追加ledger](BRAIN-TRY-START-BYTECODE-LEDGER-2026-10-05.json)はsame mapped artifactの4owners／12selected method slices（generic bridge overloadを含む）／9fieldsです。ledger SHA **f4e304de201dfc92ac1dbe47c096f89e1e6c24a69ded28237b0f24937413e4d8**。JDK／artifact／class／disassembly／21 member slices・exact descriptorsを照合します。静的sourceは実機でtransform済みclassのattestationではありません。旧ledgerを保全し、source body／JARはGitHubへ追加しません。

## Source／fixture検証

元final Behavior.tryStart、元Sinkの追加条件とstartのbytecodeでRED→GREENを行いました。試験用private accessと観測source delegateだけを置換し、元branch／status／endTimestamp／duration RNGを維持します。必要memory false／cooldown extra false／開始true、元query／create／moveTo／duration RNG回数のbaseline照合、memory／extra／RNG／startの元例外同一性、OFF／owner／cached Brain・Nav owner／revision／時間／event／byte／thread／writer、8depth／256IDs／128component、rearm／cleanupを検査しました。synthetic repeated source delegatesで8 child capと明示tail、unsupported callbackの子帰属抑止を確認します。scripted Navigationとproxy Level/RNG、synthetic nesting／capsは本物のnative branch／fallback RNG／arrivalの証明ではありません。4exact source Redirect、3protected virtual Shadow delegates、1元interface lambdaをcompiled ASMで照合し、既存R54～R56境界を維持しました。

Motion／Decision181件、production Gson→strict JavaScript42新規startケースと旧35／59／17／39／24／11／14を保持します。allbridge／genuinecombinedAPIの成功を確認しました。

## 次の検証

frozen producerから正式control85filesのfresh privateコピーを使い、自然進行Villagerのinstalled memory条件→追加条件内compute6境界→start→PATH write／Nav return→tryStart returnを直接IDで照合します。canonical／actualJFRACK・parse／cleanstop／元・control・predecessorR56・baseline85hash不変／producerと公開HEAD CIを確認するまでnative受入を主張しません。全memory理由／全compute branch・fallback RNG・cached reuse・TICK_RECOMPUTE・arrival、全Path候補・拒否・malus・effective cost、全Vanilla・FRONTIER・community、広いBoss戦、matched OFF／GPU・pixels、live Tank resize、section21全受入、最後のwhole-diff独立レビューは残ります。Draftと全体goalを継続します。
