# QB-MOD / Madoka Magica MOD analysis

Target: legacy QB-MOD 1.6.4.082 with required Garnet-MOD 1.6.4.082 and an alternate texture pack supplied on 2026-10-07.

This directory follows departments/minecraft/ANALYSIS-SPEC-v1.md and ANALYSIS-WORKFLOW.md.

## Track policy

- ANCHOR: Minecraft 1.20.1 + Forge reconstruction target
- COMPARATIVE / LEGACY: supplied Minecraft 1.6.4.082 implementation
- FRONTIER: unresolved / unpinned

Never treat a 1.6.4 API call as directly portable to 1.20.1. Extract the invariant technique, then rewrite against ANCHOR APIs.

## Documents

- SOURCE-SNAPSHOT.md — archive hashes, tree inventory, usage-condition locator and track identity
- GAMEPLAY-FEATURE-MAP.md — player-facing behavior hints tied back to source
- ANALYSIS-INITIAL-2026-10-07.md — first whole-target engineering pass
- FAILURE-REPAIR-HISTORY.md — bounded history status and candidate anomalies

Raw uploaded source, compiled classes and original assets are deliberately not committed here.

## Deep-dive catalogs

- CHARACTER-COMBAT-CATALOG.md — character-by-character normal / Rebellion / Ultimate combat patterns
- PROJECTILE-TRAJECTORY-CATALOG.md — projectile physics, homing, staged world props, fan-out and summon-seed trajectories
- BOSS-COMBAT-CATALOG.md — witch/boss phase systems, summons, terrain interaction and static anomaly leads
- ITEM-AND-RITUAL-CATALOG.md — player weapons, Soul Gem detector behavior, gun framework and hidden Grief Seed/Homulilly ritual
