# Twilight Forest — Compatibility Feature Matrix v1

Tracks:

- ANCHOR: `a7dd8f13…` — Minecraft 1.20.1 / Forge
- FRONTIER: `793c4d4c…` — Minecraft 26.1.2 / NeoForge

## Inventory

- ANCHOR compatibility-related Java: **29**
- FRONTIER compatibility-related Java: **106**
- FRONTIER active: Curios **8**, Jade **6**, JEI **30**, plus viewer-neutral/common helpers
- FRONTIER disabled: EMI **21**, REI **26**, The One Probe **4**, Cosmetic Armor **1**

## Lifecycle matrix

| Integration | ANCHOR | FRONTIER | Main evolution |
|---|---|---|---|
| Curios | ACTIVE | ACTIVE | capability/render adapter remains stable; generic visibility/consume helpers added |
| Jade | ACTIVE | ACTIVE | Quest Ram provider expands to Drying Rack and bookshelf providers |
| JEI | ACTIVE | ACTIVE | 12 → 30 files; adds Drying, Ominous Fire, Traveller Gear, Casket subtype/extensions |
| The One Probe | ACTIVE | DISABLED | adapter retained as dormant migration knowledge |
| EMI | absent in active compat tree | DISABLED | 21-file full adapter retained |
| REI | absent in active compat tree | DISABLED | 26-file client/server adapter retained |
| Cosmetic Armor | absent | DISABLED | historical adapter retained |

## Most important architectural change

FRONTIER adds viewer-neutral helpers:

- `RecipeViewerConstants`
- `RecipeViewerRecipes`
- `RecipeViewerSync`

This creates a cleaner split:

```text
gameplay recipe / canonical data
          ↓
viewer-neutral compatibility representation
          ↓
JEI / EMI / REI adapter
```

That is more reusable than any individual JEI API call.

## JEI growth

ANCHOR JEI covers:

- Crumble Horn
- Transformation Powder
- Uncrafting
- catalysts / transfer / GUI areas
- custom entity/item rendering

FRONTIER additionally covers:

- Drying
- Ominous Fire
- item subtype handling
- vanilla category extensions
- Casket repair/subtype
- Traveller Gear modifier and merge recipes

The technology to carry back to 1.20.1 is **not** the modern JEI API syntax. It is the canonical-recipe → viewer-neutral layer → adapter split.

## Curios

Curios stays active across both generations with eight Java files in each track. The exact capability API evolves, but the integration boundary remains recognizable:

```text
loader presence
  → register capability/equip policy
  → register optional render layers
  → query equipped state through adapter
```

This is a strong 1.20.1-compatible design pattern.

## Disabled code is evidence, not support

FRONTIER intentionally keeps EMI, REI and TOP code under `src/main/disabled/compat`.

KNEEKURA should preserve the same distinction:

- ACTIVE
- DISABLED / DORMANT
- HISTORICAL
- PLANNED

A source file existing does not mean the integration is currently supported.

Machine-readable detail: `COMPATIBILITY-MATRIX.json`.
