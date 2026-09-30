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

A later runtime implementation aggregate passed **1,739 tests**, with the same
103 PostgreSQL-dependent skips and one ambient-parent directory fixture excluded.
The exact Forge observer compiled and independent review cleared the repaired
contract/oracle boundaries. See the [derived preflight summary](verification/runtime-preflight-2026-09-30.json);
its original raw-report hashes are references, not public raw receipts.

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

## Runtime implementation and separate live acceptance

The dedicated receiving-client gap is implemented in the existing observer,
Store and runner. Schema-2 contracts preserve separate server-world and
client-directory identities, exact loopback socket/player pairing, independent
client state and per-workspace locks. Authenticated pair capture remains
non-atomic and does not itself establish gameplay synchronization.

A distinct target-code profile and immutable ordered dependency-byte inventory
retain all resolved compile/runtime archives without promoting the broad UNKNOWN
profile. Complete target closure is rederived from registered export/compile
receipts before contract/session acceptance. Startup checks actual archive bytes;
subsequent metadata invalidation does not attest loaded/transformed instructions.

The opt-in fixed staff build adds exact-source client branch/mutator-site tracing
and selected vanilla packet receipts. Default MOD sources remain unchanged.
Fixed retained-record checkers cover first use, the non-invoking player, cooldown
repeat and expiry. Native intermediate screenshots/state/traces participate in
identity, chronology, immutable-history and remaining-tick checks. Fixture PASS
is explicitly distinct from actual game acceptance.

U04 has a separate schema-3 integrated-client route that binds the marker compile
artifact and selected derived Twilight archive/probes independently. Its narrow
Hydra helper records the exact client entity, dispatcher renderer, default/JAPPA
marker state, texture hash, pose and captured frame. Visibility still requires
inspection of that frame. See [runtime contracts and limits](forge-observer/DEDICATED-OBSERVATION.md).

The next bounded live scenario is prepared for dedicated staff propagation,
non-invoking control, actual client use/repeat/expiry and unobstructed display,
followed by the default Hydra view. Its actual result must be recorded separately;
preparation, compilation, offline fixtures and approval are not live acceptance.
Historical occluded views, timeout receipts and the earlier manual handoff remain
unchanged. This document itself grants no launch or network-setting authority.

Windows input is unsupported and requires an authorized Windows executor for
implementation/real acceptance. Performance measurements remain unmeasured,
rather than a new unbounded benchmark project. Human canonical promotion and
deployed Core writes are outside this implementation's authority.

## Follow-on work

The [deferred improvement plan](DEFERRED-IMPROVEMENTS-2026-09-30.md) records
part-addressed editing, comparable before/after views and bounded UV/texture/
display adjustments, plus optional status/delivery clarity. It explicitly waits
for current-plan completion and a demonstrated need. No proposed improvement
has been implemented in this continuation.
