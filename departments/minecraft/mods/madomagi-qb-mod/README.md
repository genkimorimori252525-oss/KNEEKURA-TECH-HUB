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
- PROGRESSION-ECONOMY-AND-LOOT.md — QB/JB exchange economies, hidden Incubator acquisition, Soul Gem/Grief Seed progression loop
- GARNET-FRAMEWORK-AND-SHARED-AI.md — owner/mode/follow/target framework, reverse dependency and shared-AI performance leads
- WITCH-ECOLOGY-AND-FAMILIARS.md — age/kill-driven evolution, servant ecosystems and hostile imitation archetypes
- NETWORK-PERSISTENCE-AND-STATE-BOUNDARIES.md — DataWatcher/NBT/network/menu boundaries and save-load defect candidates
- CONTENT-REGISTRY-RENDER-CATALOG.md — registration, recipes, inventory, boss scale and renderer techniques
- ASSET-AND-VISUAL-INVENTORY.md — 94 PNG inventory, model/renderer surfaces and alternate texture-pack filename defect
- BINARY-SOURCE-CORRESPONDENCE.md — 193/193 Java/class structural correspondence evidence
- STATIC-PERFORMANCE-AND-SAFETY-RISK-MAP.md — LAB targets and bounded-modernization risk map
- SURFACE-COVERAGE-STATUS.md — current whole-target facet coverage and explicit non-completion reasons
- ANCHOR-PORTABILITY-MATRIX.md — legacy concept → Minecraft 1.20.1 Forge reconstruction mapping
- STATIC-INVENTORY-SUMMARY.json — compact archive/member provenance fingerprints
