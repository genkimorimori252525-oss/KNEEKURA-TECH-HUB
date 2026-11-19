# Improved Mobs — bounded upstream failure and repair history

Scope: two verified source-level repair chains relevant to 1.20.1 Forge, plus one older comparative injection conflict and two unresolved reports. This **is not an all-history crawl**, and the research does not claim runtime reproduction.

## R-01 — target selection mutation caused possible concurrency failure

- Author's [1.12.4 changelog](https://github.com/Flemmli97/ImprovedMobs/blob/029b8c20302a76bac1af9f5140e2abb6f73fea5c/Changelog.md) says "Modify target goal instead of remove and replace which should fix [a] concurrent exception".
- **Actual diff:** [commit 9c4c79712c12](https://github.com/Flemmli97/ImprovedMobs/commit/9c4c79712c12231c0bc8365e12acb663d70dd1a3), parent `e18ec801ef29991e59558190af72c40faf469b86`. Directly checked `EventCalls.java` in both revisions. Pre-fix code removed existing villager target Goal via `goalRemovePredicate` and appended a replacement. Post-fix iterated existing `NearestAttackableTargetGoal` to adjust line-of-sight and only appended if no relevant villager goal existed; `GoalSelectorMixin` lost the removal method.
- Causal diagnosis: AUTHOR_CLAIM that replacement might trigger concurrent iteration failure; exact stack/reproducer **UNKNOWN**. The code change establishes mutation-boundary repair intent, **not** proven runtime fix.
- Lesson: when overlaying AI on third-party mobs, prefer narrow goal modification to deleting an active wrapped goal while selectors may be iterating.

Before: [EventCalls at e18ec...](https://github.com/Flemmli97/ImprovedMobs/blob/e18ec801ef29991e59558190af72c40faf469b86/common/src/main/java/io/github/flemmli97/improvedmobs/events/EventCalls.java)  
After: [EventCalls at 9c4c...](https://github.com/Flemmli97/ImprovedMobs/blob/9c4c79712c12231c0bc8365e12acb663d70dd1a3/common/src/main/java/io/github/flemmli97/improvedmobs/events/EventCalls.java)

## R-02 — 1.20.1 Forge Drowned + Epic Fight ticking crash

- [Issue #283](https://github.com/Flemmli97/ImprovedMobs/issues/283): user reported Minecraft 1.20.1 Forge 47.3.11, Improve Mobs 1.13.0, TenshiLib 1.7.6 + Epic Fight 20.9.5, spawn Drowned → ticking entity crash. Report says pathing/player-villager behavior implicated.
- [Commit 7366c81f...](https://github.com/Flemmli97/ImprovedMobs/commit/7366c81f37d9ffa74b78f36194c6f2c5a23e8505), parent `ba2306a03e0fb064c0bb85d3274405761f4fabd1`, author message "schedule (dis)mount fix #283 epic fight crash". Compared parent/after `FlyRidingGoal.java`: immediate passenger `startRiding/stopRiding` changed to special mount's `scheduledRide/scheduledDismount` and tick-time processing in `RiddenSummonEntity`.
- Cause: **INFERENCE** that simultaneous goal/mount/entity lifecycle transitions caused incompatible state; actual stack mechanism not proven here. Link commit and issue support repair *intent* only.
- Lesson: orchestrate mount/dismount on a deterministic server tick boundary and validate state transitions under combat/pathing and other mods. Runtime fixed acceptance NOT_RUN.

## R-03 — historical Lithium/Roadrunner pathfinder injection conflict (NOT 1.20.1 evidence)

- [Issue #131](https://github.com/Flemmli97/ImprovedMobs/issues/131): Minecraft 1.16.5 Forge report shows Mixin `InvalidInjectionException` at a `WalkNodeEvaluator` overwrite/redirect also targeted by Roadrunner/Lithium, with world load failure.
- [Commit e048eb9...](https://github.com/Flemmli97/ImprovedMobs/commit/e048eb96878646427a707a5ee5ebc44ea5551bf0), parent `73c35c17f24f31b0efca352e8ec26a738e35a18c`, moved the invasive `WalkNodeStaticMixin` redirect to a separate **optional** Mixin config and notes Lithium already performs comparable optimization.
- Lesson: *optimization Mixins* touching shared vanilla routing should be separately gated and compatibility-tested, not loaded as unconditionally required dependencies. This old 1.18-era repair/1.16.5 report pair spans different versions: exact source release linkage and runtime proof not established.

## Selected unresolved/current community reports (no fix claim)

- [#274](https://github.com/Flemmli97/ImprovedMobs/issues/274): user alleged severe pathfinding CPU cost; author clarified turning off breaking also disables the associated pathfinding. This is a **reported symptom**, not a measured benchmark.
- [#304](https://github.com/Flemmli97/ImprovedMobs/issues/304): whether Improved Mobs works with Enhanced AI was asked; author said they did not know incompatibilities, **not proof of compatibility**.
- [#364](https://github.com/Flemmli97/ImprovedMobs/issues/364): open 2026-10-04, Minecraft 1.21.1 NeoForge 21.1.252 v1.16.0.b — user reports Drowned/NPE in `SwimNodeEvaluatorMixin` when pathfinding context is null. Reproduction by KNEEKURA **NOT_RUN**, issue diagnosis is user interpretation, and does not establish 1.20.1 behavior.
- [#255](https://github.com/Flemmli97/ImprovedMobs/issues/255): 1.20.1 Forge issue with Citizens2/Mohist pathing crash report, reproduction unverified.

## Evidence status

The source lines, commit diffs and issue bodies/comments were directly read via official GitHub at 2026-10-11, but immutable raw payload CAS profile/document IDs were **not minted** and binaries not downloaded; the structured JSON is a research staging companion, **not history-adapter import-ready**. Fix verification for all cases: NOT_RUN. Missing original log/archive hashes remain explicit.
