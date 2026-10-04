# Yes Steve Model (YSM) — architecture / animation / renderer research

## Scope

- Target: **Yes Steve Model (YSM)**
- Primary adaptation anchor: Minecraft **1.20.1 + Forge**
- Distributed target: **2.6.5-forge+mc1.20.1**
- Main focus: model runtime, Molang, animation controllers, per-entity state, rendering, model distribution and integration seams
- Research status: **FOUNDATION_ARCHITECTURE_MAPPED**
- Whole-target status: **IN_PROGRESS / NOT COMPLETE**
- Research date: 2026-10-05

This workspace follows KNEEKURA's evidence rules: distributed artifact, release-line source candidate,
frontier source, community reconnaissance and comparative implementations are kept as separate tracks.

No Minecraft implementation code is changed here.

## DISTRIBUTED ANCHOR

Official Modrinth release:

- version: **2.6.5-forge+mc1.20.1**
- version ID: **Zqooxsd2**
- Minecraft: **1.20.1**
- loader: **Forge**
- client + server
- displayed size: **5.02 MB**
- displayed license: **ARR**

The exact distributed JAR SHA-256 has not been captured in this pass.
Therefore binary/source equivalence is **NOT_ESTABLISHED**.

## RELEASE-LINE SOURCE CANDIDATE

The now-public official Git history contains a strong 2.6.5 release-line candidate:

- repository: YesSteveModel/YesSteveModel
- revision: **f184edabd1b5115ce5a24cb6d155ba5a669f5ba6**
- tree: **da392147cdba57b734aa18e25674745291d7f24a**
- source-declared version: **2.6.5-forge+mc1.20.1**
- date: 2026-04-18
- tree: 1,888 entries / 1,513 blobs / 828 Java files / 669 main-resource blobs

History immediately around it is unusually useful:

1. e1413f7 raises mod_version from 2.6.4 to 2.6.5.
2. fb23351 fixes bundled Wine Fox model content while still declaring 2.6.5.
3. f184eda adds a Fast DEV build task and still declares 2.6.5.

This makes f184eda a strong **release-line source candidate**, but it is not asserted to be byte-for-byte
the source used for Modrinth version Zqooxsd2.

The historical tree has no root LICENSE file. The current public repository is Apache-2.0, but this
research does not silently project the current license backward onto the historical snapshot.

## FRONTIER SOURCE

Current official public reconstruction:

- repository: YesSteveModel/YesSteveModel
- branch: dev/1.20
- revision: **74c53b58b2f9b680a6c6dc5d5d41e7422fc000bb**
- tree: **6cb3ff6224bd19f76481dd59f40807e0c98da5ec**
- source-declared version: **3.0-dev-forge+mc1.20.1**
- license: Apache-2.0
- tree: 2,712 entries / 2,075 blobs / 1,140 Java files / 55 Proto files / 148 test blobs / 182 docs blobs

The FRONTIER is a substantial redesign and must not be silently attributed to the distributed 2.6.5
JAR. It is valuable because the maintainers now document ownership, lifecycle, network, animation,
model-management, JNI and renderer boundaries explicitly.

## Main result

YSM is not merely a replacement player renderer.

The recoverable architecture is closer to:

~~~text
Minecraft Entity state
        |
        v
per-entity state tracker + Molang context
        |
        v
coded / Bedrock / hybrid controllers
        |
        v
bone snapshot / flattened bone state
        |
        +------ event / sound / side-effect queues
        |
        v
native-capable geometry renderer
        |
        v
Minecraft VertexConsumer / draw pipeline
~~~

On the 2.6.5 release line, Java already owns the semantic animation state and feeds flattened bone
state through a JNI renderer boundary. The 3.0 frontier makes that separation even more explicit:
Java owns model identity, lifecycle, Molang/controllers and publication, while native code is treated
as a bounded capability layer for codec/render work.

## Highest-value reusable technologies

1. **Per-entity animation runtime** rather than model-global mutable animation state.
2. **Coded + Bedrock + hybrid controller polymorphism** behind a shared controller contract.
3. **Molang as a state/query language**, with explicit queued side-effect execution.
4. **Visibility/distance-aware animation throttling** for remote or culled entities.
5. **Flattened bone-state buffers** between semantic animation and hot rendering.
6. **Named locator/bone groups** for hands, head, equipment, passengers and first-person anchors.
7. **Async animation schedule / wait barrier** separated from the render commit.
8. **Java semantic layer / native geometry layer separation**.
9. FRONTIER: **Bake -> Extract -> Render** as explicit renderer stages.
10. FRONTIER: **exact-connection session ownership** and separation of catalog publication from model-content activation.
11. **Integration adapters as translators**, demonstrated by Touhou Little Maid, rather than giving every compatibility target a second animation engine.
12. Secondary technique: **semantic structural bytecode matching** from YSM Mapping API for version-resilient external integration.

## Important limits

- The distributed 2.6.5 JAR has not been hashed here.
- Public release-line source candidate equivalence to the distributed JAR is not proven.
- Native internal implementation of protected 2.6.5 binaries is not analyzed.
- Encrypted-model protection is not bypassed.
- Reddit / user reports are reconnaissance only.
- Runtime performance and correctness have not yet been measured in KNEEKURA LAB.
- Current 3.0-dev architecture contains known unresolved concurrency, render-context and end-to-end validation gaps documented by its own maintainers.

## Files

- [ARCHITECTURE-RESEARCH-2026-10-05.md](ARCHITECTURE-RESEARCH-2026-10-05.md)
- [FAILURE-REPAIR-HISTORY.md](FAILURE-REPAIR-HISTORY.md)
- [RECONNAISSANCE-2026-10-05.md](RECONNAISSANCE-2026-10-05.md)
- [SOURCE-INVENTORY-2026-10-05.json](SOURCE-INVENTORY-2026-10-05.json)

## Research boundary

KNEEKURA does not need to defeat YSM's historical protection mechanisms to recover useful
engineering. The public source/history already exposes the model/animation/controller/integration
architecture. Where 2.6.5 native internals remain opaque, use documented Java/JNI contracts and
bounded runtime observation rather than protection bypass.
