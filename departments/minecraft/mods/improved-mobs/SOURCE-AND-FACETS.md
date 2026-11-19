# Track provenance, whole-target facet review and acquisition bounds

## ANCHOR

- Repository: https://github.com/Flemmli97/ImprovedMobs
- Branch: `1.20.1`; immutable revision: `029b8c20302a76bac1af9f5140e2abb6f73fea5c`; Git recursive tree index: **134 blobs / 106 Java**; `truncated=false`.
- Source `gradle.properties`: 1.20.1, Forge development `47.1.3`, Java 17, Fabric/Forge multi-platform layout, mod `1.13.7`, TenshiLib `1.20.1-1.7.2`. Forge metadata requires TenshiLib.
- CurseForge: https://www.curseforge.com/minecraft/mc-mods/improved-mobs/files/8282565, file ID 8282565, 1.20.1/Forge `improvedmobs-1.20.1-1.13.7-forge.jar`, ~327.8 KB published 2026-06-19.
- Relationship of live Git commit to published binary: **UNESTABLISHED**. No binary downloaded/hashes measured. Source SHA does not prove JAR bytecode or actual build inputs.
- Licensing: ARR stated by Forge `mods.toml` and distribution page. No LICENSE file found in either observed Git tree. Rights-respecting *derived notes only*.

## FRONTIER

- Branch `1.21`; immutable revision `d495a4d617d38b841f275b174f7137e0644de13c`; Git recursive tree index **167 blobs / 136 Java**, `truncated=false`.
- `gradle.properties`: Minecraft 1.21.1, NeoForge 21.1.233, Java 21, TenshiLib 1.21.1-2.3.0, project mod 1.16.0.b.
- Source now centers `common/` + `neoforge/`, with datapack entity-property overrides and expression-configured chances.
- Release binary hash/bytecode and dynamic compatibility: **UNESTABLISHED**.

## Selected ANCHOR source surfaces read

Direct, pinned source excerpts/full read:
- `BlockBreakGoal.java`, `PathFindingUtils.java`, `GroundNodeMixin.java`, `PathNavigationMixin.java`, `NodeEvaluatorMixin.java`, swim/flying Mixins and pathfinding performance Mixins.
- `BlockRestorationData.java`, `BreakableBlocks.java`, `Config.java`, `EventCalls.java`, Forge `EventHandler.java`.
- `LadderClimbGoal.java`, `FlyRidingGoal.java`, `StealGoal.java`, `ItemAIs.java`, `Utils.java`, `DifficultyData.java`, Forge `PacketHandler.java`, `MobMixin.java`, `MobEntityMixin.java`, `ClipContextMixin.java`, `improvedmobs.mixins.json`.
- `Changelog.md`; selected upstream issue threads and commit diffs, selected before/after file reads for target-goal and Epic Fight fixes.

Not acquired: all 106 Java source **bodies** locally, third-party TenshiLib full dependency implementation/classpath, original release binary/JAR, MD5/SHA archive, executed worlds, client displays, debugger/profiler traces and full upstream Issue/PR history.

## Facet state ledger

| Facet | Scoped result |
|---|---|
| Identity, source tracks, version, author, license, dependencies | EVIDENCE_BACKED (source metadata), release JAR equivalence UNKNOWN |
| Whole tree source path inventory | INVENTORIED BOTH tracks |
| AI, pathfinding, breaking, ladder, mounted behavior | EVIDENCE_BACKED_STATIC for selected ANCHOR algorithms |
| Config, difficulty, equipment, item use, target selection | MAPPED to EVIDENCE_BACKED_STATIC for selected paths |
| Block restoration, persistence and limitations | EVIDENCE_BACKED_STATIC |
| Forge registration/events, Mixin surface | MAPPED |
| Rendering/animation/model/particles/sound | INVENTORIED; no content-model architecture identified in index beyond minimal UI; NOT_ANALYZED fully |
| Worldgen/structures/dimensions/recipes/loot/tags | INVENTORIED; generated see-through block tag found; no claim of full absence |
| Networking | MAPPED two Forge payloads: difficulty/config client-sync |
| Version portability | MAPPED SELECTED FEATURES |
| Performance | RISK ANALYSIS ONLY, NOT_RUN |
| Failure/repair history | PARTIAL scoped cases; no runtime reproduction |
| Source artifact parity | NOT_ANALYZED |
| Runtime/game tests | NOT_ANALYZED |
| Knowledge Core VALIDATED | NOT_PROMOTED |

## Follow-up gates

Obtain exact 1.13.7 binary + TenshiLib artifact SHA, compare targeted class bytecode and Mixin config; run controlled tests in disposable 1.20.1 Forge (with/without Enhanced AI, separate coexistence with ZBB), path node CPU profiles with 1/10/50/100 hostiles, chunk-unload restoration and block-entity behavior; then revisit facet completion. No prior LAB run is proof for this MOD.
