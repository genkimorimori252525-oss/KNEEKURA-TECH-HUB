# Phase 7 — Client background rendering, ItemEntity merge and entity despawn compatibility

Date: 2026-10-11. **SOURCE-SELECTED ONLY. No combination launched or benchmarked.**

| Combined subsystems | Ownership and possible interaction | Confidence and acceptance gate |
|---|---|---|
| [Dynamic FPS](../../mods/dynamic-fps/README.md) with Embeddium/ImmediatelyFast | Client GLFW focus, idle and frame skipping versus individual foreground render passes | DynamicFPS source3.11.4 supports 1.20.1; do not confuse lower **background** GPU/CPU with an increase in gameplay FPS. Assert restoration of GUI and render settings on focus return |
| [Let Me Despawn](../../mods/let-me-despawn/README.md) and [Get It Together, Drops!](../../mods/get-it-together-drops/README.md) | A despawning equipment-carrying mob may produce new ItemEntity objects subsequently merged by spatial query | **Both exact user versions lack source parity.** Compare before/after inventory/owner/pickupDelay/NBT and once-only drops. This is a hypothetical integration test, not a verified incompatibility |
| Let Me Despawn and [Clumps](../../mods/clumps/README.md) | Mob gear/item-drops versus ExperienceOrb state during deaths/despawns | Different Entity classes and event contracts. Avoid mixing ItemEntity and XP semantics in optimization records |
| Let Me Despawn and future KNEEKURA invasion enemies | Source concept permits persistent picked-item Mob to despawn; wave actors and named bosses need guaranteed lifetime | Exclude active wave attackers and encounter bosses; preserve the mod design over raw entity-count reductions |
| Historical SmoothBoot and Dynamic FPS | Startup Executor worker priorities versus runtime client render throttling | Different phases; historical Forge1.19.2 source cannot prove source code for released SmoothBoot 0.0.4 |
| [Canary/Saturn source gates](PHASE-7-SOURCE-IDENTITY-GATES.md), Noisium and ModernFix | Candidate duplicated source code/Mixin surfaces but no exact Canary/Saturn 1.20.1 sources | No claim of unsafe co-install or redundancy without exact binary hook signatures |

## Reproducible next tests: NOT_RUN

1. **CLIENT-FOCUS-RETURN** — idle/unfocused/invisible/hovered 100 transitions, measure background GPU/CPU, wattage when possible, foreground FPS p95/p99 after return, sound level, lost input and full graphics option restoration.
2. **ITEMENTITY-RADIUS** — vanilla vs enabled; identical item stacks and NBT, ownership and tag exclusions; sample radius 0.5,2,8 and checkY on/off. Compare MSPT and item counts, avoid an unbounded radius=500 search in production.
3. **MOB-DESPAWN-SCOPE** — naturally spawned non-named geared mob, named mob, boss, raid attacker, picked equipment, special tags; count world drops once, check removal reason, world unload/reload and dimensional transition.
4. **BOOT-EXECUTOR** — only after 0.0.4 JAR/source identity acquisition. Compare worker threads/priorities/startup times/classloading lockups under equal JVM/CPU.
5. **SANITY** — final authoritative correctness depends on actual original Forge1.20.1 artifact bytes and loaded Mixin targets, not public Issue reports.

**Runtime/JAR/GPU/MSPT measurements: 0.**