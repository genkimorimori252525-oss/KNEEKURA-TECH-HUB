# Implementation checkpoint — 2026-09-28, real live Forge integration

> Historical checkpoint. Current implementation and explicitly separated acceptance
> results are in [CONTINUATION-2026-09-30.md](CONTINUATION-2026-09-30.md).
> The pending items below describe 2026-09-28, not the current resume order.

Status: **IN_PROGRESS — the server-side build → source capture → authenticated observation/command → GameTest loop is verified; the entire MOD-making AI environment is not yet complete**.
Design: [v1.4](../design/2026-09-28-mod-ai-environment/DESIGN.md).
Base: `0e773ccf509d2a24c6dca3830cef18f38334b2cd`, design PR #72.
Implementation: PR #73, `jolly/minecraft-mod-ai-impl-2026-09-28`; no main/prior PR merge.
Verified executable head: `3fa14453327e7992231e3d479ac1d1eebbd96b3c`. Later documentation-only commits do not extend the proven code scope.

## Published implementation

- Explicit local capture, original source/resource/JAR bytes, immutable snapshot-bound search and full reads.
- Actual ForgeGradle resolved-input export/import with exact artifacts/scopes/order/fingerprints, plus passive discovery.
- Pinned provider adapters for Vineflower/tiny-remapper; Tiny/TSRG/ProGuard lookup and JVM descriptor identities.
- JVM declaration/Mixin, AW/AT/metadata candidate inspection and bounded static relations, not dynamic compatibility verdicts.
- Existing Core exact guidance bridge and NEW observation bundle export; no automatic canonical writes/promotions.
- Registered local Gradle execution, fresh test world provisioning, compile receipts, run-contract preparation and authenticated observer protocol.
- Forge observer, client capture source, GameTest reporter ledger and separate explicit mutation route. The command `success`/`outcome` seam is now fixed and tested in the real game; a numerical zero can be a successful result. Missing callbacks/contradictory receipts remain UNKNOWN; command execution is not a behavior-test PASS.
- Failure/repair history as a mandatory MOD-analysis facet, plus captured-record import/query. Unknown cause, author claim, inference and recorded experiment remain distinct. This is not an automatic GitHub crawler.
- Disposable real-Forge integration driver and hosted workflow; exact entity-ID observation, duplicate-command and known-bad GameTest controls.

The executable/test/configuration portion of the earlier connected delivery is in GitHub. Do not reapply the old conversation ZIP. README/status are updated for actual hosted evidence rather than copied verbatim from older delivery-only notes.

## Evidence actually obtained

Current: [LIVE-VERIFICATION-2026-09-28.md](LIVE-VERIFICATION-2026-09-28.md) and [machine-readable checkpoint](verification/live-2026-09-28.json).
Earlier build/export checkpoints: [HOSTED-VERIFICATION-2026-09-28.md](HOSTED-VERIFICATION-2026-09-28.md).

- Complete current repository + configured PostgreSQL suite: **597 passed, 0 failed, 0 skipped, 8 pre-existing invalid-escape warnings**, run36381522497. PR head3fa144533..., tested synthetic merge675385657.... Python3.12, declared pytest8 environment, JDK17.
- Actual Forge1.20.1/47.4.6 MDK: compileJava/jar/reobfJar and actual resolved export/import/source search verified in earlier runs; changed command callback source also compiled in run36380185316.
- **Live run36381518610 at3fa144533... passed the existing registered build/export/capture/launch/observe/command/GameTest path**. Exactly2 tests detected/executed: bridge requiredPASS, knownbad optionalFAIL retained separately. Authentication, target UUID observation, successful zero-valued command and no duplicate scoreboard mutation are verified for this disposable scenario.
- Actual world seed/path mismatch and ambient-entity/truncation fixture defects were reproduced in two prior failed runs, corrected without relaxing production guards, and documented with their repair commits.

The historical `verification/local-run.json` and earlier ledgers remain historical. Do not rewrite their date/scope or interpret their local fixture counts as real Minecraft acceptance.

## Remaining product acceptance — do not call the entire environment complete

1. Actual Vineflower and tiny-remapper provider execution, including relevant real MOD mappings/classpaths; protocol fixtures are not tool integration proof.
2. New Core bridge/bundle end-to-end against actual Core schemas and applicable research data. Passing the existing Core/PostgreSQL suite does not prove this new caller path with real research records.
3. Client screenshot/render/network assertions, production-MOD correctness/performance, and Windows-specific process behavior. The new server integration result does not establish these.
4. Actual one-MOD editing loop and U01-U06/A01-A24 acceptance. The disposable probe is an adapter integration scenario, not an autonomous Mob implementation benchmark or all product acceptance tasks.
5. Execute the new failure/repair history facet for each target. No new upstream Twilight/Connector bug investigation was completed in this continuation. Preserve Twilight-first/Connector-next ordering and existing snapshot anchors.

The live run tested no explicitly registered runtime config files (`[]`), and does not attest all dynamic configuration or post-transform in-memory class bytes. Raw server.properties is normalized by Forge Main at startup; its original input was retained separately while actual world path/seed checks remained strict.

## Resume

Use PR #73's current branch, not older conversation patches. Read the verification ledger and latest commit before work. The command contract and real server observation/GameTest integration are DONE for this declared probe: do not recreate them. The next unverified adapters are real external decompile/remap and the new Core caller path, followed by actual MOD-editing/client acceptance as needed.

CI is explicitly allowed on GitHub-hosted standard runners; the original CI-off checkpoint is superseded. Do not use the home self-hosted runner while this repository is public, merge prior PRs, or change repository visibility as part of continuation. Keep the user-approved scope and avoid adding new subsystems merely to extend the checklist.
