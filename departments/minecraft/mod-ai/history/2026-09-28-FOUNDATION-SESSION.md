# 2026-09-28 Session Record — Minecraft MOD-making AI foundation

> Historical record, not a replacement for the current specification.
>
> This file preserves **why the Minecraft department was shaped this way, what was implemented and verified on 2026-09-28, what was deliberately not added, and where a future agent should resume**. Current normative behavior lives in the linked design/spec/status documents.

## 0. Session identity

- Date: **2026-09-28 (JST)**
- Repository: `genkimorimori252525-oss/KNEEKURA-TECH-HUB`
- Design: PR #72, Minecraft MOD-making AI environment v1.4
- Implementation: PR #73, branch `jolly/minecraft-mod-ai-impl-2026-09-28`
- Implementation head when this record was requested: `0b0eec5b94776166d88e0ba9fc08a0ac322cfb7d`
- Verified executable head for the real live Forge checkpoint: `3fa14453327e7992231e3d479ac1d1eebbd96b3c`
- Primary target: **Minecraft 1.20.1 / Forge 47.4.x / Java 17**
- Whole product status at session close: **IN_PROGRESS**
- Verified slice: **server-side build → resolved inputs/source intelligence → managed world → authenticated observation/command → GameTest completion**

## 1. The real purpose of KNEEKURA TECH HUB

The Minecraft department is **not primarily a documentation mirror or a generic MOD encyclopedia**.

Its core purpose is to build an environment in which an AI can make Minecraft MODs more like an experienced human MOD developer:

```text
problem / desired behavior
        ↓
inspect exact Minecraft + Forge + dependency environment
        ↓
read source + bytecode + mappings + other MOD implementations
        ↓
read the history of failures and repairs
        ↓
design / edit the MOD
        ↓
compile / test / launch when explicitly authorized
        ↓
observe the real game
        ↓
compare result with the intended behavior
        ↓
repair and preserve the new lesson
```

The Hub therefore exists to give the MOD-making AI **investigation ability, evidence, prior engineering experience and verification loops**, not merely more memorized API names.

Other MODs are analyzed because they are engineering evidence. Their architecture, algorithms, compatibility techniques, failure modes, repairs and trade-offs become reusable research material for future MOD creation.

## 2. How the idea developed in this session

### 2.1 Minecraft source question → Source Intelligence

The session began from the basic question: how are Java Edition MODs possible if Mojang does not simply publish a normal source repository?

That led to the explicit recognition of the practical development stack:

- compiled Minecraft classes,
- decompilation,
- Mojang/SRG/intermediary/Yarn-style mappings,
- Forge/Fabric/NeoForge loader APIs,
- Mixins / Access Transformers / Access Wideners,
- and runtime transformation.

From that came the **Minecraft Source Intelligence Layer** idea: do not store only a pile of decompiled files; preserve the exact version/environment and make classes, methods, fields, inheritance, references, intervention points and original bytes queryable.

### 2.2 Sinytra Connector → compatibility research

Sinytra Connector was selected as a major future research target because it exposes loader-compatibility engineering:

- Fabric MOD discovery on Forge/NeoForge,
- metadata translation,
- mapping/remapping,
- Mixin adaptation,
- Access Widener conversion,
- Forgified Fabric API boundaries,
- transformed artifact handling and classloading.

The upstream repository link is retained as a research source. The existing analysis queue remains:

1. **Twilight Forest first**
2. **Sinytra Connector next**

Connector is a technology source, not a reason to make NeoForge the primary development target. Forge 1.20.1 remains the ANCHOR environment.

### 2.3 Human MOD-developer workflow → AI workflow

We examined the workflow that real MOD developers repeatedly rely on:

- Minecraft/Forge source,
- other open-source MODs,
- GitHub Issues / PRs / commits / diffs,
- Forge documentation and practical support material,
- mappings such as Parchment,
- Mixin documentation and advanced injection patterns,
- runtime logs and observation,
- GameTest and actual game execution.

The conclusion was not to copy any one existing MCP/repository wholesale. Existing projects were treated as **design references**. Good ideas were absorbed only where they improved the KNEEKURA objective.

The most valuable borrowed ideas were:

- full-classpath search,
- source + bytecode dual truth,
- Mixin/AT/AW intervention discovery,
- exact mapping identities,
- live runtime observation,
- and executable game tests.

## 3. Design principles fixed on 2026-09-28

### 3.1 Forge 1.20.1 is the ANCHOR, not the only source of knowledge

Newer/Fabric/NeoForge implementations may contain better techniques. They can be analyzed as FRONTIER/COMPARATIVE tracks, but they must not silently become claims about Forge 1.20.1.

A reusable technique should separate:

- invariant concept,
- ANCHOR implementation,
- FRONTIER implementation,
- mapping/API changes,
- dependencies,
- backport feasibility,
- semantic risks.

### 3.2 Source and bytecode are complementary

Decompiler output is readable but not always sufficient for Mixin and exact JVM behavior. Therefore the AI environment preserves:

- source/decompiled source,
- original class bytes,
- JVM descriptors,
- mappings,
- disassembly,
- class/member identity and provenance.

### 3.3 Unknown is a valid result

Missing dependencies, ambiguous mappings, unexecuted Mixin plugins, unavailable evidence or incomplete history must remain visible as UNKNOWN/PARTIAL/NOT_RUN.

The system must not improve apparent completeness by inventing certainty.

### 3.4 Evidence types are not one universal quality score

Source code, bytecode, maintainer documentation, Issue discussion, runtime experiments and community reports answer different questions.

The design rejected a simplistic global ranking such as “source always beats everything.” Instead, the answer must use the evidence appropriate to the claim being made.

### 3.5 No automatic canonical promotion

AI/scanners may create research observations and evidence candidates. They do not silently turn those into validated canonical knowledge.

Existing KNEEKURA Source → SourceSnapshot → Evidence → Claim governance remains authoritative.

### 3.6 Do not expand infrastructure without a demonstrated need

Explicitly rejected as default requirements:

- a new graph database,
- a giant Vector DB/RAG layer,
- all Minecraft/loader versions at once,
- a large Web UI,
- mandatory IDE/MCP dependence,
- another autonomous agent/scheduler/database,
- an unbounded GitHub-history crawler.

After the basic loop works, new capabilities should be added because a real MOD-making task exposes a concrete gap.

## 4. Failure / Repair History became a required MOD-analysis facet

A key decision in this session was that MOD analysis must not inspect only the final working code.

For a selected, bounded history scope, the analyst should also inspect:

```text
Issue / report
    ↓
symptom
    ↓
trigger conditions
    ↓
root cause or competing explanations
    ↓
affected code
    ↓
PR / repair diff / fix commit
    ↓
before-after behavior
    ↓
reproduction / verification status
    ↓
narrow reusable lesson
```

This is now a formal analysis surface in:

- [../ANALYSIS-SPEC-v1.md](../ANALYSIS-SPEC-v1.md)
- [../FAILURE-REPAIR-HISTORY-v1.md](../FAILURE-REPAIR-HISTORY-v1.md)

The same structured record is intended for two directions:

1. **UPSTREAM** — learn from failures and repairs in other MODs.
2. **OWN_DEVELOPMENT** — preserve failures encountered while KNEEKURA creates MODs.

Important boundaries:

- closed Issue ≠ verified fix,
- merged PR ≠ reproduced root cause,
- fix commit parent ≠ necessarily bug-introducing commit,
- analyst inference must remain inference,
- “no cases found in this search scope” ≠ “this MOD has no bugs.”

A CAS-backed history importer/query surface was implemented so these records can remain evidence-linked and searchable without creating another canonical database.

## 5. What was implemented by session close

The MOD-AI environment now contains connected implementations for:

### Source / environment intelligence

- explicit local source/resource/JAR capture,
- immutable content-addressed storage,
- exact root/scope/namespace/stage/track metadata,
- full source reads rather than preview-only knowledge,
- actual ForgeGradle resolved-input export/import,
- workspace/config/source-generation fingerprints,
- Java/toolchain identity,
- exact source and class-document search.

### Source + bytecode + mappings

- JDK `javap` preparation,
- owner/member/JVM descriptor lookup,
- Tiny / TSRG / ProGuard mapping lookup,
- explicit namespace aliases,
- Parchment treated as annotation rather than an executable namespace,
- pinned provider adapters for decompile/remap operations.

### MOD intervention intelligence

- class hierarchy/static relation candidates,
- Mixin declaration/injection candidates,
- Access Widener records,
- Access Transformer records,
- Fabric metadata / mixin-config candidates,
- unresolved dynamic plugin/refmap/runtime transformations kept visible.

This does **not** claim a perfect dynamic call graph or automatic compatibility verdict.

### Existing Knowledge Core bridge

- exact-context guidance can call the existing Core,
- raw research remains available if the Core is unavailable,
- staging emits reviewable Source/Snapshot/Evidence/NEW observations,
- no automatic Claim promotion.

### Execution and observation

- explicit registered Gradle execution,
- fresh managed test-world copies,
- same-source compile receipts,
- run contracts bound to source/build/world/assertion identity,
- development-only Forge observer,
- authenticated loopback transport,
- bounded server entity/block/log observation,
- separate explicit command/mutation route,
- GameTest result ledger,
- idempotent request handling / no blind write retry.

### Failure / Repair History

- mandatory analysis workflow specification,
- structured history records,
- anchored evidence verification,
- exact track/environment filters,
- searchable symptoms/causes/repairs/lessons,
- explicit UNKNOWN / AUTHOR_CLAIM / INFERENCE / experiment distinctions.

## 6. Actual verification reached on 2026-09-28

Detailed evidence is in:

- [HOSTED-VERIFICATION-2026-09-28.md](../mod-ai/HOSTED-VERIFICATION-2026-09-28.md)
- [LIVE-VERIFICATION-2026-09-28.md](../mod-ai/LIVE-VERIFICATION-2026-09-28.md)
- [IMPLEMENTATION-STATUS.md](../mod-ai/IMPLEMENTATION-STATUS.md)
- [verification/live-2026-09-28.json](../mod-ai/verification/live-2026-09-28.json)

### Repository tests

Current verified executable checkpoint:

- **597 passed**
- **0 failed**
- **0 errors**
- **0 skipped**
- 8 pre-existing warnings

The run included configured PostgreSQL integration tests.

### Real Forge build and dependency/source pipeline

Using Minecraft 1.20.1 / Forge 47.4.6 / Java 17:

- actual Forge MDK compilation succeeded,
- JAR / reobf path succeeded,
- ForgeGradle dependency resolution/export succeeded,
- importer/capture/index/search/full-source-read succeeded.

One recorded reference run handled 205 scoped artifact entries and 37,933 captured documents. These numbers are not “205 different MODs” and do not imply complete runtime coverage.

### Real game/server loop

A disposable integration MOD was actually launched through the production adapter path.

Verified:

- managed fresh world,
- source/build/world/session identity binding,
- authenticated handshake,
- wrong-token rejection,
- registered command execution,
- successful command whose numeric result is 0,
- duplicate scoreboard command did not execute twice,
- duplicate summon request reused the same receipt,
- exact summoned entity observed by UUID,
- signed same-run GameTest completion.

Exact GameTest results:

| Test | Required | Result |
|---|---:|---|
| `bridge` | yes | **PASS** |
| `knownbad` | no | **FAIL** |

The optional failure was intentionally preserved as a negative control. It was not hidden to make the run appear greener.

### Real failures discovered while validating the environment

Two integration mistakes were reproduced and repaired without weakening the production guards:

1. The test fixture assumed GameTest world/seed defaults that the actual Forge Main path did not guarantee. The fix was to make the disposable world configuration explicit, not to remove the seed/path checks.
2. The test fixture counted ambient pigs inside a truncated entity page. The fix was to observe the exact test entity UUID, not to remove resource limits or infer global absence/count from a capped list.

The command result seam was also repaired: command success now uses Brigadier callbacks rather than assuming `result > 0`. A successful zero-valued command is valid; unconfirmed/contradictory completion remains UNKNOWN.

These incidents are examples of the development philosophy the Failure/Repair History is meant to preserve.

## 7. What is deliberately *not* claimed complete

At session close, the following remain unproven or incomplete:

1. Actual Vineflower and tiny-remapper provider execution against real relevant MOD inputs/mappings/classpaths.
2. The new Core caller/staging path exercised end-to-end with actual research records and applicable Core data.
3. Client screenshot/render/network assertions and general rendering correctness.
4. Windows-specific process/execution behavior.
5. Production MOD correctness and performance.
6. One full real MOD-editing cycle using the complete AI environment.
7. U01-U06 / A01-A24 product acceptance as a whole.
8. Actual upstream Failure/Repair History investigation for Twilight Forest.
9. Actual upstream Failure/Repair History investigation for Sinytra Connector.

The server integration probe proves the adapter loop, not the entire MOD-making AI product.

## 8. Resume order

A future agent should **not restart this project from the design phase**.

Read, in order:

1. this historical record,
2. [IMPLEMENTATION-STATUS.md](../mod-ai/IMPLEMENTATION-STATUS.md),
3. [LIVE-VERIFICATION-2026-09-28.md](../mod-ai/LIVE-VERIFICATION-2026-09-28.md),
4. [../ANALYSIS-SPEC-v1.md](../ANALYSIS-SPEC-v1.md),
5. [../FAILURE-REPAIR-HISTORY-v1.md](../FAILURE-REPAIR-HISTORY-v1.md),
6. PR #73 current head and checks.

Do not reapply the old conversation ZIPs. The connected implementation is already in the PR branch.

### Recommended next technical gaps

- verify real external decompiler/remapper providers,
- verify the new Core caller path with real research records,
- run one real MOD-editing task from investigation through implementation and game verification,
- add only the capabilities that real task proves are missing,
- exercise client-side observation only when the chosen MOD task actually requires it.

### MOD-analysis queue

- Continue **Twilight Forest** first, adding the new Failure/Repair History facet without rewriting older completed evidence.
- Analyze **Sinytra Connector** after Twilight Forest, including compatibility pipeline and Failure/Repair History.

## 9. CI / runner note from this session

During this session, the repository was temporarily public and verification used **GitHub-hosted standard runners**.

The home/self-hosted runner was deliberately not used while public.

If a future session operates with the repository private and an authorized self-hosted runner is available, it may be used under the normal execution controls. Repository visibility changes are not part of this project record or an agent-owned action.

## 10. Closing principle

The desired end state is not “an AI that has read many Minecraft files.”

It is:

> **an AI that can investigate an exact MOD environment, learn from both successful implementations and historical failures, make a change, verify what actually happened in Minecraft, and retain that engineering experience with traceable evidence.**

By the end of 2026-09-28, the server-side investigation/execution/observation loop had been demonstrated in a real Forge environment. The remaining work should be driven by real MOD-making tasks and real analysis gaps, not by adding infrastructure for its own sake.
