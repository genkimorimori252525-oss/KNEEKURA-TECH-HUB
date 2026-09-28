# Implementation checkpoint — 2026-09-28, hosted integration

Status: **IN_PROGRESS — connected adapters published; actual Forge build, dependency export/import and source lookup verified**.
Design: [v1.4](../design/2026-09-28-mod-ai-environment/DESIGN.md).
Base: `0e773ccf509d2a24c6dca3830cef18f38334b2cd`, design PR #72.
Implementation: PR #73, `jolly/minecraft-mod-ai-impl-2026-09-28`; no main/prior PR merge.

## Published implementation

- Explicit local capture, original source/resource/JAR bytes, immutable snapshot-bound search and full reads.
- Actual ForgeGradle resolved-input export/import with exact artifacts/scopes/order/fingerprints, plus passive discovery.
- Pinned provider adapters for Vineflower/tiny-remapper; Tiny/TSRG/ProGuard lookup and JVM descriptor identities.
- JVM declaration/Mixin, AW/AT/metadata candidate inspection and bounded static relations, not dynamic compatibility verdicts.
- Existing Core exact guidance bridge and NEW observation bundle export; no automatic canonical writes/promotions.
- Registered local Gradle execution, fresh test world provisioning, compile receipts, run-contract preparation and authenticated observer protocol.
- Forge observer, client capture source, GameTest reporter ledger and separate explicit mutation route.
- Failure/repair history as a mandatory MOD-analysis facet, plus captured-record import/query. Unknown cause, author claim, inference and recorded experiment remain distinct. This is not an automatic GitHub crawler.

The executable/test/configuration portion of the previous connected delivery is now in GitHub (33 files across the observer and connected-code commits). Do not reapply the old ZIP or infer that all nine old delivery-only narrative files were copied verbatim; README/status were updated to reflect actual hosted evidence instead.

## Evidence actually obtained

See [HOSTED-VERIFICATION-2026-09-28.md](HOSTED-VERIFICATION-2026-09-28.md).

- Full pre-connection repository/real PostgreSQL suite: 471 passed, no skips/failures.
- Full connected repository/real PostgreSQL suite: 567 passed, no skips/failures, 8 pre-existing invalid-escape warnings. Python3.12, pytest8 (declared range), JDK17.
- Actual Forge1.20.1/47.4.6 MDK build: compileJava, jar and reobfJar succeeded. This is an isolated reference environment, not a user workspace upgrade.
- Actual ForgeGradle export succeeded. Real importer captured 37,933 documents from 205 scoped artifact entries and found/read ForgeObserver source. Entries can repeat between compile/runtime scopes; they are not 205 distinct MODs. Capture coverage is retained rather than assumed complete.
- New history tests were exercised RED→GREEN locally (16 history tests; 63 passed together with storage/mapping regressions). The current branch's Actions checks provide the later whole-repository result.

The historical `verification/local-run.json` remains the earlier 102-test evidence; it is superseded for current status, not rewritten as if CI existed at that earlier time.

## Remaining product acceptance — do not call the entire environment complete

1. Actual Vineflower and tiny-remapper provider execution, including relevant real MOD mappings/classpaths; protocol fixtures are not tool integration proof.
2. New Core bridge/bundle end-to-end against actual Core schemas and applicable data. Passing the existing Core/PostgreSQL suite is necessary but not proof that this new caller path has been exercised with real research records.
3. Launch a managed Forge/GameTest world and prove the live build/session/world handshake, report completion and observation path. The binding is now compiled, but a real game has not been launched in this checkpoint.
4. Client screenshot/render/network assertions, production-MOD correctness and performance, and Windows-specific process behavior remain unverified. Server compile/transport tests cannot prove these.
5. Actual one-MOD editing loop and U01-U06/A01-A24 acceptance. Do not convert library test counts into product acceptance counts.
6. Execute the new failure/repair history facet for each target. No actual Twilight/Connector upstream bug cases have been claimed as newly analyzed in this checkpoint. Preserve Twilight-first/Connector-next ordering and existing snapshot anchors.

Self-review follow-up to exercise in the live loop: the Java command receipt reports `success` while the pure imported-operation oracle consumes `outcome`. Until this protocol seam is tested and reconciled, successful mutations can remain UNKNOWN. Do not weaken idempotency/retry safeguards to mask this gap.

## Resume

Use PR #73's current branch, not the older conversation patch. Read the Actions logs and latest commit before work. CI is now explicitly allowed on GitHub-hosted standard runners; do not follow the superseded 'keep CI off' instruction in the original checkpoint. Do not use the home self-hosted runner while this repository is public, merge prior PRs, or change repository visibility as part of this continuation.
