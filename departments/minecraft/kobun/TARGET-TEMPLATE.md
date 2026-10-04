# 古文 target template

新しい太古 MOD を解析するときの最小雛形。

target path:

`departments/minecraft/kobun/mods/<slug>/`

## README.md minimum

```text
# <Target>

Status:
Historical lane: 古文

## ORIGINAL
MOD version:
Minecraft:
Loader:
Java:
Mappings:
Distribution:
Artifact hash:
Source:
Revision:
License:
Release date:

## ERA-CONTEXT
Contemporary docs/forums:
Known behavior:
Known failures:

## DESCENDANT
Later ports/forks/remakes:
Relationship certainty:

## Main technologies
- ...

## Boundaries
- ...
```

## HISTORICAL-MANIFEST.json shape

```json
{
  "format": "kneekura.kobun.historical-manifest.v1",
  "target": "<name>",
  "original": {
    "mod_version": null,
    "minecraft_version": null,
    "loader": null,
    "loader_version": null,
    "java_version": null,
    "mapping_namespace": null,
    "mapping_version": null,
    "artifact": null,
    "artifact_sha256": null,
    "repository": null,
    "revision": null,
    "release_date": null,
    "license": null
  },
  "dependencies": [],
  "runtime": {
    "launch_mechanism": null,
    "side": null,
    "status": "NOT_RUN"
  }
}
```

null は UNKNOWN を意味してよいが、推測値を埋めない。

## Finding format

```text
Finding:
Evidence basis: DIRECT_OBSERVATION | AUTHOR_CLAIM | INFERENCE | UNKNOWN
Temporal role: ORIGINAL_BINARY | ORIGINAL_SOURCE | DECOMPILED_ORIGINAL |
               ERA_CONTEXT | LATER_RETROSPECTIVE | DESCENDANT_SOURCE |
               MODERN_EXTRACTION
Applies to:
Locator:
Counterevidence:
Runtime:
Notes:
```

## MODERN-EXTRACTION.md minimum

```text
Historical mechanism:
Historical assumptions:
Invariant concept:
Modern analogue:
Semantic gaps:
Reconstruction strategy:
License / copy boundary:
```

## Do not do

- 古いクラス名を現代名へ無根拠に書き換えない。
- descendant code を original code として説明しない。
- current wiki の説明を旧版へ自動適用しない。
- 1.20.1で起動しないことを「MODが壊れている」と記録しない。
- 古い JAR を modern `mods/` catalog に同居させない。
