# Twilight Forest — Compatibility / Platform Boundary

Status: **FRONTIER and ANCHOR platform boundaries mapped**

This report describes how Twilight Forest reaches beyond its own code: loader contracts, optional Mod integrations, Access Transformers, and runtime bytecode patches.

## 1. ANCHOR platform contract

Source candidate: `a7dd8f13c653e137f977f5ffaa870fcb20fc1625`.

The 1.20.1 metadata declares:

- loader: JavaFML;
- loader range: `[47,)`;
- required Forge dependency: `[47.1.0,)`;
- Minecraft range: `[1.20.1,)`;
- side: BOTH.

The associated build properties identify:

- Minecraft `1.20.1`;
- Forge-line artifact version `47.1.70`;
- Parchment mappings `2023.07.30-1.20.1`;
- Java 17;
- JEI 15.2.0.25;
- Curios 5.2.0-beta.3;
- CTM 1.1.8+4.

This is the adaptation anchor, but the exact CurseForge 4.3.2508 binary ↔ source identity remains a separate unresolved provenance question.

## 2. FRONTIER platform contract

Snapshot: `793c4d4c7b0a2892f702cbb9a8d751fbe7218828`.

`neoforge.mods.toml` declares:

- JavaFML loader;
- loader version `[4,)`;
- required NeoForge `[26.1.2,)`;
- exact Minecraft `[26.1.2]`;
- side: BOTH.

Build properties identify:

- Minecraft `26.1.2`;
- NeoForge `26.1.2.102`;
- Java 25.

### Portability consequence

The FRONTIER is intentionally strict about its Minecraft version. KNEEKURA should therefore mine concepts from it, not treat its compiled artifacts or API calls as 1.20.1-compatible.

## 3. Four extension layers

Twilight Forest uses four different ways to integrate or extend behavior.

### Layer A — normal loader/API hooks

Examples:

- DeferredRegister;
- event buses;
- data/registry APIs;
- networking APIs;
- resource reload listeners.

Prefer this layer whenever an official hook exists.

### Layer B — Access Transformers

Both tracks contain a substantial `accesstransformer.cfg`.

The AT surface opens or unfinalizes vanilla internals used by:

- world generation;
- map data;
- entity AI;
- models/rendering;
- spawners;
- block behavior;
- GUI;
- structure pieces;
- loot;
- commands.

The FRONTIER AT list is substantially broader and uses named modern symbols rather than the 1.20.1 mapped names/descriptors.

### Layer C — dedicated ASM module

FRONTIER adds a separate ASM source/module with explicit processors. See `ASM-PATCHES.md`.

This handles semantic gaps not solved cleanly by normal APIs/ATs, including:

- multipart synchronization;
- custom terrain Beardifier injection;
- chunk-status processing;
- movement/physics hooks;
- map behavior;
- rendering hooks.

### Layer D — Mod-specific compatibility adapters

FRONTIER contains **50 active Java files** under `twilightforest/compat/`.

Major active families include:

- Curios;
- Jade;
- JEI;
- shared recipe-viewer abstraction/helpers.

An additional **52 Java files** are retained under `src/main/disabled/compat/`, including:

- EMI;
- REI;
- The One Probe;
- Cosmetic Armor compatibility.

### Reusable lesson

Compatibility is treated as a **separate boundary**, not scattered conditionals through every gameplay class.

## 4. Curios integration

`TwilightForestMod` explicitly checks whether `curios` is loaded before installing Curios listeners/capabilities/rendering hooks.

This is a clean optional-dependency pattern:

```text
loader presence check
     ↓
register integration-specific capabilities/listeners/render layers
     ↓
core Mod remains loadable without optional Mod
```

## 5. Recipe-viewer compatibility

FRONTIER keeps common recipe-viewer concepts outside any one viewer and then provides concrete JEI compatibility.

The disabled EMI/REI trees show that the project has previously maintained or prepared multiple presentation adapters for the same gameplay recipes.

### Reusable pattern

Separate:

- canonical recipe/gameplay representation;
- viewer-neutral helper logic;
- viewer-specific category/widgets/plugin glue.

This prevents JEI/REI/EMI UI APIs from becoming the gameplay source of truth.

## 6. Jade / information overlays

Jade integration is isolated under `compat/jade/` with dedicated providers.

The pattern again favors small provider adapters over direct Jade calls inside blocks/entities.

## 7. Access Transformer evolution

ANCHOR ATs expose many SRG/mapped members such as fields/method descriptors required by Forge 1.20.1.

FRONTIER ATs target modern named symbols and a much larger surface.

Therefore AT portability is not textual.

For each backport:

1. identify the semantic need;
2. locate the equivalent 1.20.1 class/member;
3. verify its access/finality;
4. add the smallest necessary ANCHOR AT;
5. add a regression check.

## 8. ASM portability

Runtime transformers are even less portable than ATs.

The design can be reused:

```text
small named transformer
  → exact vanilla semantic boundary
  → call mostly-normal Java hook
```

But class names, method descriptors, local layouts and bytecode insertion sites must be re-derived for 1.20.1.

## 9. Compatibility inventory interpretation

The presence of disabled compatibility source is valuable evidence.

It shows:

- the project intentionally preserves integration knowledge even when a dependency is unavailable/currently unsupported;
- compatibility support is lifecycle-managed separately from core gameplay;
- old adapters can be used as migration evidence without pretending they are active.

KNEEKURA's Minecraft Technology Department should follow the same distinction:

- ACTIVE;
- DISABLED / DORMANT;
- HISTORICAL;
- PLANNED;

rather than treating “source exists” as “supported”.

## 10. High-value backportable principles

These are largely version-independent:

- thin optional-dependency gates;
- dedicated compatibility packages;
- viewer-neutral canonical gameplay representation;
- minimal AT surface;
- isolated ASM patches with semantic names;
- disabled/historical adapters kept as evidence;
- exact loader/version contract in metadata.

## 11. Remaining compatibility work

For complete ANCHOR/FRONTIER equivalence:

1. exact integration feature matrix per JEI/Curios/Jade/REI/EMI/TOP;
2. AT semantic diff, not only file diff;
3. ASM equivalent/absence matrix for 1.20.1;
4. runtime tests with common Mod combinations.
