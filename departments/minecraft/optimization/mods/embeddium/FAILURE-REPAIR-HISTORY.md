# Embeddium — bounded history

Scope: repository `FiniteReality/embeddium`, selected 2023 task queue refactor and one 2024 Forge 1.20.1 compatibility report. Not exhaustive and no user/JAR runtime.

## E-2023-QUEUE — repairing task cancellation and empty jobs

[Commit 5866c29da7b66b0acc2f194f9c9ef1fe3f733713](https://github.com/FiniteReality/embeddium/commit/5866c29da7b66b0acc2f194f9c9ef1fe3f733713) author message: avoiding unnecessary "empty" jobs and fixing chunk task cancellation. Parent `5b643cd136d1579cb0b7c8dcc6ddbd6acc4e61d6`.

- Directly viewed diff in `RenderSection`, `RenderSectionManager`, job context/output files. Replaced per-render section job reference with `CancellationToken`, introduced submitted-frame marker and checks against older build results; moved manager toward queued results handling.
- Diagnosis: AUTHOR_CLAIM / INFERENCE that obsolete jobs consumed resources and old completion could clobber newer state. No controlled reproduction stack or measured performance.
- Lesson: work queue cancellation and result-acceptance epoch matter as much as thread count; avoid uploading stale chunk mesh results after world/section updates.
- Fix verification: NOT_RUN.

## E-192 — 1.20.1 Forge shader + world mod collision (report only)

[Issue #192](https://github.com/FiniteReality/embeddium/issues/192), Embeddium **0.3.0** + TFC/Oculus on Minecraft 1.20.1, user reports crash when world renders; falling back to 0.2.18 resolved reporter case. Did not acquire raw log from original issue body or prove source fix.
- Distinct from user `0.3.31`, must not be presented as that release's confirmed problem.
- No verified root cause or remediation.

Evidence content hash/CAS importer missing; no runtime verification and no claims of fixed runtime.
