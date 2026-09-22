# Twilight Forest — Block / Item Render Asset Graph Specification

Status: **extractor implemented; full-checkout execution pending**

## Why this exists

The entity rendering map is already complete for all registered EntityTypes. The remaining visual dependency surface is data-driven:

```text
blockstate / item definition
        ↓
model
        ↓
parent model
        ↓
texture / atlas resource
```

The pinned FRONTIER tree contains:

- 528 blockstate JSON files
- 1,773 model JSON files
- 663 modern item-definition JSON files
- 1 atlas JSON file in the Twilight Forest namespace
- 1,159 texture PNG files

A model-only scan would therefore miss the modern item-definition layer.

## Tool

`tools/build_render_asset_graph.py`

The tool requires a local full checkout and uses only the Python standard library.

Example:

```powershell
python departments/minecraft/mods/twilight-forest/tools/build_render_asset_graph.py \
  C:\src\twilightforest \
  --source-commit 793c4d4c7b0a2892f702cbb9a8d751fbe7218828 \
  --output departments/minecraft/mods/twilight-forest/BLOCK-ITEM-RENDER-GRAPH.json \
  --summary-output departments/minecraft/mods/twilight-forest/BLOCK-ITEM-RENDER-GRAPH.md
```

## Extraction contract

The graph records:

- every relevant JSON/PNG source path
- SHA-256 and file size
- blockstate/item `model` references
- model `parent` references
- texture references
- atlas/resource references
- resolved Twilight Forest local target path
- unresolved local references
- duplicate logical assets across generated/main resource roots
- JSON parse failures
- model-parent cycles

Raw third-party textures/models are not copied into TECH HUB.

## Completion boundary

The global block/item render graph is not marked complete until this extractor is executed against the pinned FRONTIER checkout and its compact generated graph is reviewed.

The same extractor can then run against the ANCHOR checkout to produce a path/reference-level portability diff.
