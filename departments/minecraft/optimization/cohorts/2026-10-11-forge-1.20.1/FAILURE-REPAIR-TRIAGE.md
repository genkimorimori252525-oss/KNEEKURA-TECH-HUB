# Cross-target failure/repair triage — 2026-10-11

Reports are discovery evidence, not code facts. A commit and a closed Issue do not prove a corrected Forge 1.20.1 runtime. Binary/JAR parity and benchmarks are NOT_RUN.

| Target | Source/Issue environment | Reported fault | Inspected repair or contrary evidence | State |
|---|---|---|---|---|
| [FerriteCore #129](https://github.com/malte0811/FerriteCore/issues/129) | user MC **1.20.1**, Chipped+ModelGapFix | reported loading ~23s without Ferrite vs ~70s with it | [2aa56a0](https://github.com/malte0811/FerriteCore/commit/2aa56a0def18a94574bc4c0f6e1aea00db1709a5), before and after source read: replace `Arrays.hashCode` of quad vertices with stronger collision-resistant hash | **PATCH_EVIDENCE**, timing only user-reported |
| [ModernFix #332](https://github.com/embeddedt/ModernFix/issues/332) | 1.20-era Litematica + dynamic DFU | legacy schematic appears empty | [ae8cfba](https://github.com/embeddedt/ModernFix/commit/ae8cfbaa3d880a20b70a418f4ae276312fa30981), before/after source read: auto-disable dynamic DFU when Litematica present; rule still seen in selected source | **PATCH_EVIDENCE**, no runtime test |
| [ServerCore historical activation patch](https://github.com/Wesley1808/ServerCore/commit/2238660d4be5e56336e7f9a890cb7f42138eaf82) | historical activation range logic | activation immunity not checked promptly after early return (author explanation) | before/after source read: update activated tick before returning | **PATCH_EVIDENCE**, no performance test |
| [ServerCore #118](https://github.com/Wesley1808/ServerCore/issues/118) | **1.21.1** ServerCore 1.5.5, NOT 1.20.1 1.5.2 | iron farm yield reduced | maintainer notes exclusion setting requires entity/chunk reload; reporter confirmed reload fixed tested case | FRONTIER user report |
| [Particle Core #47](https://github.com/fzzyhmstrs/pc/issues/47) | **Fabric 1.21.11**, 0.3.2 | unsafe LegacyRandomSource access during async | selected 1.20.1 source contains fallback patterns, but this newer version is different | FRONTIER report only |
| [Particle Core #65](https://github.com/fzzyhmstrs/pc/issues/65) | 2026-09, OPEN | async chunk palette access exception | no confirmed code repair examined | UNVERIFIED |
| [FastSuite #47](https://github.com/Shadows-of-Fire/FastSuite/issues/47) | ATM10 user modpack | suspected deadlock | maintainer explicitly says log does **not** implicate FastSuite, suspects MiniHUD; user modified MiniHUD/JEI/MEI | **CONTRARY_EVIDENCE**: do not blame FastSuite |

## Reusable failure contracts

**Cache/hash:** poor hash distribution may make deduplication expensive even when memory use falls. Retain precise equality and a robust hash; invalidate on resource reload.

**Lazy initialization:** delaying DFU class loading changes when another MOD's Mixins/initializers execute. Compatibility exclusions should preserve old behavior.

**Activation:** skipping entity ticks must not bypass awake/immune combat or breaking nearby contraptions. Exclusion changes may require reloading entity state.

**Async particles:** avoid off-thread mutable RNG/chunk palette access; fallback for known exceptions does not magically prevent all races.

**Scope:** selected issue/commit windows only, not full history; no immutable raw API CAS imports. Six priority MOD directories contain partial history companions. NEVER promote performance or correctness to VERIFIED based only on code and Issue discussion.
