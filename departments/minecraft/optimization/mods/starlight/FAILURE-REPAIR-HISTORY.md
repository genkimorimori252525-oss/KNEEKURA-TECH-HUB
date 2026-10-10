# Starlight — exact JAR 1.1.2 Forge 1.20.1 compatibility reports, bounded history

**Track pinned:** `PaperMC/Starlight@1cda73ccfa016e35d7cf0ed848bc8786f5881740`, source version 1.1.2 dev MC 1.20 Forge 46; the user basename is `starlight-1.1.2+forge.1cda73c.jar`. **No binary SHA / direct runtime**.

## STAR-191 -> STAR-197 — Forge BlockEntity off-thread access deadlock

- [#191](https://github.com/PaperMC/Starlight/issues/191): reporter **Minecraft 1.20.1, Forge 47.1.3, Starlight 1.1.2+forge.1cda73c, Framed Blocks 9.0.3**, crashed server, removed Starlight mitigated. Maintainer closed as duplicate of [#197](https://github.com/PaperMC/Starlight/issues/197).
- **#197 (OPEN)** maintainer [causal explanation](https://github.com/PaperMC/Starlight/issues/197#issuecomment-1765348876): Forge `IForgeBlockGetter#getExistingBlockEntity` invokes `hasChunk`/getChunk without guarding off-main thread; off-thread getChunk can enqueue a request to the main thread and wait for FULL while chunk/lighting operations hold/work through opposite dependency. Vanilla `Level#getBlockEntity` includes protective off-thread behavior. The presence of extra Starlight edge checks makes the path more likely visible in particular modded blocks; maintainer says can't fix entirely inside Starlight.
- **No corresponding Starlight repair commit verified**. This is **maintainer diagnosis with code excerpt**, not a completed repair. Tests on exact modpack/Forge build NOT_RUN.
- Lesson: never perform blocking chunk fetch from lighting/worldgen workers; use pre-validated chunk data or enforce main-thread handoff and deny off-thread BlockEntity lookup.

## STAR-186 — Create elevator/windmill issue, related but not proven identical root cause

[Issue #186](https://github.com/PaperMC/Starlight/issues/186) reporter(s) on **exact user JAR** with Forge 47.1.0/Create 0.5.1.d invoke elevator/windmill and observe crash in lighting. Could be associated with #197-style block entity/off-thread light logic, but **no issue-linked patch and no proven same root**. Distinct from unrelated Fabric Create engine report; both are **user reports**, not checked launch traces. Closed 2023-10-17 without inspected repair.

## Source maintenance and performance honesty

1.1.2 source released June 2023; later Forge `forge` branch 1.1.3 / 1.20.2 changed loader/classloader behavior. TechnicalDetails 1.20 notice warns previous performance comparisons against vanilla before 1.20 no longer hold. No specific 1.20.1 performance regression proven.

Scope: selected #191/#197/#186 + exact source, no original reporter log files acquired/hash; no direct fix before/after chain, history adapter CAS NOT_IMPORTED. Open unresolved compatibility case is valid bounded result.
