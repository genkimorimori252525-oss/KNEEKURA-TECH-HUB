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

**この変更のfresh native観測はまだ未検証です。** R49の実機証拠は[独立BehaviorControlの記録](ORIGINAL-INDEPENDENT-CONTROL-RETURN-2026-10-04.md)に保全し、この変更の証拠へ置き換えません。次は元ワールドのcopyと前世代・baselineを保全したprivate fixtureで、自然なidle→restが入る観測期間を設定し、実際のquery／条件／setter／updateを同じ呼出しIDで照合します。完全な活動原因・移動結果、全Goal／Brain受入は残っています。
