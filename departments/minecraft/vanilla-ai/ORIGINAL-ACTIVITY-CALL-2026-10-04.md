# 元の活動更新呼出しの観測

## 実装範囲

`brain_activity` は明示指定する観測channelです。既定のchannel集合は変更しません。既存の `brain` channelによる `OneShot`／`GateBehavior` の全returnを含めず、活動更新の期間を有限の上限内で観測します。

固定したMinecraft 1.20.1 Forgeの `UpdateActivityFromSchedule.lambda$create$0(ServerLevel, LivingEntity, long)` が元から呼ぶ `Brain.updateActivityFromSchedule(long, long)` を、同じreceiver／引数で1回だけ実行します。`try/finally` でこの実際のvirtual callの観測frameを管理します。OFF、上限到達、違う対象、違うthreadでも元の呼出しを省略しません。元の例外は同じ例外として伝播し、正常returnの証拠は生成しません。

この呼出し内で次の境界だけを保持します。

| kind | 元の境界 | Decision stage |
| --- | --- | --- |
| `BRAIN_ACTIVITY_QUERY_RETURN` | `Brain.updateActivityFromSchedule` 内の元の `Schedule.getActivityAt(int)` virtual return | EVALUATION |
| `BRAIN_ACTIVITY_REQUIREMENTS_RETURN` | private `Brain.activityRequirementsAreMet(Activity)` の実際のboolean return | EVALUATION |
| `BRAIN_ACTIVITY_SET_RETURN` | private `Brain.setActiveActivity(Activity)` の正常return時のcached state | EXECUTION |
| `BRAIN_ACTIVITY_UPDATE_RETURN` | 元のvirtual update呼出しの正常returnと、その前後のcached state | EXECUTION |

`activityInvocationId` は同じ元の呼出しの範囲を表します。時刻の近さから追加した対応ではありません。ただし、未取得のmemory条件、独自overrideの内部、Behaviorの停止、移動結果まで説明するものではありません。normal void returnは活動切替成功のbooleanではありません。Scheduleが返すActivity、条件の戻り値、fallbackでsetterへ渡されたActivity、実際のactive setを分離します。CANDIDATE／SELECTION／RESULTを補いません。

## sourceで確認した制約

- `Brain.updateActivityFromSchedule` は `gameTime - lastScheduleUpdate > 20` の場合にcached時刻を更新し、元のvirtual `getSchedule`／`Schedule.getActivityAt` を実行します。観測側から追加のSchedule queryを実行しません。`Timeline` のcursorを動かすqueryを、説明のために再実行しません。
- 元のquery引数は `(int)(dayTime % 24000L)` です。負の値を別の正規化へ置き換えません。元のday／game引数とcached `lastScheduleUpdate` はsigned Java longを失わないdecimal stringとして保持します。
- private条件メソッドの正しい名前は `activityRequirementsAreMet` です。登録されたMemoryModule／MemoryStatusの検査を観測側で再実行しません。
- `setActiveActivity` は既にactiveなら変更を省略し、それ以外では元のmemory消去とactive set更新を行います。全Behaviorの停止を意味しません。
- このcall-site hookは既知のSchedule更新factoryを対象とします。任意の独自Brain／別のcall siteに同じ証拠があるとは主張しません。

## 有限性とcached state

既存のsession／run／snapshot／process／Arena／UUID／selection revision、server thread、時間、件数、byte上限を維持します。base `LivingEntity.brain` の参照が選択対象と一致する場合に限定します。frameは最大8階層、呼出しIDはsession内256個で、超過時にIDを再利用しません。unsupportedなnested callはcallerのframeへ誤って対応付けません。例外・rearm後にframeが漏れないように後片付けします。Brain／Scheduleのcomponent参照は既存の共有128個上限を使い、上限後は明示的に `NOT_EXPOSED` とします。

観測するcached fieldsは `activeActivities`／`coreActivities`／`defaultActivity`／`lastScheduleUpdate` です。既知のJDK／Guava set実装に限り、Activityは最大16個のprefixを保持し、件数とtruncationを明示します。custom setのiterator／size／toString、custom Brainのgetter、opaque triggerを説明のために呼びません。exact Activityの既知registry key、null、custom class、未登録を分離し、後の変更から切り離したcopyを保持します。

予算が切れた場合には内側または終端のreturnが保持されない場合があります。欠けたreturnを、元の呼出し・変更・例外が発生しなかった証拠として扱いません。updateの `preCallObserverCostNanos` と既存payload buildのcostは別に記録します。全observer overhead、GPU、無観測対照との差を測定した値ではありません。

## 現在の検証

元のgenuine Brain／Scheduleによるquery1回、`>20` guard、活動更新、例外の同一性、copy、OFF／channel／選択／thread／revision／時間／event／byteの回帰を確認しました。compiled fixture内でgenuine private条件／setterを1回ずつ実行し、true／falseと別Activityへのfallback、16件prefix、custom set不取得、8階層frame、256呼出しID、128component上限、例外後のframe解放を確認しました。4つのcompiled Mixin handlerのexact descriptor／target／required boundaryと、AI・queryを再実行しないdelegateも検証しています。

ローカルMotion／Decisionは149件成功。genuine Forge APIで全bridge／Mixinをcompileし、14のactual production Gson→JavaScriptケースと既存のtyped memory／independent control／owner／writer／Arena／overlay回帰が成功しました。Javaのuntransformed試験とcompiled fixtureは、Mixinをインストールした実機結果とは区別します。

## Frozen native R50

producer **8d84a393261617fe88f4489a95c10a08688e2a85**、`run-20261004100657-cc357948e11d`／`sess-20261004100657-01a645804a30`／`snapshot-20261004100657-1a29b18e9769`、process epoch1／Arena epoch0です。private fixtureは元controlの85ファイルから作成し、DayTime11850から自然に進行するadult Villagerを用いました。Brain memoryやactivityの選択結果をfixtureへ書き込みません。support floor／player／照明等のprelaunch setupは取得結果と分離します。

| revision | valid snapshots | normal update | original query | requirements／setter | burst |
| --- | ---: | ---: | ---: | ---: | --- |
| 1 | 124 | 200 | 10 | 1／1 | 212 events／336,712 payload bytes／WINDOW_ENDED |
| 2 | 120 | 200 | 9 | 0／0 | 209 events／332,890 payload bytes／WINDOW_ENDED |

両窓は `brain_activity` のみを明示指定し、200 local ticksの時間窓で終了しました。R49のgeneric Brain callback prefixと異なり、今回の取得は256-event上限へ達する前に期間を終えています。revision2のrequirements／setterゼロは保持された事実であり、未観測条件の復元には使いません。

revision1、game tick **40475**、dayTime引数 **12018**、`activity:1:67` において、以下の4つの実際の境界を同じoriginal update invocationで取得しました。

| source observation ID | 保持した事実 |
| --- | --- |
| `obs:forge-runtime:49144:105` | 元のSchedule queryが `minecraft:rest` を返した。実query引数とpassed dayTimeのJava remainderが一致 |
| `obs:forge-runtime:49144:106` | 元の `activityRequirementsAreMet(rest)` がtrueを返した |
| `obs:forge-runtime:49144:107` | 元のprivate setterへrestが渡され、正常return時のcached active setはcore+rest |
| `obs:forge-runtime:49144:108` | 元のupdateが正常return。cached active setは呼出し前core+idle、呼出し後core+rest |

400個の呼出しscopeそれぞれで終端updateを1件保持し、内部returnと同一Brain参照／revision／game tick／session／run／snapshot／process／Arena／UUIDを照合しました。19件の元queryについて、passed dayTimeからのquery引数と、元処理がquery前に更新したcached `lastScheduleUpdate` を照合しました。最初のsampled restは別の `obs:forge-runtime:49144:113`／tick40478です。直接のoriginal call scopeの証拠と、後続snapshotを混同しません。

この限定した実行対応は、単なる時刻の近さによる原因の推測ではありません。ただし、全MemoryModule条件のoperands、opaque trigger／独自override、Behavior停止、Navigationの採用、移動完了、完全なcandidate／selection／resultの受入は未取得です。既存Decision packetはEVALUATION／EXECUTIONとして保持し、欠けた段階を補いません。

same-snapshot PATH／Navigation reference matchは158件、sampled memory-change intervalは136件、Motion実サンプルは174件です。これらは元の活動変更と別の証拠であり、Path採用・到着結果には変換しません。

canonical **1,251 unique observations**は `EVIDENCE_COMPLETE`、SHA **a4106653caeaa3aef0c1b8575e37c7648097af3c9c2565fe2eec20d58463435e**。finalization SHA **c37872b8d15111f3f9ec8e3d80a806d4a01193f9366651b845a9ec0cc9a26831**。JFR **3,858,593 bytes**／SHA **31425dd444b507b146a3f9bf5d2804acbc838629e1dfed531621afcf9f82ca46**。clean ACK／drop0／queue0、owned launcher57300／runtime49144のOS上の終了を確認しました。元／control／predecessor R49／post-setup baselineの各85ファイルを再照合しました。

private canonical／JFR／native report／installed-activity proofを保全しています。最初のprivate proof helperのpresentation path2件のTypeErrorは元データを変更せず、既存構造を確認して追加のr3 helperで修正しました。compile済みhandlerのboolean unboxingを最初のASM testが除外していた診断も保全し、actual bytecodeに沿ってexact unboxingのみ許可しています。これらをnative failureとして記載しません。

## Source identities / hosted verification

[追加の3-owner／10-method／5-field source ledger](ACTIVITY-CALL-BYTECODE-LEDGER-2026-10-04.json)は固定mapped artifact `1b6e6a166fbc06c6d2422cd5cf515a508977479045095363d5b4c8b89cc7b4eb`、JDK disassembler、class／full disassembly／member slice hash／descriptorを保持します。ledger SHAは **7a7ec28380335065b45b516c09d323b420b37f5546fac3abea1a48c183908ab4**。source locatorは任意のtransformed resident classや全package解析の証明ではありません。元61-owner／R47／R48／R49台帳は保全します。

producerのsource push **37194234913**、source PR **37194238301**、pytest **37194238214**はSUCCESSです。actual PR checkout merge `8106688bfe102bb433ae29943fa9597a20d8af43` の親はbase `57e52f9ef44c082daf7abbb0b0f5ada3a258a406` とproducerです。149 focused／14 actual activity Gson markers、完全LAB source suite、portable Java、pinned MOD compile、dependency／resource／unit gatesを確認しました。hosted pytestは **3,149成功／332スキップ／8 warnings（282.32秒）**。後続documentation HEADのCIは別に確認します。

R49の実機証拠は[独立BehaviorControlの記録](ORIGINAL-INDEPENDENT-CONTROL-RETURN-2026-10-04.md)に保全しています。完全Goal／Brain／Navigation result、Path候補／拒否／effective cost、広いBoss戦、matched observer-effect／GPU／pixels、live Tank resize、section21全受入と最後のwhole-diff独立レビューは残っています。Draftと全体goalは継続します。
