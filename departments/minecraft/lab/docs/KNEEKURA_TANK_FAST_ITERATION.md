# Tank local iteration: storage configuration and measured scope

2026-10-06。今回の対策は既存設定で実行用gameDir/runtimeRootを低遅延のローカル領域へ置くこと。Java hook、観測頻度、MOD構成、owner/lease、強制同期、原子的な公開、ソース/生成物照合を削減しない。TECH HUB内のLABが正本。

## 反復用の配置

[設定例](../debug-workspace/config.fast-iteration.example.json)の`C:/KNEEKURA`は配置例であり、自動作成済みの環境ではない。workspaceDirを開発用checkoutへ合わせ、正式なKNEEKURA_DEBUG_WORLDを停止中にprivate game/savesへ複製し、必要なoptions/resourcepacksも揃える。正式原本を実行用へ移動しない。新しいowner登録では複製の実canonicalWorldRoot、元saveのhash、fixture差分、request/material hashを結び直す。古いrun/owner/lease/成功記録を開始権限として再使用しない。

gameDirは検査対象の設定でもあるため、この値だけを変更してもForgeの実workingDirectoryは切り替わらない。設定例が参照するprivate `local-game-dir.gradle`を次の内容で新規作成し、両者のパスを一致させる。

```groovy
gradle.beforeProject { p ->
    p.plugins.withId('net.minecraftforge.gradle') {
        p.afterEvaluate {
            p.minecraft.runs.client.workingDirectory p.file('C:/KNEEKURA/iteration/game')
        }
    }
}
```

これは既存launch.argsのinit-script指定を使う。実ownerのworld照合と既存world必須条件を維持する。設定例単体はowner操作を許可せず、表示補正も有効にしない。必要なowner/request/resource登録は従来どおり別に行う。FAST_DEBUGはMODを減らす指定ではない。

今回の端末ではC:がK:より低遅延だった。ドライブ文字だけで速度を保証しない。K:は今回空き約0.7GBで、過去の試行・大型保管物は保持し、追加の実行書き込みはC:へ分けた。保管領域にも空き容量は必要。元の記録や原本を自動削除しない。

通常の開発反復はGradle daemonと既定のincremental compilationを利用し、Java変更時は通常のrunClient/buildを実行する。`clean`を毎回挟まない。`-x compileJava`を一般の高速化手順にしない。今回の固定ソース試行だけは、既存のgenuine precompiled main guardで8,444ファイルの完全hash照合が通った生成物を再使用した。

[Gradle 8.14.3 performance](https://docs.gradle.org/8.14.3/userguide/performance.html)と[daemon](https://docs.gradle.org/8.14.3/userguide/gradle_daemon.html)はincremental compilation、入力に基づくup-to-date判定、daemon再利用を説明する。これらはMinecraftの全起動費用を消すものではない。configuration cacheはplugin/build側の適合を必要とするため、今回未検証のForgeGradle設定には追加しない。検証のための別build scan送信、依存更新、wrapper/JDK更新は行っていない。

通常水槽のMOD構成を絞る追加の指定`KNEEKURA_DEBUG_MOD_PROFILE=TANK_CORE`は
[軽量MOD構成の手順と記録](KNEEKURA_TANK_CORE_PROFILE.md)を参照する。
以下の保存先比較は従来の全構成による歴史的記録として保持する。

## 原因調査と有限の実機結果

従来のK:試行は約1秒ごとに重いserver tickがあり、OwnerConnectionの毎秒のowner-status公開がserver thread上で`force(true)`とatomic moveを実行する。実際の既存OwnerFiles writerを独立の無権限privateディレクトリで各60回測ると、K: p50/p95は100.0189/100.6662ms、C:は1.9584/2.3686ms。単独IO測定は実機での唯一の因果の証明ではないが、このwriter自体の保存先による費用差を確認した。

次にsource `d0b38af22ef33f224eafeed930d9446dd56e3c96`、MOD `53a84d06578632b5d123e3c2bb631b611bf830d7`、正式原本85ファイルからの新規複製、固定NoAI/NoGravity Pig、同一options/resourcepacks/geometryを使った。ソースと生成mainはK:に保持し、game/runtimeのみC:へ配置。private probeの変更はprivate保存先の許可パスだけで、計測・観測処理は同じ。全試行でstatus ON、gridとbrightnessは同時に切り替える。

| 試行 | grid/brightness | launch→READY (秒) | frame p95 (ms) | server p50/p95/max (ms) | server >50ms |
|---|---|---:|---:|---|---:|
| C01 | ON/ON | 96.995 | 3.5331 | 6.9162 / 11.8205 / 18.5605 | 0/200 |
| C02 | OFF/OFF | 84.418 | 3.3398 | 6.5950 / 10.9446 / 16.6903 | 0/200 |
| C03 | OFF/OFF | 84.501 | 3.4336 | 7.1586 / 13.4554 / 16.5130 | 0/200 |
| C05 retry | ON/ON | 89.583 | 3.3092 | 6.7483 / 12.7232 / 19.7424 | 0/200 |

従来のK:4試行はlaunch→READY 138.005〜141.443秒、server >50ms 11/10/9/9件、server最大86.5691〜142.4187ms。C:の採用4試行は約84〜97秒、最大19.7424ms、合計800tick中50ms超0件。この環境の繰り返し起動と長い周期的停止は改善した。中央値のserver処理はK:の約3.7〜3.8msより増えており、全指標が改善したとはしない。C02にはframe最大69.7321msが1件あり、frame stallがゼロという主張もしない。

採用pair C01/C02とC05/C03は実camera位置・yaw/pitch一致。frame p95比1.057878/0.963770、server p95比1.080030/0.945583、OS CPU/wall比1.182575/0.853724。既存の事前上限1.2以内だが、少数の有限診断であり、包括的な品質PASSではない。悪化した従来K: forward server p95比7.178は取り消さない。

launch→READYはprivate main guard終了後のlaunchDebugRunからreadCurrentまで。guard、初回依存取得、ソース変更後のmain compileはこの時間に含まれず、cold/full compileの起動時間として使わない。5秒warmup後10秒のRenderTick START→ENDはCPU submission/待機を含むwall時間でGPU完了ではない。ServerTick START→ENDは処理時間で、heartbeat間隔とは別。OS CPU境界はwarmup残り/polling/終了後の画像を含み、10秒と完全一致しない。

採用4試行は88/87/86/88 canonical、各9lane、EVIDENCE_COMPLETE、drop/error/残queue/partial 0、clean ACKとowned exit、正式原本85hash不変。640×480のderived PNGはON2枚が`96edf40e6cb14a87e38643bd82390bfe9baa673cf932a4db97a63d5f8d5da048`、OFF2枚が`291115d0fcf7caad1816f0fce3f0a3beaf571dba6e5aff2761d97a634b50ea64`。既存CAS/Cardinal captureの合格へは読み替えずcaptureManifestsは0。

private記録は`C:/temp/kneekura-tank-performance-20261006/native-r2`、採用集計`diagnostics-summary-camera-verified.json` SHA256 `e9efe8113dc825b30c896d1aa997bbb84d27249a2daa30c99b43ece73bbbed62`。C04はuser操作によるcamera向き変更で比較から除外し、report/PNG/全87canonicalを保存。初回r1のoffline準備クラス誤同梱によるmodule重複・READY前終了も保存し、private probeだけを修正した。原本や製品コードの欠陥と扱わない。raw world/JFR/private登録情報は公開しない。

## 暗さと品質の境界

今回のOFFは格子と観察用明るさ補正の両方OFF。ONのOBSERVATION_BRIGHTはclientのlightmap色を補正する既存機能で、server光量、ブロック、Mob/playerの暗視効果は変更しない。OFF画像だけから、光源不足の原因や任意の照明不具合を断定しない。観察用は登録済み補正を使い、通常外観の評価では補正OFFの結果を明示する。今回、格子と補正を独立指定する新APIは追加していない。

新status ON/OFFの費用、isolated grid/brightness、実機自律move→stop/wall→resume、複数停止弾、完全なworld/observer比較条件、GPU完了、長時間/他端末/一般MODでの品質受入は引き続き未完了。既存120秒leaseは延長せず、元のK:期限切れ検証を保持する。今回のC:採用試行は短時間で終了し、独立の期限切れ画像を取得したとはしない。Draft/merge/readinessを変更しない。
