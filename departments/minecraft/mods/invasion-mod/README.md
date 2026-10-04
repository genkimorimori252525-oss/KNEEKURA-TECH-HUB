# Invasion Mod — Analysis Workspace

## Status

**Targeted siege-system analysis: MAPPED / evidence-backed at the subsystem level. Whole-target completion: IN_PROGRESS. Runtime reproduction: NOT_RUN.**

This workspace analyzes the uploaded **Invasion 1.1.2 for Minecraft 1.7.10** JAR as the historical implementation under study, then maps the reusable mechanics onto KNEEKURA's adaptation anchor (**Minecraft 1.20.1 + Forge**) using the current public port. Player guides and community material are discovery aids only; implementation claims are grounded in the uploaded binary or pinned source.

## Tracks

### COMPARATIVE — uploaded legacy distribution

- Artifact: \`Invasion_1.1.2_1.7.10.jar\`
- Minecraft: **1.7.10**
- Mod version: **1.1.2**
- SHA-256: \`944f4c33687ef256bf692666421a757345519b1318df96de95565a53c2e28ddc\`
- Size: **1,189,673 bytes**
- ZIP entries: **327**
- Class entries: **231**
- Embedded metadata: authors Lieu / Elsee / UnstoppableN; dependency MinecraftForge
- Public-source candidate: [UnstoppableN/Invasion-mod@644a52ddea104c206d022bef9edc135c060cba1d](https://github.com/UnstoppableN/Invasion-mod/tree/644a52ddea104c206d022bef9edc135c060cba1d)
- Source tree: **392 files / 231 Java files / 75 resources**
- Boundary: metadata, class inventory and selected bytecode/source behavior are strongly consistent, but a reproducible build or whole-class semantic equality check has **not** been performed.

### ANCHOR — Minecraft 1.20.1

- Repository: \`kevintrini2811/Invasion-Mod\`
- Branch: \`1.20.1-neo\`
- Revision: [aaa6812b786eeb4c7b48ec5cc7a77d061d6b9e10](https://github.com/kevintrini2811/Invasion-Mod/tree/aaa6812b786eeb4c7b48ec5cc7a77d061d6b9e10)
- Declared Minecraft: **1.20.1**
- Build: \`net.neoforged.moddev.legacyforge\`, Java 17, Forge/NeoForge-compatible output
- Source tree: **684 files / 366 Java files / 309 resources**
- Source property version: **2.1.0**
- Runtime/distributed binary correspondence: **UNKNOWN**

### FRONTIER — current useful public source

- Repository: \`kevintrini2811/Invasion-Mod\`
- Branch: \`26.3neo\`
- Revision: [fce5d30b74f804ae90814c7a10cdff255ba80363](https://github.com/kevintrini2811/Invasion-Mod/tree/fce5d30b74f804ae90814c7a10cdff255ba80363)
- Declared Minecraft: **26.3**
- NeoForge: **26.3.0.6-beta**
- Java: **25**
- Source tree: **700 files / 371 Java files / 319 resources**
- ANCHOR and FRONTIER have diverged histories; statements are track-scoped.

## Main finding

The important Invasion technology is **not simply “mobs can break blocks.”** The original design merges movement planning and siege work into one route representation.

A path node can carry a \`PathAction\` such as \`DIG\`, \`BRIDGE\`, directional ladder construction, ladder-tower construction or \`SCAFFOLD_UP\`. The pathfinder evaluates those actions as possible edges with costs; the navigator pauses at the action node and asks a terrain worker to execute the planned construction/destruction. Thus the route is both a movement path and a small construction plan.

The 1.20.1 port preserves this invariant but does **not** port the legacy global pathfinder wholesale: it attaches actions to vanilla \`Node\`, extends \`WalkNodeEvaluator\` / \`PathFinder\`, and executes the same action semantics through modern navigation and goals. That is the recommended KNEEKURA adaptation direction.

## High-value recovered techniques

1. **Action-bearing path nodes** — route search includes digging/building as graph edges.
2. **Counterfactual scaffold planning** — generate candidate vertical construction, re-run paths with candidates hypothetically present, keep the cheapest route-enabling intervention.
3. **Dynamic crowd-density cost** — overlay local attacker density onto terrain so routes spread instead of forming one blocked queue.
4. **Costed terrain transactions** — block edits are timed jobs with reach checks, explicit callbacks and failure states.
5. **Engineer cooperation** — followers wait for the route-builder; selected helpers increase build rate while other destructors reduce competing digging.
6. **Time + direction wave composition** — waves are overlapping time windows with weighted entity pools and attack sectors.
7. **Spawn fallback without silently changing the wave plan** — sector relaxation, retry and modern failure accounting prevent impossible terrain from hanging progression.
8. **Structural resistance separate from vanilla hardness** — path preference and destruction time are independently tunable, with adjacency bonuses for constructed defenses.
9. **Persistence by system state, not only entity presence** — Nexus, wave time and scaffold plans are persisted; the legacy scheduler replays elapsed time, while modern code adds explicit recovery/phase accounting.

See [TECHNICAL-KNOWLEDGE.md](TECHNICAL-KNOWLEDGE.md), [CODE-MAP.md](CODE-MAP.md) and [VERSION-PORTABILITY.md](VERSION-PORTABILITY.md).

## Important legacy limits / defects

- \`PathfinderIM.createPath\` is a **static synchronized singleton**, serializing all legacy path searches.
- \`quickFailDepth\` is carried through \`PathCreator\` but is not consumed by the pinned \`PathfinderIM\`.
- Async \`PathCreator\` overloads are empty stubs.
- The generic Netty \`PacketPipeline\` files are entirely commented out; actual old-version synchronization mainly uses DataWatcher plus Nexus \`S35PacketUpdateTileEntity\`.
- The distributed 1.1.2 binary contains a confirmed wave-pattern bug: the T2/T3 Zombie Pigman pattern objects are created, but tiers 2 and 3 are accidentally added to the T1 object. The T2/T3 mapped patterns therefore fall back to default tier 1.
- The source contains incomplete/WIP surfaces such as the flying navigator's commented ray-trace retina update; do not treat every class in the JAR as production-proven.

## Reconnaissance sources

Secondary/player-facing sources were checked before code interpretation:

- historical 1.7.10 guide: https://www.9minecraft.net/invasion-mod/
- community reference: https://wiki.9minecraft.net/invasion-mod/reference/
- old forum discussion: https://www.minecraftforum.net/forums/minecraft-java-edition/discussion/168055-minecraft-zombie-mob-invasion-mod
- current wiki: https://invmod.ketr.de/pages/waves.html
- current distribution/release page: https://www.curseforge.com/minecraft/mc-mods/invasion-mod-unofficial/files/9027990

These are discovery evidence, not source authority. A concrete disagreement is retained in [GAMEPLAY-FEATURE-MAP.md](GAMEPLAY-FEATURE-MAP.md): a guide describes a lower maximum construction-strength bonus than the legacy implementation can calculate from all six orthogonal neighbours.

## Current facet state

| Facet | State | Notes |
|---|---|---|
| artifact/source identity | MAPPED | exact uploaded JAR hash + pinned public source candidate |
| architecture/bootstrap | MAPPED | registries, Nexus, entity families and server/client split identified |
| Nexus/wave lifecycle | EVIDENCE_BACKED | source + bytecode/source identity checks |
| pathfinding/navigation | EVIDENCE_BACKED | legacy and ANCHOR mechanisms mapped |
| terrain destruction/building | EVIDENCE_BACKED | legacy and ANCHOR mechanisms mapped |
| attacker coordination | EVIDENCE_BACKED | density/scaffold/support mechanisms mapped |
| spawning | EVIDENCE_BACKED | legacy spawn geometry + ANCHOR recovery mapped |
| persistence | MAPPED | NBT/resume and modern persistence surfaces identified |
| networking | MAPPED | active legacy sync boundary identified |
| rendering/assets | INVENTORIED | render registry/animation surface found; not fully asset-mapped |
| performance | MAPPED (static) | clear hot-path/serialization findings; no runtime measurements |
| failure/repair history | PARTIAL | bounded high-value cases reviewed; structured CAS import deferred |
| license/provenance | MAPPED with unresolved conflict | see LICENSE-PROVENANCE.md |
| runtime behavior | NOT_ANALYZED | no Minecraft launch in this research pass |

## Scope boundary

No gameplay code was changed. No old or modern MOD runtime was launched. No performance number, binary/source equivalence claim, or whole-target COMPLETE claim is made. The deliverable is a source/JAR-backed recovery of the siege technologies and a 1.20.1 adaptation map.
