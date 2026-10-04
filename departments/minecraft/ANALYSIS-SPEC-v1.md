# Minecraft Whole-Target Analysis Specification v1.2

> Performance-focused targets additionally use
> [optimization/ANALYSIS-SPEC.md](optimization/ANALYSIS-SPEC.md) and
> [optimization/BENCHMARK-SPEC.md](optimization/BENCHMARK-SPEC.md).
> Source-level optimization mechanism and runtime performance evidence are separate claims.

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
- failure/repair history: Issues, PRs, fix commits and before/after code, causes, repair and scoped reusable lessons

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

## 9. Failure/repair history — mandatory analysis facet

Follow [FAILURE-REPAIR-HISTORY-v1.md](FAILURE-REPAIR-HISTORY-v1.md). For each analyzed track, publish `FAILURE-REPAIR-HISTORY.md` and a machine-readable `FAILURE-REPAIR-HISTORY.json` under that MOD's analysis directory. Read the selected upstream Issues/PRs, repair diffs and before/after source; do not substitute a count of closed Issues or a summary of current source.

This is part of analyzing other MODs, not merely a recorder for future KNEEKURA development. Use the same record shape for our own MOD incidents, labelled OWN_DEVELOPMENT. No new scheduler, automatic crawler, separate knowledge database or automatic Claim promotion is implied.

Define the history window, queries and relevant subsystems before the review. Record inspected, deferred and unavailable material. No useful supported cases is a legitimate bounded result; it is not evidence that the MOD has no bugs. Do not grow an unbounded all-history crawl just to satisfy this facet.

Existing analysis results are not retroactively rewritten. Add this facet as NOT_ANALYZED until reviewed; preserve the previous completion/version record. A new whole-target completion claim must account for the facet, including explicit unavailable/no-supported-case findings and coverage evidence. Twilight Forest remains ahead of Connector in the analysis queue.

## 10. Player-facing behavioral reconnaissance — required discovery aid

Whole-target MOD analysis should inspect suitable **player-facing behavioral sources** early,
when they exist. Examples include the official wiki/manual, established community wikis,
攻略サイト / gameplay guides, modpack documentation, forum posts, Reddit discussions and
videos whose claims can be located precisely enough to review.

Their role is **reconnaissance, not implementation authority**.

Use them to discover:

- player-visible features and subsystem names that source-tree structure alone may hide;
- boss phases, special attacks, immunity windows and progression gates;
- item/block effects, interaction conditions and uncommon state transitions;
- biome/dimension/structure generation conditions and hidden rooms/mechanics;
- compatibility symptoms, version-specific behavior, known bugs and practical workarounds;
- terminology and concrete values that produce better Source/Bytecode/Issue/PR searches;
- candidate links from player-observed symptoms to Failure / Repair History investigations.

The default flow is:

```text
player-facing source
        ↓
behavior hint / research hypothesis
        ↓
track/version scoped search terms and Gameplay Feature Map
        ↓
Source + Bytecode + mappings
        ↓
Issue / PR / commit history when relevant
        ↓
real-game observation/test when needed
        ↓
evidence-backed engineering finding
```

Rules:

1. **Do not copy a guide claim into implementation truth.** A guide/wiki/community statement
   may seed a `CANDIDATE` / secondary report, but it does not by itself prove how the MOD is
   implemented.
2. **Bind the hint to a track/version and retrieval date when possible.** A guide written for
   another Minecraft/MOD version must not silently become an ANCHOR claim.
3. **Preserve disagreement.** If two guides disagree, record the disagreement as a search lead;
   do not vote by popularity or choose a winner without stronger evidence.
4. **Prefer exact behavioral clues over generic prose.** Names, thresholds, triggers, dimensions,
   items, structures, symptoms and reproduction steps are useful because they can be traced into
   code/history/runtime evidence.
5. **Treat Reddit/forum/video material as community reports.** They may reveal rare behavior or
   failures that official docs omit, but author confidence, likes/views and repetition are not
   validation.
6. **No suitable guide found is an acceptable result.** Record that the reconnaissance surface
   was unavailable or unhelpful; do not invent player behavior to fill the gap.
7. **Completion still depends on engineering evidence.** Player-facing reconnaissance improves
   what the analyst looks for; it cannot by itself move a required facet to `EVIDENCE_BACKED`.
8. **Do not let guides narrow the analysis universe permanently.** Full-tree inventory and the
   required analysis surfaces remain authoritative, so undocumented mechanics can still be found.

For large MODs, use the reconnaissance pass to sketch a lightweight **Gameplay Feature Map**
before deep code interpretation (for example bosses, progression, structures, worldgen, items,
rendering-visible mechanics and compatibility). The map is a navigation aid, not a second
canonical knowledge graph.


Practical execution, checklist and lightweight templates: [ANALYSIS-WORKFLOW.md](ANALYSIS-WORKFLOW.md).
This is an analyst workflow using existing retrieval/history/Core staging, not an automatic site scraper or completion gate.
