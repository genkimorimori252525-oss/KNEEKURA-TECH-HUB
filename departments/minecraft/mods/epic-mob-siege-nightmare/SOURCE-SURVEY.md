# Evidence tiers — Epic Mob Siege: Nightmare and lineage

Date 2026-10-11. Research is specifically for independent Forge 1.20.1 siege engineering.

## A. Port under study: greenchiss Epic Mob Siege: Nightmare

**[CurseForge main](https://www.curseforge.com/minecraft/mc-mods/epic-mob-siege-nightmare)**: greenchiss explicitly credits nuclearlavalamp's Nightmare Epic Siege and earlier Epic Siege Mod inspiration. Port description promises zombie obstacle mining, towering toward sky bases, close-range raids, long-range pursuit, creeper wall demolition, spiders creating webs, TNT-carrying zombies, stronger skeletons/gear, bed usage restriction and larger spawn groups.

**[File 7273546](https://www.curseforge.com/minecraft/mc-mods/epic-mob-siege-nightmare/files/7273546)**: release `NESM-1.20.1-1.0.1.jar`, uploaded 2025-11-29, approximately 60.9 KB per page, file ID 7273546. Changelog: block mining was revised to mine blocks and drop them, plus an external PR fix targeting chunk-loading deadlock. This is meaningful for rollback design: pickups/drops cannot be trivially combined with automatic resurrection without item duplication.

**[File 5003615](https://www.curseforge.com/minecraft/mc-mods/epic-mob-siege-nightmare/files/5003615)**: previous `ESM-1.20.1-1.0.0.jar`, 2024-01-03, changed worldgen freeze by report.

**Proof limit**: no official public exact release source commit or downloadable binary established. Changelog is upstream **REPORT**; does not give implementation, method, class name or confirmed fix. Do not claim `PathNavigation` subclass, `BreakBlockGoal`, mining hardness formula, exact block whitelist, Forge griefing checks, custom pathfinding or version-equivalent original source without JAR analysis.

Source licensing: port labeled **All Rights Reserved**. Original nuclearlavalamp Nightmare ESM [CurseForge](https://www.curseforge.com/minecraft/mc-mods/nightmareesm) lists **MIT**, but original license does not override a specific port release's ARR label. Do not redistribute or copy either by assumption.

## B. Historical Invasion Mod (older tower-defense product, not Nightmare port)

[Doenerstyle/Invasion-Mod source `master` pinned `0bccc286...`](https://github.com/Doenerstyle/Invasion-Mod/tree/0bccc286114ffae9f9224892ab1fe451fc97ef08) contains:
- `src/main/java/invmod/common/entity/PathAction.java` explicit path actions `DIG`, `BRIDGE`, `LADDER_UP`, `LADDER_TOWER_UP_*`, `SCAFFOLD_UP`;
- `PathfinderIM.java` A*-style weighted path expansion and `IPathfindable` action-augmented nodes;
- `TerrainBuilder.java` submits `ModifyBlockEntry` build tasks for planks/ladders/cobblestone, scaffolds, bridges, towers with build-rate cost;
- `EntityAIWaitForEngy.java` follower waits for pig engineer and supports its task;
- Nexus block, spawn waves and custom raider goals in `nexus`/entity tree.

**Interpretation**: explicit construction/digging incorporated as *planned path actions*, not merely a stuck check. Minecraft 1.7.10 code cannot be pasted into 1.20.1 Forge. This is the credible comparative match for an 'old invasion' tower-defense concept, but the exact identity of the user's previously archived Ancient/古文 artifact has **not** been independently established in this turn.

[Modrinth 1.7.10 description](https://modrinth.com/mod/invasion-mod) confirms Nexus defended against escalating waves and role-specific hostile mobs. [An independently maintained newer repo](https://github.com/kevintrini2811/Invasion-Mod) has `1.20.1-neo` branch, SHA `aaa6812b786eeb4c7b48ec5cc7a77d061d6b9e10`. It is *NeoForge*, not a verified Forge 1.20.1 adaptation, and its runtime was not tested.

## C. Comparative modern mob break/build

[XTiK555/ZombieBreakAndBuild tree `73a802...`](https://github.com/XTiK555/ZombieBreakAndBuild/tree/73a8022609d2d1554d0c1a89406dc97f7ed8aa3) has exact `1.20.1` branch. **158 Java files** observed in source tree at this revision (including common/platform/test code), and its `README.md` explicitly lists timed placed-block disappearance and mined-block restoration. Full analysis in [ZOMBIE-AI-COMPARISON.md](ZOMBIE-AI-COMPARISON.md) and [RESTORATION-SOURCE-AUDIT.md](RESTORATION-SOURCE-AUDIT.md).

License: LGPL-3.0. Reading does not imply all code may be combined directly into proprietary/non-LGPL project. Prefer independent reimplementation and attribution; review obligations if actually incorporating LGPL code.

## Next binary/static steps

Acquire the exact approved release JAR via official CurseForge and record full SHA-256, bytes, `META-INF/mods.toml`, class hierarchy, `javap` metadata, Mixin list, capabilities/events, mining/project-placement algorithms, and attack/target routing. Then compare source behavior from historical Nightmare MIT release only when specific versions/lineage are pinned, before GameTest. No guesses are a substitute for actual 1.20.1 binary proof.
