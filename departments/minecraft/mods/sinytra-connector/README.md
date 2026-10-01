# Sinytra Connector — Analysis Workspace

## Current entry point

**IN_PROGRESS: source/reconnaissance/history continuation. Runtime compatibility remains UNKNOWN.**

Read [the current plan and findings](ANALYSIS-CONTINUATION-2026-10-01.md), then
[the practical MOD-analysis workflow](../../ANALYSIS-WORKFLOW.md). The historical
[DESIGN-REFERENCE.json](DESIGN-REFERENCE.json) remains a queue-registration record,
not the current acquisition state. Earlier [U06 split-track static acceptance](../../mod-ai/verification/connector-static-2026-09-30/README.md) is preserved unchanged.

## Original queue and target

- Priority: **2 — after The Twilight Forest**
- Upstream: Sinytra/Connector
- Kind: loader compatibility / translation layer
- License: MIT
- Original queue status: **QUEUED**; resumed 2026-10-01 UTC at the user's request
- Current scope: both Connector source trees acquired/inventoried; five source-scoped feature leads mapped; bounded failure/repair review; whole-target analysis incomplete

Connector is a high-value target because it translates foreign-loader Mod assumptions instead of requiring every Fabric Mod to be manually ported first.

## ANCHOR — Minecraft 1.20.1 + Forge

Upstream branch identified: **1.20.1**.

Pinned ANCHOR source declares:
- versionMc=1.20.1
- versionForge=47.4.6
- Connector branch version 1.0.0-beta.50
- upstream README describes Fabric Mods running on MinecraftForge
- Forgified Fabric API is used as the Fabric API replacement

Source revision: **7f68ac02291fde986119a3f5cab85436bed5c350**. All 141 repository files are acquired and hash-verified. Matching beta.50 binary, resolved build/runtime dependency closure and source-binary equivalence remain unestablished. See the [inventory](SOURCE-INVENTORY-2026-10-01.json) and [separate CAS identities](STATIC-VERIFICATION-2026-10-01.json).

## FRONTIER — current upstream

Upstream default branch identified: **26.1.x**.

The historical registration identified the following lineage; the selected official release is now pinned:
- Connector translates Fabric Mods to **NeoForge**
- **26.1.2** is the primary supported line
- **1.21.1** is long-term-support
- visible release: **3.0.0-beta.6+26.1.2**, published 2026-08-15
- current stack includes **Launchpad**, **Forgified Fabric API**, and Connector
- Connector exposes a transformer plugin API

Source revision: **c84a96a3c04aa4c5253032c338434de5329be08a**, tagged **3.0.0-beta.6+26.1.2**. All 131 repository files are acquired and hash-verified in a separate FRONTIER profile. Declared NeoForge 26.1.2.95 / Java 25 and dependency versions are source settings, not an observed runtime. Current website/wiki text remains a mutable discovery source.

## Full acquisition scope

Both pinned Connector source trees have now been acquired and inventoried in full. Complete the remaining semantic analysis and separate dependency snapshots before claiming whole-target completion.

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

These expected outputs remain the whole-target plan. The current continuation adds bounded, source-backed findings and a [failure/repair record](FAILURE-REPAIR-HISTORY.md); it does not establish complete implementation coverage or runtime compatibility.
