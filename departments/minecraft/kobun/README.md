# 古文 — Ancient Minecraft MOD Studies

KNEEKURA TECH HUB の **太古の Minecraft MOD 専用解析区画**。

ここは `departments/minecraft/mods/` の旧版置き場ではない。
**現代の 1.20.1 Forge 技術棚と混ぜると時代差そのものが情報を壊す対象**を、原版の歴史的コンテキストごと隔離して読むための場所。

## なぜ別区画にするか

古い MOD では、同じ単語でも意味が違う。

- Forge / FML / ModLoader の責務が違う
- MCP / SRG / obfuscated 名が現代 Mojmap と一致しない
- Entity AI / pathfinding / rendering / networking / worldgen の API 世代が違う
- Java runtime、Gradle、launchwrapper、coremod、ASM 前提が違う
- 1.7.10 以前の設計を 1.20.1 の class 名へ直訳すると、実装事実と現代解釈が混ざる

そのため古文では、最初から 1.20.1 を ANCHOR にしない。

まず **当時その MOD が何を、どの Minecraft / loader / mapping / Java 環境で実現していたか** を確定する。
現代へ持ち帰る作業は、その後の派生分析として分離する。

## 対象

典型的には次を古文候補とする。

- Minecraft 1.7.10 以前の MOD
- ModLoader / 旧 Forge / FML / LaunchWrapper / coremod 世代
- MCP/SRG 名や古い bytecode patch が技術理解に不可欠な MOD
- 後世へ直接続いていない歴史的 MOD
- 現代版と同名でも、実装系譜が切れている旧版
- ユーザーまたは研究担当が「古文として読むべき」と判断した対象

**1.7.10 は目安であって絶対境界ではない。**
1.8–1.12.2 でも、現代 lane に置くことで API 世代差が誤解を生む場合は古文へ入れてよい。

逆に古くても、現行 upstream へ連続した系譜を持ち ANCHOR / FRONTIER 比較が自然なら、通常の
`departments/minecraft/mods/` で扱ってよい。

## ディレクトリ

```text
departments/minecraft/
├─ mods/                 現代技術 lane
│  └─ ...                ANCHOR 1.20.1 Forge + FRONTIER
└─ kobun/                古文 lane
   ├─ README.md
   ├─ ANALYSIS-SPEC.md
   ├─ TARGET-TEMPLATE.md
   ├─ catalog/
   │  └─ MODS.md
   └─ mods/
      └─ <target-slug>/
```

## 古文の4つの時間レイヤー

### 1. ORIGINAL — 必須

歴史的原版そのもの。

固定するもの:

- MOD version
- Minecraft version
- loader / modloader
- Java version
- mapping namespace/version
- dependencies
- 配布 artifact
- source revision
- license
- release date

実装事実の主証拠はここに属する。

### 2. ERA-CONTEXT — 推奨

当時の資料。

- 公式フォーラム
- 当時の wiki / 攻略
- readme / changelog
- issue / commit
- contemporaneous video / blog
- Wayback 等で回収した歴史資料

目的は **当時どう使われ、何が不具合で、何が特徴と認識されていたか** を復元すること。

### 3. DESCENDANT — 任意

後世の port / remake / fork / spiritual successor。

原版の解析補助には使えるが、**DESCENDANT の実装を ORIGINAL の実装事実にしてはいけない。**

### 4. MODERN-EXTRACTION — 派生分析

現代へ持ち帰る技術。

これは SourceSnapshot ではない。

```text
historical mechanism
      ↓
version-independent concept
      ↓
modern analogue
      ↓
semantic gap
      ↓
1.20.1 Forge reconstruction strategy
```

「古い class を現代 class へ置換しただけ」の表を作る場所ではない。

## Temporal Firewall

古文で最重要の規則。

1. ORIGINAL の class/method 名を現代名へ黙って置換しない。
2. MCP / SRG / obfuscated / named の対応は、mapping 証拠がある時だけ結ぶ。
3. 後世の wiki や port の説明を原版挙動へ遡及させない。
4. 現代 Minecraft の常識から古いコードの意味を補完しない。
5. 「今ならこう作る」と「当時こう動いていた」を同じ段落で事実扱いしない。
6. modern reconstruction は必ず ORIGINAL finding から一段派生したものとして書く。

## 証拠

基礎ラベルは通常 lane と共通:

- `DIRECT_OBSERVATION`
- `AUTHOR_CLAIM`
- `INFERENCE`
- `UNKNOWN`

加えて temporal role を持つ:

- `ORIGINAL_BINARY`
- `ORIGINAL_SOURCE`
- `DECOMPILED_ORIGINAL`
- `ERA_CONTEXT`
- `LATER_RETROSPECTIVE`
- `DESCENDANT_SOURCE`
- `MODERN_EXTRACTION`

同じ主張に複数時代の証拠がある場合も、時代を潰して「多数決」しない。

## 保存原則

Git に残す:

- exact artifact/source identity
- hashes
- historical environment manifest
- source/bytecode maps
- subsystem maps
- failure/repair history
- period-specific terminology
- mappings/name correspondence
- modern extraction notes
- evidence locator

Git に通常残さない:

- 原配布 JAR
- full decompile
- upstream 全 source checkout
- third-party assets
- old launcher/runtime bundles

## 実機

古い MOD の起動は現行 LAB と同一視しない。

必要なら:

- era-correct Java
- era-correct loader
- disposable world
- isolated game directory
- network-off / 最小依存
- exact artifact identity

で別実験として扱う。

「現代 Forge で起動しない」は古文対象の失敗ではない。

## 入口

- 古文 catalog: [catalog/MODS.md](catalog/MODS.md)
- 詳細規則: [ANALYSIS-SPEC.md](ANALYSIS-SPEC.md)
- 新規 target 雛形: [TARGET-TEMPLATE.md](TARGET-TEMPLATE.md)
