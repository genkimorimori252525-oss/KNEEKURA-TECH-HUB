# Connector dependencies, API ownership and source provenance

This is a static source-boundary study. Declared coordinates are not a resolved
classpath, and matching a release tag to source does not establish compiled-class
equivalence. No build, wrapper, game or dependency binary was executed.

## 1. The bridge is distributed across components

| Component | Responsibility established in this pass | What it does not establish |
|---|---|---|
| Connector | Finds/adapts foreign metadata and bytecode; coordinates host loading, targeted semantic patches and Mixin compatibility | A general conversion of every Fabric/Forge API or arbitrary incompatible MOD |
| Forgified Fabric Loader | Connector calls its metadata, resolver, environment, MOD-list and entrypoint APIs | Exact implementation-source association for the declared loader builds remains unresolved here |
| Forgified Fabric API (FFAPI) | Supplies Fabric-facing API classes and host-adapted implementations/hooks | API compatibility claims do not cover internal implementation classes or all loader-specific assumptions |
| Adapter definition/data/runtime or core/runtime | Connector consumes patch definitions, generated adaptation data, analysis/audit and runtime helpers | Adapter algorithms and exact built data are not proven solely by Connector's call sites |
| Mapping/renaming libraries, Mixin, access tooling | Implement the bytecode/name/access mechanisms Connector orchestrates | Successful construction of a transformer is not successful application to a target MOD |
| Launchpad, FRONTIER only | Provides the pinned NeoForge Fabric-convention metadata, nested-JAR, access and lifecycle integration described in the frontier report | A drop-in Forge 1.20.1 dependency or replacement for Connector's incompatibility repairs |
| Connector Extras | Optional third-party integration layer in release declarations | Required for every MOD, or proven compatible with the current candidate |

Ownership is traceable in [ANCHOR dependencies](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/build.gradle.kts#L317-L346),
[FRONTIER host dependencies](https://github.com/Sinytra/Connector/blob/c84a96a3c04aa4c5253032c338434de5329be08a/build.gradle.kts#L103-L133)
and [transformer dependencies](https://github.com/Sinytra/Connector/blob/c84a96a3c04aa4c5253032c338434de5329be08a/transformer/build.gradle.kts#L51-L69).

## 2. Exact declarations and acquisition boundary

ANCHOR values come from [gradle.properties](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/gradle.properties#L6-L20)
and its dependency block. FRONTIER module coordinates and versions come from its
[version catalog](https://github.com/Sinytra/Connector/blob/c84a96a3c04aa4c5253032c338434de5329be08a/gradle/libs.versions.toml#L1-L26).

| Boundary | ANCHOR declaration | FRONTIER declaration | Source association in this pass |
|---|---|---|---|
| Host | Forge 1.20.1-47.4.6 / Java 17 | NeoForge 26.1.2.95 / Java 25 | Connector-owned use sites read; full resolved host closure unacquired |
| Loader fork | dev.su5ed.sinytra:fabric-loader:2.7.15+0.19.3+1.20.1 | org.sinytra:forgified-fabric-loader:2.5.85+0.19.3+26.1.2 | Same-named exact version tags returned 404; generic tags 2.7/2.5 are not equivalent |
| FFAPI | dev.su5ed.sinytra.fabric-api:fabric-api:0.92.0+1.11.5+1.20.1 | org.sinytra.forgified-fabric-api:forgified-fabric-api:0.155.2+26.1.2+3.5.0 | Exact tags resolved; selected base/lifecycle sources captured separately |
| Adapter | definition 1.11.67-1.20.1; data 1.11.55-1.20.1-20240428.153904; runtime 1.0.0+1.20.1 | core 2.0.54+26.1.2; runtime 1.0.0+26.1.2 | Exact source/data association unresolved; generic Adapter tag 1.11 is insufficient |
| Renaming | org.sinytra:ForgeAutoRenamingTool:1.0.14; srgutils 0.5.4 | org.sinytra:AutoRenamingTool:2.0.23 | Call sites only, no full exact dependency-source/compiled closure |
| Access | net.fabricmc:access-widener:2.1.0 | net.fabricmc:class-tweaker:0.3.0-beta.2 | Connector/Launchpad conversion use sites are available; external library internals are not fully acquired |
| Mixin | org.sinytra:sponge-mixin:0.12.11+mixin.0.8.5; mixin-transmogrifier 0.4.7+1.20.1; MixinExtras 0.3.2 | transformer declares net.fabricmc:sponge-mixin:0.15.2+mixin.0.8.7 | Declared roles only; no runtime-selected version assertion |
| Launchpad | Not a declared ANCHOR dependency | org.sinytra.launchpad:launchpad:1.9.1+26.1.2 | Exact tag and full 67-file source tree captured |
| Extras | Development runtime uses CurseMaven file 5027683; release metadata optional | Release metadata optional | No exact Extras source snapshot acquired in this pass |

The ANCHOR also explicitly shades SAT4J core/PB 2.3.6. FRONTIER's transformer
declares FML loader 11.0.13, Mojang logging 1.2.7, Log4j BOM 2.24.3, annotations
13.0 and runner-only Picocli 4.7.7. Those are declarations, not a complete
transitive closure. ANCHOR build plugins include version ranges and `+` selectors;
both tracks permit `mavenLocal()`. A fixed Connector commit alone therefore does
not make a reproducible resolved build.

The public [dependency evidence inventory](DEPENDENCY-SOURCE-EVIDENCE-2026-10-01.json)
records the separate capture identities:

- ANCHOR FFAPI tag `0.92.0+1.11.5+1.20.1` →
  [6ba6353854d0138d5c6a0ca2a6c1eb00ab8a6a6f](https://github.com/Sinytra/ForgifiedFabricAPI/tree/6ba6353854d0138d5c6a0ca2a6c1eb00ab8a6a6f):
  58 selected files from a 1,796-file tree
- FRONTIER FFAPI tag `0.155.2+26.1.2+3.5.0` →
  [6b6e10ac2ccea496b6dfbde891be6ba50e2bfe57](https://github.com/Sinytra/ForgifiedFabricAPI/tree/6b6e10ac2ccea496b6dfbde891be6ba50e2bfe57):
  72 selected files from a 2,858-file tree
- FRONTIER Launchpad tag `1.9.1+26.1.2` →
  [a1d958c952f5ffd38daa8671354e9b8fdf30f9c9](https://github.com/Sinytra/Launchpad/tree/a1d958c952f5ffd38daa8671354e9b8fdf30f9c9):
  all 67 files acquired; full byte inventory is not a full dependency-system proof

All 197 newly selected dependency files have size/Git-blob/SHA-256 checks and
272 CAS byte-readback pages. These sources supplement, rather than mutate, the
earlier Connector and U06 COMPARATIVE profiles. FFAPI selection covers base and
lifecycle main/client sources/resources plus top-level provenance files; other
modules are explicitly unacquired. Exact loader/Adapter source tags and Maven
POM retrieval were unavailable through the attempted read paths; this is not a
claim that no matching source or artifact exists anywhere.

## 3. Concrete API example: an event needs a real implementation and trigger

Consider a Fabric MOD registering a server-tick callback. This is an illustrative
source path, not an executed MOD fixture:

1. In pinned ANCHOR FFAPI, `ServerTickEvents.END_SERVER_TICK` is an Event created
   through EventFactory. Its invoker loops over registered callbacks.
   [API source](https://github.com/Sinytra/ForgifiedFabricAPI/blob/6ba6353854d0138d5c6a0ca2a6c1eb00ab8a6a6f/fabric-lifecycle-events-v1/src/main/java/net/fabricmc/fabric/api/event/lifecycle/v1/ServerTickEvents.java#L29-L45)
2. EventFactory delegates to EventFactoryImpl, which constructs an ArrayBackedEvent.
   Registration retains phase ordering and rebuilds the invoker. That behavior is
   implemented by FFAPI classes; it is not fabricated by renaming the MOD.
   [Factory](https://github.com/Sinytra/ForgifiedFabricAPI/blob/6ba6353854d0138d5c6a0ca2a6c1eb00ab8a6a6f/fabric-api-base/src/main/java/net/fabricmc/fabric/api/event/EventFactory.java#L43-L76),
   [implementation](https://github.com/Sinytra/ForgifiedFabricAPI/blob/6ba6353854d0138d5c6a0ca2a6c1eb00ab8a6a6f/fabric-api-base/src/main/java/net/fabricmc/fabric/impl/base/event/EventFactoryImpl.java#L36-L50),
   [registration](https://github.com/Sinytra/ForgifiedFabricAPI/blob/6ba6353854d0138d5c6a0ca2a6c1eb00ab8a6a6f/fabric-api-base/src/main/java/net/fabricmc/fabric/impl/base/event/ArrayBackedEvent.java#L47-L124)
3. FFAPI's own MinecraftServerMixin injects at the tail of `tick` and invokes the
   event. The trigger is therefore a concrete game hook. It is inaccurate to
   describe every FFAPI event as a universal Fabric-event→Forge-event-bus mapping.
   [Trigger](https://github.com/Sinytra/ForgifiedFabricAPI/blob/6ba6353854d0138d5c6a0ca2a6c1eb00ab8a6a6f/fabric-lifecycle-events-v1/src/main/java/net/fabricmc/fabric/mixin/event/lifecycle/MinecraftServerMixin.java#L66-L74)

This establishes the selected source mechanism. Whether the correct FFAPI binary,
Mixin application and callback are active in a particular pack still requires
runtime evidence. The earlier real Clumps COMPARATIVE fixture also reaches the
EventFactory API, but it remains beta.49 evidence and is not relabeled beta.50.

### A portability detail already visible in the dependencies

ANCHOR FFAPI's lifecycle implementation is an FML `@Mod` constructor that invokes
client setup conditionally; its source build uses Yarn names and declares Forge
47.2.6 plus loader fork 2.6.0+0.15.0+1.20.1, distinct from Connector's own declared
versions. FRONTIER's corresponding implementation is a Fabric `ModInitializer`
whose `onInitialize` is supplied through the newer loader/lifecycle arrangement.
These are concrete source differences, not interchangeable artifacts.
[ANCHOR initializer](https://github.com/Sinytra/ForgifiedFabricAPI/blob/6ba6353854d0138d5c6a0ca2a6c1eb00ab8a6a6f/fabric-lifecycle-events-v1/src/main/java/net/fabricmc/fabric/impl/event/lifecycle/LifecycleEventsImpl.java#L33-L70),
[ANCHOR declarations](https://github.com/Sinytra/ForgifiedFabricAPI/blob/6ba6353854d0138d5c6a0ca2a6c1eb00ab8a6a6f/gradle.properties),
[FRONTIER initializer](https://github.com/Sinytra/ForgifiedFabricAPI/blob/6b6e10ac2ccea496b6dfbde891be6ba50e2bfe57/fabric-lifecycle-events-v1/src/main/java/net/fabricmc/fabric/impl/event/lifecycle/LifecycleEventsImpl.java#L23-L61)

## 4. Packaging is part of compatibility

ANCHOR deliberately shades the loader into the service layer, relocates selected
libraries, embeds a separate mod JAR, and synthesizes a dummy loader JAR with
version 999.999.999 to influence Jar-in-Jar selection. This is source-declared
classloader/conflict management, not proof of the runtime winner. Its Maven POM
publication code removes dependency metadata, so a POM alone cannot reconstruct
the packaged dependency closure.
[Packaging](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/build.gradle.kts#L81-L178),
[POM handling](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/build.gradle.kts#L449-L458)

FRONTIER shades a transformer subproject and selected libraries, separately
Jar-in-Jar packages the mod and Adapter runtime, explicitly depends on Launchpad,
and excludes the loader module from its FFAPI dependency edges. Transformer
compilation separately declares that loader. This arrangement demonstrates why
the role, phase and selected classloader matter as much as the artifact name.
[Host packaging/dependencies](https://github.com/Sinytra/Connector/blob/c84a96a3c04aa4c5253032c338434de5329be08a/build.gradle.kts#L103-L180),
[transformer dependency boundary](https://github.com/Sinytra/Connector/blob/c84a96a3c04aa4c5253032c338434de5329be08a/transformer/build.gradle.kts#L51-L69)

## 5. License/provenance observations, not a redistribution approval

- Connector: root MIT at both pinned source revisions; explicit file-level notices
  also exist (for example ANCHOR BootstrapMixin carries Apache-2.0). Root metadata
  must not erase a selected file's header
- Selected FFAPI files: Apache-2.0 root license and corresponding source headers
- Launchpad: source SPDX declares **GPL-3.0-only WITH Classpath-exception-2.0**;
  its README and license text include the exception. Do not infer MIT from the
  surrounding Connector project
- Unacquired dependencies: exact license/notice completeness remains unresolved

[Connector license](https://github.com/Sinytra/Connector/blob/7f68ac02291fde986119a3f5cab85436bed5c350/LICENSE),
[FFAPI license](https://github.com/Sinytra/ForgifiedFabricAPI/blob/6ba6353854d0138d5c6a0ca2a6c1eb00ab8a6a6f/LICENSE),
[Launchpad declaration](https://github.com/Sinytra/Launchpad/blob/a1d958c952f5ffd38daa8671354e9b8fdf30f9c9/src/main/java/org/sinytra/launchpad/service/FabricModJsonFileReader.java#L1-L4),
[Launchpad license](https://github.com/Sinytra/Launchpad/blob/a1d958c952f5ffd38daa8671354e9b8fdf30f9c9/LICENSE)

The published deliverables contain derived findings, source hashes and locators.
They contain no raw dependency source/JARs and do not authorize copying or
redistributing implementations without checking the applicable notices and terms.
