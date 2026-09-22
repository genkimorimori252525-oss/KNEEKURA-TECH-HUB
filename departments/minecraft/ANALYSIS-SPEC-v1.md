# Minecraft Whole-Mod Analysis Specification v1

## 1. Compatibility contract

Canonical department data MUST target:

- Minecraft `1.20.1`
- Loader `Forge`

A result from another version/loader may be attached only as comparative evidence and must carry an explicit compatibility mismatch flag.

## 2. Source lock

Before analysis, pin the exact inspected artifact:

- upstream repository
- release/tag/commit when available
- downloadable artifact identity
- JAR SHA-256
- source archive SHA-256 when used
- license identifier/text locator
- dependency versions

No analysis is considered reproducible without a Source Snapshot.

## 3. Archive inventory

Create a complete path inventory before interpretation.

Classify at minimum:

- Java/classes
- mixins / access transformers
- META-INF / mods.toml
- assets/<namespace>/textures
- models / blockstates
- animations
- shaders
- particles
- sounds
- lang
- data/<namespace>
- recipes / loot tables / tags / advancements
- worldgen / structures / dimensions
- data generators / generated resources

For binary assets, record path, size, SHA-256, type, and relevant dimensions/metadata without requiring the binary itself to be committed.

## 4. Code architecture map

Map:

- Forge entrypoints
- DeferredRegister / registries
- event subscribers
- capability usage
- config
- networking channels and packet directions
- client-only vs common/server boundaries
- persistence / NBT / saved data
- commands
- data generation
- integration hooks

Produce path-level evidence for each important statement.

## 5. AI and behavior map

For every entity with non-trivial behavior, inspect:

- vanilla Goal / TargetGoal composition
- Brain / Sensor / Memory usage
- navigation/pathfinding class
- target selection
- combat decisions
- cooldowns/timers
- phase/state changes
- boss state machines
- environmental reactions
- cooperative/group behavior
- server authority and client visualization split
- persistence across save/reload

Represent complex behavior as a state/transition table or graph. Do not infer behavior solely from class names.

## 6. World systems

Inspect:

- dimensions
- portals
- biomes
- structures
- configured/placed features
- processors/templates
- spawn rules
- chunk/world lifecycle hooks
- progression gates tied to world state

## 7. Rendering and assets

Create explicit dependency mappings such as:

`entity -> renderer -> model/layer -> texture(s) -> animation/pose source`

and

`block/item -> model -> texture(s)`

Inventory:

- textures and resolution
- atlas/sprite usage
- UV/model references
- animated textures
- emissive/special render paths
- custom RenderType/shader use
- particles
- entity/model animation code
- sounds/music and their triggers

## 8. Data-driven systems

Map JSON/data assets back to the code or gameplay systems that consume them:

- recipes
- loot tables
- tags
- advancements
- damage types
- worldgen data
- language keys
- custom codecs/data registries

## 9. Performance and lifecycle

Look for:

- per-tick work
- scans over entities/blocks/chunks
- allocation-heavy loops
- caches
- async work
- synchronization
- client/server duplicate computation
- resource reload listeners
- event handlers with broad frequency

Performance notes are hypotheses until measured or directly supported by evidence.

## 10. Compatibility and patch surface

Record:

- hard dependencies
- optional dependencies
- integrations
- Mixins
- Access Transformers
- reflection
- replaced vanilla behavior
- event priority/cancellation assumptions

## 11. Provenance discipline

Every substantive finding should point to a stable locator when possible:

- repository + commit + path + line/range
- JAR hash + internal path
- asset hash + internal path
- generated manifest record

AI summaries are not primary evidence.

## 12. Repository boundary

By default, do not commit raw third-party JARs, full decompiled trees, or complete copied asset sets. Keep those in ignored local artifacts and commit derived inventories/mappings/analysis. If a specific upstream license clearly permits redistribution, that still does not make copying mandatory.

## 13. Completion states

Facet status vocabulary:

- `NOT_ANALYZED`
- `INVENTORIED`
- `MAPPED`
- `EVIDENCE_BACKED`
- `NOT_APPLICABLE`

A Mod is `COMPLETE` only when all required facets are either `EVIDENCE_BACKED` or `NOT_APPLICABLE`, and the Source Snapshot is pinned.
