# Jujutsu Verse 9.0 — Minecraft 1.20.1 Forge / selected static audit

**Status:** `PARTIAL_STATIC_ANALYSIS` — selected visual/domain/compatibility facets only; runtime `NOT_RUN`; target **NOT COMPLETE**.

## Snapshot (ANCHOR and current selected FRONTIER)

- Target: Tehen's Jujutsu Kaisen / Jujutsu Verse 9.0, `modId=jujutsu_kaisen`; `mods.toml` declares version `9.0`.
- Exact user-provided file: `jujutsu_kaisen-9.0-forge-1.20.1(1).jar`, **40,621,200 bytes**, SHA-256 `fdf1f8a6c28833c093dc778764b5a6147fc0552ec34e172f918fa4be8dccc065`.
- Minecraft: **1.20.1**; loader: JavaFML / Forge `[47,)`; dependencies: GeckoLib and Player Animator (declared mandatory, with duplicate optional entries in metadata).
- 6,436 ZIP entries / 3,818 Java `.class` files; CRC test PASS. Individually checked 38 indexed internal paths and SHA-256 values.
- Official distribution: https://www.curseforge.com/minecraft/mc-mods/jujutsu-verse/files/9609792 ; rights and license information: https://www.curseforge.com/minecraft/mc-mods/jujutsu-verse .
- `FRONTIER` for this snapshot: same 9.0 (no separately verified newer Minecraft/loader implementation). Future 'latest' releases require independent pinning.
- `COMPARATIVE`: **8.1 repository research**, not an available 8.1 JAR. Previous work resides on [draft PR #100](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/pull/100) and its [fixed artifact provenance](../../JAR-PROVENANCE.md).

## Documents

- [FINAL-TECH-AUDIT-2026-11-18.md](FINAL-TECH-AUDIT-2026-11-18.md) — class-level evidence, display/attack/domain maps, bounded conclusions, and corrections to the comparison.
- [FINAL-evidence-2026-11-18.json](FINAL-evidence-2026-11-18.json) — 38 class/resource SHA-256 records, inventory counts, Mixin declarations, animation and shader metadata.
- [TECHNIQUE-HARVEST.md](TECHNIQUE-HARVEST.md) — independently usable concepts split by subsystem rather than one monolithic attack framework.
- [FAILURE-REPAIR-HISTORY.md](FAILURE-REPAIR-HISTORY.md) / [JSON](FAILURE-REPAIR-HISTORY.json) — mandatory research facet, explicitly `NOT_ANALYZED`.

## Scoped findings

| Subsystem | Finding | Confidence / boundary |
|---|---|---|
| Black Flash | Procedural geometry, moving stroke/ribbon, shader uniforms `Age`, `Seed`, `Pass` | EVIDENCE_BACKED for selected code/resource structure; no runtime view |
| Beam | Volume shader with SceneDepth, post-processing, emission/bloom; server hitbox kept separate | EVIDENCE_BACKED selected paths; performance not measured |
| Simultaneous domain cut-in | Client chooses up to 3 participants with 2/3-way composition | EVIDENCE_BACKED for rendering; NOT a proof of 3-way battle solver |
| Domain contest | Selected damage/DOMAINHP math `>=120` removal, `/8` player, `/14` nonplayer | EVIDENCE_BACKED selected path, matches documented 8.1 math |
| Terrain | BlockState + BlockEntity-NBT snapshot, chunk/owner indexes, restoration queues | EVIDENCE_BACKED static structure; data recovery untested |
| Malevolent Shrine budget | 16,384 checks, 1,536 destructions, 4 ms budget numbers per tick | Static configuration only; 4ms execution is **not proven** |
| Mixin/compatibility | 186 configured mixin declarations, conditional Embeddium/Rubidium mitigation | Static map, not actual compatibility PASS |

## Explicit limits

- Do **not** treat ZIP inventory as full interpretation of 3,818 classes.
- Do **not** claim actual FPS/TPS, multiplayer contest correctness, or shader compatibility from static bytecode.
- Do **not** claim a true 8.1→9.0 per-class diff. 8.1 source JAR is unavailable in this pass. The earlier generated draft accidentally used a **Jujutsu Craft** hash for Verse 8.1; the final GitHub report and JSON correct it against PR #100.
- Do **not** commit original JAR, decompiled classes, shader source, music, textures or other third-party assets. Use insights for clean-room independent designs subject to licensing review.
- No canonical Core Claim promotion or human validation is asserted. A future deep audit must evaluate unreviewed facets and issue/PR repair history.

## Process

Scoped to [ANALYSIS-WORKFLOW](../../../ANALYSIS-WORKFLOW.md) and [ANALYSIS-SPEC-v1](../../../ANALYSIS-SPEC-v1.md); selected facets only. The parent directory's V8.1 record is historical and remains unchanged except for a version-link note.
