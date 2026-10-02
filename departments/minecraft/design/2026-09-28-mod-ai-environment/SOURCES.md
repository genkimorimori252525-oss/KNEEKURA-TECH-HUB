# 根拠と参考実装 — 2026-09-28 JST確認

これは参照台帳。外部文書での機能説明、実際のソース読取、Hubでの動作検証を区別する。全リポ監査や全機能試験を済ませたという記録ではない。S番号は参照IDであって品質順位ではない。

## 既存リポとの接続根拠

### S01 — 既存coreと拡張境界（ファイル読取）

https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/3741e90a5762371ce7c5e372d33cf4abd7fba620/docs/architecture/CORE-FEATURE-FREEZE-v1.md

既存の由来・承認・context guidance・機能凍結方針を確認。新しいMinecraft adapterを理由にcanonical coreを作り直さない。全symbolをKnowledge Entityへ自動登録する設計は採らない。

### S02 — 既存Minecraft技術部・黄昏の森（ファイル・PR読取）

https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/pull/71

https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/3741e90a5762371ce7c5e372d33cf4abd7fba620/departments/minecraft/README.md

https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/3741e90a5762371ce7c5e372d33cf4abd7fba620/departments/minecraft/mods/twilight-forest/README.md

PR #71はopen/unmerged、headは上記commit。ANCHOR/FRONTIERと完全取得・保存方針を維持する。黄昏READMEの描画グラフ完了記載は再利用するが、今回runtimeやコンパイル済みclassの同一性を再検証したわけではない。

### S03 — 既存Connector登録（ファイル読取）

https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/3741e90a5762371ce7c5e372d33cf4abd7fba620/departments/minecraft/mods/sinytra-connector/README.md

QUEUED、黄昏の森の次、ANCHOR/FRONTIER別解析、依存境界と期待成果を確認。既存記録はSource Snapshot未固定と明記している。今回の設計に参照commitを記録することと、全件解析やcanonical snapshot ingestを完了することは別。

### S04 — 二層データ・由来（既存設計の確認）

S01およびS02を使用する。解析索引は派生データ、知識主張は既存coreへ接続するという採用判断。新しい実装が実際にcoreと往復可能かはACCEPTANCE A12で確認する。既存schemaへ勝手に新recordを投入していない。

## 対象版と外部技術の根拠

### S05 — Forge開発環境（公式docs読取）

https://docs.minecraftforge.net/en/1.20.x/gettingstarted/

1.20系の開発基準として確認。1.20.xという文書系列だけで各APIが1.20.1の特定Forge buildと完全一致すると断定せず、実classpathで解決する。

### S06 — Connector ANCHOR（固定commitのファイル読取）

https://github.com/Sinytra/Connector

https://github.com/Sinytra/Connector/tree/1.20.1

https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/gradle.properties

GitHub connectorで上記ファイルを再取得した。blob=e2e8714f0448d8ee2bea6950cbfe6636b75f49b0。versionMc=1.20.1、versionForge=47.4.6、versionConnector=1.0.0-beta.50、mixinextrasVersion=0.3.2を確認。これはbuild設定であり、配布releaseの同一性や動作保証ではない。Web取得のcache missはGitHub connectorの成功で補完した。ブランチ先端の継続監視はしていない。

### S07 — physical/logical side（公式docs読取）

https://docs.minecraftforge.net/en/1.20.x/concepts/sides/

物理client/serverと論理sideを区別し、client-only型がserver上に存在しないケースを設計へ反映。singleplayer成功だけでdedicated serverを保証しない。

### S08 — MCDxAI/minecraft-dev-mcp（README機能説明の確認）

https://github.com/MCDxAI/minecraft-dev-mcp

decompile/remap、MOD JAR解析、validator、全文検索、CLI/MCPの構成を参考にする。READMEの1.20.1 tested表記を確認したが、当HubのForge classpath・全変換stageでの適合試験は未実施。外部validatorの結果を互換性保証へ昇格させない。

### S09 — MixinMCP（README機能・前提の確認）

https://github.com/muon-rw/MixinMCP

全classpath、参照/階層、bytecode閲覧、Gradleによる依存source準備を参考にする。READMEはIntelliJ IDEA 2026.2+とIDE/Gradle pluginの前提を記載。これを採用してもHubの標準headless経路をIDE必須にしない。機能・性能は今回実行検証していない。

### S10 — mcdev-mcp / DebugBridge（README機能説明の確認）

https://github.com/use-ai-for-mc/mcdev-mcp

https://github.com/use-ai-for-mc/debugbridge

静的解析と実行中Minecraft観測の分離、session制御、snapshot/ログ/画像を参考にする。外部DebugBridgeが当HubのForge 1.20.1で動作するという一次証拠は今回取得していない。コードの移植量・適合性は未評価。任意Groovy実行やport自動走査の方式を無条件でコピーしない。

### S11 — Parchment（公式FAQ読取）

https://parchmentmc.org/faq

名前・説明を補う注釈情報として扱う。採用するmapping版と入力hashは実装時に固定する。別のgetting-startedページはtimeoutで取得できなかったため、そのページの内容は根拠に使わない。

### S12 — Mixin / MixinExtras（WrapOperation公式wiki読取）

https://github.com/LlamaLad7/MixinExtras/wiki/WrapOperation

複数のoperation wrapperが連鎖できるという説明は、「同一methodへ二つ介入する=即競合」という単純判定への反例。これは全injector・全版・全意味的組合せの安全証明ではない。利用する機能はprofileの実際のMixinExtras版で確認する。

補助原典候補: https://github.com/SpongePowered/Mixin/wiki

### S13 — Forge GameTest（1.20.x公式docs読取）

https://docs.minecraftforge.net/en/1.20.x/misc/gametest/

構造templateを使うゲーム内検証、required/optional、namespace設定、runGameTestServerの終了コードがrequired失敗件数に基づく説明を確認。終了コードだけを合格証明にしない設計の根拠。今回はMinecraftを起動していない。

### S14 — 実装例・コミュニティ（状態を分離）

確認した参考サイト: https://mcjty.eu/docs/intro

Forge 1.20とNeoForge 1.20.4の教材リンクが別にあることを確認。教材は対応コード・版を固定してExample候補にする。掲載されているだけで技術的に優位・正しいと扱わない。

取り込み候補（この作業で全内容を再監査していない）:
- https://forums.minecraftforge.net/ — 症状・修正事例。
- https://wiki.fabricmc.net/documentation:start — Connector側の用語・仕組みを調べる原典候補。
- https://mappings.dev/1.20.1/ — 名前・版の閲覧補助。binary identityの代替にはしない。
- https://github.com/Vineflower/vineflower — decompiler部品候補。
- https://github.com/FabricMC/tiny-remapper — remapper部品候補。

過去の会話に出たReddit URLを再取得したが本文取得に失敗した:
- https://www.reddit.com/r/feedthebeast/comments/1fgkd94/
- https://www.reddit.com/r/feedthebeast/comments/184hw4s/

したがって「多数の作者が支持」「最強の学習法」といった過去の一般化は、この確定設計の証拠に使用しない。Redditから原典候補を発見するという役割だけを採用する。

## 未実行・未変更

外部MCPのinstall/build/統合試験、Connector全件解析、Minecraft実行、DB ingest、canonical昇格は今回未実施。Durable Workflowのlist_workflowsは429、再試行は404で利用できず、workflowの再作成・更新は行っていない。作業成果と再開情報はこのdocs-only PRへ保存する。
