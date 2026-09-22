# Sinytra Connector — Analysis Workspace

## Queue

- Priority: **2 — after The Twilight Forest**
- Upstream: Sinytra/Connector
- Kind: loader compatibility / translation layer
- License: MIT
- Status: **QUEUED**

Connector is a high-value target because it translates foreign-loader Mod assumptions instead of requiring every Fabric Mod to be manually ported first.

## ANCHOR — Minecraft 1.20.1 + Forge

Upstream branch identified: **1.20.1**.

Queue-registration evidence currently shows:
- versionMc=1.20.1
- versionForge=47.4.6
- Connector branch version 1.0.0-beta.50
- upstream README describes Fabric Mods running on MinecraftForge
- Forgified Fabric API is used as the Fabric API replacement

Source Snapshot: **NOT_PINNED**. Pin an exact commit/release and hashes when full analysis begins.

## FRONTIER — current upstream

Upstream default branch identified: **26.1.x**.

Current upstream README/release metadata at registration time shows:
- Connector translates Fabric Mods to **NeoForge**
- **26.1.2** is the primary supported line
- **1.21.1** is long-term-support
- visible release: **3.0.0-beta.6+26.1.2**, published 2026-08-15
- current stack includes **Launchpad**, **Forgified Fabric API**, and Connector
- Connector exposes a transformer plugin API

Source Snapshot: **NOT_PINNED**. 'Latest' is a moving discovery pointer and must be converted to an immutable snapshot before evidence-backed claims.

## Full acquisition scope

When this target reaches the front of the queue, obtain complete local source checkouts for the pinned tracks and inventory the entire trees.

Analyze Connector plus dependency boundaries needed to understand the mechanism:
- Sinytra/Connector
- Sinytra/ForgifiedFabricAPI
- Sinytra/Launchpad for the current lineage
- Sinytra/ConnectorExtras where it demonstrates extension patterns
- relevant mapping / Mixin / loader APIs

Related repositories remain separate SourceSnapshots even when studied as one system.

## Questions to answer

### Boot / discovery
- How are Fabric Mods detected inside Forge/NeoForge?
- At what phase does translation begin?
- How are nested JARs and libraries handled?
- How are Fabric metadata and dependencies represented to the host loader?

### Mapping / bytecode
- Which namespace transitions occur?
- How are intermediary/named/host mappings resolved?
- What exactly is transformed in the input JAR?
- Which transforms happen ahead of class loading versus during loading?
- How are transformed artifacts cached and invalidated?

### Fabric semantics
- Which Fabric Loader assumptions are emulated?
- Which Fabric API surface is supplied by Forgified Fabric API?
- Which behavior is translated versus reimplemented?
- Where does compatibility become impossible?

### Mixins / patching
- How are Fabric Mixins made compatible?
- How are redirects, injectors, targets, priorities, descriptors, and mappings repaired?
- How do custom Mixin method patches work?
- How are Access Wideners / Class Tweakers mapped?

### Version delta
- What changed from 1.20.1 Forge to the current NeoForge lineage?
- Which concepts survived unchanged?
- Which components were rewritten due to loader/API divergence?
- Which FRONTIER improvements can be backported to 1.20.1 Forge?

## Expected outputs

OVERVIEW.md / CODE-MAP.md / TRANSFORMATION-PIPELINE.md / MAPPING-PIPELINE.md / MIXIN-COMPATIBILITY.md / FABRIC-API-BRIDGE.md / CLASSLOADING.md / CACHE-LIFECYCLE.md / PLUGIN-API.md / DEPENDENCY-MAP.md / COMPATIBILITY.md / VERSION-PORTABILITY.md / PERFORMANCE.md / LICENSE-PROVENANCE.md

No implementation conclusion here is verified yet; these are queue-registration facts and analysis requirements.
