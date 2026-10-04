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

## Frozen native R57

producer **d1269520e91eb639cfdad6c65b2a7465733a9179**、run-20261004160121-0a03e7d121f3／sess-20261004160121-d9cd4cd03963／snapshot-20261004160121-5f3f5774ac2a、process epoch1／Arena epoch0、private adult Villager UUID55555555-6666-7777-8888-000000000001です。正式control85ファイルのfresh privateコピーを使い、自然day11850から進行しました。desired result／Brain memory／navigationをseedしていません。

**344新規start events、169 complete tryStart groups、1 partial group**を取得しました。hasRequiredMemoriesはfalse166／true4、追加条件はfalse2／true2、tryStart正常returnはfalse168／true1、start正常dispatchは1です。completeは取得された元short circuitと正常returnの一致を意味し、全MemoryStatus・priority・Activityの選択理由や到着ではありません。

**1組の13-event direct chain**で元memory条件→追加条件内compute6境界→追加条件→PATH書込み→Navigation戻り値→Sink start戻り値→元start dispatch→tryStart戻り値を照合しました。parent try-start:1:68／compute compute:1:1／Sink sink:1:2、game tick 40477、runtime40028、component component:1:1。実際のsource ID末尾は **185 → 187 → 188 → 189 → 190 → 191 → 192 → 193 → 194 → 195 → 196 → 197 → 198**です。

元memory=true／extra=true／private reached=false／Path.canReach=false／compute=true／Navigation=true／tryStart=trueを別々に保持します。元distance／closeEnoughは38／4。元格納Sink.path、PATH書込み引数、Navigation引数、Sink before/after PATH・Nav raw参照はpath:1:20で一致し、元Navはabsent→present、speed0.5です。元virtual条件・interface呼出し・child frame ID、全UUID／run／session／snapshot／process／Arena／revision、元gameTimeArgument、instanceIdentity、eventIndexと生のPath参照を照合しました。時間や位置の近さから関係を推測していません。Navigationのtrueは移動成功・到着を証明しません。

R55/R56のcomputeは2 complete6-event groupsを保持しました。compute:1:1／tick40477のsource187→188→189→190→191→192はdistance38／4、compute:2:1／tick41140のsource925→926→927→928→929→930はdistance33／4で、どちらもreached=false／canReach=false／compute=trueです。しかしrevision2のparent try-start:2:102は条件2点のprefixだけです。PATH書込み／Nav戻り値も残りますが、256events上限後のstart dispatch／tryStart正常returnは未取得です。この組を2本目の完全開始chain・成功・失敗・未呼出しとして補いません。

| revision | valid snapshots | 全callbacks／payload bytes | Motion実サンプル | same-snapshot PATH／Nav参照一致 | callback終了理由 |
| --- | ---: | --- | ---: | ---: | --- |
| 1 | 124 | 256／287343 | 68 | 60 | EVENT_BUDGET |
| 2 | 120 | 256／264514 | 64 | 56 | EVENT_BUDGET |

全512 callbacks／244 valid snapshots、canonical **1,241 unique observations**はEVIDENCE_COMPLETE、SHA **e866e5d0c8a82d431695bc489ca7eacb6cfd2c006f6e36ebcacac5e600b06d72**、finalization SHA **6a4beed4a5e4854376150dcdb619f3e81e74f84cfeb6da993b63fadef095782a**です。既存200ticks／256events／524,288bytes／32nodesを維持し、revision1 local101..301 exclusiveとrevision2 local721..921 exclusiveはEVENT_BUDGETで閉じています。132 Motion実サンプル／116 same-snapshot参照一致は別の事実です。

clean ACK／drop0／queue0／finalWriterSeq1241、owned launcher52368／runtime40028のOS終了、元／control／predecessor R56／baseline各85ファイルのhash不変を確認しました。正式save、private runtime data、mapped JAR、source bodyはGitHubに追加しません。

JFR設定34,835bytes／SHA d4d74f3594bfe342397f53aaa75a7551e7b2d9ac6f86c7ca2bc016690501b37dのpreflight、actual start／stop ACK、保存fileのJDK parseを確認しました。JFR **3786978bytes**／SHA **4d83c144ec4ffeb5d64602d4c7c74b3b689e50e6b6b4f428b300ba3ff926c5db**、63秒／ExecutionSample321／CPULoad60／ThreadCPULoad440です。単独記録であり、matched OFF／GPU／pixels／observer-effect受入ではありません。過去のR51未取得を含む記録を保全します。

## Hosted producer CI

producer push37215124788／PR source37215129322／pytest37215129331はSUCCESS。actual PR checkout merge **858cea2f75813e6ecd718cb6637008dca42330ce**の親は57e52f9ef44c082daf7abbb0b0f5ada3a258a406／d1269520e91eb639cfdad6c65b2a7465733a9179です。181focused／42新規actual Gson、および旧35／59／17／39／24／11／14、完全LAB source／portable Java／pinned MOD compile／dependency／resource／unit gatesを確認しました。hosted pytestは**3,149 passed, 332 skipped, 8 warnings in 230.13s**。document publication HEADのCIは別に確認します。

## 残る検証

個別MemoryStatus／entryConditionの元checkMemory戻り値、全priority／Activity候補理由、nativeの他compute枝・duration／fallback RNG・cached reuse・TICK_RECOMPUTE・例外／cap／rearm、完全Brain理由と到着、全Path候補・拒否・malus・effective cost、全Vanilla・FRONTIER・community、広いBoss戦、matched OFF／GPU・pixels、live Tank resize、section21全受入、最後のwhole-diff独立レビューは残っています。Draftと全体goalを継続します。
