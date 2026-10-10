# Raids: Enhanced — version and compatibility tracks

The Minecraft Tech Hub rule applies: **Minecraft 1.20.1 + Forge is the ANCHOR, not the latest-version ceiling**. This report does not merge incompatible loaders/branches or assume one release's binary matches a public source snapshot.

| Dimension | ANCHOR | COMPARATIVE |
|---|---|---|
| Upstream branch | `1.20.1` | `master` |
| Exact source commit | [`6354ebf97faaeba79affaf7e71d01ed5ae651e85`](https://github.com/FINDERFEED/raidsenhanced/tree/6354ebf97faaeba79affaf7e71d01ed5ae651e85) | [`a1a6ded47abc1504a5319a68716cf17a5838e0e6`](https://github.com/FINDERFEED/raidsenhanced/tree/a1a6ded47abc1504a5319a68716cf17a5838e0e6) |
| Minecraft | 1.20.1 | 1.21.1 |
| Loader | Forge (dev property 47.1.104; range [47.1.1,)) | NeoForge (dev property 21.1.218) |
| Java toolchain | 17 | 21 |
| Project property version | 1.0.2 | 1.0.2 |
| FDLib dependency range | [1.0.8,2.0.0) | [1.0.8,2.0.0) in project properties |
| Java source files in observed tree | 66 | 65 |
| Target evidence | pinned official Git source | pinned official Git source |
| Distributed binary match | UNESTABLISHED | UNESTABLISHED |

The two branches have diverged: the GitHub comparison against the ANCHOR reports 12 commits ahead and 12 behind for master and shows file differences in `REConfig`, `RaidDrill`, `RaidBlimp`, `PlayerBlimpEntity`, other entity classes, spawn-egg assets and build files. Branch delta is **not** a loader migration patch guaranteed to cherry-pick.

[Exact branch comparison](https://github.com/FINDERFEED/raidsenhanced/compare/6354ebf97faaeba79affaf7e71d01ed5ae651e85...a1a6ded47abc1504a5319a68716cf17a5838e0e6)

## Strict source of truth

- **Release page statements** are product descriptions, e.g. the Drill's described automatic-burrow ceiling.
- **Git source statements** are proven for the pinned Git tree, e.g. ANCHOR `REConfig.raidDrill.automaticBurrowTimes=3`.
- **Release JAR claims** require obtaining the exact approved binary, SHA-256, JAR metadata and selected bytecode/source equivalence checks.
- **Gameplay claims** require successful isolated Forge/NeoForge test or recorded runtime observation.

Do not quietly harmonize the web description's **five burrows** with the ANCHOR source default of **three**. It is unresolved; defaults/configs, download releases and timelines may differ.

## Compatibility hardening

1. Avoid copying/replacing the `Raid.spawnGroup` injection across versions without confirming the invocation anchor in the target Minecraft artifact.
2. FDLib is an explicit runtime dependency: version and packet/animation serialization must be pinned and verified alongside the MOD.
3. Inspect 1.21.1 differences as a new comparative track, then backport **independently reconstructed concepts** only after license review and Forge 1.20.1 tests.
4. Keep open external issue reports separate from verified local behavior, especially [Flan claims (#1)](https://github.com/FINDERFEED/raidsenhanced/issues/1), [raid tags and Zapper crash (#2)](https://github.com/FINDERFEED/raidsenhanced/issues/2), and [dedicated connection / FDLib (#3)](https://github.com/FINDERFEED/raidsenhanced/issues/3).

## Follow-up artifact requirements

Record public release URL, filename, `sha256`, JAR size, `mods.toml` metadata, Java class counts, FDLib companion artifact identity, Mixin target signatures and startup receipts. No binary or decompiled source checked into public Tech Hub.
