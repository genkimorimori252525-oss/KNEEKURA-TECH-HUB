# Twilight Forest U01–U05 static acceptance, 2026-09-30

The existing MOD-AI adapters were exercised on actual pinned public inputs. This is a partial static acceptance result, not full runtime acceptance.

- Source: TeamTwilight/twilightforest commit `a7dd8f13c653e137f977f5ffaa870fcb20fc1625`; 49 selected files independently match their Git blob identities
- Distribution: 4.3.2508, SHA-256 `0bdc89263616d1b35c32ef82c5e9c14cbd20368e2fe8b468c72a28320be7a778`, 23,332,091 bytes
- Cached Minecraft 1.20.1 / Forge 47.4.6 / Java 17 inputs were used; 101 baseline compile artifacts were rehashed. This is not a resolved Twilight Forest dependency/config closure
- Existing profile/index preparation captured 173 documents, prepared 91 exact classfiles and repeated with 91 cache hits and an unchanged index identity
- 45 query groups over 78 pages executed; 170 source/bytecode/resource documents were fully retrieved over 320 pages and rehashed. Ten exact JVM member selectors resolved
- Independent packaged-resource verification found 6,156 exact matches, zero mismatches and zero missing paths
- Focused regression: 105 tests passed

## Task results

- U01: Naga/Goal/target declarations and exact inherited Monster → PathfinderMob → Mob → LivingEntity chain reached; serverAiStep and Goal descriptors inspected
- U02: Hydra multipart damage delegation and the exact attackEntityFromPart descriptor reached. Forge 47.4.6 attack/hurt/damage events, source patches and actual mapped LivingEntity calls were checked before suggesting any Mixin. No intervention was selected or applied
- U03: Registration → ASMHooks tracking-entity send → packet serialization → queued client handler → TFPart data update traced. Coremod script content was preserved as bytes. Transformation execution and dedicated-server/client synchronization remain untested
- U04: Legacy/JAPPA Hydra renderer/model selector and exact packaged hydra4 texture reached. Same-run pose/render/frame evidence remains NOT_RUN
- U05: Liveroot item/block registration, data generators, generated item/loot JSON and distribution texture/resource correspondence reached. No MOD changes or new build were made
- U06: BLOCKED. The candidate Fabric MOD and its immutable inputs/dependency closure were not supplied

## Important boundaries

All five authored mojmap MOD-owner lookups returned PARTIAL with no binary hit. The shipped distribution uses SRG; explicitly corrected SRG queries resolve its real class locators. Source and binary namespaces were never silently relabeled.

Relations remain PARTIAL. Dynamic dispatch, callbacks, reflection, runtime class loading, executed coremods, transformed ordinals and full dependency closure are unresolved. Source-to-binary compiled-class equivalence remains NOT_ESTABLISHED. Wiki search results were only lightweight discovery hints; technical findings use pinned source/artifacts. No canonical promotion, database writes, game launches, upstream build/code execution, active source edits or publication occurred.

See `summary.json` for public source links, exact content hashes, profile/index IDs, member descriptors and task-specific limits. Raw acquisition and query evidence stays private outside the repository.
