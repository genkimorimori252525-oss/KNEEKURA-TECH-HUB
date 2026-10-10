# SporeのSignal派遣に関する合成分岐試験

**2026-10-11。実行済みの数学的マイクロモデル。Minecraft実機と原作JARは実行していない。**

## 何を確認したか

[Minecraft原作のBytecode調査](../../../../minecraft/mods/fungal-infection-spore/GROUP-COMMAND-SIGNAL-BYTECODE-2026-10-11.md)に基づき、**Proto.checkForCalamities** の特定の決定分岐を独立に再実装した。これは原作ソースの転載ではなく、50%の独立した条件付き試行を表現する小さな確率モデルである。

- Calamityが任務を持たない状態かつ指揮官の探索範囲に存在するものと**仮定**する。
- 各候補へそれぞれ50%で派遣を試み、1体でも採用すればリダイレクト。全て外れた場合はWomb生成を**試みる**。
- 部隊が1体でも使用可能なら必ず転用する「優先配備」は**当部門の独立した比較案**であって原作にある設計ではない。
- MinecraftのLevel、Map、距離、Signal作成、tick、配置、Entity AI、戦果や実際のWomb成功率はシミュレートしない。

## 再現方法

Python 3.10以上、外部ライブラリは不要。実験スクリプトと、実際に動かした結果：

- [probe.py](probe.py) — SHA-256 **2e803e5aa3fe5158fcf4403c2d651aec88031158f870ecd85b8917221b72b40c**
- [results.json](results.json) — SHA-256 **aa98996ab05349df181e9498090f546489cde925dd68e792fbccf06ea033292e**

~~~bash
python3 probe.py --trials 30000 --seed 20261011 > results.json
~~~

Python 3.13.5で各候補数0〜5に対し30,000回ずつ、合計180,000回の意思決定を実行。乱数はPython random.Randomで固定し、**同一条件2回で結果のバイト一致**を確認。別のRNGを用いるMinecraftとbit単位の一致は主張しない。

## 理論式と合成結果

候補数 n が全員利用可能で、各判定が独立の50%成功なら、

`P(Womb attempt | n eligible)=2^(-n)`

| 利用可能なCalamity | 理論上のWomb生成**試行**率 | 合成モデルの試行率 | 別案: 先に部隊を転用 |
| ---: | ---: | ---: | ---: |
| 0 | 100% | 100% | 100% |
| 1 | 50% | 50.2267% | 0% |
| 2 | 25% | 25.43% | 0% |
| 3 | 12.5% | 12.6133% | 0% |
| 4 | 6.25% | 6.2133% | 0% |
| 5 | 3.125% | 3.0567% | 0% |

上記は**算術の再現であり、ゲームの派遣成功率やTPS測定ではない**。30,000回の標本結果は式に近く、スクリプトには統計的な許容範囲のassertを含む。

## 学習と将軍AIへの接続

派遣に失敗した際に新兵站拠点を作る設計は、多様性・新拠点確保の利点があるかもしれない。一方、すでに利用できる部隊があれば既存戦力を優先する、Wombを新設するときは資源残量とチケット負荷を確認する、という設計もあり得る。

「敵が賢い」と判断するには、到達率・戦力損耗・移動時間・生成費用・プレイヤーの防衛状況・サーバー負荷を実ゲームか独立の戦場モデルで比較しなければならない。**原作より別案が優秀とはまだ言えない。**

- [原作のSignal発信・Wombフォールバック・Goal挙動](../../../../minecraft/mods/fungal-infection-spore/GROUP-COMMAND-SIGNAL-BYTECODE-2026-10-11.md)
- [AI部門のSignal指揮設計と未解決](../../../multi-agent/SIGNAL-ROUTING-CASE-STUDY-2026-10-11.md)
- [MinecraftのLAB受け入れ条件](../../../../minecraft/mods/fungal-infection-spore/LAB-GAMETEST-ACCEPTANCE-2026-10-11.md)

**状態**: PASS_SYNTHETIC_MODEL / MINECRAFT_RUNTIME_NOT_RUN / PERFORMANCE_NOT_MEASURED / ALL_WORLD_SCENARIOS_NOT_TESTED。
