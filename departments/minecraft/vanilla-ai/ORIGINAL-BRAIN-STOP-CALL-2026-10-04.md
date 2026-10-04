# 元のBrain停止呼出しとmemory消去

## 実装範囲

明示指定する既存`brain_navigation` channelに、固定Minecraft 1.20.1 Forgeのexact `MoveToTargetSink`の停止観測を追加します。既定channel集合は変更しません。元のsynthetic bridge→protected concrete `stop`を、単一のvirtual Shadow delegateと`try/finally`で囲みます。任意のSink subclassは観測対象外です。

元のconcrete `stop`の中で、元のvirtual Navigation停止の正常void return、WALK_TARGET／PATHそれぞれの元のvirtual memory消去の正常void return、Sinkの正常void returnを分離します。同じ直接取得した`sinkInvocationId`へ接続し、時刻の近接から親子・因果関係を補いません。

`BRAIN_PATH_NAVIGATION_STOP_RETURN`／`BRAIN_PATH_MEMORY_ERASE_RETURN`と停止時の`BRAIN_PATH_SINK_RETURN`は、Decision Modelの`EXECUTION`／`brain_navigation: PARTIAL`へ接続します。元の例外はそのまま伝播し、失敗したcallの正常returnを作りません。既に完了したcallの正常returnは別の事実として保持します。正常void returnは、custom receiverによる状態消去、停止理由、目的地への到着RESULTを保証しません。

## sourceとcached stateの境界

[追加source ledger](BRAIN-STOP-CALL-BYTECODE-LEDGER-2026-10-04.json)は、同じ固定mapped artifactの4 owners／9 methods／6 fieldsをclass、disassembly、member sliceのhashとdescriptorで保持します。ledger SHAは`85a7d8349787bc53a4091eacda7a9fc9c43a497e4335b0917ce21afd88681035`。以前の台帳は変更しません。cached Path、speed、wrapperの既知field契約は既存[R52](ORIGINAL-BRAIN-NAVIGATION-CALL-2026-10-04.md)、[R51](ORIGINAL-NAVIGATION-RESULT-2026-10-04.md)、typed memoryのsource証明を維持します。

元の`Behavior.doStop`は、virtual generic `stop`を呼ぶ**前**にstatusをSTOPPEDへ設定します。concrete Sink停止のbefore snapshotから、RUNNING→STOPPEDの変化や停止理由を推測しません。

元のSink `stop`は、WALK_TARGETのquery／到達条件を確認し、条件によってNavigationのstuck状態とRNG／cooldownを処理した後、Navigation停止、WALK_TARGET消去、PATH消去、Sink Pathへのnull代入を実行します。今回のhookは、この後半の元のcall siteとconcrete呼出し終了です。観測側はgetter、target、到達条件、stuck query、RNG、memory query、AI処理を再実行しません。前半のbranch reasonは未取得です。

before／afterは宣言したcapture boundaryのbase cached Path／speed／Brain PATHとWALK_TARGET slotです。PATHは既存の共有Snapshot参照と既知wrapper fieldを保持します。WALK_TARGETは**exact HashMap内の登録済みOptional slotが非emptyかどうかだけ**を読み、値の型、targetの位置、到達条件を取得・検証しません。custom mapやOptionalでないentryは明示的な未取得です。Optional非emptyは、有効なWalkTarget値や実行可能な移動を保証しません。

base `PathNavigation.stop`はcached Pathをnullへ設定するだけで、speedを消去しません。custom overrideは正常returnしてもPathを保持できます。`Brain.eraseMemory`は元のvirtual Optional `setMemory`へ委譲し、未登録slotを新たに登録しません。custom overrideが正常returnしてもslotが残る場合を、cached stateの別の事実として表します。

既存のexact owner／cached Brain／cached Navigation、session／run／snapshot／process／Arena／選択revision、server thread、時間／event／byte／writerの境界を維持します。frame8段階／256 invocation IDs、component128個、共有Snapshot参照256個、typed Path node prefix64個の上限を再利用します。stop site追加後も、start-only PATH write／moveToのreceiptがstop frameを取得しないこと、stop receiptがstart frameを取得しないことを確認します。

## 検証

genuine元のconcrete `stop`のabsent-WALK_TARGET branchで、Brain getter3回、Navigation getter1回、元query1回、Navigation停止1回、memory消去2回、Optional write2回を確認してから、停止frameが取得できないREDを再現しました。元のstop bytecodeを用いる明示的なtest fixtureでは、private field access／protected helper／観測call siteだけを試験用に置換しています。到達条件／RNG branchや、インストールされたMixinの実機証明へ置き換えません。

custom queryがfalseを返し、Navigation／erase overrideが状態を保持するケース、元例外の同一性、途中まで完了したreturnの保持、detached copy、未登録／壊れたslot、custom map、rearm中のframe除去、OFF／thread／owner／revision／時間／event／byte／writer、Path／component上限、非有限speed、phase分離を確認しました。compiled Redirectのexact descriptor／require1・require2／単一delegate、stop Shadow lambdaの単一virtual callも確認しました。既存のprotected Shadow検証は、同じdescriptorのstop delegateだけを追加して維持しています。

Motion／Decision **161件成功**。**39件のactual production Gson→JavaScriptケース**はNavigation停止10件／memory消去19件／Sink return10件で、bounded consumer契約を通りました。EXECUTION／PARTIALのみへ接続し、CANDIDATE／SELECTION／到着RESULTを補いません。

hash照合したgenuine依存関係で全bridge／Mixinをcompileし、combined API／owner／writer／Arena／overlay回帰が成功しました。既存24件のBrain Navigation、11件のNavigation、14件のactivity Gsonも維持しています。今回のfrozen native実機証拠とexact HEADのhosted CIは未取得です。source／genuine API／test fixtureの成功を実機検証済みとは扱いません。

完全な停止・到達条件／RNG／compute branchの理由、全Path候補・拒否・cost、広いBoss戦、Vanilla／FRONTIER／community、matched observer-effect／GPU／pixels、live Tank resize、section21全受入、最後のwhole-diff独立レビューは残っています。Draftと全体goalを継続します。
