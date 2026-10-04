# 元のprivate経路計算条件と判定operand

既存のdefault-OFF brain_navigationと[R55の直接経路計算scope](ORIGINAL-BRAIN-PATH-COMPUTE-2026-10-04.md)を使います。exact MoveToTargetSinkの元private tryComputePathが実際に呼んだprivate reachedTargetとvirtual Path.canReachの正常booleanを、BRAIN_PATH_COMPUTE_CONDITION_RETURNとしてEVALUATION／PARTIALへ保持します。元private処理のpublic化、追加のAI／tracker／getter／query／RNG呼出し、booleanの再計算を行いません。

private reachedTargetは元WT tracker position、元Mob.blockPosition、元virtual BlockPos.distManhattan、元virtual WT.getCloseEnoughDistを使い、元のsigned int比較でbooleanを返します。predicateだけの有限reached subframeが、実際のdistanceとcloseEnoughの元戻り値を保持します。対応source callbackが0回／複数回ならNOT_CAPTUREDで、別の取得やcached fieldから補いません。元predicateがthrowした場合は正常return記録を作らず、元の例外をそのまま伝播します。元Path.canReachがthrowした場合、既に完了したreachedTargetの記録は別の事実として残ります。

base BlockPosはdistManhattanを宣言せず、Vec3iのvirtual実装を継承します。この実装は6つの元coordinate getterを使い、int subtraction→Math.abs→float化→3項float加算→int返却です。overflow、float丸め、customなvirtual distance／閾値もあるため、数学的なdouble距離式やcached座標から戻り値を代用しません。signed負値も元の結果として保持します。consumerは両operandが取得されたexact private comparatorの記録だけ整合性を検査し、新しいAI booleanを作りません。

Path.canReachはbase classではreached fieldを返しますが、customなvirtual overrideの最終booleanは異なり得ます。元のcallを1回実行し、その実際のreturnと渡されたPath／callback後のcached Sink.pathのraw参照一致を保持します。内部cached reachedをvirtual戻り値として捏造しません。reachedTarget=trueの場合やnull Pathの場合に、元のshort circuitで呼ばれなかったcanReachを補いません。predicate true、Path.canReach true、private compute true、Navigation採用、実際の到着は別の事実です。

元private reachedTargetのexact Invoker／tryfinally、private compute内の2 source call Redirect、private reached bodyのdistance／closeEnoughの2 source Redirectを使います。unsupported owner／WT reference／nested sourceはframeを抑止して元の処理を維持します。compute frameの再入・再選択・終了時にもreached frameを解放し、getter中のrearm後に旧returnを新frameへ接続しません。R55の7境界、payload、既定channel、200ticks／256events／524,288bytesは保持します。reached8IDs／depth8を既存compute256／depth8、component128、Snapshot Path参照256の下に追加します。

[追加ledger](BRAIN-PATH-COMPUTE-CONDITION-BYTECODE-LEDGER-2026-10-05.json)はsame mapped artifactの4 selected owners／10 methods／4 fieldsと、BlockPosの継承照合を保持します。ledger SHA **23b022ef2689629d3df2ff3d65288052e73c39ba3cea29d672380b653f15a4a5**。JDK／class／disassembly／14 member sliceとdescriptorを照合し、旧ledgerを保全します。source bodyやmapped JARをGitHubに追加しません。

元private compute／reached bytecodeによるRED→GREENを使用しました。fixtureではprivate accessと観測source delegateだけを試験用に置換し、元のcomparator／short circuitを保ちます。nonnull-unreachable、already-reached、initialnull＋reached、custom virtual距離／閾値／canReach、Integer.MIN_VALUEの元overflow結果、元例外、getter回数、OFF／thread／owner／WT・Nav owner／context／時間／event／byte／writer、8depth／8reached IDs、128component／256Path参照、unknown sourceoperand、rearm、detachを検査しました。4exact Redirectと1private Invoker／singledelegate、およびR55の既存7境界をcompiled ASMで検査します。synthetic nesting／cap／absent operand fixtureは本物のnative branchやfallback RNGの証明ではありません。

Motion／Decision175件、actual production Gson→strict JavaScript35件と旧59／17／39／24／11／14を保持し、allbridge／combinedAPIの成功を確認しました。

## Frozen native R56

producer **72e2521500e82fd444c2978df9867eb978868545**、run-20261004150819-c63d01443cff／sess-20261004150819-8a35f7fcf0e1／snapshot-20261004150819-0d3165943662、process epoch1／Arena epoch0、private adult Villager UUID55555555-6666-7777-8888-000000000001です。正式control85ファイルのfresh privateコピーを使い、自然day11850から進行しました。desired result／Brain memory／navigationをseedしていません。

2 complete compute groupsで**4新規predicate events**（reachedTarget／Path.canReach各2）、R55のFinder／create／元field write／compute return **8 events**を取得しました。同じcompute/create/Finder/reached ID、exact UUID、全run／session／snapshot／process／Arena／revision、元gameTimeArgument、instanceIdentity、eventIndexと生のPath参照で照合しました。runtime22220の実際のsource ID順序は次のとおりです。

| compute invocation | game tick | Finder→create→元代入→reached→canReach→computeのsource ID末尾 | actual distance／closeEnough | reached／canReach／compute |
| --- | ---: | --- | --- | --- |
| compute:1:1 | 40477 | 34 → 35 → 36 → 37 → 38 → 39 | 25／4 | false／false／true |
| compute:2:1 | 41032 | 644 → 645 → 646 → 647 → 648 → 649 | 37／4 | false／false／true |

距離と閾値は元virtual callの実戻り値です。actual predicate booleanも元private処理の戻り値で、座標から再計算した結果ではありません。元Path.canReachのfalse、private computeのtrueを別々に保持しています。canReach argumentと元格納Sink.pathは同じraw参照です。generic search IDはbrain_navigation単独のためNOT_CAPTUREDですが、direct Finderの元正常returnは取得済みです。外側開始条件／tryStart→後続PATH write・Navigation採用・到着のdirect caller scopeは今回未取得です。

| revision | valid snapshots | 新規predicate events | 全callbacks／payload bytes | Motion実サンプル | same-snapshot PATH／Nav参照一致 | callback終了理由 |
| --- | ---: | ---: | --- | ---: | ---: | --- |
| 1 | 120 | 2 | 248／321851 | 72 | 61 | WINDOW_ENDED |
| 2 | 120 | 2 | 256／335659 | 86 | 74 | EVENT_BUDGET |

全504 callbacks／240 valid snapshots、canonical **1,285 unique observations**はEVIDENCE_COMPLETE、SHA **f7d61a2e5e0f70b84db00c09964ed0f34f6a0ae6120f0e37bf4e7ee5dde50825**、finalization SHA **eccc7aebb006486ffd84a32632aa9fd6f571fba76ab0e580eb31a6503325a311**です。既存200ticks／256events／524,288bytes／32nodesを維持しました。revision1のlocal121..321 exclusiveはWINDOW_ENDED、revision2のlocal721..921 exclusiveはEVENT_BUDGETで閉じています。new predicate／compute groupのpartialは0ですが、上限後の未取得tailを未呼出し・失敗・正常に補いません。158 Motion実サンプル／135 same-snapshot参照一致は別の事実です。

clean ACK／drop0／queue0／finalWriterSeq1285、owned launcher22924／runtime22220のOS終了、元／control／predecessor R55／baseline各85ファイルのhash不変を確認しました。正式save、private runtime data、mapped JAR、source bodyはGitHubに追加しません。

JFR設定34,835bytes／SHA d4d74f3594bfe342397f53aaa75a7551e7b2d9ac6f86c7ca2bc016690501b37dのpreflight、actual start／stop ACK、保存fileのJDK parseを確認しました。JFR **3952287bytes**／SHA **5aae2dfba0effb65ad9c42a00aabe82e73cd12832cb795126229f7a1c63827d5**、63秒／ExecutionSample352／CPULoad60／ThreadCPULoad431です。単独記録であり、matched OFF／GPU／pixels／observer-effect受入ではありません。過去のR51未取得を含む記録を保全します。

## Hosted producer CI

producer push37211878428／PR source37211880700／pytest37211880695はSUCCESS。actual PR checkout merge **3b33729393b114354e983ed2028d448396ec57e6**の親は57e52f9ef44c082daf7abbb0b0f5ada3a258a406／72e2521500e82fd444c2978df9867eb978868545です。175focused／35新規actual Gson／59旧compute Gson、および完全LAB source／portable Java／pinned MOD compile／dependency／resource／unit gatesを確認しました。hosted pytestは**3,149 passed, 332 skipped, 8 warnings in 282.61s**。document publication HEADのCIは別に確認します。

## 残る検証

nativeでのreached=true／canReach=true／private compute=false／initialnull／fallback RNG／TICK_RECOMPUTE／cached reuse／custom override／例外・cap・rearm、outer start condition→compute→PATH write／Navigation採用・到着、完全Brain理由、全Path候補・拒否・malus・effective cost、全Vanilla・FRONTIER・community、広いBoss戦、matched OFF／GPU・pixels、live Tank resize、section21全受入、最後のwhole-diff独立レビューは残っています。Draftと全体goalを継続します。
