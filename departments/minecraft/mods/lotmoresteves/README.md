# LotMoreSteves — reconnaissance (2026-11-26)

Status: IN_PROGRESS / metadata and author-described behavior only. Static binary NOT_ANALYZED; runtime NOT_RUN; failure history NOT_ANALYZED. No canonical claim promotion.

## Provenance
- Author: Crimson_Steve; CurseForge project 449901; https://www.curseforge.com/minecraft/mc-mods/lotmoresteves
- FRONTIER candidate: LMS_0.1.8_1.16.5.jar, Forge 1.16.5, 2021-06-28, beta, ~1.5 MB. https://www.curseforge.com/minecraft/mc-mods/lotmoresteves/files/all
- ANCHOR: Forge 1.20.1 adaptation destination only; no native release in official listing.
- MCreator according to author; All Rights Reserved. No public source verified. Exact binary hash/file ID/dependencies not yet verified. Do not treat this note as an immutable binary snapshot or redistribute original assets/code.
- Earlier comparative releases 0.1.0–0.1.3 and 0.1.6–0.1.7, Forge 1.16.x.
- Behavioral reconnaissance candidate: https://www.youtube.com/watch?v=0hBv4kuvNYI (not watched).

## Author-described behavior, not implementation evidence
| Mob | HP | Behavior |
|---|---:|---|
| Human | 20 | Neutral, classic-style motion, changes over time |
| Stivimal | 20 | Upright idle, crawl locomotion, hostile at low HP |
| RunningSteve | 45 | Hostile running melee |
| Squateve | 60 | Squat motion, stronger/slower than RunningSteve |
| ParalyzingSteve | 50 | Armor 15, shaking, brief immobilization, cold biome |
| Stevvither | 300 | Flying charge, terrain damage, head projectiles and beam; rare spawning after 100 Steve kills |
| MASSIVETEVE | 500 | Fast giant, terrain damage, emits Humans and eats them to heal; rare spawning after 250 kills |

## Next static research priorities
1. Acquire exact official JAR locally; hash SHA-256; inventory classes/resources and mods.toml; establish dependencies and mappings. Do not execute unknown binary just for inspection.
2. Identify entity/model/renderer associations; locate Human and RunningSteve motion code or animation assets; record time inputs, angular units, pose axes, phase, frequency/amplitude and movement-dependent transitions. Compare classic animation already adopted separately; do not assume identical implementation.
3. Map Stivimal/Squateve pose states, synchronized data, hitbox changes, attack timing and interruption. Analyze AI goals, target selection and state machines.
4. Map boss flight, charges, beams, projectile lifecycle, block destruction authority/rules, spawning thresholds, persistent counters, faction and healing.
5. Map registries, networking, worldgen, data, sounds, particles, performance hot paths and failure history per ANALYSIS-SPEC-v1.md.
6. Derive Forge 1.20.1 implementation concepts with separate version/API mapping; no direct binary compatibility assumed. Validate in authorized disposable LAB only if needed.

## Limits
Local connector returned offline tunnel error; local guides, JAR, bytecode and runtime unavailable in this pass. This is a public-safe reconnaissance record, not whole-target completion. No original assets or decompiled source committed.
