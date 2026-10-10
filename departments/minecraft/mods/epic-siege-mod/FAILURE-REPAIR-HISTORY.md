# Original Epic Siege Mod — selected source-level repair history

Scope: 1.12 branch `da3dsoul/Epic-Siege-Mod`, selected performance-related [commit a51465f74452f74e8b605625986b980d47fe1994](https://github.com/da3dsoul/Epic-Siege-Mod/commit/a51465f74452f74e8b605625986b980d47fe1994). **Case is only a direct diff + author message review, not measured runtime regression proof**.

## ESM-1.12-2018-PATH-THROTTLE

- Symptom: commit author's message reports a major latency issue linked to vanilla wandering and excessive path searches over large distances.
- Trigger/context: 1.12 AI entities using custom `ESM_EntityAIAttackMelee`, `ESM_EntityAIAttackRanged`, `ESM_EntityAITarget` and `EntityAIWander`; no exact report/measurements captured.
- Before/after diff directly inspected: melee path request delay becomes at least `distance - 16` when far away, new "already near correct final path node" check avoids redundant recalc; ranged AI adds `navDelay` and final path point check; target AI now scales target search delay with distance. `ESM_EntityAIWander` wrapper enforces delayed wandering for passenger case.
- Related author changes: pillar material configurability, blacklist policy and attacker cap logic; specific mechanics outside bounded repair case.
- Root cause diagnosis: **author claim/inference**, not independently validated with old Minecraft profiler. Runtime efficiency effect **NOT_RUN**.
- Reuse lesson: avoid computing the same costly path every tick when target displacement/path endpoint does not justify it. Use existing path suitability, cooldown, distance-aware adaptive repath and preserve MOB logic/reaction time. An invariant of "never repath beyond X" is unsafe: combat geometry may change.

Source comparator: [historical 1.12 branch](https://github.com/da3dsoul/Epic-Siege-Mod/tree/d02bf54c935b29664bf8058b0e914ebaf49e16dd).

**Partial scoped evidence.** Reproduction, benchmarking and remaining upstream history not reviewed. Source license undecided for concrete reuse.
