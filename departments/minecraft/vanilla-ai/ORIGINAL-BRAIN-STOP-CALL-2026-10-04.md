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

hash照合したgenuine依存関係で全bridge／Mixinをcompileし、combined API／owner／writer／Arena／overlay回帰が成功しました。既存24件のBrain Navigation、11件のNavigation、14件のactivity Gsonも維持しています。

## Frozen native R53

producer **e3d7bf6840f20e0e8bbabb15f62f4dc807a00f6e**、`run-20261004122747-d6dc8cb6a07c`／`sess-20261004122747-182548defd18`／`snapshot-20261004122747-21617b0d75cf`、process epoch1／Arena epoch0です。private adult Villager UUIDは`55555555-6666-7777-8888-000000000001`。元control85ファイルからcopyし、R50〜R52と同じprelaunch floor／照明／player設定、DayTime11850の自然進行を使用しました。memoryや停止結果をfixtureへ書き込みません。

| revision | valid snapshots | Stop／WALK_TARGET erase／PATH erase／Stop終了 | 全channel events／payload bytes | Motion実サンプル | same-snapshot PATH／Navigation参照一致 |
| --- | ---: | --- | --- | ---: | ---: |
| 1 | 120 | 2／2／2／2 | 133／323,007 | 76 | 64 |
| 2 | 120 | 2／2／2／2 | 134／324,769 | 91 | 81 |

各窓は`brain_navigation`のみ、200 ticks／256 events／524,288 bytes／32 search nodesの既存上限で、WINDOW_ENDED（101..301／701..901 exclusive）です。267件の正常return証拠は、4組の停止call（16件）、4組のstart call（12件）、239件のtick returnです。247 invocation IDsをrevisionごとに照合しました。4組の停止callに部分取得はありません。

| invocation ID | game tick | Navigation stop observation ID | WALK_TARGET erase observation ID | PATH erase observation ID | Sink return observation ID |
| --- | ---: | --- | --- | --- | --- |
| `sink:1:18` | 40426 | `obs:forge-runtime:44292:49` | `obs:forge-runtime:44292:50` | `obs:forge-runtime:44292:51` | `obs:forge-runtime:44292:52` |
| `sink:1:87` | 40544 | `obs:forge-runtime:44292:197` | `obs:forge-runtime:44292:198` | `obs:forge-runtime:44292:199` | `obs:forge-runtime:44292:200` |
| `sink:2:42` | 41050 | `obs:forge-runtime:44292:601` | `obs:forge-runtime:44292:602` | `obs:forge-runtime:44292:603` | `obs:forge-runtime:44292:604` |
| `sink:2:112` | 41173 | `obs:forge-runtime:44292:750` | `obs:forge-runtime:44292:751` | `obs:forge-runtime:44292:752` | `obs:forge-runtime:44292:753` |

4組ともbeforeのSink Path／Brain PATH／Navigation Pathはpresentで、WALK_TARGET Optional slotも非emptyです。Navigation停止のnormal return後にはcached Navigation Pathがabsentになり、Brain PATHはまだpresentでした。その後、WALK_TARGET消去、PATH消去、Sink終了のnormal returnsを同じ直接取得したinvocation ID／gameTimeArgument／source method／eventIndex順序で照合しました。afterの3箇所のPathとWALK_TARGET slotはabsent、Navigation speedは0.5のままでした。最初の`sink:1:18`のbefore Path参照は`path:1:2`です。

これはこの元call内で取得したnormal returnsとbase cached状態であり、WALK_TARGETの値、到達条件、RNG／cooldown、上流の停止理由、目的地到着を証明しません。167件のMotion実サンプルと145件のsame-snapshot参照一致からも、到着や未取得の因果関係を補いません。custom保持、例外、未登録・壊れたslot、参照上限、非有限speedはgenuine API／test fixtureの範囲で、このnative窓では取得していません。nested restart／tick reconciliationも未観測です。

canonical **1,081 unique observations**は`EVIDENCE_COMPLETE`、SHA **a36b555e526e0f6d366629a7df017a4947ce5fa9b7a2cc0588d990cb357a6095**。finalization SHA **beb31de8873d406b673fb5b4540fcc8d2704be53d1a754ff5feed658a1eff4b5**。clean ACK／drop0／queue0／finalWriterSeq1081、owned launcher41296／runtime44292のOS上の終了と、元／control／predecessor R52／fixture baseline各85ファイルのhash不変を確認しました。

JFR設定34,835 bytesのSHA`d4d74f3594bfe342397f53aaa75a7551e7b2d9ac6f86c7ca2bc016690501b37d`を起動前に照合し、actual start／stop応答を要求しました。保存JFR **3,944,464 bytes**、SHA **4d4bd4e738df3f0af52f23bc2f8d009d6f5c444c530585a5aba95c340f6d0281**はJDK`jfr summary`でparse成功です。記録期間63秒にExecutionSample348／CPULoad60／ThreadCPULoad446を含みます。単独記録であり、matched OFF対照、GPU／pixels、性能上限や観測影響の受入ではありません。

private canonical／native report／installed-stop proof／JFR／post-setup baselineと以前の証拠を保全しています。GitHubへsave、JAR、source body、private runtime dataを追加しません。

## Hosted producer CI

source push **37202102207**／source PR **37202106471**／pytest **37202106507**はSUCCESSです。actual PR checkout merge`a5460b26534ad8ce709ea87a21e486ccbb491afc`の親はbase`57e52f9ef44c082daf7abbb0b0f5ada3a258a406`とproducer`e3d7bf6840f20e0e8bbabb15f62f4dc807a00f6e`。161 focused／39 actual Brain stop Gson markers、完全LAB source suite、portable Java、pinned MOD compile、dependency／resource／unit gatesを確認しました。hosted pytestは**3,149成功／332スキップ／8 warnings（256.39秒）**。documentation publication HEADは別に確認します。

## 残る検証

完全な停止・到達条件／RNG／compute branchの理由、全Path候補・拒否・cost、広いBoss戦、Vanilla／FRONTIER／community、matched observer-effect／GPU／pixels、live Tank resize、section21全受入、最後のwhole-diff独立レビューは残っています。Draftと全体goalを継続します。
