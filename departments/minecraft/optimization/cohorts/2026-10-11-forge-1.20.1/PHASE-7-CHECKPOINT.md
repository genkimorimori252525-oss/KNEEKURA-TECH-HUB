# Phase 7 checkpoint — exact-source Dynamic FPS, two comparative entities, three blocked originals

Date: 2026-10-11. Parent optimization category PR #91 remains unmerged. Continuing research PR #111 and 58 basename intake. Prior [Phase 6](PHASE-6-CHECKPOINT.md) reached 20/27 distinct candidate dossiers with selected source mechanisms and 50 catalog concepts.

| Candidate | Source identity boundary | Observed mechanics or incident | Classification |
|---|---|---|---|
| [Dynamic FPS 3.11.4](../../mods/dynamic-fps/README.md) | Source backport [499b5eed](https://github.com/juliand665/Dynamic-FPS/tree/499b5eed268ad0d55be7e3dc4e3384d53bacad7b) build version3.11.4, Minecraft development 1.20.0, supported through 1.20.1, Forge module; exact distributed JAR SHA unavailable | Focus/hover/minimize/idle-based background frame skipping, minimum 15FPS **client render-loop cadence**, vanilla option restore and optional library checksum; [#204](https://github.com/juliand665/Dynamic-FPS/issues/204) older Gson crash actual [fix](https://github.com/juliand665/Dynamic-FPS/commit/3bfa1b35747b5e41c9f68bf4a8b7709a53f26fca); [#283](https://github.com/juliand665/Dynamic-FPS/issues/283) newer 1.21.11 setting restoration fix [b7316de9](https://github.com/juliand665/Dynamic-FPS/commit/b7316de9b2d9a6ed65d23ebbbebeefe4f21a07a9) | SELECTED ANCHOR SOURCE; PERF_NOT_VERIFIED |
| [Get It Together, Drops! 1.3](../../mods/get-it-together-drops/README.md) | Exact MC1.20 Forge source not pushed by developer; historical [1.19.2 Forge source](https://github.com/bl4ckscor3/GetItTogetherDrops/tree/5adec7a58162d9762feeb1348eb11ce349638ae6) version1.3 is **COMPARATIVE** only | ItemEntity nearby merge with excluded/do-not-combine tags, configured radius and Y search (old source default radius2.0), separate from XP Clumps; no confirmed 1.20 source/fix commit | COMPARATIVE ONLY / ANCHOR NOT_PROVEN |
| [Let Me Despawn 1.5.0](../../mods/let-me-despawn/README.md) | Exact 1.5.0 Forge source not found. Original source branches have older 1.18 Forge1.0.3 and 1.21 NeoForge/Fabric1.4.4, neither exact | Concept allow naturally despawning otherwise-persistent equipped mobs while returning gear; exact [#66](https://github.com/frikinjay/let-me-despawn/issues/66) reports 1.5.0 Endermen stuck atop tall trees; no confirmed 1.5.0 patch | COMPARATIVE ONLY / ANCHOR NOT_PROVEN |
| Smooth Boot Reloaded 0.0.4 | [Source gate](PHASE-7-SOURCE-IDENTITY-GATES.md): original 1.20.1 source NOT_FOUND, historical Forge1.19.2 0.0.2 fork available | Historical configurable Forge worker pools and priority; publisher 0.0.4 says worker count algorithm changed, so old defaults not attributable | SOURCE_BLOCKED |
| Canary 0.3.3 | [Source gate](PHASE-7-SOURCE-IDENTITY-GATES.md): original Forge0.3.3 source NOT_FOUND; Lithium1.20.1 main code COMPARATIVE only | Noisium 2.3.0 selects a compatibility Mixin if Canary mod ID present; only source proof of **Noisium** design | SOURCE_BLOCKED |
| Saturn 0.1.3 | [Source gate](PHASE-7-SOURCE-IDENTITY-GATES.md): original Forge0.1.3 source NOT_FOUND | Earlier MemoryLeakFix/Saturn collision concerned Forge1.18.2 not 1.20.1 | SOURCE_BLOCKED |

## Cumulative coverage accounting

- **58 input basenames** preserved; **27 performance-first candidates**; other 31 are related/diagnostic/utility, not mistaken for core optimizers.
- 20 partial in-cohort candidate dossiers through Phase6; **3 added** in Phase7 (Dynamic FPS source corresponds to 3.11.4 development branch; GetDrops and LetMeDespawn are **comparative-only**), thus **23/27 in-cohort partial dossiers**. Independently AI Improvements source dossier exists in parent genre, bringing **24 of the 27 with at least some research dossier across the optimization category**; this does NOT mean complete analysis.
- The other **three originals remain source-identity-blocked**, not analyzed. The fourth non-in-cohort case is AI Improvements handled in parent.
- Added **five** carefully bounded technique concepts, 50→**55**; COMPARATIVE_ONLY specified for historical ideas. This is a concept catalog, **not 55 proven performance improvements**.
- Six MOD catalog rows updated with direct bounded READMEs or source-identity gate, including release v3.11.4 accurate branch source and LMD/GetDrops comparative warnings.
- **Zero** JAR SHA/source bytecode parity, complete source-body+CAS acquisitions, imported failure history drafts, actual Forge launches, TPS/FPS/GPU benchmarks, canonical validated knowledge promotions.

## Next stage

First investigate **spark** and **Observable** only as performance-diagnostic tools with source code, sampling overhead and measured sidecar design; do not call these FPS boosters. Next, obtain original Forge 1.20.1 JARs if user chooses to upload; isolate correctness and paired benchmark in disposable environment. Reopen three provenance gaps only on fresh primary evidence, rather than endlessly guessing forks.

Supporting [client/ItemEntity/despawn compatibility matrix](CLIENT-IDLE-DESPAWN-DROPS-MATRIX.md), [Phase 7 machine receipt](PHASE-7-RECEIPT.json).