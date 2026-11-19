# SPELLCARD ATLAS — 五つの難題MOD+ X1

Status: **ORIGINAL_SOURCE / ORIGINAL_BINARY static analysis; runtime NOT_RUN**

Scope: active `SpellCardRegistry` entries in the user-supplied X1 distribution.

- Active cards: **35**
- Active IDs: `0–30, 33–35, 40`
- Dormant implementation: `THSC_BrilliantDragonBullet` (registration commented out)
- Timing: `THSpellCard.time` advances once per update; **20 ticks = 1 second**
- Dodge-pressure notes are **static design inference**, not runtime play-test evidence.

## Active inventory

| ID | Card | Owner | Need Lv | Lifetime | Archetype |
|---:|---|---|---:|---:|---|
| 0 | 霊符「夢想封印」 | `REIMU` | 5 | 90t / 4.50s | 遅延展開→追尾 |
| 1 | 恋符「マスタースパーク」 | `MARISA` | 5 | 109t / 5.45s | 固定主砲＋螺旋随伴弾 |
| 2 | 死蝶「華胥の永眠」 | `YUYUKO` | 3 | 150t / 7.50s | 反転二重リング |
| 3 | 星符「メテオニックシャワー」 | `MARISA` | 1 | 60t / 3.00s | ランダム照準ショットガン |
| 4 | 境符「波と粒の境界」 | `YUKARI` | 5 | 320t / 16.00s | 連続3D球殻 |
| 5 | 魍魎「二重黒死蝶」 | `YUKARI` | 3 | 200t / 10.00s | 停止→再加速する反曲線蝶 |
| 6 | 紅符「スカーレットシュート」 | `REMILIA` | 4 | 120t / 6.00s | 階層クラスター扇 |
| 7 | 「全人類の緋想天」 | `TENSHI` | 5 | 150t / 7.50s | 登録済み・主弾幕なし |
| 8 | メイド秘技「殺人ドール」 | `SAKUYA` | 4 | 110t / 5.50s | 時間停止＋再照準ナイフ |
| 9 | 凍符「パーフェクトフリーズ」 | `CIRNO` | 1 | 110t / 5.50s | 弾幕捕獲→凍結→再射出 |
| 10 | 幻巣「飛光虫ネスト」 | `YUKARI` | 4 | 160t / 8.00s | ランダム配置遅延レーザー巣 |
| 11 | 水符「河童のポロロッカ」 | `NITORI` | 3 | 140t / 7.00s | 移動母弾→反射子弾 |
| 12 | 魔符「スターダストレヴァリエ」 | `MARISA` | 4 | 120t / 6.00s | 回転母星→螺旋トレイル |
| 13 | 土着神「ケロちゃん風雨に負けず」 | `SUWAKO` | 2 | 200t / 10.00s | 構造化風雨＋ランダム雨 |
| 14 | 奇跡「ミラクルフルーツ」 | `SANAE` | 1 | 60t / 3.00s | 減速母弾→遅延多層放射 |
| 15 | 奇跡「ファフロッキーズの奇跡」 | `SANAE` | 1 | 40t / 2.00s | ランダム落下物イベント |
| 16 | 妖怪退治「妖力スポイラー」 | `SANAE` | 2 | 80t / 4.00s | 敵中心リング→ブーメラン帰還 |
| 17 | 開海「モーゼの奇跡」 | `SANAE` | 2 | 180t / 9.00s | 二枚の回転弾幕壁 |
| 18 | 大奇跡「八坂の神風」 | `SANAE` | 3 | 270t / 13.50s | 呼吸する反転風リング |
| 19 | 氷符「アイシクルフォール」 | `CIRNO` | 1 | 180t / 9.00s | 減速扇→90°折れ→落下 |
| 20 | 禁弾「スターボウブレイク」 | `FLANDORE` | 3 | 150t / 7.50s | 成長虹リング→終端反転 |
| 21 | 禁弾「カタディオプトリック」 | `FLANDORE` | 3 | 110t / 5.50s | 超大量無限反射クラスター |
| 22 | 祟符「ミシャグジさま」 | `SUWAKO` | 3 | 90t / 4.50s | 急減速する二重呪リング |
| 23 | 「レッドマジック」 | `REMILIA` | 4 | 190t / 9.50s | 母弾軌道＋遅延子弾の軌跡描画 |
| 24 | 奇術「エターナルミーク」 | `SAKUYA` | 2 | 50t / 2.50s | 高速連続狙いナイフ |
| 25 | 恋符「ノンディレクショナルレーザー」 | `MARISA` | 3 | 103t / 5.15s | 回転五芒レーザー輪 |
| 26 | 幻想「花鳥風月、嘯風弄月」 | `YUUKA` | 5 | 90t / 4.50s | 移動レーザー花＋反対向き花弁弾 |
| 27 | 神槍「スピア・ザ・グングニル」 | `REMILIA` | 3 | 50t / 2.50s | 登録済み・主弾幕なし |
| 28 | 月符「ムーンライトレイ」 | `RUMIA` | 1 | 60t / 3.00s | 七本回転長レーザー |
| 29 | 華符「芳華絢爛」 | `MEIRIN` | 2 | 170t / 8.50s | 二重編みリング＋周期赤壁 |
| 30 | 彩符「彩光乱舞」 | `MEIRIN` | 2 | 80t / 4.00s | 規則リング↔左右回転ランダム雲 |
| 33 | 蓬莱「凱風快晴  -フジヤマヴォルケイノ-」 | `MOKOU` | 5 | 120t / 6.00s | 停止地点爆発→フラクタル分裂 |
| 34 | 蟲符「リトルバグストーム」 | `WRIGGLE` | 2 | 150t / 7.50s | 同一弾の多段変身 |
| 35 | 蛍符「地上の流星」 | `WRIGGLE` | 1 | 120t / 6.00s | 回転母弾→流星トレイル |
| 40 | 雷矢「ガゴウジサイクロン」 | `TOZIKO` | 2 | 120t / 6.00s | 直角ジグザグ矢＋周期リング |

---

## ID 0 — 霊符「夢想封印」

- **Class:** `THSC_MusouFuuin`
- **Original owner:** `REIMU`
- **Need level:** 5
- **Card lifetime:** 90 ticks (4.50s)
- **Archetype:** **遅延展開→追尾**
- **Flow:** t=15〜48、2tickごと。低速で展開した光弾が約15tick減速してから追尾へ移行。
- **Trajectory:** 初期方向は time×33° で回転。追尾は1tickあたり約12°までの角度修正で、急な瞬間旋回ではない。速度はその後0.6へ加速。
- **Pressure (static inference):** 最初は空間占有、後半は追尾で退路を削る。

## ID 1 — 恋符「マスタースパーク」

- **Class:** `THSC_MasterSpark`
- **Original owner:** `MARISA`
- **Need level:** 5
- **Card lifetime:** 109 ticks (5.45s)
- **Archetype:** **固定主砲＋螺旋随伴弾**
- **Flow:** t=1でミニ八卦炉を生成し、そこから長いLaserB主砲。t=30〜98は毎tick、7個の星弾を追加。
- **Trajectory:** 主レーザーは八卦炉に追従。副弾は主軸の周囲を time×6° で回る7点配置で、虹色の螺旋状ジャケットになる。
- **Pressure (static inference):** レーザー本体の進入禁止帯を副弾が締める二層圧力。

## ID 2 — 死蝶「華胥の永眠」

- **Class:** `THSC_Kasho_no_Eimin`
- **Original owner:** `YUYUKO`
- **Need level:** 3
- **Card lifetime:** 150 ticks (7.50s)
- **Archetype:** **反転二重リング**
- **Flow:** t<90、time%6==3で、回転方向が逆の蝶弾リングを2組。
- **Trajectory:** 各15way。rotationSpeed +1.6/-1.6で反対向きに曲がり、0.2→0.7へ加速。基準角は毎回ランダム。
- **Pressure (static inference):** 逆回転2層が交差し、単純なリング隙間追従を崩す。

## ID 3 — 星符「メテオニックシャワー」

- **Class:** `THSC_MeteonicShower`
- **Original owner:** `MARISA`
- **Need level:** 1
- **Card lifetime:** 60 ticks (3.00s)
- **Archetype:** **ランダム照準ショットガン**
- **Flow:** t=12〜38の偶数tick、ターゲット方向へランダム円錐内に星弾。
- **Trajectory:** 約40°のランダム散布。0.4→0.6。色・サイズがランダムで、サイズに応じてダメージも変化。
- **Pressure (static inference):** 狙い軸は追従しつつ射線が不規則な反応型。

## ID 4 — 境符「波と粒の境界」

- **Class:** `THSC_Nami_to_Tubu_no_Kyoukai`
- **Original owner:** `YUKARI`
- **Need level:** 5
- **Card lifetime:** 320 ticks (16.00s)
- **Archetype:** **連続3D球殻**
- **Flow:** t=5〜279、ほぼ毎tick、12way球状弾幕。
- **Trajectory:** yaw/pitch自体がsin/cosの累積式で動き続け、紫光弾の球殻方向が漂う。0.2→0.6。
- **Pressure (static inference):** 長時間、三次元的な面が移動して上下逃げも削る。

## ID 5 — 魍魎「二重黒死蝶」

- **Class:** `THSC_NijuuKokushichou`
- **Original owner:** `YUKARI`
- **Need level:** 3
- **Card lifetime:** 200 ticks (10.00s)
- **Archetype:** **停止→再加速する反曲線蝶**
- **Flow:** t=10と80に大規模バースト。各反復で8way蝶弾を多数生成。
- **Trajectory:** 初期速度はランダム。最初25tickはmotion×0.9で停滞、t=25からlimit=2.0/accel=0.03、色系統でyaw±10°。
- **Pressure (static inference):** 止まりかけた弾が再び曲がって広がり、未来の隙間を読みにくくする。

## ID 6 — 紅符「スカーレットシュート」

- **Class:** `THSC_ScarletShoot`
- **Original owner:** `REMILIA`
- **Need level:** 4
- **Card lifetime:** 120 ticks (6.00s)
- **Archetype:** **階層クラスター扇**
- **Flow:** t=20,45に広い5軸扇、t=80にほぼ正面3軸集中。
- **Trajectory:** 1軸あたり大弾1＋中弾11＋小弾22。中小弾は軸周囲へランダム散布。
- **Pressure (static inference):** 大弾が骨格、小弾が隙間を埋める多スケール弾幕。

## ID 7 — 「全人類の緋想天」

- **Class:** `THSC_Zenzinrui_no_Hisouten`
- **Original owner:** `TENSHI`
- **Need level:** 5
- **Card lifetime:** 150 ticks (7.50s)
- **Archetype:** **登録済み・主弾幕なし**
- **Flow:** このX1クラスにはspellcard_main()がない。
- **Trajectory:** SPECIAL_HISOUTEN01は別の気質弾向け成長/衝突処理として登録されるが、このカード自身は生成しない。
- **Pressure (static inference):** カード単体では静的解析上、弾幕なし。別Entity挙動を混同しない。
- **Boundary:** active registry entry exists, but this X1 class has no `spellcard_main()`; similarly named item/mob behavior is not projected into the card.

## ID 8 — メイド秘技「殺人ドール」

- **Class:** `THSC_SatuzinDoll`
- **Original owner:** `SAKUYA`
- **Need level:** 4
- **Card lifetime:** 110 ticks (5.50s)
- **Archetype:** **時間停止＋再照準ナイフ**
- **Flow:** t=5〜14に毎tick32way青ナイフ球、t=16/20に赤9wayリング。t=36でSakuyaWatch。
- **Trajectory:** 時間停止中、既存の自分の青/赤ナイフの一部を消し、ターゲット方向またはランダムへ緑ナイフとして再生成。
- **Pressure (static inference):** 先に置く→止める→一部を狙い直す。静的障害物が突然射線へ変わる。

## ID 9 — 凍符「パーフェクトフリーズ」

- **Class:** `THSC_PerfectFreeze`
- **Original owner:** `CIRNO`
- **Need level:** 1
- **Card lifetime:** 110 ticks (5.50s)
- **Archetype:** **弾幕捕獲→凍結→再射出**
- **Flow:** t>5〜57は毎tickランダム虹弾。t=64で半径20の既存THShot群を走査。
- **Trajectory:** 対象弾を白いほぼ静止弾へ置換し、FREEZE specialで約20tick後に0.01→0.3へ再加速。
- **Pressure (static inference):** 現在の弾幕場そのものを凍結地雷へ変換し、再始動で安全地帯を変える。

## ID 10 — 幻巣「飛光虫ネスト」

- **Class:** `THSC_HikouchuuNest`
- **Original owner:** `YUKARI`
- **Need level:** 4
- **Card lifetime:** 160 ticks (8.00s)
- **Archetype:** **ランダム配置遅延レーザー巣**
- **Flow:** 毎tick最大4候補点を選び、視線が通る位置に短命Sukimaを生成。
- **Trajectory:** Sukimaは生存5tick目に紫LaserAを生成。発射点は使用者周囲1〜6ブロック程度のランダム空間。
- **Pressure (static inference):** ボス正面以外から遅延レーザーが増殖する多方向網。

## ID 11 — 水符「河童のポロロッカ」

- **Class:** `THSC_KappaPororoca`
- **Original owner:** `NITORI`
- **Need level:** 3
- **Card lifetime:** 140 ticks (7.00s)
- **Archetype:** **移動母弾→反射子弾**
- **Flow:** t>=5、10tickごとに左右2つの青母弾。
- **Trajectory:** 母弾は移動しながら4tick周期で子弾を吐き、子弾はBOUND01でブロックに1回反射。
- **Pressure (static inference):** 移動弾源＋壁反射で地形込みの二次射線が生じる。

## ID 12 — 魔符「スターダストレヴァリエ」

- **Class:** `THSC_StardustReverie`
- **Original owner:** `MARISA`
- **Need level:** 4
- **Card lifetime:** 120 ticks (6.00s)
- **Archetype:** **回転母星→螺旋トレイル**
- **Flow:** t=5に難易度依存数の大型虹星を円形配置。
- **Trajectory:** 各母星が毎tick、自身の進行軸周りに ticks×13° 回した方向へ子星を放つ。子星0.1→0.3。
- **Pressure (static inference):** 移動母弾の軌跡に螺旋/コークスクリュー帯が残る。

## ID 13 — 土着神「ケロちゃん風雨に負けず」

- **Class:** `THSC_Kerochan_Fuuu_ni_Makezu`
- **Original owner:** `SUWAKO`
- **Need level:** 2
- **Card lifetime:** 200 ticks (10.00s)
- **Archetype:** **構造化風雨＋ランダム雨**
- **Flow:** t>=2。t<140は4本の規則ストリーム、同時に全期間2本のランダム雨弾。
- **Trajectory:** 4本はyaw/pitchが周期揺動。別系統の水色米弾はランダムyaw/pitchで重力落下。
- **Pressure (static inference):** 規則的な流れの隙間をランダム雨が塞ぐ。

## ID 14 — 奇跡「ミラクルフルーツ」

- **Class:** `THSC_MiracleFruit`
- **Original owner:** `SANAE`
- **Need level:** 1
- **Card lifetime:** 60 ticks (3.00s)
- **Archetype:** **減速母弾→遅延多層放射**
- **Flow:** t=6,36に8way赤楕円母弾。t=1では使用者のPotion効果も解除。
- **Trajectory:** 母弾は2.0→0.1へ減速。寿命時に8方向×6発の小弾を生成し、delay 3,5,7,9,11,13tick。
- **Pressure (static inference):** 止まりかけた予告点から時間差連射が立ち上がる。

## ID 15 — 奇跡「ファフロッキーズの奇跡」

- **Class:** `THSC_Fafurotskies_no_Kiseki`
- **Original owner:** `SANAE`
- **Need level:** 1
- **Card lifetime:** 40 ticks (2.00s)
- **Archetype:** **ランダム落下物イベント**
- **Flow:** t=1のみ10個のキャリアを発射し、0〜99のpatternを選ぶ。
- **Trajectory:** 終端で通常は3Dナイフ、魚、Creeper、Chicken等。特定日付にはCreeper/NuclearShotへ分岐。
- **Pressure (static inference):** 幾何学弾幕より、何が落ちるか不確定な混沌型。

## ID 16 — 妖怪退治「妖力スポイラー」

- **Class:** `THSC_YouryokuSpoiler`
- **Original owner:** `SANAE`
- **Need level:** 2
- **Card lifetime:** 80 ticks (4.00s)
- **Archetype:** **敵中心リング→ブーメラン帰還**
- **Flow:** t=0〜19と41〜59にターゲット位置中心の7wayリングを逆回転で生成。
- **Trajectory:** 初段2.0→0.2へ減速。special後半で使用者方向へ再照準し、低速から1.0へ加速して戻る。
- **Pressure (static inference):** 往路と復路が交差するブーメラン型。

## ID 17 — 開海「モーゼの奇跡」

- **Class:** `THSC_MosesMiracle`
- **Original owner:** `SANAE`
- **Need level:** 2
- **Card lifetime:** 180 ticks (9.00s)
- **Archetype:** **二枚の回転弾幕壁**
- **Flow:** 偶数tickを除外し、ほぼ全期間で左右2列×高さ11段の青弾。
- **Trajectory:** 左右発射位置がtime×6°で回転し、各列が垂直に並ぶため2枚の壁/カーテンになる。
- **Pressure (static inference):** 二つの壁の間の通路自体が時間で回転する。

## ID 18 — 大奇跡「八坂の神風」

- **Class:** `THSC_Yasaka_no_Kamikaze`
- **Original owner:** `SANAE`
- **Need level:** 3
- **Card lifetime:** 270 ticks (13.50s)
- **Archetype:** **呼吸する反転風リング**
- **Flow:** t>=5は毎tick。46tick周期の前後半で緑/水色リングと回転方向が交代。
- **Trajectory:** リング幅/角度がsin/cosで脈動し、0→1.6。WIND01は強い押し出し＋上方向、空中相手はダメージ増。
- **Pressure (static inference):** 弾密度に加え、被弾後の位置まで壊す制圧型。

## ID 19 — 氷符「アイシクルフォール」

- **Class:** `THSC_IcicleFall`
- **Original owner:** `CIRNO`
- **Need level:** 1
- **Card lifetime:** 180 ticks (9.00s)
- **Archetype:** **減速扇→90°折れ→落下**
- **Flow:** 5tickごと、難易度で扇本数が増え左右対称。
- **Trajectory:** 速度iから0へ減速後、±90°へ方向変更し重力を有効化して再加速。
- **Pressure (static inference):** 放射扇が途中で横折れ＋落下へ位相変化。

## ID 20 — 禁弾「スターボウブレイク」

- **Class:** `THSC_StarbowBreak`
- **Original owner:** `FLANDORE`
- **Need level:** 3
- **Card lifetime:** 150 ticks (7.50s)
- **Archetype:** **成長虹リング→終端反転**
- **Flow:** 3〜23tick相当の窓を60tick周期で繰り返し、way数を段階的に増やす虹リング。
- **Trajectory:** 前方へ加速し、寿命時specialで向きを反転/微偏向、負の初速から別方向へ再加速する子弾を作る。
- **Pressure (static inference):** 通過済み領域が折り返しで再び危険になる。

## ID 21 — 禁弾「カタディオプトリック」

- **Class:** `THSC_Catadioptric`
- **Original owner:** `FLANDORE`
- **Need level:** 3
- **Card lifetime:** 110 ticks (5.50s)
- **Archetype:** **超大量無限反射クラスター**
- **Flow:** t=1,26,51。毎回5軸のScarletShoot型クラスター。
- **Trajectory:** 各軸大1＋中11＋小22、すべて青BOUND04。3バーストで理論上510発の初期弾が反射を繰り返す。
- **Pressure (static inference):** 地形があるほど反射弾が蓄積する極端な面制圧。

## ID 22 — 祟符「ミシャグジさま」

- **Class:** `THSC_Mishagujisama`
- **Original owner:** `SUWAKO`
- **Need level:** 3
- **Card lifetime:** 90 ticks (4.50s)
- **Archetype:** **急減速する二重呪リング**
- **Flow:** 9tick周期で32way×2の緑米弾リング。
- **Trajectory:** 2組はrotationSpeed +1.2/-1.2。1.9→0.2へ強く減速しながら逆方向に曲がる。
- **Pressure (static inference):** 高速展開後に低速高密度の壁として残る。

## ID 23 — 「レッドマジック」

- **Class:** `THSC_RedMagic`
- **Original owner:** `REMILIA`
- **Need level:** 4
- **Card lifetime:** 190 ticks (9.50s)
- **Archetype:** **母弾軌道＋遅延子弾の軌跡描画**
- **Flow:** t=5と75に紫母弾を複数リング生成。2回目は曲がり方向反転。
- **Trajectory:** 母弾specialが3tick周期で回転する赤光弾をほぼ静止で残し、子弾は後から0.1→0.3へ動く。
- **Pressure (static inference):** 母弾の通過履歴が後から動き出す危険線になる。

## ID 24 — 奇術「エターナルミーク」

- **Class:** `THSC_EternalMeek`
- **Original owner:** `SAKUYA`
- **Need level:** 2
- **Card lifetime:** 50 ticks (2.50s)
- **Archetype:** **高速連続狙いナイフ**
- **Flow:** t=0〜39、毎tick、ターゲット方向基準に3本。
- **Trajectory:** 約50°ランダム円錐内へ青ナイフを速度1.5で射出。
- **Pressure (static inference):** 高レート照準＋小ランダムずれで静止/直線移動を咎める。

## ID 25 — 恋符「ノンディレクショナルレーザー」

- **Class:** `THSC_NonDirectionalLaser`
- **Original owner:** `MARISA`
- **Need level:** 3
- **Card lifetime:** 103 ticks (5.15s)
- **Archetype:** **回転五芒レーザー輪**
- **Flow:** t=3に5本、t=63にさらに5本LaserB。
- **Trajectory:** 72°間隔。前半-4°/tick、後半+4°/tick、太さ0.7・長さ約20.8。
- **Pressure (static inference):** 回転するレーザー壁の安全角が連続移動し、後半は回転方向も反転。

## ID 26 — 幻想「花鳥風月、嘯風弄月」

- **Class:** `THSC_Kachoufuugetu`
- **Original owner:** `YUUKA`
- **Need level:** 5
- **Card lifetime:** 90 ticks (4.50s)
- **Archetype:** **移動レーザー花＋反対向き花弁弾**
- **Flow:** 10tickごとに5方向へ母弾＋各母弾に5本の短LaserB。その他の偶数tickには黄弾ペア。
- **Trajectory:** 全体軸time×3°、pitchはsinで振れ、t>30で回転符号反転。母弾のレーザーも4°回転。
- **Pressure (static inference):** 複数の回転座標系が重なる移動レーザー花。

## ID 27 — 神槍「スピア・ザ・グングニル」

- **Class:** `THSC_Spear_the_Gungnir`
- **Original owner:** `REMILIA`
- **Need level:** 3
- **Card lifetime:** 50 ticks (2.50s)
- **Archetype:** **登録済み・主弾幕なし**
- **Flow:** このX1クラスはコンストラクタだけでspellcard_main()を持たない。
- **Trajectory:** 同名の槍/レーザー系実装は別経路にあるが、この登録スペカからは呼ばれない。
- **Pressure (static inference):** カード単体では静的解析上、弾幕なし。
- **Boundary:** active registry entry exists, but this X1 class has no `spellcard_main()`; similarly named item/mob behavior is not projected into the card.

## ID 28 — 月符「ムーンライトレイ」

- **Class:** `THSC_MoonlightRay`
- **Original owner:** `RUMIA`
- **Need level:** 1
- **Card lifetime:** 60 ticks (3.00s)
- **Archetype:** **七本回転長レーザー**
- **Flow:** t=3に1回、7本のLaserB。
- **Trajectory:** 360°/7間隔、-2°/tickで回転。長さ40、太さ0.8+level×0.2。
- **Pressure (static inference):** 7本の長いスポークが円周方向の退路を掃く。

## ID 29 — 華符「芳華絢爛」

- **Class:** `THSC_HoukaKenran`
- **Original owner:** `MEIRIN`
- **Need level:** 2
- **Card lifetime:** 170 ticks (8.50s)
- **Archetype:** **二重編みリング＋周期赤壁**
- **Flow:** t<150で3tickごとに黄6wayリング2組。20tickごとに赤32wayリング。
- **Trajectory:** 黄2組はbaseAngle ±time×2、リング広がりはsinで変動。赤リングが高密度アクセント。
- **Pressure (static inference):** 編み目が変化する黄格子を周期的な赤壁が区切る。

## ID 30 — 彩符「彩光乱舞」

- **Class:** `THSC_SaikouRanbu`
- **Original owner:** `MEIRIN`
- **Need level:** 2
- **Card lifetime:** 80 ticks (4.00s)
- **Archetype:** **規則リング↔左右回転ランダム雲**
- **Flow:** 最初60tickを30tick周期で三相に分割。
- **Trajectory:** 相1は15way拡大リング。相2はランダム3D弾が+3°回転し1.5→0.4。相3は-3°回転。
- **Pressure (static inference):** 整然→右旋乱流→左旋乱流で読み方を切り替えさせる。

## ID 33 — 蓬莱「凱風快晴  -フジヤマヴォルケイノ-」

- **Class:** `THSC_FujiyamaVolcano`
- **Original owner:** `MOKOU`
- **Need level:** 5
- **Card lifetime:** 120 ticks (6.00s)
- **Archetype:** **停止地点爆発→フラクタル分裂**
- **Flow:** t=0,15,30とt=63,70,77,84にターゲット方向へ青キャリア。
- **Trajectory:** 距離依存の負加速度で停止を狙い、停止時44way赤大弾球へ爆発。大→中→小→極小へ各段2分裂。ブロック衝突は40大弾。
- **Pressure (static inference):** 少数キャリアから危険量が非線形に増える局所爆発→面制圧。

## ID 34 — 蟲符「リトルバグストーム」

- **Class:** `THSC_LittleBugStorm`
- **Original owner:** `WRIGGLE`
- **Need level:** 2
- **Card lifetime:** 150 ticks (7.50s)
- **Archetype:** **同一弾の多段変身**
- **Flow:** t=0〜59、毎tick sphereShot。特殊系統01/11を15tickごとに切替。
- **Trajectory:** 寿命ごとに90°ターン＋急減速→小/光弾化→黄/白点滅→-45°または+135°ターン→大型米弾→0.5へ再加速。
- **Pressure (static inference):** 同一弾が何度も意味を変え、視覚形状変化が次フェーズの予告になる。

## ID 35 — 蛍符「地上の流星」

- **Class:** `THSC_MeteorOnEarth`
- **Original owner:** `WRIGGLE`
- **Need level:** 1
- **Card lifetime:** 120 ticks (6.00s)
- **Archetype:** **回転母弾→流星トレイル**
- **Flow:** t=5と65に母弾リング。2回目は回転符号反転。難易度で母弾数/追加リング変化。
- **Trajectory:** 母弾が2tickごとに基準軸周りticks×13°の水色小弾を生成。子弾は30tick後に加速開始。
- **Pressure (static inference):** 母弾の螺旋尾が残り、第2波の逆回転尾と交差する。

## ID 40 — 雷矢「ガゴウジサイクロン」

- **Class:** `THSC_GagoujiCyclone`
- **Original owner:** `TOZIKO`
- **Need level:** 2
- **Card lifetime:** 120 ticks (6.00s)
- **Archetype:** **直角ジグザグ矢＋周期リング**
- **Flow:** 0〜40/60〜99の偶数tickに9矢リング。20tickごと円弾リング。難易度で中央矢・赤矢追加。
- **Trajectory:** 矢は初期45°回転＋急減速後、20tick周期の9/19tickで-90°/+90°へ向きを変え速度1へ戻す。
- **Pressure (static inference):** 雷のような直角ジグザグに通常リングが重なり、折れ線回避を狭める。

## Dormant / unregistered implementation — 神宝「ブリリアントドラゴンバレッタ」

`THSC_BrilliantDragonBullet` is present in the distributed source/class set and `ja_JP.lang` has display ID 41, but its `CommonProxy.registerSpellCard(...)` line is commented out. The commented line tries to use numeric ID **34**, which is actively occupied by Little Bug Storm.

Its implementation emits two counter-sweeping red familiar carriers every 5 ticks. At carrier end it emits randomized light shots and four short moving lasers. This is preserved as **dormant prototype evidence**, not counted among the 35 active cards.

## Localization residue

`ja_JP.lang` also contains names at IDs 42–45, 50 and 51 without matching active registrations/implementation classes in this X1 tree:

- 42 神宝「ブディストダイヤモンド」
- 43 神宝「サラマンダーシールド」
- 44 神宝「ライフスプリングインフィニティ」
- 45 神宝「蓬莱の玉の枝　-夢色の郷-」
- 50 結界「夢と現の呪」
- 51 夜符 "ナイトバード"

These remain localization/reserved residue unless another exact historical artifact supplies implementation evidence.
