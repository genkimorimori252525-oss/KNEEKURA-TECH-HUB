# Asset integration — preparation and sealed pilot

> **INTEGRATION HOLD: this branch is a review-only candidate, not the active PR #74 implementation.**
> Read [the concurrent-guard reconciliation checkpoint](CONCURRENT-GUARD-HOLD-2026-09-28.md) first.
> Do not load the candidate plugin or merge both guard implementations.

Status: **M1 IMPLEMENTED; M2 GUARDED-WRITER CODE / FIXTURE TESTS IMPLEMENTED;
FULL-UPSTREAM COMPOSITION AND LIVE BLOCKBENCH / MINECRAFT NOT_RUN**.

The [M2 writer checkpoint](M2-WRITER-2026-09-28.md) describes the opt-in
`asset_session` CLI, sealed blueprint, provider-side dispatcher and export capture.
The M1 `assets` preparation/probe CLI below remains unchanged and read-only toward
the editor. The original upstream probe and the guarded M2 pilot must not be
installed together in the same editor instance.
See [integration design](../ASSET-INTEGRATION.md) and
[unified implementation order](../../../../docs/superpowers/plans/2026-09-28-minecraft-mod-ai-unified.md).

This is part of the existing Minecraft department, not a second application/core.
The existing host AI remains the planner, coder and visual reviewer. This slice
provides a strict asset-spec contract and a read-only sosadly bridge probe.
M2 adds a bounded, one-shot static-item pipeline from an AI-authored blueprint.
It is not an autonomous natural-language model generator, a MCP server, or a complete ModSpec ability compiler,
a client input driver, or a claim that Vibecraft can finish the environment.

## Use with the existing environment

Use Python 3.11+ and the existing repository install, or set `PYTHONPATH=src`.
No extra dependency, Blockbench plugin installation or global config change occurs.

```text
python -m kneekura_tech_hub.minecraft.assets check --spec departments/minecraft/mod-ai/assets/celestial-staff.spec.json
python -m kneekura_tech_hub.minecraft.assets --store CACHE prepare --index INDEX_ID --spec departments/minecraft/mod-ai/assets/celestial-staff.spec.json
python -m kneekura_tech_hub.minecraft.assets --store CACHE probe --registry departments/minecraft/mod-ai/assets/provider.example.json
```

Replace `CACHE` with the existing Minecraft CAS directory and `INDEX_ID` with the
actual `index_snapshot_id` returned by the existing profile prepare/import/resolve
flow. The asset CLI reads that snapshot without invoking Gradle, javap, an editor,
or Minecraft. A complete, pinned ANCHOR profile for Forge 1.20.1 / Java 17 is
required; its exact Forge version is retained rather than replaced with 47.4.6.
`--profile PATH` alternatively accepts the complete JSON from `capture_profile`;
it is mutually exclusive with `--index` and does not accept a guessed ID alone.

`check` does not create or write a cache. `prepare` stores the spec, style, profile,
request and optional input index/reference links in the existing hash-checked CAS.
It derives relative export names but **does not write .bbmodel, model JSON or PNG**.
Re-running the same preparation yields the same request hash. Asset structural,
visual and runtime checks remain NOT_RUN.

The provider example is disabled. After installing the pinned upstream plugin in
a separately managed Blockbench desktop and starting its loopback server, the
user can copy this registry to a local managed configuration and explicitly set
`allow_probe` to true. The read-only probe then makes exactly GET `/ping`, POST
`get_status`, and POST `list_formats`, on 127.0.0.1 only. Registry permission is
not a sandbox or a new OS permission. A different local process could impersonate
that endpoint. No loaded commit or disabled-script setting is attested by replies.

`java_item_export=ADVERTISED_NOT_VERIFIED` only means the `java_block` format was
advertised; no exporter was invoked. A successful probe is not asset quality PASS.
Each probe has a fresh ID; command envelopes must echo the corresponding ID.
There are no retries. Redirects, encoded/chunked responses and oversized,
truncated or ambiguous JSON are rejected. Each of three requests has its own
0.1..30-second total deadline, including a slow header/body stream; default example
budget is two seconds/request. Responses are bounded at one MiB in the example.

Exit codes: `0` request/spec/probe completed in its declared scope; `2` malformed
input or local evidence failure; `3` disabled/unavailable/partial provider probe.
All operational outputs are JSON. `--help` prints normal help text.

## Spec scope

The example is ONE static Java item. Spec and nested StyleProfile accept only
declared fields; destinations, host URLs, commands and permissions cannot be
embedded as configuration. Natural-language brief text stays untrusted inert data.
IDs are lowercase namespaced paths with portable path components. Texture sizes
are powers of two 16..256; palette has 1..32 RGB entries; front/left/back are
mandatory among distinct supported views; up to eight distinct existing CAS
references may be attached. JSON duplicate keys and non-finite numbers are invalid.

Static item JSON, GeckoLib geometry/animation and worn armor are distinct formats.
The latter are not implemented by this slice. Existing model quality must never
be represented by a minimum cube count or a provider's reference-match percentage.

## Evidence and next step

[Checkpoint](IMPLEMENTATION-2026-09-28.md) describes exactly what was tested and
what was not. Raw probe replies may contain local project information; they remain
in the private local CAS and are not automatically committed, uploaded or promoted
to canonical knowledge. The checked-in tests are local HTTP protocol fixtures,
not live Blockbench proof. The source pin identifies reviewed upstream code only.

M2 now has guarded-dispatch, no-overwrite, export consistency and uncertain-write
handling code, exercised with local protocol/host fixtures. The next acceptance
is full pinned-source composition and a real disposable editor run: generate,
render, review and capture one staff. Do not mark M2's live gate complete from the
fixture tests. After that reuse the existing Forge build/Observer and add verified real
client input. Do not recreate the already verified server loop or introduce
an independent agent/scheduler/database. The original real provider/Core and
Twilight-first/Connector-next acceptance tasks are still on the unified roadmap.
