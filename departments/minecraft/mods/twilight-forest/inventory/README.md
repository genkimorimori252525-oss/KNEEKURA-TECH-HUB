# Twilight Forest — Full Tree Inventory

This directory stores exhaustive path-level inventories derived from immutable upstream Git trees.

## ANCHOR release-source candidate

- Repository: `TeamTwilight/twilightforest`
- Commit: `a7dd8f13c653e137f977f5ffaa870fcb20fc1625`
- Role: Minecraft 1.20.1 / Forge release-source candidate for CurseForge 4.3.2508
- Evidence: CurseForge file 5468648 is dated 2024-06-24. Public commit `a7dd8f13c653e137f977f5ffaa870fcb20fc1625` is also dated 2024-06-24, remains on the 1.20.1 line, and its Discord-URL change matches a 4.3.2508 release-note item. This makes it the strongest public source candidate identified so far, but the exact distributed-JAR ↔ source identity is still unproven.
- Status: source pinned; exact binary-to-source identity remains to be proven by JAR hash/build metadata.

Counts:
```json
{
  "files": 7467,
  "java": 1265,
  "json": 4986,
  "png": 906,
  "ogg": 137,
  "nbt": 65,
  "mcmeta": 41,
  "textures": 945,
  "worldgen": 264,
  "structures": 321,
  "entity_paths": 403,
  "client_paths": 270
}
```

## FRONTIER

- Repository: `TeamTwilight/twilightforest`
- Commit: `793c4d4c7b0a2892f702cbb9a8d751fbe7218828`
- Branch: `latest`
- Minecraft: 26.1.2
- Loader: NeoForge 26.1.2.102
- Mod line: 4.9
- Status: immutable source snapshot pinned.

Counts:
```json
{
  "files": 9592,
  "java": 1735,
  "json": 6047,
  "png": 1160,
  "ogg": 229,
  "nbt": 273,
  "mcmeta": 82,
  "textures": 1241,
  "worldgen": 342,
  "structures": 619,
  "entity_paths": 608,
  "client_paths": 336
}
```

## Files

- `anchor-a7dd8f13-files.json` — every path/blob SHA/size in the ANCHOR candidate tree.
- `frontier-793c4d4c-files.json` — every path/blob SHA/size in the FRONTIER tree.

These are inventories, not redistributed third-party content.
