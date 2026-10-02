# KNEEKURA-LAB — Tech Hub integrated laboratory

> Current cross-layer status and resume order: [`../CURRENT-HANDOFF-2026-10-02.md`](../CURRENT-HANDOFF-2026-10-02.md). Historical LAB documents below retain their original milestone wording.\n\nこのディレクトリが、2026-10-02以降のKNEEKURA Minecraft実験・観測層の正本です。旧 `KNEEKURA-LAB` リポジトリのソースは `f2d6165b16587672ac56f83c001c65bc2fa6d06a` から同一Tech Hubリポジトリへ移行されました。旧リポジトリは移行元・履歴参照として残し、新規実装は原則ここで行います。

霊夢 AI の挙動を記録・再生・解析し、実Minecraftを権威ある検証環境として扱います。Minecraft/TouhouLittleMaid本体の製品コードとは責任を分離したまま、Tech Hubの知識・TaskContext・Evidence・実験契約と同一commitで管理します。

> **Architecture note (2026-09-18):** live verification is moving to a real-Minecraft-first model.
> Minecraft is the authoritative visual/test environment; the Web side becomes a remote-control,
> evidence-collection, and analysis hub. Existing Viewer/render work remains as research/regression
> infrastructure where useful, but live Web rendering is no longer the primary target.
> See [docs/KNEEKURA_LAB_HISTORY.md](docs/KNEEKURA_LAB_HISTORY.md).
>
> Current implementation plan: [docs/KNEEKURA_AUTONOMOUS_DEBUG_WORKSPACE_V1_PLAN.md](docs/KNEEKURA_AUTONOMOUS_DEBUG_WORKSPACE_V1_PLAN.md).

## Quick start

```powershell
npm test
node simlab/serve.mjs
```

Viewer は `http://localhost:8777` を開きます。実機または Forge 側の bridge が
`run/sim/traces` に JSONL トレースを書き出すと、Viewer と解析器がそれを読み込みます。

```powershell
node simlab/analyze.mjs run/sim/traces --json
node simlab/schema-check.mjs simlab/fixtures --coverage
```

## Repository boundary

- `simlab/`: Node.js の解析、スキーマ検査、Viewer、fixture、シナリオ
- `bridge/tlm-forge/`: Minecraft Forge/TouhouLittleMaid に接続する観測アダプタ
- `simlab/schema.json`: bridge と Viewer の間で共有する JSONL 契約
- `simlab/NETWORK_COMPANION.md`: client/server process をまたぐ Forge network runtime evidence 契約
- `simlab/YSM_GRAPH_SCAN.md`: containerを含むYSM runtime object graph探索とcomplete/negative契約
- `simlab/YSM_MOLANG_STATE_PROBE.md`: M5以降のYSM scalar state探索とM6 evidence境界

`bridge/tlm-forge` は TLM のクラスパス上で動くため、このリポジトリ単体の
Node.js ツールとは別にビルドします。TLM 側の AI や弾幕実装をこのリポジトリへ
取り込むことはせず、bridge は観測とシナリオ実行の接続だけを担当します。

## Data policy

実機の `.minecraft`、YSM モデル、生成された `run/` データはコミットしません。
必要な fixture は小さく再現可能なものだけ `simlab/fixtures/` に置きます。

## Runtime network evidence

Forge 1.20.1 の `SimpleChannel` send/receive は arena trace と別の `.net.jsonl` companion に記録する。main trace の `meta.run` と companion の `net_meta.run` を照合し、別runを自動吸着させない。詳細は `simlab/NETWORK_COMPANION.md`。

Runtime network companion は packet class/direction に加え、public scalar field の安全な浅い `payload` snapshot も保持できます。private/nested object は走査せず、ReimuSpellCardMolangPacket の `molangExpression` のような wire意味を証拠として残します。 同じcompanionの `net_semantic` 行には、handler到達やYSM Molang command dispatchなどnetwork後段のmilestoneをglobal `seq` 順で追加できます。
