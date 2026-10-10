# EntityCulling — bounded repair history and cross-version separation

Scope: `tr7zw/EntityCulling` sources `1.20` plus selected newer 2025, 2026 issue/commit chains; **not** all repository Issues.

## EC-204 / EC-WHITELIST (2025-05/06, Fabric 1.21.4 and newer implementation)

[Issue #204](https://github.com/tr7zw/EntityCulling/issues/204) reproduces a block_display rendered at stale location after teleport while not visible. Reporter says adding display entity to `tickCullingWhitelist` resolved one test; maintainer later discovered whitelist was inadvertently assigned to ordinary rendering whitelist. [Commit `8449cf49c11afd...`](https://github.com/tr7zw/EntityCulling/commit/8449cf49c11afd8625f1718fa6cc045180373e78) added display EntityTypes; **subsequent repair commit `5542327d4a81...`](https://github.com/tr7zw/EntityCulling/commit/5542327d4a81c5fadfdad4c0d4c676862eea131b) corrected tick whitelist lookup/insertion. Direct repair diff and `1.20` source `EntityCullingModBase.clientTick` / `ClientWorldMixin` read. The old fixed source shows merged list semantics; fix is **NOT present in selected source**, but could be present in user's later **1.10.5** binary (unknown).

Lesson: keep `renderWhitelist`, `tickWhitelist` and `forceVisible` policies separate; dynamic teleported displays must not retain stale render state. Actual 1.20.1 binary runtime **NOT_RUN**.

## EC-328 (2026-09, ONLY 26.3)

[Issue #328](https://github.com/tr7zw/EntityCulling/issues/328) and related #326/#330 reports frozen entity motion then catch-up; author [commit `984ae74b7fe...`](https://github.com/tr7zw/EntityCulling/commit/984ae74b7fe191922e8bdc044e9be009e83f4091) adds new `entity.getInterpolation().interpolate()` to reduced `basicTick`. Code diff read, diagnosis from report, no independent performance/correctness retest; **Minecraft 26.3**, whose interpolation API is not interchangeable with 1.20.1.

## EC-167 (2024-08, 1.20.1 Fabric but different installed binary)

[Issue #167](https://github.com/tr7zw/EntityCulling/issues/167) reports Botania magic missile invisible despite blacklist in Fabric 1.20.1 / EntityCulling 1.6.7. No inspected source repair for this exact interaction. Do not conflate with above tick whitelist repair unless runtime confirms common cause.

Strict result: **PARTIAL** source/history evidence, no JAR equivalence, no measured frame values and no 1.10.5 modpack replay.
