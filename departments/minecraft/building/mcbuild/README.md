# mcbuild — 建築ジャンルへの導入

**状態：OPTIONAL LOCAL BRIDGE / 実機未検証（2026-11-13）**

[upstream: harrynull/mcbuild](https://github.com/harrynull/mcbuild) の Python CLI を、KNEEKURA TECH HUB の建築ジャンルに**必要なときだけ**接続する。upstream 本体・Minecraft由来の画像やブロック状態データはリポにコピーしない。参照するソースは [manifest.json](manifest.json) の exact commit に固定する。

## 何を利用できるか

- 自然言語 → sandboxed Blueprint DSL → 疎な voxel grid → 複数視点レンダリング → 画像を使ったAIによる見直し → Sponge/WorldEdit `.schem` 出力。
- `str_replace` / `edit_region` / `query` 等の部分修正・点検操作。upstream に実装されている機能で、Tech Hub 固有の動作検証済みとはまだ言わない。
- `--fake-llm` を使うAPI不要のオフライン・デモ。意図しない課金なしに一連の処理の流れを確認できる。
- LLM で本番生成するには別途 OpenRouter API キーと従量課金が必要。

## 実際に導入したもの

`runner.py` は標準ライブラリのみの薄い起動アダプタ。

- `status`: 読み取り専用。git/uv と source checkout の状態を出すだけ。
- `prepare`: **明示実行時のみ** pinned commit の Git ソースを `departments/minecraft/local-artifacts/mcbuild/upstream/` に取得。
- `install`: **明示実行時のみ** upstream の `uv.lock` に基づいて依存パッケージを導入。
- `demo`: FakeLLM を用いた非API実験（既にパッケージを導入済みであることが前提）。
- `build`: `--online` と `OPENROUTER_API_KEY` が揃った時だけ OpenRouter に問い合わせ、`.schem` を出力。
- 出力先：`departments/minecraft/local-artifacts/mcbuild/runs/`（Git管理対象外）。

既存の Core、DB、runner、Minecraft MOD-AI、LAB の設定は変更しない。

## 手順（Tech Hub のルートから）

Python 3.11+、Git、[uv](https://docs.astral.sh/uv/) が必要。Windows PowerShell、Linux/macOS いずれもコマンドは同じ。

```sh
python departments/minecraft/building/mcbuild/runner.py status
python departments/minecraft/building/mcbuild/runner.py prepare
python departments/minecraft/building/mcbuild/runner.py install
python departments/minecraft/building/mcbuild/runner.py demo --prompt "a tiny stone hut"
```

デモの終了後、上記 `runs/` の下に `prompt.txt`、反復ごとの設計・画像・統計、完成した場合 `final.schem` が出る。

実際のモデルで設計するとき（従量課金あり）、PowerShell では環境変数を設定してから実行する。APIキーをソースやissueに貼らないこと。

```powershell
$env:OPENROUTER_API_KEY = "YOUR_KEY_FROM_OPENROUTER"
python departments/minecraft/building/mcbuild/runner.py build --prompt "a small Japanese shrine" --online --cost-ceiling 2
```

`--cost-ceiling` はupstream実装による**ベストエフォートのAPI使用額停止条件**で、請求金額の厳密な上限保証ではない。画像を含むモデルへ依頼内容が送られるため、ワールドや個人の秘密をプロンプトに含めない。

## Minecraftへの反映とバージョン境界

| トラック | 内容 | 現状 |
|---|---|---|
| **FRONTIER** | upstream の NeoForge **1.21.1** MOD + WebSocket、`/build` | upstream記載のみ。Tech Hub上で構築・検証していない。**認証なしでローカル/信頼済みワールド専用**。 |
| **ANCHOR** | Minecraft **1.20.1 + Forge** | `.schem` を作ってWorldEdit等で別途インポートする構成。**実ゲームでの取り込み・ブロックステート互換性は未検証**。 |

本アダプタは**Minecraftワールドを書き換えない**。実際にインポートする際は、専用ワールドのバックアップ・配置座標・既存建築との干渉・ドア/階段/水等のブロック状態を確認する。upstreamのライブMODをForge 1.20.1へ直接コピーしない。

## 重要な境界・限界

- upstream Python DSL は実装上 sandbox を備えるが、無害な外部プログラムであると監査済みではない。コードと依存物は固定commitから必要時だけ実行し、初回は隔離された環境を推奨。
- upstreamのレンダラーはMinecraft本体の完全なピクセル再現ではない。状態付きブロックの一部は簡易的な描画となる。
- 長期の建築記憶・過去作品の自動再利用はupstreamに未搭載。視覚的な自己批評も人間の審美判断を置き換えない。
- ライブ生成は upstream でも一度に一つ、認証なし。パブリックサーバーへ無造作に接続しない。
- upstreamコードはMIT（Copyright (c) 2026 Harry）。**同梱のMinecraftブロックテクスチャ/ブロックステートは別扱い**で、[asset notice](https://github.com/harrynull/mcbuild/blob/main/src/mcbuild/assets/NOTICE.md) とMinecraft利用ガイドラインを確認。アセットやupstream全体をこのGitリポへ再頒布しない。
- 検証状態はステップごとに分ける：`SOURCE_PINNED`、`LOCAL_SETUP`、`OFFLINE_DEMO_PASS`、`SCHEM_EXPORTED`、`FORGE_1201_IMPORTED`、`WORLD_VISUALLY_VERIFIED`。後半を未実施のまま合格と記録しない。

## 技術参照

[TECHNIQUE-MAP.md](TECHNIQUE-MAP.md) に内部モジュール、再利用候補、リスクおよび段階的な検証項目を記録。自動テスト：`python -m pytest tests/test_mcbuild_bridge.py`（外部アクセスしないアダプタ単体テスト）。

## 最終判断

この変更は**カテゴリ登録、ピン留め、実行アダプタ、単体テストの導入**。mcbuildの実体をすでにダウンロードした、APIに接続した、Forge内で動いた、とは主張しない。採用は技術候補の段階で、人間レビューなしにKnowledge Coreのcanonical claimを昇格させない。
