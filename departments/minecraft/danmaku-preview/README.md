# 弾幕スケッチ / JavaFX 3D

Minecraft再起動前に弾幕の形・密度・時間変化を調整する、小さな下書きツール。
単一Patternのv1画面と、複数Trackを重ねるScore Mode v2を分離している。

## 起動

Windows x64、JDK17以上。

単一Pattern:

```powershell
./run.ps1 -JavaHome 'C:/Program Files/Java/jdk-17'
```

Grand Danmaku Score Mode:

```powershell
./run.ps1 -JavaHome 'C:/Program Files/Java/jdk-17' -Score
```

別Score:

```powershell
./run.ps1 -Score -ScoreFile 'C:/path/to/score.json'
```

## Score Mode v2

Scoreは既存`Pattern.Config`を複数Trackとして重ねる。Pattern JSON v1は変更しない。

Track主要項目:
- startTick / endTick
- WORLD / PLAYER_VIEW
- forwardSpeed
- phaseDeg
- hue / radius
- FAN / RING / SPIRAL
- 既存Pattern速度・間隔・回転等

`phaseDeg`はTrack全体を発射軸まわりに回転する。
これにより同じFANを60°ずつ6本重ねて花弁を作ったり、螺旋を位相ずらししたり、安全地帯の方向を意図的に残せる。

旧Score JSON v2に`phaseDeg`が無い場合は0°として読む。

## PLAYER_VIEW

基準:
- Soutou Ghast発射点 = (0,2,0)
- player = (0,2,24)
- +Z = Ghast -> player
- +Y = up
- 20 tick/s
- 1 unit = 1 block

PLAYER_VIEWではPattern平面をプレイヤー画面のright/upへ写し、forwardSpeedでプレイヤー方向へ進める。

Score ModeはPlayer POVを既定視点として開く。
目的は世界座標での美しさではなく、**戦闘中のプレイヤー画面で弾幕がどう咲くか**を調整すること。

## 現在の Grand Danmaku score

`presets/grand-danmaku-score.json`

約14秒 / 280 tick。

構成:

1. **Halo Gold** — 最初の円環。総統ガストを弾幕の中心として認識させる。
2. **Twin Spiral** — 青/桃の逆回転螺旋。
3. **Six Petal Bloom** — 60°間隔の6つのFAN。各花弁28°なので、花弁間に約32°のnegative spaceを意図的に残す。
4. **Weave** — cyan/violetの速度・位相違い逆回転螺旋で交差感を作る。
5. **Double Finale** — 黄/桃の二重リングで収束。

最大live countは3000契約より十分低い範囲に保つ。
現在の譜面は「全弾が総統ガストから発射され、飛行の結果として模様になる」というsource-integrity原則を維持する。

## UI

- Track選択/ライブ数値編集
- phaseDeg編集
- Score JSON v2保存/読込
- Player POV
- 上面/側面/自由視点
- live bullet count
- active Track count
- play/pause/1tick/seek
- 左drag orbit / 右drag pan / wheel zoom

## 制約

- Score/Pattern期間 最大60秒
- Score Track 最大32
- combined live bullets 最大3000
- 上限では弾を黙って落とさず入力を拒否

## 境界

これはauthoring toolでありMinecraft runtimeそのものではない。

未実装:
- Minecraft collision/damage
- terrain
- Forge networking
- Minecraft batched renderer parity
- runtime performance acceptance

NaturalGhast側では同じScore v2を読むowner-managed VirtualBullet runtimeを別Draftで実装している。

## 検証

```powershell
./run.ps1 -Test
./run.ps1 -CompileOnly
./run.ps1 -Smoke
```

GitHub Actions:
- Windows JavaFX draft: Score phase/Player POVを含めSUCCESS
- repository suite: Score純Java契約を含め検証
