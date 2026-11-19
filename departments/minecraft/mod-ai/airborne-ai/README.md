# Airborne AI Cross-MOD Research — 2026-10-04

## Status

- Scope: cross-MOD static research and reusable design extraction for Minecraft 1.20.1-oriented airborne AI.
- Result: **STATIC_RESEARCH_COMPLETE / RUNTIME_NOT_RUN / CANONICAL_PROMOTION_NOT_PERFORMED**.
- Baseline: the existing [Olympus Harpy flight AI research](../../mods/olympus/FLIGHT-AI-RESEARCH-2026-10-04.md).
- This directory is a synthesis layer. It does **not** mark every upstream MOD as fully analyzed under the repository-wide `ANALYSIS-SPEC-v1.md`.
- Source/binary equality, full issue-history closure, and in-game reproduction remain UNKNOWN unless stated otherwise.

## Research set

| Source | Role in this study | Evidence level |
| --- | --- | --- |
| Olympus / Harpy | 3D combat navigation baseline, orbit, dodge, dash, recovery | source-backed existing TECH HUB research |
| Saint's Dragons | large-flyer flight stack, landing transition, tactical air/ground choice, pack combat | source-backed |
| Alex's Mobs / Crimson Mosquito | compact hostile-flyer combat lifecycle | source-backed |
| Fowl Play | ecology schedule, Brain-gated behavior, perch/rest, flocking | source-backed |
| Cosy Critters & Creepy Crawlies | lightweight client flock, Boids, simple landing/perch FSM | source-backed current tree + 1.20.1 release-history corroboration |
| Ice and Fire | legacy large-dragon flight target geometry, navigator switching | source-backed |
| Ice and Fire: Dragon Fix | repair-history clues for Ice and Fire flight defects | release/history evidence; exact source closure not claimed here |
| Hostile Mobs and Girls | reusable cheap hostile-flight shell with replaceable attack Goals | source-backed |
| Book of Dragons | LOS/search behavior and flight-strafe repair clue | **observation/changelog only; ARR** |

## Documents

- [TASK-2026-10-04.md](TASK-2026-10-04.md) — task definition, completion boundary and follow-up.
- [SOURCE-AND-LICENSE-MATRIX-2026-10-04.md](SOURCE-AND-LICENSE-MATRIX-2026-10-04.md) — source entry points, branches/revisions and license boundaries.
- [TECHNIQUE-MATRIX-2026-10-04.md](TECHNIQUE-MATRIX-2026-10-04.md) — reusable mechanisms by subsystem.
- [FAILURE-REPAIR-LESSONS-2026-10-04.md](FAILURE-REPAIR-LESSONS-2026-10-04.md) — observed failure classes and design invariants.
- [FOUNDATION-ARCHITECTURE-2026-10-04.md](FOUNDATION-ARCHITECTURE-2026-10-04.md) — proposed KNEEKURA Airborne AI Foundation.
- [Olympus failure/repair history](../../mods/olympus/FAILURE-REPAIR-HISTORY.md) remains the detailed baseline for Olympus-specific cases.

## Main conclusion

There is no single "best flying AI" to copy. The useful techniques occupy different layers:

1. **Tactical decision** — Saint's Dragons, Olympus, Alex's Mobs.
2. **Ecology / schedule / Brain** — Fowl Play.
3. **Route planning** — Olympus and Saint's Dragons.
4. **Continuous steering** — Olympus, Saint's Dragons, Ice and Fire, Alex/HMaG.
5. **Landing and takeoff ownership** — Saint's Dragons and Fowl Play, with Cosy as a lightweight FSM reference.
6. **Local flock steering** — Fowl Play and Cosy.
7. **Group combat coordination** — Saint's Dragons.
8. **Cheap hostile-flight shell** — HMaG.
9. **Ambient non-authoritative mass flight** — Cosy.
10. **Failure boundaries** — Ice and Fire / Dragon Fix, Saint's release history, Cosy/Fowl/HMaG release histories, Book of Dragons LOS history.

The recommended foundation therefore uses replaceable layers and performance tiers instead of forcing every flying creature through one expensive universal controller.

## Offline prototype\n\nThe follow-up executable contract prototype is under [prototype/README.md](prototype/README.md). It keeps Tier A/Tier B logic and failure regressions outside the active LAB/native observer paths. Its status is **OFFLINE_CONTRACT_PROTOTYPE / MINECRAFT_RUNTIME_NOT_RUN**.\n\n## Runtime boundary

No Minecraft client/server was launched for this synthesis. No claim here establishes:
- actual TPS cost;
- binary equivalence to distributed JARs;
- full collision correctness in every structure/cave;
- multiplayer synchronization behavior;
- exact parity with any upstream MOD.

Those require the separate LAB/runtime acceptance stage.
