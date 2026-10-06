# 弾幕スケッチ / JavaFX 3D

Minecraft再起動前に弾幕の形・密度・時間変化を調整する、小さな下書きツール。
扇状・全周・回転連射、球の弾、格子、プレイヤー目印を表示する。

## 起動

Windows x64、JDK17以上。PowerShellでこのディレクトリに移動して実行する。
既定のJDK17がある場合は`run.cmd`をダブルクリックしても起動できる。

```powershell
./run.ps1 -JavaHome 'C:/Program Files/Java/jdk-17'
```

初回だけMaven CentralからOpenJFX21.0.9のbase/graphics/controlsを取得する。
SHA256固定で照合し、`.cache`へ保持する。JARやnative DLLはGitに含めない。
JAVA_HOMEが設定済みなら`-JavaHome`は不要。毎回ソースを再コンパイルする。
Minecraft、Forge、Gradle、サーバー接続は不要。

## 操作

- 数値変更で現在時刻の下書きへ即反映。無効入力時は前の有効設定を保持し、保存を拒否する。
- 再生/停止、最初から、1tick送り、時間スライダーで時刻を調整する。
- 上面/側面/自由視点、ドラッグで回転、ホイールで拡大・縮小。
- JSON保存/読込。例は`presets/fan.json`。FAN=扇状、RING=全周、SPIRAL=回転全周。
- 橙は発射点(0,2,0)、緑は固定プレイヤー目印(0,2,8)。格子間隔1block。

## 計算・保存契約

1単位=1block、20tick/秒、+Y上、基準方向+Z。速度はblock/tick。
初回はtick0、以後intervalTicksごとに期間未満で発射し、age>=lifetimeTicksで消える。
回転は発射時点の角度に適用し、飛行中に弾を曲げない。仰角は全弾共通。
全周は末尾で同方向を重複しない。単発扇は中央方向。
時刻から直接計算するため、巻き戻しは同じ位置へ戻る。
最大同時弾数3,000、期間60秒。上限では入力を拒否し、弾を黙って省略しない。

`Pattern.java`はJavaFX/Minecraftに依存しない。JSON v1はこのツール用の平坦な固定schema。
未知/重複/不足項目、型違い、非有限値、別schema/tickRateを拒否する。
Minecraft取り込みadapterは未実装。このJSONを置くだけでMODへ反映されるとは扱わない。
既存MODの重力・ばらつき・衝突・damage・描画・遅延は再現しない。
下書き確定後、同じ設定/計算をMOD側へ接続し、水槽実機で仕上げる。

## 検証

```powershell
./run.ps1 -Test
./run.ps1 -Smoke
```

`-Test`はOpenJFX取得なしの純Java回帰。`-Smoke`は有限の実JavaFX操作確認で、
`build/smoke`にJSONと画面PNGを保存して自分のウィンドウを終了する。
実機Minecraftの受入記録としては使用しない。
2026-10-06: JDK17で43件の純Java assertionsに成功。保存された例JSONも同じcodecで確認する。
実JavaFX SCENE3D起動、数値編集、無効入力保持/保存拒否、巻き戻し、停止、視点、
JSON保存読込を有限smokeで確認し、PNGを目視確認した。
独立レビューの保存誤動作と整数丸めをRED→GREENで修正した。
既存リポ全体回帰とWindows JavaFXコンパイルはGitHub CIでも実行する。
Ver1.00、既存MOD、正式ワールドは変更しない。
