# 弾幕スケッチ / JavaFX 3D

Minecraft再起動前に弾幕の形・密度・時間変化を調整する、小さな下書きツール。
単一Patternのv1画面と、複数Trackを重ねるScore Mode v2を分離している。

## 起動

Windows x64、JDK17以上。PowerShellでこのディレクトリに移動して実行する。
既定のJDK17がある場合は`run.cmd`をダブルクリックしても単一Pattern画面を起動できる。

```powershell
./run.ps1 -JavaHome 'C:/Program Files/Java/jdk-17'
```

Grand Danmaku用のScore Mode:

```powershell
./run.ps1 -JavaHome 'C:/Program Files/Java/jdk-17' -Score
```

別のScore JSONを開く:

```powershell
./run.ps1 -Score -ScoreFile 'C:/path/to/score.json'
```

初回だけMaven CentralからOpenJFX21.0.9のbase/graphics/controlsを取得する。
SHA256固定で照合し、`.cache`へ保持する。JARやnative DLLはGitに含めない。
Minecraft、Forge、Gradle、サーバー接続は不要。

## 単一Pattern v1

- FAN=扇状、RING=全周、SPIRAL=回転全周。
- 弾数、速度、発射間隔、扇角度、回転、仰角、寿命、期間を即時編集。
- 再生/停止、最初から、1tick送り、時間スライダー。
- 上面/側面/自由視点、左ドラッグorbit、右ドラッグpan、ホイールzoom。
- 厳格な平坦JSON v1を保存/読込。
- `Pattern.java`はJavaFX/Minecraft非依存。

## Score Mode v2

Scoreは既存`Pattern.Config`を複数Trackとして重ねる。v1 Pattern JSONは変更しない。

各Track:
- name
- startTick / endTick
- WORLD / PLAYER_VIEW frame
- forwardSpeed
- hue / radius
- FAN / RING / SPIRALと既存Pattern数値

`PLAYER_VIEW`では、既存Patternのyaw平面をプレイヤー画面の右/上へ写し、
`forwardSpeed`で総統ガストからプレイヤー方向へ進ませる。
これにより、総統ガストを中心にリングや螺旋が「画面上で咲きながら前進する」下書きを作れる。

Score画面には:
- 複数Track同時描画
- Track選択とライブ数値編集
- Score JSON v2保存/読込
- Player POV
- 上面/側面/自由視点
- live bullet count / active Track count
- 再生/停止/1tick/seek

を持つ。

同梱`presets/grand-danmaku-score.json`は、
Halo + 逆回転Twin Spiral + Finaleの最小Grand Danmaku下書き。

## Player POV契約

プレビューでは:
- 総統ガスト発射点 = (0,2,0)
- player marker = (0,2,24)
- +Zが総統ガストからプレイヤー方向
- +Yが上
- 1単位=1block
- 20tick/秒

Player POVではカメラをplayer markerへ置き、総統ガスト方向を見る。
「世界座標では綺麗」ではなく「戦闘中のプレイヤー画面で綺麗」を評価するための視点。

## 上限

- Score期間 / Pattern期間: 最大60秒
- 最大同時弾数: 3,000
- Score Track: 最大32
- 上限超過時は入力を拒否し、弾を黙って省略しない

## 計算境界

これはMinecraft実機そのものではない。

未実装:
- Minecraft collision/damage
- terrain interaction
- Forge networking
- VirtualBullet runtime
- Minecraft renderer parity
- automatic NaturalGhast MOD import

下書き確定後、同じ純Java計算契約をNaturalGhast側へ移し、
水槽/LABで実機の見た目・当たり判定・性能を仕上げる。

## 検証

```powershell
./run.ps1 -Test
./run.ps1 -CompileOnly
./run.ps1 -Smoke
```

`-Test`はOpenJFX不要でPattern v1とScore v2の純Java計算/JSONを検証する。
`-CompileOnly`は既存PreviewAppとScorePreviewAppの両方を実JavaFX依存でコンパイルする。
既存`-Smoke`はv1画面の有限JavaFX smokeを維持する。
