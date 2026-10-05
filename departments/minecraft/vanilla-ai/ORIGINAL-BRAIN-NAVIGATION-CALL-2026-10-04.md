# 元のBrain PATH書き込みとNavigation呼出し

## 実装範囲

`brain_navigation` は明示指定する観測channelです。既定のchannel集合は変更しません。固定Minecraft 1.20.1 Forgeのexact `MoveToTargetSink` に限定し、synthetic bridgeからconcrete `start`／`tick`、および元の`tick`からの`start`再呼出しを、元のvirtual delegateを一度だけ実行する`try/finally`で囲みます。任意のSink subclassは観測対象外です。

同じ`sinkInvocationId`内で、元のPATH `Brain.setMemory`の正常void return、元のvirtual `PathNavigation.moveTo(Path,double)`の最終boolean、concrete呼出しの正常void returnを別々に記録します。nested restartのparent IDは取得済みの元呼出しだけを表し、時刻の近接から親子関係を補いません。例外時には例外をそのまま伝播し、正常returnを生成しません。rearm、取得対象外のnested呼出し、例外後もframeを残しません。

`BRAIN_PATH_MEMORY_WRITE_RETURN`／`BRAIN_PATH_NAVIGATION_RETURN`／`BRAIN_PATH_SINK_RETURN` はDecision Modelの`EXECUTION`／`brain_navigation: PARTIAL`へ接続します。Sinkのvoid returnやNavigationのtrueを、目的地への到着RESULT、候補選択、完全なBrain decisionへ変換しません。R51のbase Navigation returnと、今回のcall siteにおける最終virtual returnは別の境界です。

## sourceとcached stateの境界

[追加source ledger](BRAIN-NAVIGATION-CALL-BYTECODE-LEDGER-2026-10-04.json)は、同じ固定mapped artifactの2 owners／11 methods／3 fieldsをclass、disassembly、member sliceのhashとdescriptorで保持します。ledger SHAは`e0bc713fb1626c8b016c0ce2afed6ae36cea1568dc074a3b774cd26426e23844`。元の`stop`／`tryComputePath`とBehaviorのdispatchもsource上で照合していますが、それらのbranch解析やhookを完成したとはしません。以前の台帳は変更しません。

元の`start`はPATH書き込み後にNavigationへPathとspeedを渡し、booleanを破棄します。元の`tick`はNavigation Pathのraw参照が異なる場合にSinkのcached Pathを更新してPATHを書き込み、後段では元の条件に従って経路再計算と`start`を実行します。観測側はBrain getter、Navigation getter、tracker、path query、AI処理を再実行しません。

before／afterは宣言したcapture boundaryにおけるbase cached fieldsです。passed Path、cached Brain PATH、cached Navigation Pathを分け、raw参照一致を独立して記録します。cached Brain memoryはexact `HashMap`とexact `ExpirableValue`の既知fieldだけを読みます。custom map／wrapper／不明な値は`NOT_EXPOSED`です。正常なcustom `setMemory` returnも、渡した値の保持を保証しません。

Path参照には既存Snapshotの256個上限とrevisionを共有し、Sink／Brain／Navigation componentには別の128個上限を使います。frameは8段階／256 invocation IDsまで、typed Path node prefixは既存64個までです。session／run／snapshot／process／Arena／選択revision、exact owner／cached Brain／cached Navigation、server thread、時間／event／byte／writerの既存境界を維持します。上限後の参照、非有限speed、取得できないmemoryは明示的な未取得です。

## 検証

genuine元の`start`による書き込み／Navigation／getterの実行回数を確認してから、元のconcrete `start`とearly `tick`のbytecodeを使用する明示的なtest fixtureで、同じframeの書き込み→Navigation→void returnを確認しました。fixtureのprivate field accessとprotected delegateの置換は試験専用です。後段の`tryComputePath` branchや、インストールされたMixinの実機証明に置き換えません。

base Navigationがtrueを返した後にcustom overrideがfalseを返すケース、元例外の同一性、例外前の正常writeの保持、detached copy、OFF／thread／owner／context／revision／時間／event／byte／writer、depth／invocation／component／Path上限、rearmを確認しました。6個のexact Redirect descriptor／`require=1`／単一delegateと、protected Shadow lambdaの単一virtual callもcompiled bytecodeで確認しました。

Motion／Decision **157件成功**。hash照合したgenuine依存関係で全bridge／Mixinをcompileし、combined API／owner／writer／Arena／overlay回帰が成功しました。**24件のactual production Gson→JavaScriptケース**はwrite9件／Navigation7件／Sink return8件で、すべてbounded consumer契約を通りました。既存11件のNavigation Gson、14件のactivity Gsonも維持しています。

## Frozen native R52

producer **4820cd1d18e0fcbd455e63bd6f39c6eccca11b11**、`run-20261004114729-5f88ba1b5db9`／`sess-20261004114729-5bfc7ce87d86`／`snapshot-20261004114729-7618abc66950`、process epoch1／Arena epoch0です。private adult Villager UUIDは`55555555-6666-7777-8888-000000000001`。元control85ファイルからcopyし、R50／R51と同じprelaunch floor／照明／player設定、DayTime11850の自然進行を使用しました。Brain memoryやNavigation結果をfixtureへ書き込みません。

| revision | valid snapshots | write／Navigation／Sink normal returns | burst | Motion実サンプル | same-snapshot PATH／Navigation参照一致 |
| --- | ---: | --- | --- | ---: | ---: |
| 1 | 120 | 2／2／121 | 125 events／313,255 payload bytes／WINDOW_ENDED（101..301 exclusive） | 75 | 65 |
| 2 | 120 | 1／1／126 | 128 events／317,460 payload bytes／WINDOW_ENDED（701..901 exclusive） | 91 | 83 |

各窓は`brain_navigation`のみ、200 ticks／256 events／524,288 bytes／32 search nodesの既存上限です。247の元呼出しで253件のnormal-return証拠を取得しました。3件のstartと244件のtickです。3組のwrite→Navigation→Sink returnは同じ直接取得したinvocation IDと同じgame tickに属し、eventIndexの順序とactual source methodを照合しました。

| invocation ID | game tick | PATH write observation ID | Navigation observation ID | Sink return observation ID | cached canReach |
| --- | ---: | --- | --- | --- | --- |
| `sink:1:1` | 40477 | `obs:forge-runtime:11276:39` | `obs:forge-runtime:11276:40` | `obs:forge-runtime:11276:41` | false |
| `sink:1:79` | 40567 | `obs:forge-runtime:11276:190` | `obs:forge-runtime:11276:191` | `obs:forge-runtime:11276:192` | true |
| `sink:2:28` | 41040 | `obs:forge-runtime:11276:565` | `obs:forge-runtime:11276:566` | `obs:forge-runtime:11276:567` | false |

3組とも`START_FROM_BRIDGE`、original virtual booleanはtrue、passed／cached speedは0.5、passed Pathとcached Brain PATH／cached Navigation Pathのraw参照一致はtrueです。最初の`sink:1:1`では、beforeのBrain PATHとNavigation Pathがabsent、Sink Pathが`path:1:17`、afterの3箇所が同じ参照でした。これはこの元呼出し内のwrite／return／cached状態の直接証拠であり、searchからの採用理由、完全なBrain decision、目的地への到着を証明しません。2件の`canReach=false`とtrue returnは両立します。

この実機窓では`START_FROM_TICK`のnested restart、`TICK_PATH_RECONCILE`、false return、custom receiver／map、identity上限、stop／後段compute branchを取得していません。genuine API／test fixtureの範囲を実機結果へ置き換えません。166件のMotion実サンプルと148件のsame-snapshot参照一致も、到着や未取得の因果関係を補いません。

canonical **1,041 unique observations**は`EVIDENCE_COMPLETE`、SHA **5d1baa2770e4730db1b80114e05a38ec5ee9c1aea711fee70f00cce38cf81997**。finalization SHA **b0792ce5add1acb11e4a46ebe968ea0a66e2c7376794d2d7a710fe0b82f67254**。clean ACK／drop0／queue0／finalWriterSeq1041、owned launcher57468／runtime11276のOS上の終了と、元／control／predecessor R51／fixture baseline各85ファイルのhash不変を確認しました。

JFR設定34,835 bytesのSHA **d4d74f3594bfe342397f53aaa75a7551e7b2d9ac6f86c7ca2bc016690501b37d**を起動前に照合し、actual`Started recording 1`／`Stopped recording`応答を要求しました。保存JFR **4,061,180 bytes**、SHA **ec6390da5cc6eb7a593a5ac5e75ffbb1ddeca89bebfbe7bd74b95aab1739959e**はJDK`jfr summary`でparse成功です。記録期間63秒にExecutionSample350／CPULoad60／ThreadCPULoad433を含みます。単独の取得記録であり、matched OFF対照、GPU／pixels、性能上限や観測影響の受入にはしません。R51のJFR未取得記録は保全しています。

private canonical／native report／installed-call proof／JFR／post-setup baselineと以前の証拠を保全しています。GitHubへsave、JAR、source body、private runtime dataを追加していません。hosted producer／publication CIは別に確認します。

## 残る検証

完全なBrain条件／後段branch／Path候補と拒否・cost、広いBoss戦、matched observer-effect／GPU／pixels、live Tank resize、section21全受入と最後のwhole-diff独立レビューは残っています。Draftと全体goalを継続します。


## Hosted producer CI

source push **37199846597**／source PR **37199849389**／pytest **37199849388**はSUCCESSです。actual PR checkout merge `d40da6d9cf3bdf86a6c393b1abb21e2b7a9cd502`の親はbase `57e52f9ef44c082daf7abbb0b0f5ada3a258a406`とproducer `4820cd1d18e0fcbd455e63bd6f39c6eccca11b11`。157 focused／24 actual Brain Navigation Gson markers、完全LAB source suite、portable Java、pinned MOD compile、dependency／resource／unit gatesを確認しました。hosted pytestは**3,149成功／332スキップ／8 warnings（280.62秒）**。documentation publication HEADは別に確認します。
