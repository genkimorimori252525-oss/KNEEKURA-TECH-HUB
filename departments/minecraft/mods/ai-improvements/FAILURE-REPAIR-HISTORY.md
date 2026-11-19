# AI Improvements — scoped failure/repair notes

Investigation: 2026-10-11; 0.5.x ANCHOR-adjacent and selected prior history, NOT whole-repo review.

## Case AI-31 — duplicate event modifications cost performance

[Issue #31](https://github.com/BuiltBrokenModding/AI-Improvements/issues/31): user reported an overloaded server and linked a spark profile. [Fix commit 2e95e6e62edeea7cfd86a06865d5cebaf190ab39](https://github.com/BuiltBrokenModding/AI-Improvements/commit/2e95e6e62edeea7cfd86a06865d5cebaf190ab39) removed the **extra `LivingSpawnEvent` subscriber**, leaving `EntityJoinLevelEvent` as the modifier entry point.

The commit author says the former spawn event has several subevents, meaning the same modifier logic ran extra times and degraded performance. Actual diff confirms event subscriber removal. This was part of the `1.19` source ancestry before 0.5.2; **runtime fix effectiveness and issue's spark profile were NOT independently reproduced**.

**Lesson**: count execution frequency of hooks before optimizing a Goal's inner loop. An event-driven "one-time" pass can accidentally execute multiple times and be costly.

## Case AI-10 — optional look-goal pruning needs per-mob policy

[Issue #10](https://github.com/BuiltBrokenModding/AI-Improvements/issues/10) user requested mob allow/deny lists because removing idle looking from some mobs ruined their appeal. [Commit 4f89b9f86729c4967670b7e5fb4190f25a1](https://github.com/BuiltBrokenModding/AI-Improvements/commit/4f89b9f86729c4967670b7e5fb4190f25a1) adds filtered look Goals and look-controller policies. Compared publicly available diff: `ConfigMain` gained `FilteredConfigValue`, `ModifierSystem` switches to `FilteredRemove`.

**Lesson**: feature flags should scope to entity type/role and preserve player-visible behavior; no blanket deletion of look/target tasks for siege bosses.

## Case AI-25 — Forge update broke startup, historical 1.19

[Issue #25](https://github.com/BuiltBrokenModding/AI-Improvements/issues/25): report for Forge 41.0.94 / MC 1.19. The branch history references a Forge-compatibility repair, but the exact before/after diff for this incident was **not** reviewed in this phase. Keep the case DEFERRED and do not infer a root cause or verified repair. Do not import an incomplete case as validated.

No recorded case proves 1.20.1 Forge 47 performance or interoperability.
