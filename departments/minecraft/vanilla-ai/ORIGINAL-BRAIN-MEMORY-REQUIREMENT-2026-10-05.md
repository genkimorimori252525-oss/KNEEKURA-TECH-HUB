# 元のBrainメモリ要求判定と有限の実戻り値

[R57の元開始条件](ORIGINAL-BRAIN-TRY-START-CALL-2026-10-05.md)内で、Behavior.hasRequiredMemoriesが実際に呼んだvirtual Brain.checkMemoryの引数と正常booleanを保持します。元loopのentryCondition・owner.getBrain・checkMemory・first-false short circuitを変更せず、元checkMemoryを1回だけ実行します。memory／AI／getter／entry iterator／registry queryを追加しません。exact選択MoveToTargetSink/current cached Brain・Nav/rawNavowner、現在のHAS_REQUIRED_MEMORIES source scopeの一致が必要です。

元Brain.checkMemoryのbase bodyはcached memoriesのslotを調べ、未登録ならfalse、REGISTEREDならtrue、VALUE_PRESENT／VALUE_ABSENTはOptionalのpresenceで判定します。しかしvirtual callにはcustom override／Mixinがあり得るため、記録は元実戻り値です。observerがslotを読み直して理由やbooleanを再計算することはありません。元Sink constructorの要求はCANT_REACH_WALK_TARGET_SINCE=REGISTERED／PATH=VALUE_ABSENT／WALK_TARGET=VALUE_PRESENTです。moduleはこれら3つのraw identityだけをlabelし、unknown/null moduleはNOT_EXPOSED、null MemoryStatusもNOT_EXPOSEDとします。未知のMOD memoryを既知型へ偽装しません。

新しいBRAIN_PATH_MEMORY_REQUIREMENT_RETURNはEVALUATION／brain_navigation／PARTIALです。元predicateが正常returnし、実際のsource checkの正常returnを1件以上取得した場合だけ、独立requirementInvocationIdと元condition boolean、checkIndex順のpassed module／requested MemoryStatus／元check booleanのprefixを記録します。最大8件、9件目の元正常returnでchecksTruncated=trueです。check配列の内容から元predicateのbooleanを書き換えたり、全eligibility・priority・Activity・internal memory理由・到着を取得済みとは扱いません。空のloop／未対応source／例外／上限後の未取得は、未呼出し・成功・失敗へ補いません。旧R57／compute／Sink payloadは変更しません。

requirement IDs256／prefix8、共有StartFrame256／depth8／component128、既存200ticks／256events／524,288bytes／32nodesを維持します。unsupported source owner／Brain／Behaviorでは元callを1回実行し、callback中は古いrequirementを一時抑止します。同じ元loop内に不一致sourceが混ざった場合は新requirement summary全体を抑止し、欠測を圧縮した連続checkIndexへ偽装しません。旧memory条件の実booleanは独立に維持します。正しいnested predicateは別IDに記録し、元parentを復元します。source delegate中のrearm／clear／cached-owner・context変更／thread／時間・event・byte・writer gateで、旧returnを新sessionへ付けません。元例外とtryfinally cleanupを維持します。observerCostNanosは既存のsummary build／first-byte-check範囲で、prefix収集を含む観測全体のCPU費用ではありません。

[追加ledger](BRAIN-MEMORY-REQUIREMENT-BYTECODE-LEDGER-2026-10-05.json)はsame mapped artifactの4owners／4method slices（Sink constructors2を含む）／5fields、9member hashes／exact descriptorsです。ledger SHA **39001d22fff449cbd898bbf0d43cf10e435e5509b5128b5e94d47cc56c92e4ae**。JDK／artifact／class／disassembly／member slicesを照合しました。静的sourceはinstalled transformed classのattestationではありません。旧ledgerを保全し、source body／JARはGitHubへ追加しません。

## Source／fixture検証

元protected hasRequiredMemoriesのbytecodeをcloneし、試験用private entryCondition accessorと元checkMemory source delegateだけを置換しました。元owner.getBrain・loop・first falseの元bytecodeを保持し、genuine baselineと元getter／query回数・booleanを照合するRED→GREENを行いました。3既知MemoryStatus／false条件／全3true／unknown・null module／null status／custom virtualtrue／9-entry prefix8＋tail／requirementID256、nested arbitrary callback抑止と正しいnested scopes分離、空loop、source args不一致／genuine loop中のforeign Brain混入（RED→GREEN）、元例外同一性、OFF／channel／cachedBrain／rawNavowner／revision／time／event1／byte1／thread／rearm／component128／writer failureとframe解放を検査しました。synthetic test map／reflection writes／unsafe subjectはfixtureだけで、native全branch／AI理由の証明ではありません。

compiled ASMでsource-specific mandatory Redirectのexact method／target／handler args／require1、1production delegate、各OFF／observed branchの元virtual checkMemory1回を照合しました。旧R54～R57 compiled境界とGsonを維持します。Motion／Decision188件、production Gson→strict JavaScript16新規requirementケースと旧42／35／59／17／39／24／11／14です。null等のmalformed nested checkを安全に拒否するJS regressionもRED→GREENです。allbridge／genuinecombinedAPIの成功を確認しました。

## Frozen native R58

producer **263a9cf2b7d98b21e50b13fb2ee9ed1bb0ab8e03**、run-20261004164937-0ace1c53a83a／sess-20261004164937-33681c253b81／snapshot-20261004164937-5f613bcfa9da、process epoch1／Arena epoch0、private adult Villager UUID55555555-6666-7777-8888-000000000001です。正式control85filesのfresh privateコピー、自然day11850から進行し、desired Brain memory／path／resultをseedしていません。

**80新規requirement receipts**に、元virtual checkMemoryの**240正常returns**（各3件）が含まれます。個別checkに別observation IDを付けたのではなく、1receipt内のsource prefixです。CANT_REACH_WALK_TARGET_SINCE／REGISTERED=trueが80、PATH／VALUE_ABSENT=trueが80、WALK_TARGET／VALUE_PRESENT=falseが79／trueが1でした。これは元実戻り値で、cached memoryを読み直してboolean・未登録／欠測理由を再計算していません。

**79 complete requirement→元memory条件→tryStart正常return groups、1 partial group**です。partialではrequirement正常return自体は取得済みですが、上限後の元memory条件／tryStart receiptは未取得であり、そのtailを失敗・未呼出し・完全開始処理へ補いません。native prefixは3件でtruncation=false、synthetic9件／ID256／custom／null等のfixtureと区別します。既知constructorの実source順序とfirst-falseを照合しましたが、全priority・Activity eligibilityや内部slot理由の受入ではありません。

全3要求がtrueとなった **memory-requirement:1:8／try-start:1:8**（tick40437、runtime26392）では、requirement summaryと[R57の13点](ORIGINAL-BRAIN-TRY-START-CALL-2026-10-05.md)をつないだ**1 complete14-event direct chain**を照合しました。実source ID末尾は **148 → 149 → 150 → 151 → 152 → 153 → 154 → 155 → 156 → 157 → 158 → 159 → 160 → 161**です。computecompute:1:1／Sinksink:1:22、raw path:1:6の元格納／PATHwrite／Nav引数／before-after参照、exact UUIDと全run／session／snapshot／process／Arena／revision、元gameTimeArgument、instanceIdentity、eventIndexを照合しました。memory=true／extra=true／reached=false／Path.canReach=true／compute=true／Nav=true／tryStart=true、元distance／closeEnoughは8／0です。R55/R56の6compute境界は1complete／partial0です。今回は元Path.canReach=trueをnativeで取得しましたが、NavのtrueやPath.canReachは実到着ではありません。

| revision | valid snapshots | 新requirement receipts | 全callbacks／payload bytes | Motion実サンプル | same-snapshot PATH／Nav参照一致 | 終了理由 |
| --- | ---: | ---: | --- | ---: | ---: | --- |
| 1 | 120 | 8 | 256／325010 | 98 | 91 | EVENT_BUDGET |
| 2 | 120 | 72 | 256／277683 | 83 | 72 | EVENT_BUDGET |

全512 callbacks／240 valid snapshots、canonical **1,340 unique observations**はEVIDENCE_COMPLETE、SHA **fe63d8b3a799a7f891a2a36164b03386f229858489064e1c7ac11273979daafd**、finalization SHA **8b60f53b8e51b2d8f6144f727746adff4bd1ee4f299fb70911f245e5c42f17e8**。旧start160events／79completegroupsと旧compute4events／predicate2eventsを保持します。既存200ticks／256events／524,288bytes／32nodes、revision1 local101..301 exclusiveとrevision2 local701..901 exclusiveのEVENT_BUDGETを維持しました。181Motion実サンプル／163same-snapshot参照一致は独立した事実です。全tail／全AIを取得済みとはしません。

clean ACK／drop0／queue0／finalWriterSeq1340、owned launcher23544／runtime26392のOS終了、元／control／predecessorR57／baseline各85filesのhash不変、MOD53a84の8,444precompiled files／149compile artifacts／TF hash不変を確認しました。正式save／private runtime data／mapped JAR／source bodyはGitHubへ追加しません。

JFR34,835bytesのpreflight／actual start-stop ACK／JDK parseを確認しました。保存 **4643766bytes**／SHA **38b06374b77ad72fea344308a3b0f9aadde2601fe7f18ead09a0ea1bdbd36e78**、63秒／ExecutionSample338／CPULoad60／ThreadCPULoad467です。単独記録で、matched OFF／GPU／pixels／observer-effect受入ではありません。R51未取得やR56初回CI失敗の履歴を保全します。

## Hosted producer CI

push37218159840／PR source37218163557／pytest37218163565はSUCCESS。actual PR checkout merge **4e2e5fb9acad76ffdb67f9aeeafc0ed612209111**の親は57e52f9ef44c082daf7abbb0b0f5ada3a258a406／263a9cf2b7d98b21e50b13fb2ee9ed1bb0ab8e03です。188focused／16newactualGsonと旧42／35／59／17／39／24／11／14、complete LAB source／portable Java／pinned MOD compile／dependency／resource／unit gatesを確認しました。hosted pytest: **2026-10-04T16:53:34.9475097Z 3149 passed, 332 skipped, 8 warnings in 239.70s (0:03:59)**。document publication HEADのCIは別に確認します。

## 残る検証

全priority／Activity候補・internal memory理由、他native source branches／custom／null／cap／例外／rearm、全compute枝・duration／fallback RNG・cached reuse・TICK_RECOMPUTEと実到着、全Path候補・拒否・malus・effective cost、全Vanilla・FRONTIER・community、広いBoss戦・coordination、matched OFF／GPU・pixels、live Tank resize、section21全受入、最後のwhole-diff独立レビューは残っています。Draftと全体goalを継続します。
