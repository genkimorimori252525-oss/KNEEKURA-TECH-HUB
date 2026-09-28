# Unified MOD-AI / assets checkpoint — 2026-09-28

**M0 and M1 implemented. M2–M5 NOT_RUN / outstanding.**
Baseline: PR #73 at `89cb81f412dd91df64785940569028e1a8be9920`.
This is an additive child change; no main, #71, #72 or #73 merge.
The older 597-test and live Forge evidence remains historical at its stated code
revision; this document does not repurpose it as evidence for the asset adapter.

## Delivered

- One [integrated design](../ASSET-INTEGRATION.md) and [ordered plan](../../../../docs/superpowers/plans/2026-09-28-minecraft-mod-ai-unified.md), with a successor link in the old implementation plan.
- Strict static-item spec / StyleProfile, captured-profile and optional existing-index binding, deterministic AssetRequest, reference checks and existing CAS retention.
- Read-only sosadly bridge probe: explicit permission, fixed loopback, three operations only, strict JSON/envelopes/IDs, bounded data/deadline, no retry and no source-attestation claim.
- Executable `python -m kneekura_tech_hub.minecraft.assets` check/prepare/probe CLI, examples and operational docs. No new external dependency.

The backend source is pinned to sosadly `028cdd76589de2e2cea51bfd79495b50a3c7d1d2`.
Vibecraft `fc02e08a485e1effa0e2251bc69934c213ce232f` remains reference-only: inspected
build code uses NeoForge/Java21, while the documented RPA source path returned 404.
A README demonstration is not a supplied Forge1.20.1 client driver.

## Fresh local verification

A selected-file checkout was necessary because direct container GitHub access
failed DNS. Each reused baseline file was verified against its actual Git blob ID.
No incomplete checkout is described as the whole repository.

```text
PYTHONPATH=src python -m pytest -q tests/test_minecraft_storage.py tests/test_minecraft_asset_contract.py tests/test_minecraft_blockbench.py tests/test_minecraft_assets_cli.py --junitxml=final.xml
159 passed, 0 failed, 0 errors, 0 skipped
```

30 tests are unchanged storage regressions. 129 are new: 79 asset-contract,
37 provider-probe and 13 subprocess CLI cases. The probe suite uses an actual
local HTTP fixture, not an actual Blockbench application. Missing modules/interfaces
were observed RED before their implementation; all three audit regressions below
were observed failing before the fixes. The checked-in [verification manifest](verification.json)
records exact tested source/test hashes and JUnit/log digests.

Author self-review, not an independent agent audit, reproduced and fixed:

1. A local CAS permission failure was incorrectly classified as a provider failure:
   moved evidence writes outside the transport exception boundary.
2. A 5,000-digit Content-Length bypassed the intended error envelope via Python's
   integer conversion limit: bound header length before numeric conversion.
3. An extreme integer timeout raised float OverflowError: validate the range before
   finite conversion.

Also checked: duplicate keys, non-finite JSON, unsafe/Windows-reserved IDs, authority
fields in specs, wrong/partial/tampered profiles, missing/corrupt references, wrong
response IDs, protocol mismatches, redirect refusal, large/truncated/slow responses,
permission-off no-IO, proxy/host environment ignored, and no automatic retries.

The existing standard-hosted test workflow may run on the new child PR; its status
and evidence must be read separately. No workflow/runner configuration or visibility
is changed; no manual CI dispatch or home runner is used by this slice.

## Not verified or implemented by this slice

No Blockbench desktop connection, model/PNG export, aesthetic review, worn armor,
GeckoLib animation, actual Minecraft launch, new Forge integration, Windows client
input, network/performance assertion, external decompile/remap integration or Core
caller acceptance was performed here. No screenshot existence is called a visual
PASS. No format advertisement is called successful export. Actual generation and
structural/visual/runtime verdicts stay NOT_RUN.

Durable list_workflows returned MCP 404; no duplicate workflow was created. The
plugin directory search for Blockbench/sosadly returned no connected option. No
upstream plugin or script was automatically installed to work around this.

## Resume

Use this child branch and the unified plan, not old conversation ZIPs. M2 is next:
prove managed disposable editor/project and path/write guards, then expose the
minimum geometry/texture/export operations and create one staff. Continue with
existing provider/Core acceptance, same-generation Forge build, existing client
capture, verified scoped input, and one real edit/observe/repair cycle. Keep the
original U01-U06/A01-A24 and Twilight Forest -> Connector history work visible.
Do not recreate already verified server adapters or the frozen Knowledge Core.
