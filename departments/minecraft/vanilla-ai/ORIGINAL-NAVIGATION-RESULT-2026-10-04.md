# 元のNavigation戻り値とPath参照

## 実装範囲

`navigation_result` は明示指定する観測channelです。既定のchannel集合は変更しません。固定Minecraft 1.20.1 Forgeのbase `PathNavigation.moveTo(Path, double)` の正常RETURNだけを、非キャンセルのMixinで取得します。任意のcustom overrideの最終戻り値や、目的地への到着を表すものではありません。

`NAVIGATION_MOVE_TO_RETURN` は元のboolean、passed speed、return後のcached speed、passed Pathとcached Pathのpresent／raw参照一致を別々に保持します。非有限のspeedは数値を省略し `NOT_EXPOSED` とします。Decision Modelでは `EXECUTION`／`navigation_move_to: PARTIAL` へ接続し、CANDIDATE／SELECTION／到着RESULTを補いません。

## sourceと観測の境界

[追加source ledger](NAVIGATION-RESULT-BYTECODE-LEDGER-2026-10-04.json)は同じ固定mapped artifactの2 owners／3 `moveTo` overloads／4 fieldsを、class／disassembly／member slice hashとdescriptorで保持します。ledger SHAは `ec2d6c648f0711cb5fa7decd994e0d4959e55b8c42fb782e7d0192b6324f1ca9`。この変更のhook対象はPath overloadだけです。exact Pathのcached field証明は既存[typed memory記録](TYPED-BRAIN-MEMORY-2026-10-04.md)を再利用し、元61-owner／R47〜R50台帳は変更しません。

元のbase methodはnullでcached Pathを消去してfalseを返します。nonnullでは元のvirtual `sameAs`、`isDone`、`trimPath`、`getNodeCount`、`getTempMobPos` 等を実行します。別のPathを渡しても同じ経路ならcached参照を保持するため、trueはpassed参照の採用を保証しません。trueでも `Path.canReach` がfalseの場合があります。観測側はこれらのquery／AI処理を再実行しません。

session／run／snapshot／process／Arena／selection revision、server thread、時間、event、byte上限を維持します。cached final `PathNavigation.mob` が選択対象と同じ参照であり、base `Mob.navigation` が観測receiverと同じ参照である場合に限定します。cached fieldsはRETURNとcapture gatesの後の読み取りです。任意のcustom実装のatomic状態や、元処理のbranch reasonを復元するものではありません。

exact Pathのcached fieldsは既存typed memoryの契約を再利用します。Path参照IDはmemory／Navigation snapshotと同じ `SNAPSHOT_REFERENCE` の256個上限、Navigation componentは別の128個上限です。node prefixは64個まで、custom Path／custom node list／上限後の参照は明示的に未取得とします。同じraw参照の場合は取得済みcopyを複製し、再読込しません。Pathの等しい座標からsearchとの対応、選択理由、到着を推定しません。両方nullのraw一致もPath採用の証拠ではありません。

## 検証

genuine元methodによるnull消去false、done／empty false、同じ経路の別参照を保持するtrue、reachableでないPathのtrue、custom virtual call／例外の同一性、copy、非有限speed、custom node list、64-node prefix、共有Path参照／256個上限、owner／navigation／thread／channel／context／window／event／byte／writerの回帰を確認しました。test-only Navigation overrideは明示し、インストールされたMixinの実機証明とは区別します。compiled exact RETURN descriptor／require1／boolean delegateも確認しました。

Motion／Decision **153件成功**。hash照合したgenuine依存関係で全bridge／Mixinをcompileし、combined API／owner／writer／Arena／overlay回帰と、**11のactual production Gson→JavaScriptケース**が成功しました。typed cached Pathの共通検証をmemoryとoriginal-returnで共有し、異なるrevision／allocator／参照一致の偽装、欠測の完全取得表示、speedの矛盾、到着／原因の偽装を拒否します。

## Frozen native R51

producer **6aef9d44fb381d9786882aa4f974c9f51ef3fdf4**、`run-20261004105216-53f3cc2d6914`／`sess-20261004105216-d73ce0c45afd`／`snapshot-20261004105216-9dc24ff9b86f`、process epoch1／Arena epoch0です。private adult Villager UUIDは `55555555-6666-7777-8888-000000000001`。元control85ファイルからcopyし、R50と同じprelaunch floor／照明／player設定、DayTime11850の自然進行を使用しました。Brain memoryやNavigation結果をfixtureへ書き込みません。

| revision | valid snapshots | original normal returns | burst | Motion実サンプル | same-snapshot PATH／Navigation参照一致 |
| --- | ---: | ---: | --- | ---: | ---: |
| 1 | 120 | 2 | 7,946 payload bytes／WINDOW_ENDED（101..301 exclusive） | 85 | 73 |
| 2 | 120 | 2 | 7,331 payload bytes／WINDOW_ENDED（701..901 exclusive） | 78 | 66 |

各窓は `navigation_result` のみ、200 ticks／256 events／524,288 bytes／32 search nodesの既存上限です。Pathのtyped cached prefix上限64は別の契約です。4件ともactual production Gson、source method、選択UUID／revision／session／run／snapshot／process／Arenaを照合しました。Decision packetにはEXECUTIONだけを追加し、CANDIDATE／SELECTION／到着RESULTを補いません。

| source observation ID | game tick | Path参照 | cached node count | cached canReach | original boolean |
| --- | ---: | --- | ---: | --- | --- |
| `obs:forge-runtime:31028:40` | 40477 | `path:1:19` | 7 | false | true |
| `obs:forge-runtime:31028:108` | 40580 | `path:1:23` | 11 | true | true |
| `obs:forge-runtime:31028:436` | 41057 | `path:2:7` | 9 | false | true |
| `obs:forge-runtime:31028:512` | 41154 | `path:2:12` | 5 | false | true |

4件ともpassed／cached speedは0.5、raw Path参照一致trueでした。3件の `canReach=false` とtrue returnは両立しています。今回の実機窓ではfalse、null、同じ経路の別参照、custom Path、参照上限は取得していません。それらのgenuine API試験を実機受入へ置き換えません。139件のsame-snapshot参照一致と163件のMotion実サンプルは、元のNavigation呼出しへの因果対応や到着成功を証明しません。

canonical **792 unique observations**は `EVIDENCE_COMPLETE`、SHA **03746e4212c2e675fd7bb1d5e76eb518d8c2da00ce6eb301ee052f1591c1653a**。finalization SHA **74b4ff561d62f5a925ce8d6082aedb9e1af596ff3c2bcb271c69a5a923ca8eb8**。clean ACK／drop0／queue0／finalWriterSeq792、owned launcher46312／runtime31028のOS上の終了と、元／control／predecessor R50／fixture baseline各85ファイルのhash不変を確認しました。

**JFRは未取得です。** private起動補助で設定ファイルのcopyが漏れ、jcmdは `Could not parse settings file` と `Could not stop recording` を返しました。exit codeだけを成功と扱わず、元report／outputを保全し、final receiptへ `NOT_CAPTURED / PRIVATE_SETTINGS_FILE_MISSING_AT_START` を明記しました。補完後のattach試行時には対象PIDが既に終了していたことを独立確認しました。Navigation証拠の成立と、性能／paired observer-effectの未取得を分けます。最初のprivate proof helperがstop metadataにないArena epochを参照したassertionも保全し、actual canonicalのArena0を照合するr2 helperで検証しました。canonicalデータは変更していません。

private canonical／native report／installed-navigation proof／post-setup baselineと以前のR50証拠を保全しています。GitHubへsave・JAR・source body・private runtime dataを追加していません。

R50の[元の活動更新](ORIGINAL-ACTIVITY-CALL-2026-10-04.md)の証拠はそのproducerに保全します。完全なBrain memory条件、全Behavior／Navigation result、Path候補／拒否／effective cost、広いBoss戦、matched observer-effect／GPU／pixels、live Tank resize、section21全受入と最後のwhole-diff独立レビューは残っています。Draftと全体goalは継続します。

## Hosted producer CI

source push **37196768354**／source PR **37196771356**／pytest **37196771374** はSUCCESSです。actual PR checkout merge `e2f7d8260f1767050016ba10fd5aa65f806dfd3a` の親はbase `57e52f9ef44c082daf7abbb0b0f5ada3a258a406` とproducer `6aef9d44fb381d9786882aa4f974c9f51ef3fdf4`。153 focused／11 actual Navigation Gson markers、完全LAB source suite、portable Java、pinned MOD compile、dependency／resource／unit gatesを確認しました。hosted pytestは **3,149成功／332スキップ／8 warnings（190.67秒）**。documentation publication HEADは別に確認します。
