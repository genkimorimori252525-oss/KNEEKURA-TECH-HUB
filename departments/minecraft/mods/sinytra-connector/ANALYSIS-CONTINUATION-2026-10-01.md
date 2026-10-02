# Connector analysis continuation — 2026-10-01 UTC

## Later static-knowledge milestone

The finite source-only continuation of steps 2, 3 and 6 below is now documented in
[Technical knowledge](TECHNICAL-KNOWLEDGE-2026-10-01.md), with path/facet ledgers,
eight staged research candidates and [version portability](VERSION-PORTABILITY-2026-10-01.md).
Exact dependency gaps remain explicit; the history window below is preserved.
The user excluded runtime testing for this continuation, so the earlier conditional
runtime step is not active work or authorization. The earlier acquisition results
and PARTIAL/UNKNOWN capture boundaries below remain historical evidence.


## Result and exact scope

**Whole-target analysis: IN_PROGRESS. Runtime compatibility: UNKNOWN.**
The existing queued plan is now active. This continuation performs external
reconnaissance, acquires and inventories both complete Connector source trees,
maps five concrete research leads, and reviews a bounded failure/repair window.
It does not reopen the completed MOD-AI tooling acceptance or relabel U06.

Start with the shared [practical workflow](../../ANALYSIS-WORKFLOW.md), then
the [Feature Map and provenance](BEHAVIOR-HINTS-2026-10-01.json),
[source inventory](SOURCE-INVENTORY-2026-10-01.json), and
[capture/query verification](STATIC-VERIFICATION-2026-10-01.json).
Raw source, binaries, full web captures and private paths are excluded here.

### Fixed tracks

| Track | Immutable input | Declared environment, not resolved runtime |
|---|---|---|
| ANCHOR | [7f68ac02291fde986119a3f5cab85436bed5c350](https://github.com/Sinytra/Connector/tree/7f68ac02291fde986119a3f5cab85436bed5c350) | Connector 1.0.0-beta.50; Minecraft 1.20.1; Forge 47.4.6; Java 17; FFAPI 0.92.0+1.11.5+1.20.1 |
| FRONTIER | [c84a96a3c04aa4c5253032c338434de5329be08a](https://github.com/Sinytra/Connector/tree/c84a96a3c04aa4c5253032c338434de5329be08a), official [3.0.0-beta.6+26.1.2 release](https://github.com/Sinytra/Connector/releases/tag/3.0.0-beta.6%2B26.1.2) | Minecraft 26.1.2; NeoForge 26.1.2.95; Java 25; Launchpad 1.9.1+26.1.2; FFAPI 0.155.2+26.1.2+3.5.0 |
| COMPARATIVE, unchanged | Existing [U06 released-stack receipt](../../mod-ai/verification/connector-static-2026-09-30/README.md) | Connector beta.49 + Clumps Fabric 12.0.0.4 + FFAPI 0.92.6+1.11.15; static comparison only |

Version declarations come from each pinned tree's build files. Related projects
are separate SourceSnapshots, not silently included by a dependency coordinate.
FRONTIER namespace is left `unknown` in its research profile; no mapping or
compiled-class identity is inferred from readable Java names.

### Completed now versus historical evidence

- ANCHOR: all **141 files / 584,015 bytes** acquired; FRONTIER: all **131 files /
  914,256 bytes** acquired. Both inventories are non-truncated, with no gitlinks;
  every file's size and Git blob SHA-1 were checked and a SHA-256 recorded.
- All **272 captured documents** were retrieved in **538 byte-view pages** and
  matched the acquired bytes. Eleven literal searches per track were paginated;
  every opposite-track query returned zero hits. The two indexes remain separate.
- Text search covers **125/141 ANCHOR** and **109/131 FRONTIER** documents. Current
  adapter suffix handling treats some files, including `.js`, `.mdx`, service
  records and extensionless files, as bytes. They were retained and read by byte
  view/manual inspection; zero literal hits do not mean universal semantic absence.
- Both profiles correctly remain **PARTIAL**: no runtime/dependency resolution,
  toolchain or source-binary equivalence is established. The captured Gradle
  wrapper JAR is inventory only and has no separately indexed nested root.
- Existing source/index/storage/history adapter regressions: **140 passed** with
  the pre-existing JDK 17. These are tool fixtures, not Connector runtime tests.
- U06's older 27-document ANCHOR slice and separate beta.49 COMPARATIVE receipts
  remain intact. This expanded source capture does not retroactively change them.

## Reconnaissance → code: worked Feature Map

The [official site](https://connector.sinytra.org/) currently describes NeoForge
26.1.2. Its linked wiki redirects to `latest`; the configuration page is useful
for discovering keys, but is not a versioned Forge 1.20.1 specification.

The [1.20.1 community discussion](https://github.com/Sinytra/Connector/discussions/180)
contains version/config-dependent and conflicting reports. Only a visible bounded
pass was reviewed; its table is not a compatibility certificate. A
[1.20.1 showcase video](https://www.youtube.com/watch?v=iZgKRa2JROs) was discovered,
but the opened page exposed no usable playback/transcript, so no timestamp or
behavioral evidence was invented. Captured representation, date, hash and access
limitations are recorded in the Feature Map.

| Hint | Code/history finding | Boundary / next evidence |
|---|---|---|
| Alias/config workaround | ANCHOR `ConnectorConfig` accepts single/list aliases; `DependencyResolver` applies aliases and widens constraints, dropping aliased BREAKS and fabricloader requirements | Metadata acceptance does not establish matching APIs or a successful integration; inspect the actual loader/dependency implementation |
| Hide an incompatible optional integration | ANCHOR `ConnectorEarlyLoader.init` filters host IDs before `addFmlMods`, while retaining Connector-transformed MODs | This hides visibility to Fabric Loader; it does not uninstall a MOD or prevent Forge loading it |
| Latest wiki's `enableMixinSafeguard` | ANCHOR's config schema has three fields; pinned FRONTIER adds this option, default true, and receives failing Mixin audit entries | This exact config/API differs by track; do not paste it into a 1.20.1 guide as an established feature |
| Client-only MOD on a server | ANCHOR recursively discovers nested JARs and filters final candidates by environment after resolution | Read the repair→regression→repair history; early filtering can erase nested dependency candidates |
| Current transformer plugins | FRONTIER has a transformer subproject and ServiceLoader-based plugin registration | ANCHOR has no same-named API in its captured tree; other extension mechanisms and backport feasibility remain to be mapped |

Each row has immutable path/line and CAS document locators in
[BEHAVIOR-HINTS-2026-10-01.json](BEHAVIOR-HINTS-2026-10-01.json). All five are
`MAPPED`, source-only findings; none is a runtime or whole-facet completion claim.

### Important version trap

The current wiki's safeguard hint led to a useful contradiction check. At ANCHOR,
[`ConnectorConfig`](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/src/main/java/org/sinytra/connector/locator/ConnectorConfig.java#L31-L62)
contains version, hiddenMods and globalModAliases. At FRONTIER,
[`ConnectorConfig`](https://github.com/Sinytra/Connector/blob/c84a96a3c04aa4c5253032c338434de5329be08a/src/main/java/org/sinytra/connector/util/ConnectorConfig.java#L30-L64)
adds enableMixinSafeguard; the
[`safeguard`](https://github.com/Sinytra/Connector/blob/c84a96a3c04aa4c5253032c338434de5329be08a/src/main/java/org/sinytra/connector/locator/MixinTransformSafeguard.java#L17-L53)
uses NeoForge loading errors and Adapter audit information. This supports a
specific API delta, not a claim that ANCHOR lacks all Mixin error handling.

## Whole-tree navigation and honest coverage

The inventory, not the visible guide features, defines the analysis universe.

| Surface | Current state | Next primary evidence |
|---|---|---|
| Full Connector source trees and licensing | INVENTORIED; both full byte inventories verified, MIT LICENSE files captured | Check separate dependency licenses and any required distribution notices before reuse |
| Discovery, metadata, side selection, nested JARs | MAPPED for cited ANCHOR paths and repair cases | Trace actual Fabric Loader solver, recursive selection, split packages and FRONTIER lifecycle |
| Mapping, remapping, Mixins, AW/Class Tweaker, coremods | MAPPED in earlier U06 slice / INVENTORIED elsewhere | Complete caller-to-transform order, refmap semantics, adapter patches and class-tweaker delta |
| Fabric API/emulation and external dependencies | INVENTORIED declarations, selected U06 comparative implementations only | Pin/acquire matching FFAPI, loader, Adapter and relevant host implementations as separate snapshots |
| Classloading, module boundaries, cache | MAPPED in earlier selected ANCHOR paths; full tree INVENTORIED | Complete invalidation inputs, classloader order, service selection and failure fallback |
| Registry/events, client-server/network/persistence | INVENTORIED | `src/mod` registry/network/boot compatibility mixins and associated loader boundaries |
| Rendering/model/assets, items, tags/recipes, worldgen/AI | INVENTORIED, applicability review pending | `src/mod` HUD/fieldtypes/render/tag/recipebook compatibility plus transformation patches; do not mark these N/A just because Connector is a bridge |
| Plugin API / version portability | MAPPED for the small cited delta | Detailed ordered plugin lifecycle and migration boundary; no direct-backport claim |
| Failure/repair history | PARTIAL bounded review | [Case records](FAILURE-REPAIR-HISTORY.md); remaining subsystem/history scope stays explicit |
| Performance and runtime compatibility | NOT_ANALYZED in this continuation / UNKNOWN | Authorized comparable measurements and exact runtime assertions; source cache design is not measured performance |

ANCHOR inventory includes 42 main Java files, 59 mod Java files, 3 test Java
files, 11 mod resources and 3 service records. FRONTIER separates the transformer
main/runner trees from host integration and includes its own documentation.
These counts describe paths, not depth of interpretation.

## Continue the existing plan, in this order

1. **Done in this batch:** pin both Connector tracks, complete byte inventories,
   reconnaissance/Feature Map, separate CAS readback and bounded history cases.
2. **Next static pass:** complete ANCHOR discovery→dependency→mapping→transform→
   Mixin/AW→classloading→cache call paths. For every external boundary, pin the
   exact dependency source or record it unavailable. Preserve config/side and
   namespace uncertainty; do not substitute beta.49 artifacts for beta.50.
3. **Then:** complete FRONTIER equivalents and write scoped version portability
   for each reusable technique: concept, changed APIs/namespaces/dependencies,
   required rewrite and semantic risk. Begin with safeguard/plugin/lifecycle
   differences already located, without assuming their backport is safe.
4. **Expand history by subsystem**, with an explicit window and before/after
   source; connect meaningful failures to those maps. Do not unboundedly crawl
   all history or treat closed issues as verified fixes.
5. **Runtime only for a concrete unanswered claim:** first resolve matching
   beta.50 binary/build identity, full selected dependency closure, side/config,
   candidate and planned assertions. A new build/launch configuration requires
   its own valid authorization and registry; this document grants none.
6. **Final review:** produce the existing requested overview, transformation /
   mapping / Mixin / Fabric API / classloading / cache / plugin / dependency maps,
   compatibility, portability, performance and license/provenance findings.
   Consolidate related sections rather than manufacturing empty files. Only
   then apply the whole-target completion rule in the analysis specification.

No Connector/FFAPI/Clumps build, Java wrapper, game launch, remapped candidate,
runtime compatibility claim, canonical write, merge or deployment occurred in
this continuation. Public records contain derived evidence and pointers only.
