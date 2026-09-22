# Minecraft Whole-Target Analysis Specification v1.1

## 1. Compatibility contract — dual track

Every target should define:
- ANCHOR: Minecraft 1.20.1 + Forge adaptation target
- FRONTIER: latest useful upstream implementation
- optional COMPARATIVE tracks when an intermediate version or loader transition materially explains the technology

If native 1.20.1 Forge code exists, analyze it as ANCHOR. If it does not, ANCHOR remains the destination environment for an explicit backport design.

Never merge evidence across tracks. A FRONTIER statement is not automatically valid on ANCHOR.

## 2. Track-specific SourceSnapshot

Pin for each track: role, Minecraft version, loader, repository, branch/release/tag/commit, artifact identity, hashes when available, license locator, and dependency versions.

## 3. Full-tree acquisition

- obtain the full upstream source tree locally when available
- inventory the whole tree before interpretation
- do not limit whole analysis to search hits or a few classes
- keep raw worktrees/JARs/decompiled trees outside Git by default
- commit derived inventories, hashes, maps, deltas, and evidence locators

## 4. Required analysis surfaces

- loader entrypoints / registries / events / config
- client-server boundaries / networking / persistence
- AI / goals / brain / navigation / combat / state machines
- dimensions / biomes / structures / worldgen / progression
- renderer / models / animation / textures / atlas / UV / shaders / particles / sound
- recipes / loot / tags / advancements / data registries
- Mixins / Access Transformers / Access Wideners / Class Tweakers / reflection / coremods
- mappings / remapping / classloading / bytecode transformations
- dependencies / integrations / optional compatibility
- tick cost / startup cost / caches / allocation / async / synchronization

## 5. Loader bridge / transformation systems

For targets such as Sinytra Connector additionally map:

- foreign-loader mod discovery
- metadata and dependency translation
- namespace/mapping remap pipeline
- JAR and bytecode transformation pipeline
- Mixin compatibility and method patching
- Access Widener / Class Tweaker conversion
- Fabric API replacement/emulation boundary
- classloader/module interactions
- nested JAR handling
- transformed-artifact cache lifecycle
- plugin/extension APIs
- incompatibility detection and fallback

## 6. Version portability

For each reusable technique record:

- invariant concept
- ANCHOR implementation
- FRONTIER implementation
- changed Minecraft API
- changed loader API
- changed mappings/namespaces
- dependencies introduced/removed
- direct backport feasibility
- rewrite requirements
- semantic risks

The objective is to recover the technique and reconstruct it correctly for 1.20.1 Forge, not to copy/paste incompatible source.

## 7. Provenance

Every substantive finding should use a stable locator where possible: repository + commit + path/lines, JAR hash + internal path, asset hash + path, or generated manifest record. AI summaries are not primary evidence.

## 8. Completion states

Facet states: NOT_ANALYZED / INVENTORIED / MAPPED / EVIDENCE_BACKED / NOT_APPLICABLE.

A target is COMPLETE only when required tracks are pinned or explicitly unavailable, required facets are evidence-backed or not applicable, and ANCHOR↔FRONTIER portability is recorded.
