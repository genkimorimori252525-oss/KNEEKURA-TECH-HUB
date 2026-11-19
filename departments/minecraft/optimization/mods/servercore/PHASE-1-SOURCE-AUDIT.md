# ServerCore — Phase 1 source/repair audit (2026-10-11)

**SourceSnapshot:** [Wesley1808/ServerCore `1.20.1` @ `d1d0a02d39d0739441419e3a20f46fbc88d98ec5`](https://github.com/Wesley1808/ServerCore/tree/d1d0a02d39d0739441419e3a20f46fbc88d98ec5), 135 source-tree blobs / 105 Java. User's JAR version: `servercore-forge-1.5.2+1.20.1.jar`; source release association/bytecode not compared. ANCHOR source branch Minecraft 1.20.1, modern Frontier pending.

**Mechanism source backed:**
- `ActivationRange.java`: classify entities into groups (`RAIDER`, `VILLAGER`, `ZOMBIE`, `MONSTER`, `FLYING`, etc.), expand bounding regions around active players and set expiration of active state, skip scheduled work when out of range. Protect particular entities through exclusions/active-combat/immunity checks: projectiles, Wither, Dragon, active targets etc.
- `DynamicManager.java`: every **20 ticks** reads average MSPT; only reacts beyond a **±5 ms** hysteresis band around target; can change view/simulation distance, mobcap multiplier in enumerated order. This is **load shedding**, not free speedup: it changes world and spawn simulation; track effects.
- `ServerCore` Mixin tree contains per-entity inactive ticks and per-dimension chunk optimizations, not all audited yet.

**Risk for KNEEKURA Invasion:** Mods with attack-active NPCs must not be frozen at the wrong time; automatic reduced view/mobcap can silently change wave difficulty and tower defense balance. Base-world redstone and villager farms may behave differently. No current integration enabled or profiled.

**Concrete source repair:** [commit `2238660d4be5e56336e7f9a890cb7f42138eaf82`](https://github.com/Wesley1808/ServerCore/commit/2238660d4be5e56336e7f9a890cb7f42138eaf82), parent `845a152d694b51484a9ea39b82eee8826db790eb`, actual diff: when an entity `shouldTick()` directly passes, update `activatedTick(currentTick)` before returning. Author explains that previous behavior failed immediate re-check of activation immunities and could break redstone contraptions; runtime fix effectiveness not validated.
- [Issue #118](https://github.com/Wesley1808/ServerCore/issues/118) is **FRONTIER Minecraft 1.21.1 / ServerCore 1.5.5**: reporter says iron farm golems stop/slow with activation; maintainer says reload chunk after edited exclusion; reporter confirmed chunk reload restored behavior. This **does not prove an ANCHOR 1.20.1 bug** and is not same commit.

**Licensing caution:** source `ActivationRange.java` cites an Aikar/Paper/Spigot implementation and **GPL-3.0** in its header, so copyright of this component must be audited independently before adapting or copying. Derived technical summaries only.

**Benchmark:** paired A/B server for 1/10/50/100 invading actors and villagers, 4-second combat immunity, mob spawn outcomes, 20-tick aggregate hysteresis, p95/p99 MSPT and entity tick counts. With activation off, game outcomes should match baseline; with activation on, record acknowledged semantic changes.

**Facet:** mechanism EVIDENCE_BACKED_STATIC for reviewed files, full index INVENTORIED, repair DIFF_READ, performance NOT_RUN and source binary parity UNVERIFIED.

[ActivationRange.java](https://github.com/Wesley1808/ServerCore/blob/d1d0a02d39d0739441419e3a20f46fbc88d98ec5/common/src/main/java/me/wesley1808/servercore/common/activation_range/ActivationRange.java) / [DynamicManager.java](https://github.com/Wesley1808/ServerCore/blob/d1d0a02d39d0739441419e3a20f46fbc88d98ec5/common/src/main/java/me/wesley1808/servercore/common/dynamic/DynamicManager.java).
