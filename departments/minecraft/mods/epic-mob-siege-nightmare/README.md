# Epic Mob Siege: Nightmare — Siege AI and reversible terrain research

**Date:** 2026-10-11  
**Technology home:** KNEEKURA-TECH-HUB / Minecraft / MOD research  
**Target:** Epic Mob Siege: Nightmare, `NESM-1.20.1-1.0.1.jar`, Minecraft 1.20.1 + Forge  
**Research purpose:** future independent **KNEEKURA Invasion MOD**, a tower-defense/Nexus-style invasion with zombies that breach walls, build towers and bridges, and reversible battlefield damage.

## Evidence state

- **PRODUCT-DESCRIPTION CONFIRMED:** [CurseForge main page](https://www.curseforge.com/minecraft/mc-mods/epic-mob-siege-nightmare) attributes port to greenchiss, original to nuclearlavalamp; labels 1.20.1 / Forge, license All Rights Reserved.
- **RELEASE METADATA CONFIRMED:** [file 7273546](https://www.curseforge.com/minecraft/mc-mods/epic-mob-siege-nightmare/files/7273546): `NESM-1.20.1-1.0.1.jar`, 2025-11-29; changelog says block mining now mines/drops, and StockiesLad PR addressed chunk-loading deadlock. Previous `ESM-1.20.1-1.0.0.jar` file 5003615 was released 2024-01-03 and claimed a worldgen-freeze fix.
- **EXACT BINARY: NOT OBTAINED:** CDN inaccessible in this runtime. SHA-256, JAR class/bytecode inventory, real `getNavigation()` / break/place call sites, effective Forge events and performance **UNKNOWN**. No claim of actual source-to-binary equivalence.
- **HISTORICAL COMPARATIVE SOURCE:** [Doenerstyle/Invasion-Mod `0bccc286114ffae9f9224892ab1fe451fc97ef08`](https://github.com/Doenerstyle/Invasion-Mod/tree/0bccc286114ffae9f9224892ab1fe451fc97ef08), Minecraft 1.7.10 (different mod/product; never equate to Nightmare). `PathAction`, `PathfinderIM`, `TerrainBuilder` demonstrate built-in tactical construction paths.
- **MODERN COMPARATIVE SOURCE (very high relevance):** [XTiK555/ZombieBreakAndBuild `1.20.1` `73a8022609d2d1554d0c1a89406dc97f7ed8aa3d`](https://github.com/XTiK555/ZombieBreakAndBuild/tree/73a8022609d2d1554d0c1a89406dc97f7ed8aa3d), LGPL-3.0, source-inspected AI and *both* restore-broken / delete-placed timers.
- **ALTERNATIVE ROLLBACK SOURCE:** [AMPerez04/MineZero `1.20.1-forge` `84084b48e2dc5141e821177f53f8c29563a03093`](https://github.com/AMPerez04/MineZero/tree/84084b48e2dc5141e821177f53f8c29563a03093), checkpoint world restoration. Compare event coverage, block entity NBT and save model; not assumed battle-ready.
- **LEGACY DOMAIN/STRUCTURE REFERENCES:** JujutsuCraft (Sorcery Fight), JJCV domain addon, WorldEdit snapshots/history and Forge SavedData; verified/reported boundaries retained separately.

## Product-independent target

- Enemy path planning may attack fortifications using **BREAK, PILLAR, BRIDGE, LADDER, REPATH** actions.
- **ALL terrain modifications authored by invasion actors are ephemeral**, with protected-world guarantees: preserved original blockstate and block entity where supported, temporary edits removed, restoration scheduled and persisted across server restart.
- Players' unrelated legitimate edits and other mods' region protections must not be silently overwritten.
- This **must be a module separate from AI**; neither 'auto undo commands' nor whole-world rollback is sufficient.

## Reports

- [SOURCE-SURVEY.md](SOURCE-SURVEY.md) — original release identification and evidence boundaries.
- [ZOMBIE-AI-COMPARISON.md](ZOMBIE-AI-COMPARISON.md) — late-stage AI tactics vs Invasion Mod actionable paths.
- [RESTORATION-SOURCE-AUDIT.md](RESTORATION-SOURCE-AUDIT.md) — code review of real reversible-block mechanisms.
- [REFERENCES-AND-GAPS.md](REFERENCES-AND-GAPS.md) — Jujutsu domains, MineZero, WorldEdit, Forge, Reddit issues.
- [RESEARCH-RECEIPT-2026-10-11.json](RESEARCH-RECEIPT-2026-10-11.json) — snapshots and review status.
- [../../design/kneekura-invasion-reversible-terrain-v1.md](../../design/kneekura-invasion-reversible-terrain-v1.md) — future product design and LAB acceptance, design-only.

No upstream code bodies/assets/JARs are committed. This PR documents research only; it does not implement KNEEKURA Invasion MOD, and no runtime tests were performed.
