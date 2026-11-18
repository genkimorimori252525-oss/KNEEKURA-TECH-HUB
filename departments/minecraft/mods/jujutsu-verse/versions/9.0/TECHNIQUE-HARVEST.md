# Jujutsu Verse 9.0 — modular technique harvest (independent design notes)

This is a list of candidate **concepts** extracted from a bounded binary inspection, not an imported codebase, licensed asset, proven performance method, or canonical TECH-HUB knowledge. Local technical evidence is in [the audit](FINAL-TECH-AUDIT-2026-11-18.md) and [manifest](FINAL-evidence-2026-11-18.json).

| Topic / suggested TECH-HUB category | Mechanism seen in 9.0 | Recommended independent abstraction | Required validation |
|---|---|---|---|
| Rendering / procedural VFX | BlackFlashRenderer: generated lightning branches, traveling line, ribbons and impact | Shape state -> time progression -> screen/world output separated from damage | Low-entity and high-entity visual pacing, cross-platform shader behaviour |
| Rendering / volumetric beam | BeamRenderer + beam_volume/post shader: SceneDepth and layered emission/composite | Quality tiers and depth-aware compositing; no effect-specific source copying | Visual occlusion, GPU cost by pass count, shader pack interactions |
| Combat / authority | BeamServerHitBox runs server hit scan independently of graphics | Server-authoritative hit validation + compact effect state; optimize candidate collection | Dedicated server, client disparity, high-entity TPS test |
| UI / simultaneous cinematic | DomainCutinOverlay renders up to three locked participants with masking | Presentation cardinality independent from battle-logic participant state | 2/3+ casters, spectator, skin/model and latency tests |
| World / reversible terrain | DomainTerrain Snapshot + SavedData + chunk/owner indexes, restore queue | Transactional block change log, idempotent restoration, failure recovery | Chunk unload/load, restart, tile entity, overlapping claims |
| Performance / bounded work | MalevolentShrineTerrain: count- and time-budgeted jobs | Work queues, tick budgets, accounting for overshoot and fairness | Worst-case tick duration, multi-domain and rollback tests |
| Compatibility / conditional transformation | RenderCompatibilityPlugin switches off one named Mixin for Embeddium/Rubidium | Opt-in guarded compatibility hooks scoped to exact known conflicts | Real compatibility matrix with Iris/Oculus/Embeddium/Rubidium |
| Animation / phase state | simple_domain.animation.json: expansion/hold/collapse variants | State-directed animations + semantic phase IDs rather than fixed one-shot timelines | Animation blending, interrupt, state sync, low FPS |

Do not force these independent primitives into a single 'Jujutsu style' reusable library; consumers can select only the needed technique. The source is All Rights Reserved according to distribution; reproduce ideas with independently authored implementation/assets.
