# mcbuild 技術マップと検証境界

対象：[`harrynull/mcbuild`](https://github.com/harrynull/mcbuild) / [manifest.json](manifest.json) の固定 SHA。以下はソース構成とREADMEに基づく**静的確認**であり、Tech Hub環境で実行した測定値ではない。

| 上流パス | 機能 | Tech Hubでの扱い |
|---|---|---|
| `src/mcbuild/agent/` | LLMツール選択、反復、修正・検査 | 設計・実行分離の参考 |
| `src/mcbuild/dsl/` | Blueprint DSL、実行制限、幾何プリミティブ | 安全境界の個別監査候補 |
| `src/mcbuild/voxel.py` | sparse voxel grid | ブロック差分・領域検証候補 |
| `src/mcbuild/render/` | isometric・自由カメラ・切断面 | 目視検証、Minecraft実画面との差分を検証 |
| `src/mcbuild/export/` | Sponge Schematic export | Forge 1.20.1での互換性を別途実測 |
| `src/mcbuild/rundir.py` | 反復ごとの実験ファイル保存 | 実験の出所と生成物ハッシュを記録 |
| `src/mcbuild/server/` / `mod/` | WebSocket + NeoForge 1.21.1 のライブ配置 | **未統合**。認証、権限、ロールバック設計なしにForgeへ移植しない |
| `src/mcbuild/assets/` | ブロック外観素材 | Mojang/Microsoft由来の第三者素材。転載しない |

## 完成データの対象版別出力（1.20.1を含む）

- **重要な結論**：Forge/NeoForgeという実行MODのローダー差と、ブロックID/状態/相対座標で表される完成建築の移植可能性は別問題。mcbuild本体をForge 1.20.1に移植しなくても、その建築成果物は1.20.1向けの形へ変換可能。
- 確認した固定上流 `src/mcbuild/export/schem.py` は `Version=3` / `DataVersion=3953`（**Minecraft 1.21**）を生成する。NeoForge実行MODの対象Minecraft 1.21.1は **3955** であり、上流の値と説明は一致していない。これは1.20.1向けWorldEdit 7.2.15がそのまま受け入れることを意味しない。
- 将来のターゲット別エクスポータは、Minecraft 1.20.1ではSponge **v2** / **DataVersion 3465**、他バージョンでは各対象のリーダー仕様を明示して出力する。
- **ブロックと状態の変換を独立に行う**。1.20.1にない素材・性質は一律にairへ置き換えず、代替候補を報告する。自動置換はユーザー承認されたマッピングだけを用い、変換前後の座標・数・変更点を保存する。
- **メタデータ改竄を変換と呼ばない**。Sponge v3とv2はNBTレイアウト自体が違うので、Version/DataVersionを書き換えるだけではダメ。
- このPRでは変換コード・ターゲットブロック定義・実機試験はまだ導入していない。初期のexport結果はv3であることを明記する。

詳細：[軽量監査](AUDIT-2026-11-14.md)、[実装計画](PLAN-2026-11-14-CROSS-VERSION.md)。

## 段階的な受け入れ

1. **コード固定**：remote URL / commit SHA / tracked worktree がmanifestと一致する（runnerが開始前にチェック）。この手順だけではコードの安全性を証明しない。
2. **オフライン動作**：デモが、入力、失敗からの修復、レンダリング、完成出力を再現すること。スクリーンショットがあるだけで品質合格にしない。
3. **設計図検査**：`.schem` をパースし、座標・寸法・置換空気・ブロック状態・外接サイズを定量化する。現段階では未実装。
4. **Forge 1.20.1実機**：バックアップ済み専用ワールドに手動取り込みし、ドア/階段/水/階層/通路などの見え方と機能を比較する。未実施。
5. **建築品質**：要件充足と建築的魅力を別々に評価。独創性を画一的な自動スコアで強制しない。再修正が本当に必要な場合だけ反復。
6. **将来のライブ反映**：ローカル限定、認証、実行権限、領域制限、変更差分、取り消し、ワールド保護を別途設計。upstreamの認証なし仕様をそのまま公開サーバーへ持ち込まない。

## 講じない操作

通常のCore検索・MOD開発・LAB起動で、Git clone、uv sync、LLM API呼出し、Minecraft実機起動、ワールド変更を勝手に実行しない。水槽観測は必要な実機証拠が不足する場合のみ、別の許可された手順で使う。

## 出典と不確実性

- [README](https://github.com/harrynull/mcbuild/blob/34ce86372d4c23f4d83d4e24fc256cb399d6c3e3/README.md)
- [upstream license](https://github.com/harrynull/mcbuild/blob/34ce86372d4c23f4d83d4e24fc256cb399d6c3e3/LICENSE)
- [third-party asset notice](https://github.com/harrynull/mcbuild/blob/34ce86372d4c23f4d83d4e24fc256cb399d6c3e3/src/mcbuild/assets/NOTICE.md)

結果や性能・安全性の実測をしていない段階では、他リポとの比較・レンダリング品質・API費用効率を確定評価しない。
