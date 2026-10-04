# 古文 Analysis Specification v1

## 1. Purpose

古文は、歴史的 Minecraft MOD を **その時代の実装物として読む**ための隔離解析 lane。

現代 lane の
`ANCHOR = Minecraft 1.20.1 + Forge`
を ORIGINAL へ強制しない。

通常の [Minecraft Whole-Target Analysis Specification](../ANALYSIS-SPEC-v1.md) の
provenance / full-tree / failure-history / evidence-basis の原則は継承するが、
version-track contract は本仕様を優先する。

## 2. Admission

古文へ入れる目安:

- default candidate: Minecraft <= 1.7.10
- 古い Forge/FML/ModLoader/coremod/LaunchWrapper 世代
- API/mapping/runtime 差が大きく、現代 ANCHOR と同じ catalog 行に置くと誤読しやすい
- historical-only / abandoned / lineage-broken target
- 研究責任者が歴史隔離を明示的に指定した target

version number だけでは決めない。

## 3. Track contract

### ORIGINAL — required

最低1本の歴史的原版 track を固定する。

```text
track_role: ORIGINAL
mod_version:
minecraft_version:
loader:
loader_version:
java_version:
mapping_namespace:
mapping_version:
artifact:
artifact_hash:
repository:
revision:
dependencies:
license:
release_date:
```

source が存在しない場合、配布 JAR + hash + internal inventory + decompile/bytecode locator を
ORIGINAL としてよい。

### ERA-CONTEXT — recommended

同時代資料。

主張ごとに:

- published/retrieved date
- intended MC/MOD version
- author/source type
- archive/original URL
- captured representation/hash when possible

を残す。

### DESCENDANT — optional

port/fork/remake。

ORIGINAL と別 track にし、source equality を仮定しない。

### MODERN-EXTRACTION — derived only

SourceSnapshot ではない。
ORIGINAL evidence から抽出された設計知識。

## 4. Historical Environment Manifest

古文では source pin だけでなく、実行時代を固定する。

最低限:

- Minecraft version
- Forge/FML/ModLoader version
- Java major
- mappings namespace/version
- launch mechanism
- required coremods / libraries
- side assumptions
- config format/location
- save/world assumptions

UNKNOWN は許可する。推測値で埋めない。

## 5. Namespace preservation

古文では名前の時代性を証拠として扱う。

例:

```text
obfuscated name
SRG name
MCP name
source-local wrapper name
modern analogue
```

は別 field。

modern analogue は mapping ではない。

対応根拠なしに:

`EntityCreature(old) == PathfinderMob(modern)`

のような等号を作らない。

## 6. Required surfaces

通常 spec の全体面に加えて古文では以下を重視する。

- historical loader/bootstrap
- class transformers / coremods / ASM
- old event bus / tick hooks
- old packet/channel model
- Entity AI before modern Goal/Brain split
- old pathfinding implementation
- numeric IDs / registry assumptions
- metadata / NBT schema
- world/save compatibility
- renderer pipeline of the era
- MCP/SRG/obfuscation boundary
- Java/runtime assumptions
- archived dependency recovery
- historical failure/repair chain

## 7. Player-facing reconnaissance

当時の攻略情報は重要だが、実装 authority にはしない。

特に古文では current wiki が旧版情報を書き換えている場合がある。

優先順:

1. versioned official archive
2. contemporary forum/release/readme
3. contemporary community guide
4. later retrospective
5. descendant docs

各 evidence に temporal role を付ける。

## 8. Failure / repair history

可能なら当時の:

- forum bug report
- issue
- commit
- changelog
- hotfix release
- source diff

を結ぶ。

古い project では issue tracker が消滅していてもよい。
「見つからない」を history absence と同義にしない。

## 9. Runtime verification

現代 LAB の 1.20.1 runtime gateをそのまま流用して PASS にしない。

古文 runtime は別 experiment identity として:

- historical Java/runtime
- exact loader
- exact target JAR
- minimal dependencies
- disposable world
- isolated directory

を固定する。

runtime unavailable は古文解析の失敗ではない。

## 10. Modern extraction

各技術は次の形で書く。

```text
Historical mechanism:
  ORIGINAL source/binaryで確認した仕組み

Historical assumptions:
  当時の API / tick / registry / renderer / loader 前提

Invariant concept:
  version非依存で残る設計思想

Modern analogue:
  1.20.1 で近い責務を持つ subsystem
  ※同一実装とは限らない

Semantic gaps:
  現代化で失われる/変わる意味

Reconstruction strategy:
  1.20.1 Forgeで再設計するならどうするか

Copyability:
  license / API / risk
```

## 11. Completion

Facet states は通常 lane と同じ:

- NOT_ANALYZED
- INVENTORIED
- MAPPED
- EVIDENCE_BACKED
- NOT_APPLICABLE

古文 target を COMPLETE とするには:

- ORIGINAL pin が十分
- historical environment が記録済み
- required surfaces が evidence-backed または N/A
- failure/history coverage が明示
- modern extractionを行った場合、ORIGINALと分離済み

であること。

DESCENDANT や modern port が存在しないことは completion blocker ではない。

## 12. Storage

target root:

`departments/minecraft/kobun/mods/<slug>/`

推奨成果物:

- `README.md`
- `HISTORICAL-MANIFEST.json`
- `SOURCE-INVENTORY.json`
- `OVERVIEW.md`
- `CODE-MAP.md`
- `AI-BEHAVIOR.md`
- `RENDERING.md`
- `NETWORKING.md`
- `WORLD-SAVE.md`
- `FAILURE-REPAIR-HISTORY.md`
- `MODERN-EXTRACTION.md`
- `LICENSE-PROVENANCE.md`

全部が必須ではない。targetの性質に応じて N/A を明示する。
