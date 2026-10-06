# QB-MOD / Garnet-MOD 1.6.4.082 — Whole-target surface coverage status

Date: 2026-10-07

This is a static-analysis coverage statement for the supplied LEGACY/COMPARATIVE snapshot.

It is **not** a claim that the target is COMPLETE under ANALYSIS-SPEC-v1:
- FRONTIER remains unpinned;
- historical VCS repair evidence is unavailable;
- original 1.6.4 runtime has not been executed in this analysis;
- performance is mapped statically, not benchmarked;
- ANCHOR 1.20.1 reconstruction is not implemented.

## Track status

| Track | State | Notes |
| --- | --- | --- |
| ANCHOR — Minecraft 1.20.1 + Forge | MAPPED as destination only | Portability risks/primitives recorded; no reconstruction/runtime |
| COMPARATIVE/LEGACY — QB/Garnet 1.6.4.082 | EVIDENCE_BACKED snapshot | supplied archive hashes + complete Java/class inventory |
| FRONTIER | NOT_ANALYZED / unpinned | no maintained later upstream source/repository established |

## Acquisition / provenance

| Surface | Status | Basis |
| --- | --- | --- |
| archive identity / hashes | EVIDENCE_BACKED | three SHA-256-pinned supplied ZIPs |
| full Java tree inventory | EVIDENCE_BACKED | QB 156 + Garnet 37 Java |
| full top-level class-tree inventory | EVIDENCE_BACKED | QB 156 + Garnet 37 class |
| source↔class structural correspondence | MAPPED | all 193 path pairs + SourceFile basename, sampled javap |
| full semantic bytecode equivalence | NOT_ANALYZED | no per-method instruction/decompile comparison |
| rights/usage locator | EVIDENCE_BACKED for supplied readmes | modification/reference permitted, commercial use prohibited; not generalized as OSS license |

## Bootstrap / registration / config

| Surface | Status |
| --- | --- |
| mod entrypoints/version/dependency | EVIDENCE_BACKED |
| item/block/entity registration | EVIDENCE_BACKED |
| numeric-ID config surface | EVIDENCE_BACKED |
| system config behavior | EVIDENCE_BACKED |
| natural spawn registrations + entity-local gates | EVIDENCE_BACKED |
| GUI handler registration | EVIDENCE_BACKED |
| custom payload registration | EVIDENCE_BACKED |

System config behavior mapped:
- EasyMode: friendly-fire suppression for same-owner magical girls;
- HeightCorrection: renderer-only pre-scale switch;
- SatelliteMode: enables optional tactical mode;
- GSLightLevel: Grief Seed light spawn threshold;
- GSSpawning: Grief Seed local spawn probability gate;
- canWalpurgisSpawn: runtime global Walpurgis spawn gate.

## AI / combat / state machines

| Surface | Status |
| --- | --- |
| Garnet owner/follow/target framework | EVIDENCE_BACKED |
| companion command modes | EVIDENCE_BACKED |
| magical-girl form/corruption machine | EVIDENCE_BACKED |
| short/mid/long attack dispatch | EVIDENCE_BACKED |
| seven implemented character attack sets | EVIDENCE_BACKED |
| Rebellion/Ultimate special AIs present in snapshot | EVIDENCE_BACKED where implemented |
| projectile/trajectory family | EVIDENCE_BACKED |
| boss/witch attack systems | EVIDENCE_BACKED for cataloged source paths |
| familiar evolution/ecology | EVIDENCE_BACKED |
| servant/clone/phantom relations | EVIDENCE_BACKED static structure |
| runtime balance/fairness | NOT_ANALYZED |

## Progression / content

| Surface | Status |
| --- | --- |
| QB contract flow | EVIDENCE_BACKED |
| QB/JB Grief Seed exchanges | EVIDENCE_BACKED |
| hidden Incubator drop condition | EVIDENCE_BACKED |
| Soul Gem item↔entity state loop | EVIDENCE_BACKED |
| witch → Grief Seed loop | EVIDENCE_BACKED |
| Grief Seed hidden Nutcracker ritual | EVIDENCE_BACKED static path |
| signature weapon recipes | EVIDENCE_BACKED |
| barrier blocks | EVIDENCE_BACKED |
| 5-slot tactical inventory | EVIDENCE_BACKED |

### Reserved / incomplete content traces

`mod_QB` declares/configures:
- `orikoGem` / `orikoGemID`;
- `yumaGem` / `yumaGemID`;
- `entityOrikoID`;
- `entityYumaID`.

However the supplied Java tree contains no `EntityOriko` or `EntityYuma` classes, and the searched symbols are not instantiated/registered into usable content in this snapshot.

State: **INVENTORIED as dead/reserved implementation trace, not a player-facing feature**.

## Rendering / presentation

| Surface | Status |
| --- | --- |
| client renderer registration | EVIDENCE_BACKED |
| major model classes inventory | INVENTORIED / MAPPED |
| character form model/texture switching | EVIDENCE_BACKED |
| posture→pose mapping | EVIDENCE_BACKED |
| boss scale/model phase changes | EVIDENCE_BACKED |
| Shadow polymorphic visuals | EVIDENCE_BACKED |
| luminous projectile renderer | EVIDENCE_BACKED |
| PNG asset inventory | EVIDENCE_BACKED |
| alternate texture-pack path mapping | EVIDENCE_BACKED |
| custom sound assets | NOT_APPLICABLE — none found |
| stock sound/particle vocabulary | MAPPED |
| animation curves/keyframes as a modern animation system | NOT_APPLICABLE — legacy model/render code |

The texture pack contains one direct path defect candidate:
- intended Madoka UF filename uses full-width `ｍ`, not ASCII `m`.

## Networking / persistence

| Surface | Status |
| --- | --- |
| Garnet gun custom payload | EVIDENCE_BACKED |
| legacy GUI/menu boundary | EVIDENCE_BACKED |
| owner/mode NBT | EVIDENCE_BACKED |
| magical-girl form/corruption/inventory NBT | EVIDENCE_BACKED |
| Soul Gem stack detector NBT | EVIDENCE_BACKED |
| Grief Seed countdown/corruption NBT | EVIDENCE_BACKED |
| special Homulilly seed persistence | EVIDENCE_BACKED defect candidate |
| Charlotte phase persistence | EVIDENCE_BACKED defect candidate |
| witch ecology age persistence | EVIDENCE_BACKED as absent |
| master/encounter reference persistence | MAPPED as mostly runtime-only |

## World / biome / structure surfaces

| Surface | Status | Notes |
| --- | --- | --- |
| custom dimension | NOT_APPLICABLE | no DimensionManager/WorldProvider surface found |
| custom biome | NOT_APPLICABLE | vanilla biomes only used for spawn registration |
| custom structure/world generator | NOT_APPLICABLE | no IWorldGenerator/MapGen/Structure registration found |
| terrain mutation in combat | EVIDENCE_BACKED | witch clearance, boss destruction, TNT conversion |
| protected terrain vocabulary | EVIDENCE_BACKED | Mami Ribbon / Kyouko Shield exceptions |

The absence is bounded to the supplied full Java tree; it is not a statement about other historical releases.

## Data / loot / achievements / transforms

| Surface | Status |
| --- | --- |
| code-authored recipes | EVIDENCE_BACKED |
| entity drops / progression loot | EVIDENCE_BACKED |
| data-pack recipes/loot/tags | NOT_APPLICABLE to this 1.6.4 implementation |
| custom achievements | NOT_APPLICABLE in source search |
| OreDictionary integration | NOT_APPLICABLE in source search |
| Mixins | NOT_APPLICABLE |
| Access Transformers / Access Wideners | NOT_APPLICABLE in supplied tree/archive scan |
| coremod / IClassTransformer / ASM transform layer | NOT_APPLICABLE |
| custom dimensions/structures | NOT_APPLICABLE |

## Dependency / integration surface

| Surface | Status |
| --- | --- |
| QB → Garnet declared dependency | EVIDENCE_BACKED |
| Garnet generic AI/projectile/gun foundation | EVIDENCE_BACKED |
| Garnet → QB reverse concrete type reference | EVIDENCE_BACKED defect/architecture lead |
| stale source-only external imports | EVIDENCE_BACKED source-release cleanliness lead |
| other optional mod integrations | NOT_ANALYZED / none established |

## Performance / safety

| Surface | Status |
| --- | --- |
| static tick/query/world-edit risk map | MAPPED |
| measured TPS | NOT_ANALYZED |
| measured FPS/render cost | NOT_ANALYZED |
| startup/loading cost | NOT_ANALYZED |
| allocations/GC | NOT_ANALYZED |
| async/synchronization behavior | MAPPED as overwhelmingly synchronous legacy logic |
| multiplayer concurrency/reentrancy | MAPPED; GUI shared-container risk identified |

See `STATIC-PERFORMANCE-AND-SAFETY-RISK-MAP.md`.

## Failure / repair history

Status:
`NOT_ANALYZED / HISTORICAL_VCS_UNAVAILABLE_WITH_CURRENT_EVIDENCE`

Current static anomaly list is useful for future historical matching and runtime probes, but no Issue→PR→fix-commit chain has been fabricated.

## Community reconnaissance

Status: MAPPED.

Useful sources found:
- original distribution topic locator — currently inaccessible;
- creator introduction metadata;
- contemporary 1.6.4 community guide/update;
- gameplay series/indexes.

Important version discipline:
- 1.6.4.080-era guide behavior conflicts with supplied 1.6.4.082 Homura Ultimate source;
- some recorded gameplay used trial builds;
- community material therefore seeds searches but does not override 1.6.4.082 source.

## Current conclusion

The **supplied 1.6.4.082 static implementation is now broadly whole-tree mapped** across the required content-MOD surfaces.

Remaining work is qualitatively different from “read more classes”:
1. original-version runtime verification;
2. full source↔bytecode semantic comparison if desired;
3. historical repair-chain recovery from archives;
4. FRONTIER/later-version discovery;
5. 1.20.1 ANCHOR reconstruction and LAB validation.

Therefore the correct project state is **STATIC WHOLE-TREE MAPPED, NOT COMPLETE**.