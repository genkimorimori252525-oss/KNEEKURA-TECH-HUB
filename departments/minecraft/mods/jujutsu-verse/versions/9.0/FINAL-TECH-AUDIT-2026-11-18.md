# Jujutsu Verse 9.0 — 最終再監査 / TECH-HUB引き継ぎ

**調査日**: 2026-11-18 (JST)  
**対象**: `jujutsu_kaisen-9.0-forge-1.20.1(1).jar` （ユーザー提供）  
**分析手法**: 実JARのZIP全体目録、構成JSON、シェーダーI/F、選定したJavaクラスとメソッドの`javap -p -c/-v`による静的確認。ゲーム実機起動なし。  
**成果物**: 本Markdown、および `JujutsuVerse-9.0-FINAL-evidence-2026-11-18.json`。  
**作業状態**: 選定範囲の静的解析（TECH-HUBの全ファセットCOMPLETEではない）。

## A. 技術調査の基準・証拠境界

- TECH-HUB mainの手順: `departments/minecraft/ANALYSIS-WORKFLOW.md` SHA `2eb4ac9443d14b08037258251df2aed34be0b777`。
- TECH-HUB mainの仕様: `departments/minecraft/ANALYSIS-SPEC-v1.md` SHA `3bdb615406be81c2fe0bf36028dc59bd0fa1b23f`（本文v1.2）。
- **ANCHOR**: Minecraft 1.20.1 / Forge 47+ / Jujutsu Verse 9.0。`mods.toml`で`jujutsu_kaisen`, `geckolib`, `playeranimator`を確認。Java 17向けMixin設定。
- **FRONTIER**: 2026-11-18の公式配布で同9.0。別Minecraft版は確認せず。
- **COMPARATIVE**: TECH-HUB Draft PR #100に8.1の固定バイナリ研究記録がある。今回はGitHub記録を照合し、8.1実JARの直接再検証やバイナリ差分とは区別する。
- **権利**: 公式配布はAll Rights Reservedで、作者は内部データへの無断アクセス・抽出禁止を明記。コード・モデル・テクスチャ・シェーダー本文は再配布せず、個別ファイルハッシュや機能要約に限定。独立実装には権利・許諾の確認が必要。

公式: https://www.curseforge.com/minecraft/mc-mods/jujutsu-verse/files/9609792  
8.1: https://www.curseforge.com/minecraft/mc-mods/jujutsu-verse/files/8097357  
概要と注意: https://www.curseforge.com/minecraft/mc-mods/jujutsu-verse

### 対象の整合性

| 項目 | 検査結果 |
|---|---|
| JAR SHA-256 | `fdf1f8a6c28833c093dc778764b5a6147fc0552ec34e172f918fa4be8dccc065` |
| サイズ | 40,621,200 bytes |
| ZIP内部エントリ | 6,436 |
| `.class` | 3,818 |
| Core shader files | 36 |
| GeckoLib animation JSON | 155 |
| GeckoLib geo JSON | 156 |
| Particle JSON | 40 |
| `data/jujutsu_kaisen`ファイル | 452 |
| ZIP CRC | 全エントリ検査で失敗なし |
| Mixin declarations | 186 (2設定ファイル合計、静的対象クラス欠落0) |

※「クラス・データを全部目録化した」と「全クラスのロジックをレビューした」は異なる。

## B. 8.1の既存GitHub研究との限定比較（2026-11-18訂正）

**訂正の出典:** この対象の8.1研究は未マージのDraft PR [#100](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/pull/100) に現存する。8.1の実JAR同一性は [JAR-PROVENANCE.md](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/jolly/jujutsu-verse-8.1-analysis-2026-10-06/departments/minecraft/mods/jujutsu-verse/JAR-PROVENANCE.md) の保存記録に基づく。**8.1の実JARは今回再取得できていないため、9.0とのクラス単位の直接差分ではない。**

| 項目 | 8.1（PR #100の記録） | 9.0（本JAR実測） | 差し引き |
|---|---:|---:|---:|
| SHA-256 | `d0f2f4e427ae3db92432cfac186a7db137ab8960807ed13ebfa64c7971cb8217` | `fdf1f8a6c28833c093dc778764b5a6147fc0552ec34e172f918fa4be8dccc065` | 別バイナリ |
| ZIPエントリ | 4,860 | 6,436 | +1,576 |
| Java `.class` | 2,619 | 3,818 | +1,199 |
| サイズ（bytes） | 28,285,565 | 40,621,200 | +12,335,635 |

旧版レポートにあった`094247a3…`というハッシュは、**同じTECH-HUBにある別対象「Jujutsu Craft ver50.1」**のものであり、Jujutsu Verse 8.1のハッシュではない。旧メモの`6,377エントリ / 3,493クラス`もこの8.1研究記録と一致しないため、比較根拠から除外した。これは今回の公開前検証で修正した点である。

8.1の[DOMAIN-CLASH-AND-CUTIN.md](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/jolly/jujutsu-verse-8.1-analysis-2026-10-06/departments/minecraft/mods/jujutsu-verse/DOMAIN-CLASH-AND-CUTIN.md)には、ダメージ120以上での領域解除、プレイヤー`DOMAINHP -= damage / 8`、非プレイヤー`DOMAINHP -= damage / 14`、2/3人カットインが記録されている。9.0の選定Bytecodeでも当該数式と表示枠を確認した。**両版で見つかった同様の処理が同一実装だとは断定しない。**

8.1のTECHNIQUE-VFX-ATLASは18のプレイヤーキット別に技を整理している。9.0では全技について同じ粒度の再解析をしていないため、変更有無は未判定。8.1領域の近傍探索50と9.0の`DEFAULT_DOMAIN_SIZE=20`は異なる意味の値であり、領域半径が50→20に変わったと推論してはならない。

## C. 9.0で直接確認したFeature Map（選定範囲）

| ID | 対象 | JAR内の根拠 | 直接確認した実装上の特徴 | 判定 |
|---|---|---|---|---|
| VFX-01 | 黒閃 | `BlackFlashRenderer.class`, `black_flash.fsh/json` | `growMain/grow/growEcho`で複数の枝、`travellingStroke/stroke`で進行、`ribbon/impact`で表示。`Age/Seed/Pass` uniformとnoise関数 | EVIDENCE_BACKED（静的構造） |
| VFX-02 | ビーム | `BeamRenderer.class`, `beam_volume.fsh/json`, `beam_post.fsh/json` | SceneDepth、行列と境界情報、ボリューム描画、発光・Bloom・深度ガード。EffectModeでビーム/チャージ/衝突/先端/着弾系。サンプリング段数24/32/40/48の選択肢 | EVIDENCE_BACKED（描画パイプライン） |
| HIT-01 | ビーム当たり判定 | `BeamServerHitBox.class` | Server `LevelTickEvent.END` でレベルのEntity集合を一巡して発射中のLaser/Pureloveを抽出し、`BeamHitBoxProcedure`につなぐ | EVIDENCE_BACKED（列挙と呼出し） |
| VFX-03 | 無下限 | `LimitlessVFXRenderer$LimitlessVFXClientEvents.class` | 輪、帯、フラクタル稲妻、破片、フレア等の描画関数が分離 | MAPPED（全技/全引数未追跡） |
| VFX-04 | 簡易領域 | `SimpleDomainVFXRenderer.class`, `simple_domain.animation.json` | 地面、エネルギー中心、展開、壁面、継続の複数メソッド。リソースに拡張4段階、サイズ維持ループ4種、段階縮小、崩壊4種 | EVIDENCE_BACKED（資産と構造） |
| VFX-05 | 炎の矢 | `FugaArrowVFXRenderer.class`, `fuga_arrow.fsh/json` | Time/Opacity/Flying/Seed/GlowPassパラメータを受ける独立シェーダー | EVIDENCE_BACKED（I/F） |
| VFX-06 | 地形破壊 | `TerrainBreakManager.class`, `TerrainBreakVFXRenderer.class` | 地形側の判定・破壊と、破片/煙/ガラス破片などのクライアント表示を分離 | EVIDENCE_BACKED（クラス構成） |
| DOM-01 | 領域カットイン | `DomainCutinOverlay.class` | 自分の領域/DOMAINTICKを起点に近傍LivingEntityを探索、最大3枠の2人/3人向けマスク＋3Dエンティティ表示 | EVIDENCE_BACKED（表示条件と分岐） |
| DOM-02 | 領域HP | `DomainbattleProcedure.class`, `Attackhit1Procedure.class` | ダメージ系Event側が領域HP処理を参照。÷8/÷14/120解除の分岐 | EVIDENCE_BACKED（選定メソッド） |
| DOM-03 | 発動と更新 | `DomainexpantionMobEffect.class`, `Domain_expansion_startProcedure.class`, `DomainexpansiontickupdateProcedure.class` | 領域の状態異常クラスが開始/毎tick更新手順へ静的参照。更新側は`SetdomainblockProcedure`を参照 | MAPPED（全勝敗分岐未読） |
| DOM-04 | ブロック生成 | `SetdomainblockProcedure.class`, `UnlimitedVoidSync.class` | OwnerProgress/GenerationProgress/SliceRange、DEFAULT_DOMAIN_SIZE=20、TOTAL_TICKS_TO_FINISH=50。同期側はSimpleChannelとBATCH=4096 | EVIDENCE_BACKED（構造と定数） |
| DOM-05 | 保存と復元 | `DomainTerrain$Snapshot.class`, `$Data.class`, `DomainTerrain.class` | BlockState+CompoundTagによる元状態、SavedData、所有者/チャンク索引、復元待ちキュー、ChunkLoad/Tick処理 | EVIDENCE_BACKED（保存設計） |
| DOM-06 | 伏魔御廚子 | `MalevolentShrineTerrain.class`, `$Budget.class` | ServerTickの共有Budget（1tick 16384チェック、1536破壊、4,000,000ns目安）、64の量子単位。実測上限/完了時間は不明 | EVIDENCE_BACKED（定数/割当） |
| COMP-01 | シェーダー互換性 | `ShaderVfxProtection.class`, `$Api.class`, `RenderCompatibilityPlugin.class` | Irisシャドウパスの判別、遅延/再実行層、Embeddium/Rubidium検知による特定Mixin適用抑止 | EVIDENCE_BACKED（分岐） |
| UI-01 | 映像演出 | `CutsceneManager.class` | 記録、保存、再生、カメラ補間、プレイヤーアニメ管理などのメソッド。一般プレイ時の公開条件は未検証 | MAPPED |
| GAME-01 | クエスト/囚獄/追加キャラ/世界生成 | `network/`, `world/`, `data/`, `PrisonRealm*` | インベントリ・クエスト・戦闘Mixin・構造物などの登録物の存在 | INVENTORIED |

### 重要な具体的ディテール

**C.1 同時領域展開カットイン**: `DomainCutinOverlay.checkDomainCondition`は`DOMAINEXPANTION`状態異常の有無と`DOMAINTICK`を参照し、`onRenderGui`ではローカルプレイヤーの条件成立時にAABBを50拡張してLivingEntityを探索する。候補を絞って最大3件を切り出し、2件または3件なら分割描画。**50は候補探索距離であり領域自体の半径ではない**。表示はクライアント側。サーバーでの勝敗・開始同期・勝敗通知の全因果は未検証。

**C.2 ビーム体積描画**: `beam_volume.fsh`は`EffectMode`ごとに`beam/charge/clash/head/surfaceImpact/chargeComplete`等を分岐し、SceneDepthを参照。描画用の`SceneDepth/emission/coarseEmission/blurA/blurB`資源は`BeamRenderer`にある。`beam_post.fsh`は`Source/Bloom/SceneDepth/SourceDepth/BloomDepth`などを受け、遮蔽を考慮する関数を持つ。**FPS/TPSや正しい見え方は未測定**。

**C.3 サーバー負荷リスク**: `BeamServerHitBox.onWorldTick`は`LevelTickEvent.END`かつサーバーレベルで処理し、`ServerLevel`からイテレート可能なEntity全体を取得、最初に候補のListを構築してから発射中Laser/Pureloveを探す。大量Entityの状況では線形列挙およびList生成が負荷になる**可能性**がある。これだけで「重い」とは断定しない。

**C.4 簡易領域のアニメーション**: `simple_domain.animation.json`に17のanimation stateが存在。拡大とサイズ維持は0.25秒ベースのループ/段階、崩壊は4〜7.5秒のキーを持つ。実際の時間はゲーム側の再生速度・呼び出し条件に左右される。

**C.5 地形復元**: `DomainTerrain$Snapshot`に`BlockState`と`CompoundTag`。`DomainTerrain$Data`は`SavedData`でエントリ、チャンク索引、所有者索引、復元待ちキュー、期限を持つ。ChunkLoad時はServer.execute経由で作業をキュー化。事故時の復元正確性は未テスト。

**C.6 Mixinの範囲と互換性分岐**: 2ファイルで合計186件のMixin名が定義され、名称に対応するclassは全件JAR内に存在。ただしすべて適用されるとは限らず、対象MOD/クラスのロードが保証されたわけでもない。`RenderCompatibilityPlugin.shouldApplyMixin`は原則trueだが、`CutsceneTerrainMixin$RenderCenter`についてのみ、EmbeddiumまたはRubidiumが検出された時falseを返す。これは「全描画Mixinを無効化する」実装ではない。

## D. 呼出し関係の局所証拠

以下はJAR定数プール内のクラス参照と、該当箇所の`javap`確認に基づく**局所的な候補グラフ**。全体の実行パス保証ではない。

```text
DomainexpantionMobEffect (効果のライフサイクル)
  ├─ Domain_expansion_startProcedure
  └─ DomainexpansiontickupdateProcedure
       └─ SetdomainblockProcedure
            └─ UnlimitedVoidSync (無量空処関連の同期経路)

Attackhit1Procedure (LivingHurtEvent)
  └─ DomainbattleProcedure.execute(target, value)
       ├─ DOMAINEXPANTION の解除条件
       └─ DOMAINHP の調整

描画：DomainCutinOverlay → 2/3人UI＋実Entity描画
保存：SetdomainblockProcedure$Placement → DomainTerrain（原状態保存/復元）
```

※「同tickでの複数人開始→競合結果決定→映像切替」の全分岐は今回の証拠では閉じていない。

## E. 9.0公式更新内容との突合

公開パッチノート（2026-11-14）では、Simple Domain / Domain Amplification / Black Flash / Terrain Destruction / Limitless / Sukuna / Beam-based SkillsのVFX改修、キャラ技改修、Player Menu / Character Info、Quest、Prison Realm、シェーダー互換性を記載。

- **AUTHOR_CLAIM**: 「9.0で改修した」は公式発表。8.1→9.0 diff未取得のため、個々のメソッドが新規か改変か、どの修正がシェーダー不具合を解消したかは不明。
- **DIRECT_OBSERVATION**: 9.0の描画クラス、シェーダー、Mixin、地形保存の構造・定数・ローカル呼出し関係。
- **INFERENCE**: 同じ描画部品を複数技で共有する設計、サーバー負荷の潜在的な問題、TECH-HUBへの転用価値。
- **UNKNOWN**: オリジナル8.1の最終取得物との差分、正確なTPS/FPS、実ゲームでの演出、複数領域の勝敗・優先順位、ShaderPack互換性。

## F. 規模とテストのリスク

1. `BeamServerHitBox`のサーバー毎tickの全Entity走査と短命List生成は、エンティティ数を振る単独ベンチマーク候補。
2. `MalevolentShrineTerrain`は`System.nanoTime()+4ms`を期限とするBudgetをセットするが、サーバーtick全体が4msに収まる意味ではない。複数領域と復元競合の測定が必要。
3. `DomainTerrain`は所有者・チャンク・復元処理を持つが、チャンクアンロードやワールド停止、BlockEntityを挟んだ復元の正確性は未テスト。
4. Mixin定義186件は、導入MODとの競合候補の探索面を広くする。対象全件が実際に競合する根拠にはならない。
5. 公式も一部ShaderPackでの問題残存を認めている。Embeddium/Rubidiumの静的分岐だけでOculusその他の組合せをPASSと判定しない。

## G. TECH-HUBへ回収する技術（独立したジャンルで保管）

- **Rendering / Procedural VFX**: 黒閃の形状生成→時間進行→帯状描画、EffectModeによる共通ビームシェーダー。
- **Rendering / Volume and Post**: SceneDepthを用いたビームの体積・遮蔽・Bloom・ポスト処理の分離。
- **Combat / Server-authoritative Hit**: VFXとサーバー側当たり判定の分離。全Entity走査はコピーせず空間クエリ化を検討。
- **Domain / Multiplayer UI**: 同時発動のキャスター候補と2/3人分割画面。描画の選択/タイムラインを戦闘判定から分離。
- **World / Transactional Terrain**: BlockState+BlockEntity NBTスナップショット、所有者索引、チャンク別の復元キュー。
- **Performance / Work Budgets**: 1tickあたりの数・時間両方の予算管理、複数仕事のラウンドロビン。
- **Compatibility / Conditional Mixin**: MOD存在判別で特定Mixinだけ適用除外する設計と、描画パスの遅延・再実行。
- **Animation / Phase-State**: 簡易領域の拡張/維持/縮小/破損の独立アニメ状態。

**重要**: TECH-HUBの単一「呪術演出テンプレート」に統合しない。概念と証拠をジャンルごとに区分し、必要な技術だけ採用できる構造が適切。原著作物の移植を促すものではない。

## H. TECH-HUB Completion / 採用見積り

| ファセット | 今回の状態 | 足りない証拠 |
|---|---|---|
| 9.0 JAR識別 / 全ファイル目録 | EVIDENCE_BACKED | 公式CDNとのバイト同一性は未証明 |
| ローダー / 依存 / Mixin定義 | EVIDENCE_BACKED（静的） | 実起動・競合MODでの適用結果 |
| 主要VFX / selected Domain | EVIDENCE_BACKED（選定コード） | 個別全技の実測、全呼出し分岐 |
| AI/移動/スキル全体 | INVENTORIED | 全追跡未実施 |
| worldgen / quests / progression | INVENTORIED | 生成条件・完全動作 |
| 8.1→9.0の実JAR diff | NOT_ANALYZED | 同一由来の8.1 JAR再取得 |
| Source / Issues / PR履歴 | NOT_ANALYZED | 作者による公開ソース/修正コミットの確証 |
| Failure-Repair History | NOT_ANALYZED | 9.0修正前後のソースと再現ケース |
| ゲーム実機 / 性能 / 互換性 | NOT_ANALYZED | Forge/依存のバージョン固定環境と再現実験 |
| canonical knowledge 昇格 | NOT_ANALYZED | review と provenance 完備 |

コミュニティ検索で見つかった「JujutsuCraft」など別MODのクラッシュ報告は、**Jujutsu Verse 9.0の不具合証拠として採用していない**。適用バージョン不明・対象取り違えの情報も取り込まない。

## I. 出典一覧

- 実JARロケータ: SHA `fdf1f8a6c28833c093dc778764b5a6147fc0552ec34e172f918fa4be8dccc065` と同梱JSON中の`evidence[].path`/`sha256`。
- 8.1原研究: TECH-HUB Draft PR #100のJAR-PROVENANCE.md、DOMAIN-CLASH-AND-CUTIN.md、TECHNIQUE-VFX-ATLAS.md。今回の8.1 JAR実体再検証はなし。
- 9.0公式: https://www.curseforge.com/minecraft/mc-mods/jujutsu-verse/files/9609792
- 8.1公式: https://www.curseforge.com/minecraft/mc-mods/jujutsu-verse/files/8097357
- 作者の注意と前提: https://www.curseforge.com/minecraft/mc-mods/jujutsu-verse
- TECH-HUB手順: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/main/departments/minecraft/ANALYSIS-WORKFLOW.md
- TECH-HUB仕様: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/main/departments/minecraft/ANALYSIS-SPEC-v1.md

**結論**: この回で選定範囲の静的技術回収は一区切り。JARだけで「全96技の8.1との差分」「複数領域勝敗の完全な証明」「実機性能」まで解析済みと称さない。