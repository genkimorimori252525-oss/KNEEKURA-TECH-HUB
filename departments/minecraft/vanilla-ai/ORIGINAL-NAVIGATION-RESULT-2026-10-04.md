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

**この変更のfresh native観測はまだ未検証です。** 次にclean producerを固定し、元／control／predecessor／fixture baselineを保全したprivate adult Villagerで、有限の `navigation_result` 窓を取得します。

R50の[元の活動更新](ORIGINAL-ACTIVITY-CALL-2026-10-04.md)の証拠はそのproducerに保全します。完全なBrain memory条件、全Behavior／Navigation result、Path候補／拒否／effective cost、広いBoss戦、matched observer-effect／GPU／pixels、live Tank resize、section21全受入と最後のwhole-diff独立レビューは残っています。Draftと全体goalは継続します。
