# Current-plan acceptance reconciliation

Status: **current plan remains in progress; optional improvements are deferred.**

This is a criterion-by-criterion continuation of the current handoff, based on
the original [acceptance contract](../design/2026-09-28-mod-ai-environment/ACCEPTANCE.md).
It supersedes the old acceptance map as a navigation aid without rewriting its
historical tests or signed receipts. See the
[current machine-readable map](verification/current-acceptance-map-2026-09-30.json).

## Offline acceptance completed in this continuation

The original specification explicitly permits small fixtures for identity,
coverage, pagination and oracle behavior. These cases do not all require a
Minecraft launch.

Direct regressions now cover deliberately mismatched source-JAR/class bytes
(A06), shifted instruction positions with distinct static stages (A07), two
compatible injector declarations at one exact member (A09), failed-provider
composition (A10), injected storage exhaustion/interruption (A14), 1,000 search
matches and 1,025/1,027 relation edges (A15), inert README/log instructions (A16),
and distinct non-null tick/frame/log intervals (A20). A12 also links the existing
Core rejection of observations spanning multiple snapshots.

A23 exposed an implementation gap: the target-only oracle correctly kept
unrelated optional failures separate, but did not enforce the scenario's
declared known-bad controls. A new scenario gate preserves that target result
and separately requires each fixed optional control to report FAIL. Missing,
skipped, unexpectedly passing or mode-changed controls prevent scenario PASS.
The actual assertion content must match its captured hash, so removing controls
cannot bypass the gate. Genuine legacy contracts retain their original
three-field assertion hash and target-only meaning. Registered execution and
the report CLI use the scenario gate. No historical report is changed.

All mapped A01–A24 regression nodes passed in the current local aggregate:
**1,065 passed, 103 PostgreSQL-dependent skips, one known sandbox-incompatible
directory fixture deselected**. Java17 and Gson checks ran. The unchanged
directory fixture and PostgreSQL cases still require the hosted aggregate.
The map records a derived summary and original report hash; the raw report is
not published. Physical disk exhaustion, real Mixin transforms, dynamic graphs
and gameplay synchronization are not inferred from these fixtures.

## Original research questions versus whole-target runtime proof

| Task | Original criterion reached | Remaining distinct limit |
|---|---|---|
| U01 | Naga/Goal/server-side inheritance and implementation-example locators | Full dynamic dispatch and whole-target dependency closure are unproven |
| U02 | Version-bound Forge damage options, patch/API and exact member descriptors | No intervention was selected/applied; post-transform runtime positions are unproven |
| U03 | Packet/side path traced, with dedicated success explicitly unclaimed | Dedicated synchronization is NOT_RUN |
| U04 | Hydra renderer/model/texture route reached | Same-run Hydra render/config/pose evidence is still required |
| U05 | Registry, generated data/resources and distribution correspondence reached | Source-class equivalence is not established |
| U06 | Bounded compatibility investigation produces a supported UNKNOWN | Exact beta.50 binary/dependencies and positive runtime compatibility remain absent |

The [Twilight static results](verification/twilight-static-2026-09-30/README.md)
and [split Connector results](verification/connector-static-2026-09-30/README.md)
remain the evidence. U01/U02/U05 need not manufacture a gameplay run to answer
their source-oriented questions. U06's required conservative UNKNOWN is a valid
investigation result, not a promise of compatibility. None of these distinctions
closes the broader M4 live scenario or U04 rendering requirement.

## Genuine remaining implementation and live work

The current observer starts with a local ServerStartedEvent and captures server
state before adding client pixels. A client joined to a dedicated server has no
local server lifecycle. Authenticated receiving-client evidence therefore needs
a bounded role/lifecycle extension to the existing observer and contracts; it
cannot be claimed merely by running the existing integrated-client fixture.

The required design must preserve separate server-world and client-directory
identities, independent client-side state, exact build/epoch/config binding and
the existing per-workspace lock. Pairing must be demonstrated on actual scoped
connections. No second runtime service or database is needed. Implementation,
compile/fixture checks and approved live acceptance remain separate gates.

Remaining live criteria include the staff's unobstructed third-person view,
post-metadata-fix startup, dedicated propagation/non-invoking-player checks,
client-branch-specific mutation evidence, and Hydra's U04 render observation.
The previous 15-minute launch approval expired; this document grants no new
launches or network/config changes. The user's manual visual handoff remains
valid until they explicitly choose another bounded test.

Windows input is unsupported and requires an authorized Windows executor for
real acceptance. Performance measurements remain unmeasured, rather than a new
unbounded benchmark project. Human canonical promotion and deployed Core writes
are outside this implementation's authority.

## Follow-on work

The [deferred improvement plan](DEFERRED-IMPROVEMENTS-2026-09-30.md) records
part-addressed editing, comparable before/after views and bounded UV/texture/
display adjustments, plus optional status/delivery clarity. It explicitly waits
for current-plan completion and a demonstrated need. No proposed improvement
has been implemented in this continuation.
