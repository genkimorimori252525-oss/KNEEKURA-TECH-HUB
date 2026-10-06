# Jujutsu Verse V8.1 vs Jujutsu Craft ver50.1

This comparison is scoped to the two exact binaries analyzed in KNEEKURA-TECH-HUB. It is an engineering comparison, not a gameplay ranking.

## Identity

Jujutsu Craft and Jujutsu Verse are separate mods and must remain separate provenance records.

## Domain architecture

### Jujutsu Craft

Prior static analysis found:
- common domain creation
- shared active lifecycle
- shared Domain Expansion battle procedure
- character-specific payload
- distinct anti-domain mechanisms

Its reusable strength is shared combat-state infrastructure.

### Jujutsu Verse

This V8.1 binary exposes:
- DOMAINHP initialized to 100
- ordinary combat damage routed into domain durability
- active amplifier-based push/pull
- explicit win/lose handoff flags
- progressive sure-hit shell traversal
- progressive barrier teardown

Its reusable strength is explicit contest durability plus amortized large-area work.

## Simultaneous Domain presentation

Jujutsu Verse has a dedicated DomainCutinOverlay that:
- finds simultaneous nearby domain users,
- locks participants,
- supports 2-way and 3-way layouts,
- creates procedural panel backgrounds,
- uses depth-buffer masks,
- renders actual participant models.

The existing Jujutsu Craft ver50.1 analysis did not identify an equivalent dedicated 2/3-way GUI cinematic layer. This statement is scoped to the prior evidence and is not an absolute absence claim.

## Visual-effect architecture

Jujutsu Craft evidence emphasizes:
- Geo/field actors for Blue, Red and Purple
- procedure-driven effects
- PlayerAnimator vs GeckoLib animation separation
- shared combat resolver/counters

Jujutsu Verse adds especially reusable presentation primitives:
- procedural Black Flash geometry
- client-reconstructed beam trails from synchronized state
- large local VFX caches
- universal aura bridge across vanilla + GeckoLib
- target-anchored post-process ripple
- FBO-backed domain surfaces
- depth-masked 2/3 participant GUI cinematic
- Projection Sorcery render/culling intervention

Engineering conclusion:
- Jujutsu Verse is the stronger reference for presentation architecture.
- Jujutsu Craft remains especially valuable for combat-system organization and reusable rule abstractions.

## Performance lessons

Good patterns:
- local reconstruction from compact synchronized state
- 20-tick shell traversal
- scheduled domain cleanup
- cached trail/VFX history
- deterministic seeded procedural visuals

Risks:
- particle limiter forced on
- large procedural drawing loops
- broad nearby-entity scans in generated Procedures
- full-screen post chains
- extra off-screen render target work

The extraction target is the separation of responsibilities, not wholesale copying.
