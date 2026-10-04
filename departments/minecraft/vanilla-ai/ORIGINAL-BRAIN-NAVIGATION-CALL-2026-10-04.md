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

## 残る検証

この記録時点ではR52のfrozen native実機証拠とexact HEADのhosted CIは未取得です。source／genuine API／test fixtureの成功を実機検証済みとは扱いません。

完全なBrain条件／後段branch／Path候補と拒否・cost、広いBoss戦、matched observer-effect／GPU／pixels、live Tank resize、section21全受入と最後のwhole-diff独立レビューは残っています。Draftと全体goalを継続します。
