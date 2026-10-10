# Spore 2.2.0j — 原作Bytecodeの自動再検証（2026-10-11）

**限定結果：固定された原作JARの9クラス SHA-256 照合 PASS 9/9、Bytecode契約の静的検査 PASS 13/13。Forge実機・TPS・勝率・互換性はNOT_RUN。**

## 入力と再実行方法

- 入力：個人保有 spore_1.20.1_2.2.0j.jar、Minecraft 1.20.1 Forge。JAR SHA-256：d20c4be6606f9752ecfd964eba625363eb76a28e327d67fe6dda4be748401489。
- 自作の検査器：[tools/verify_spore_bytecode.py](tools/verify_spore_bytecode.py)。実行済みPythonファイル SHA-256：1541b636ee23262435844bf76bb5f889fe49ba363f3853bd25e9c0b222068a71。コードは原作者のJavaソースを複製したものではない。
- 結果：[verification/bytecode-gate-2026-10-11.json](verification/bytecode-gate-2026-10-11.json)。検証済み出力SHA-256：53715e3c92e5ed930f2f4513023f00f027809389bdc5fe0a9e7509cae7450fc6。
- 実行環境：Linux、Python 3.13.5、JDK 21.0.12.1のjavap。標準ライブラリのみ使用し、ゲームを起動しない。

Windows PowerShell例（TECH-HUBルート、Java JDKのjavapにPATHが通っている場合）：

~~~powershell
py -3 .\departments\minecraft\mods\fungal-infection-spore\tools\verify_spore_bytecode.py "C:\Path\To\spore_1.20.1_2.2.0j.jar" --out "C:\Temp\spore-bytecode-report.json"
~~~

実際にJARを指定して実行した。2回連続実行はJSONのバイト列まで一致。別のSRParasites JARを誤指定したときは、内容を解析せず BLOCKED_HASH_MISMATCH を返した。原JARやライセンス付き資産は公開Gitへ入れない。

## 13件の静的検証

| 契約 | 結果 |
| --- | --- |
| 1. Protoの抽選した個体位置kと、memberタグに書かれる部隊番号jが異なる変数 | PASS_STATIC |
| 2. 初期部隊に4候補をshuffleして入れる | PASS_STATIC |
| 3. LivingDamageEventの攻撃側加点と被害側減点の経路 | PASS_STATIC |
| 4. 報酬処理がそのイベントの被ダメージ量に比例しない | PASS_STATIC |
| 5. 加点+0.05、減点-0.10 | PASS_STATIC |
| 6. 通常重み更新は選択した4要素に[-1,1]のclamp | PASS_STATIC |
| 7. 線形スコアに対する決定論的argmaxと標的null時の固定入力 | PASS_STATIC |
| 8. moraleBoostは別経路で乱数を加算、同メソッドではclampなし | PASS_STATIC |
| 9. Biomassを波の前に判定し、減算側に非負下限なし | PASS_STATIC |
| 10. Proto数はディメンション別フィルタがないstaticリストのsize | PASS_STATIC |
| 11. onWorldLoadは保存要求のdimension判定なしで現在のLevelにforceChunk | PASS_STATIC |
| 12. 新規ChunkLoadRequestをcontainsValueで調べるがequals overrideなし | PASS_STATIC |
| 13. EntityJoin/EntityLeaveを通してProtoを登録・解除 | PASS_STATIC |

これは「指定したバイナリにその構造がある」という検査であり、**必ず実ゲームでその分岐が実行される**ことや、他クラスや依存MODで抑止処理が存在しないことまで保証するものではない。

## 今回確定した3つの分析上の区別

### 学習とダメージ量

Forgeの [LivingDamageEvent](https://mcstreetguy.github.io/ForgeJavaDocs/1.20.1-latest/net/minecraftforge/event/entity/living/LivingDamageEvent.html) は防具等の軽減処理後、被ダメージ適用直前に発火する。原作の報酬ブランチはダメージ量を更新幅に掛けず、**イベント回数**に応じ+0.05/-0.10を加算する。

条件付き数学例：2回加点・1回減点の合計は0。イベントが互いに排他的な成功/失敗であり、重みのclampや士気処理を無視できるなら、平均値が非負となる加点比率は 2/3 以上。**これを対人戦闘の勝率66.7%とは呼ばない。**

射撃10ヒットは加点10回となり得るが、射撃1ヒット（同程度の総ダメージ）なら加点1回になる可能性がある。これが目的達成・攻撃の価値と一致するかは別の実験が必要。

### 部隊の帰属とMobの種類

初期チームの候補は4個。部隊index jに対し個体抽選index kは4通りあり、全16組のうち12組でj≠k（75%）。**これは個体位置の不一致率の計算**であって、必ず75%の確率で異なる**種類**のMobが表彰・入替されるという意味ではない。同じ種類が複数の位置へ入る設定もある。

Proto.awardMemberは与えられた位置の個体種をfavoritesへ追加、punishMemberはその位置を取り除いてリスト末尾へ代替を入れる。被害の実態・改善の有効性は依然としてBUG_CANDIDATE/NOT_RUN。

### 判定境界とゲームの実測

static Proto数・チャンクの復元ループなどの**静的なスコープ**は検査したが、実サーバーのEntity登録順・chunk unload/load・Forge ticket・マルチプレイ実測までは試験していない。

原典：[学習と個体評価の監査](HIVEMIND-LEARNING-LIFECYCLE-AUDIT-2026-10-11.md)、[ディメンションの監査](CROSS-DIMENSION-AI-BOUNDARY-AUDIT-2026-10-11.md)。次の観測仕様：[隔離GameTest/LAB受け入れ契約](LAB-GAMETEST-ACCEPTANCE-2026-10-11.md)。

## 成熟度

- Evidence: SHA-256を固定したOriginal JAR Bytecode / 選定9クラス
- Static contracts: 13/13 PASS（本検証器の限定契約のみ）
- GameTest: NOT_RUN
- Source equivalence to author's official release: NOT_VERIFIED
- ANCHOR: Minecraft 1.20.1 Forge 2.2.0j
- FRONTIER: 1.21.1 NeoForgeの別配布物、解析対象外
- 全1,350クラスの解析: NOT_COMPLETE
- ライセンス: 原作All Rights Reserved、原JAR/全decompileソース/資産はGitに複製しない。
