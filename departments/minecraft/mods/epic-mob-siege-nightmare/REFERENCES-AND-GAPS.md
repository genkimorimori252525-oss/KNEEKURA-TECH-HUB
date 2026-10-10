# Supporting mods, communities and verification gaps

Research date 2026-10-11. Evidence levels: **PINNED_SOURCE**, **UPSTREAM-DESCRIPTION**, **COMMUNITY-REPORT**, **UNVERIFIED**.

## Reference map

| Source | Specific fact / utility | Level | Relationship to invasion rollback |
|---|---|---|---|
| [Epic Mob Siege: Nightmare](https://www.curseforge.com/minecraft/mc-mods/epic-mob-siege-nightmare/files/7273546) | 1.20.1 port; new release reports mining/dropping and chunk-loading-deadlock fix | UPSTREAM-DESCRIPTION | TARGET, binary still missing |
| [Nightmare Epic Siege](https://www.curseforge.com/minecraft/mc-mods/nightmareesm) | original product credited by port; CurseForge MIT label | UPSTREAM-DESCRIPTION | LINEAGE; not 1.20.1 port proof |
| [Invasion Mod 1.7.10](https://github.com/Doenerstyle/Invasion-Mod) | Nexus-wave defense, custom path actions, pig engineer/scaffold/bridge source | PINNED_SOURCE | tower-defense action-planner inspiration |
| [Zombies Break & Build 1.20.1](https://github.com/XTiK555/ZombieBreakAndBuild/tree/1.20.1) | agent break/bridge/pillar behavior and timed block restoration using SavedData | PINNED_SOURCE | **best direct source for both user-requested mechanics** |
| [MineZero 1.20.1 Forge](https://github.com/AMPerez04/MineZero/tree/1.20.1-forge) | checkpoint preimages, explosion changes, block entity NBT, chunk-indexed restore | PINNED_SOURCE | wider restoration comparison |
| [WorldEdit history docs](https://worldedit.enginehub.org/en/latest/usage/general/history/) | `//undo` stores direct operations; explicitly does not undo many indirect fluids/attached blocks | OFFICIAL DOCS | reason not to rely on undo alone |
| [WorldEdit snapshots docs](https://github.com/EngineHub/WorldEditDocs/blob/master/source/usage/snapshots.rst) | bounded region restore from world backups | OFFICIAL DOCS | option for explicit administrative recovery |
| [Forge 1.20.1 ForgeEventFactory API](https://lexxie.dev/forge/1.20.1/net/minecraftforge/event/ForgeEventFactory.html) | block placement/block multi-place hooks | API DOCS | protection integration tests |
| [Forge SavedData docs](https://docs.minecraftforge.net/en/1.17.x/datastorage/saveddata/) | data lives per-level; needs dirty mark to save | OLDER OFFICIAL DOCS | conceptual, inspect 1.20.1 exact API |
| [@Avatar Block Restoration](https://www.curseforge.com/minecraft/mc-mods/avata-blockrestoration) | 1.20.1 Forge radius-20 banner protection, restore during daytime | UPSTREAM-DESCRIPTION | localized restoration UX alternative |
| [BlockEcho](https://www.curseforge.com/minecraft/mc-mods/blockecho) | preview-first Forge 1.20.1 undo of builds/explosions | UPSTREAM-DESCRIPTION | admin preview/conflict UX, no source audit |
| [VonixGuardian](https://github.com/Vonix-Network/VonixGuardian) | rollback/audit core with action, NBT, queue, rollback plan/engine | SOURCE TREE OBSERVED | future audit-journal and batch rollback comparison; not integrated |

## Jujutsu Craft domain expansion: what is and is not established

- [Original Jujutsu Craft (Sorcery Fight)](https://www.curseforge.com/minecraft/mc-mods/sorceryfight) is confirmed 1.20.1 Forge and contains domains as a gameplay feature, but this turn has **not bytecode-inspected** the exact `JujutsuCraft-ver50.1-forge-1.20.1.jar`. The prior user's domain-expansion investigation does **not** authorize guessing implementation data layout or guarantee restoration semantics.
- [JJCV 1.20.1 update 2.3](https://www.curseforge.com/minecraft/mc-mods/jujutsu-craft-v/files/6973339) explicitly states that a domain-block customization command was added, warning that blocks **not** configured as domain blocks can remain after domain closing. This is an especially relevant **reported failure boundary**: restoration may be based on a selected block palette or domain teardown, not a general snapshot of every world mutation.
- [JJCD](https://modrinth.com/mod/jujutsu-domain) is an independent player-domain add-on, not the base JujutsuCraft or proof of its exact restoration mechanism.
- For parity research: obtain exact authorized base JAR and target revision of JJCV, locate domain creation/teardown state, snapshot scope, scheduled tick restoration, explosions, actor/block ownership and conflict behavior. Categorize any observed logic as `SNAPSHOT`, `PALETTE`, `TEMPORARY-DIMENSION` or `RECONSTRUCTION` only after code/bytecode confirms.

## Community leads (secondary discovery, not proof)

- [r/feedthebeast modded base griefing discussion, 2024](https://www.reddit.com/r/feedthebeast/comments/1euoqz3/): the player wants fortifications that mobs must actually breach; Epic Siege port recommended by a commenter. Useful design inspiration, not algorithmic evidence.
- [r/feedthebeast mob griefing discussion, 2025](https://www.reddit.com/r/feedthebeast/comments/1kz34i4/): disabling global mobGriefing can affect other gameplay; recommend per-invasion action policy.
- [r/feedthebeast parasites destruction discussion, 2022](https://www.reddit.com/r/feedthebeast/comments/y9f9wu/): players explicitly dislike losing lovingly built structures despite wanting challenging fights; aligns with reversible-grief product objective.
- [XTiK555/ZombieBreakAndBuild issue #1](https://github.com/XTiK555/ZombieBreakAndBuild/issues/1): group-of-zombies crash report, no reproduced root cause; prioritize horde concurrency tests.

## Candidate studies rejected as primary proof

- **Pure WorldEdit `//undo`**: indirect world changes not captured.
- **Jujutsu domain visual teardown**: visual return ≠ persistent block/BlockEntity/NBT restoration.
- **Nightmare ESM MIT label applied to Epic Mob Siege port**: separate product license cannot be inferred.
- **Whole-world checkpoint rollback**: would overwrite player progression and third-party mod state outside invasion.
- **Forced chunk loading or background unbounded restore**: risks deadlock and runaway RAM; use loaded-chunk scheduler and pending durable records.

## Remaining source/artifact tasks

(1) Exact `NESM` JAR hash and bytecode; (2) base Jujutsu 50.1 domain teardown/decompiled class claims from an authorized artifact; (3) live Forge + server dedicated tests; (4) negative tests with claim/protection mods; (5) persistence recovery and competing player modification replay.
