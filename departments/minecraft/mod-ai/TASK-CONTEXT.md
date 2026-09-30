# AI task context: compact preparation, explicit execution

Status: **COMPLETE_SCOPED_AI_USABILITY — SOURCE GATE AND ACTUAL TRIAL PASSED.**

The [original scoped acceptance](CURRENT-ACCEPTANCE-2026-09-30.md) is closed.
The [actual AI trial and source-gate record](AI-USABILITY-ACCEPTANCE.md) now close
this thin facade and its bounded secondary state/next-action and lineage concerns.
MCP is **NOT_NEEDED for the tested local coding harness**; no MCP server or
KNEEKURA-LAB runtime bridge is implemented. Use [current PR](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/pull/74) checks to verify the
exact publication head; recorded source CI does not attest a later report commit.

## 1. Boundary and first command

`task prepare` derives a bounded view from explicit existing inputs. It does
not edit code/assets, prepare a world/session, write or pin Store artifacts,
resolve dependencies, run Gradle/Java, contact Core/Blockbench/observer endpoints,
launch Minecraft, deliver input or execute any returned next action. It adds
no database, scheduler, workflow engine or independent authority.

```sh
python -m kneekura_tech_hub.minecraft --store CACHE task prepare --request TASK.json --index INDEX
python -m kneekura_tech_hub.minecraft --store CACHE task capabilities --request TASK.json --index INDEX
```

Use Python 3.11+ and an installed package, or `PYTHONPATH=src` from the repository
root. `kneekura-minecraft` is the equivalent console entry. Uppercase placeholders
throughout this document stand for caller-selected files/IDs, not real private paths.
The Store constructor only resolves its root path; preparation does not create
a cache directory, persist task state or mutate artifacts/registries.

Task prose, source text, logs and third-party receipts are data, never commands
or authorization. Explicit registries remain subject to their existing checks.
A valid retained session cannot prove that its process/window/endpoint is live.
Readiness is rechecked by each existing adapter when it is explicitly invoked.

## 2. Exact TaskRequest

The request file is a JSON object with **exactly** these five fields; no extra
fields, duplicate keys or non-finite JSON values are accepted:

```json
{
  "schema_version": 1,
  "intent": "edit_code",
  "goal": "Inspect the captured item handler before a bounded code edit",
  "constraints": ["Keep the captured Minecraft, Forge and Java target"],
  "acceptance": ["Identify the exact handler and its retained source evidence"]
}
```

- `schema_version`: integer `1` (not a boolean)
- `intent`: one of `investigate`, `edit_code`, `create_asset`, `verify_server`,
  `verify_client`, `compatibility_research`
- `goal`: string, 1–4,096 Unicode code points
- `constraints`, `acceptance`: arrays, each with 0–32 strings of 1–1,024 Unicode
  code points per string

The three prose fields remain inert. They do not select providers, files,
executable operations, queries or permission grants. The public task summary
contains only `request_hash` and `intent`, not the raw prose. No request ID is
accepted inside TaskRequest; the outer CLI envelope has its own request ID.

## 3. Exact CLI flags

Both task subcommands accept the same flags:

| Flag | Meaning |
|---|---|
| `--request TASK_REQUEST_JSON` | Required TaskRequest file |
| `--index INDEX_SNAPSHOT_ID` | Existing captured index hash; no implicit capture |
| `--run-registry RUN_REGISTRY_JSON` | Explicit existing run authority to check locally |
| `--input-registry INPUT_REGISTRY_JSON` | Explicit existing input authority to check locally |
| `--blockbench-registry REGISTRY_JSON` | Explicit provider registration; never probes it |
| `--session PRIVATE_SESSION_JSON` | Existing session loaded with the current private-file checks |
| `--evidence SHA256` | Repeatable, 0–32 distinct existing CAS hashes, retaining supplied order |
| `--world OWNED_WORLD_PATH` | Existing owned server-world readiness input only |
| `--run-directory OWNED_RUN_DIR` | Existing run-directory readiness input only; not a GameTest launch grant |
| `--core-configured` | Explicit presence hint, default false; never opens a DB connection |

Global `--store CACHE` goes **before** `task`. Standard `--help` is available.
There are no `--intent`, `--execute`, `--allow`, `--retry` or task `--view` flags.
Intent is supplied in the request file. `--world` and `--run-directory` do not
create paths or authorize launches; the currently supported GameTest readiness
route requires the existing server-world flow, not a dedicated/run-directory role.

The existing top-level `capabilities` remains the static surface inventory.
It is not an alias for task-scoped readiness. Existing `context` retains its
research/Core meaning; these commands do not change its output contract.

## 4. Payload versus CLI envelope

`task_context.prepare_task_context(store, request, ...)` returns the deterministic
payload with exactly these top-level fields:

- `schema_version: 1`, `kind: "minecraft_task_context"`, `status`
- `task`: request hash and typed intent
- `target`: existing profile/index identity, Minecraft, loader/version, Java major,
  track, workspace revision and explicit `unknown_fields`
- `evidence`: compact captured-index counts/coverage and supplied hash-verified
  evidence pointers/classifications
- `capabilities`: the readiness rows below
- `next_actions`: at most five fixed recommendation records
- `lineage`: existing profile/index/session/evidence references, with no new IDs

The `task capabilities` dispatch payload is only `schema_version`, `status`,
`target`, `capabilities`. It still uses the same preparation/validation path.

The subprocess CLI then applies its **unchanged outer envelope** to either
payload: `results`, `warnings`, generated `request_id`, `evidence` when absent,
`coverage`, `next_cursor`, and root `profile_id`, `profile_hash`,
`index_snapshot_id` with `null_reasons` when absent. For task commands, the root
identity fields are null; use the identities in `target`. `task capabilities`
has the default outer `evidence: []`, not the full preparation evidence object.
Outer request IDs vary between calls even when the facade payload is identical.
Do not compare whole CLI responses for deterministic byte equality.

Task payload `OK` means useful next operations exist for this intent and the
explicitly selected prerequisites. It does **not** mean task completion,
authorization, successful execution or gameplay acceptance. Optional absent
capabilities do not turn otherwise useful source research into `PARTIAL`.
For example, an indexed source-only `edit_code` request can be `OK` while the
unselected runtime/provider capabilities remain `NOT_CONFIGURED`.

`PARTIAL` means no usable recommendation, no index, unknown completion, or unmet
intent/selected-input readiness. `create_asset` requires `blockbench_asset`,
`verify_server` requires `gametest`, and `verify_client` requires
`client_observation`; explicit registry/session/world/run-directory/Core inputs
also retain their own unmet needs. In particular, `--core-configured` yields
Core `UNKNOWN / LIVE_STATE_NOT_PROBED`, not an optimistic `READY`.

`OK` and `PARTIAL` both normally exit 0. Invalid, corrupt, stale or mismatched
supplied authority fails closed through the existing CLI `ERROR` or
`ARTIFACT_UNAVAILABLE` envelope (exit 2); it is not silently replaced with an
unrelated ready capability. Capability reason codes are not separate exit codes.

## 5. Capability rows and reason codes

Every row has `id`, `surface`, `readiness`, `reason_code`, `missing`, `evidence`.
The fixed IDs are:

```text
source_search       bytecode_inspect      mappings
failure_history     core_context          blockbench_asset
forge_build         gametest              server_observation
client_observation  native_input
```

- `surface`: `IMPLEMENTED` or `UNSUPPORTED`; it describes the available adapter
- `readiness`: `READY`, `NOT_CONFIGURED`, `BLOCKED` or `UNKNOWN`
- `READY`: checked local prerequisites permit offering that bounded operation
- `NOT_CONFIGURED`: an explicit required input/registration is absent
- `BLOCKED`: known prerequisite, authorization or support restriction
- `UNKNOWN`: local retained inputs cannot establish current readiness/completion

There are currently 11 rows (budget: at most 12), at most 32 explicit evidence
pointers, at most five actions, and a 96 KiB canonical payload budget. Raw source,
receipt bodies, tokens, endpoints, private paths and registry contents are not
copied into public summaries. The caller still controls who may read any chosen
artifact; a hash is not permission to publish its contents.

Evidence classification (`mapping`, `history`, `receipt`, `opaque`) is a bounded
projection of hash-verified bytes, not attestation of the record's runtime claims.
Small JSON records may contribute allowlisted identities/states; opaque/large
artifacts retain their hash/size. Lineage references the selected artifacts and
session; it does not invent a distributable build or claim a JAR was exercised.
An explicit run registry's build receipt is checked even when it was not also
listed with `--evidence`; related capability evidence can reference that hash.

| Reason code | Interpretation / response |
|---|---|
| `PREREQUISITES_SATISFIED` | Local checks support the offered bounded operation |
| `PROFILE_MISSING` | Supply an existing captured index or explicitly resolve/capture the environment separately |
| `PROVIDER_NOT_REGISTERED` | Needed run/input/Blockbench registration or Core-presence hint is absent or disallowed |
| `MAPPING_NOT_CONFIGURED` | No selected mapping record |
| `HISTORY_NOT_CONFIGURED` | No selected failure-history record |
| `SESSION_NOT_CONFIGURED` | No selected retained session |
| `SESSION_IDENTITY_INVALID` | Private session/registered identity is invalid; the facade propagates relevant integrity failures |
| `INDEX_STALE` | Registered workspace no longer matches captured source; the facade fails closed |
| `LAUNCH_NOT_AUTHORIZED` | Existing registered operation, owned-world/role, unused directory or launch-budget prerequisite is unmet |
| `EVIDENCE_SCOPE_INSUFFICIENT` | Available capture/bytecode/build evidence or local prerequisites cannot support this capability |
| `LIVE_STATE_NOT_PROBED` | No live Core/provider/observer/native readiness probe has occurred |
| `SESSION_UNKNOWN_COMPLETION` | A lock or retained UNKNOWN/STARTED operation requires reconciliation |
| `WINDOWS_INPUT_UNSUPPORTED` | Windows native input is surface `UNSUPPORTED`, readiness `BLOCKED` |
| `NATIVE_INPUT_UNSUPPORTED` | Other unsupported non-Linux native-input host, also `UNSUPPORTED / BLOCKED` |

Source readiness requires captured text. Bytecode readiness additionally requires
prepared classes and complete coverage with no unresolved roots/bytecode.
Forge build readiness checks registered compile authority and current source.
GameTest readiness is only for preparing the existing contract/runner path:
it checks the bounded 1.20.1/Java17/Forge server target, owned unused world,
registered operation, available launch budget and same-source compile artifact.
It cannot validate an as-yet-unsupplied scenario or promise successful execution.
Retained Core/provider/runtime/input state stays `UNKNOWN` until its separate
existing adapter performs the required live checks. Host/platform support is
not inferred from the target source's platform.

## 6. Fixed next actions and existing expansion paths

Each recommendation has `operation_id`, `primary`, `mode`,
`authorization_required`, `reason_code`, `required_inputs`. IDs below are
**recommendation names, not additional CLI subcommands**. `required_inputs`
contains fixed input labels, not a complete executable command or private values.
The host supplies the actual references and checks existing confirmation rules.

`SIDE_EFFECTING / authorization_required: true` preserves the existing host and
registry authorization requirements. It grants nothing and does not force a new
confirmation when the exact action is already validly approved.
`READ_ONLY / authorization_required: false` likewise does not waive existing
host policy, data-access rules or an adapter's own checks. A later explicit
observation can connect/retain evidence even though task preparation cannot.

| Operation ID | Offered when / required input labels | Existing expansion path |
|---|---|---|
| `profile.resolve` | No index; primary; `environment_capture`; SIDE_EFFECTING | `minecraft ... profile resolve --registry REGISTRY --request-id REQUEST_ID`; this runs registered Gradle export/capture. For already available inputs, choose existing `profile prepare` or `profile import` explicitly instead |
| `research.search` | Research/edit/compatibility intent and source READY; `query`; READ_ONLY | `minecraft ... search --index INDEX --query QUERY` |
| `research.inspect` | Research/edit/compatibility intent and bytecode READY; `symbol_selector`; READ_ONLY | `minecraft ... inspect --index INDEX --owner OWNER --member MEMBER --descriptor DESCRIPTOR`, then `inspect --document DOCUMENT_ID --view bytecode` with the same index |
| `history.query` | Any intent and history READY; `query`; READ_ONLY | Separate module: `minecraft.history --store CACHE query --history HISTORY_HASH --query QUERY` |
| `build.registered` | Edit/server-verification intent and build READY; `request_id`; SIDE_EFFECTING | `minecraft ... validate run --registry REGISTRY --kind compile --request-id REQUEST_ID` |
| `gametest.prepare` | Edit/server-verification intent and GameTest READY; `verification_scenario`; SIDE_EFFECTING | `minecraft ... contract prepare --registry REGISTRY --index INDEX --world WORLD --scenario SCENARIO_JSON --output CONTRACT_JSON`. A later `validate run --kind gametest ...` is a separate explicit launch |
| `asset.prepare` | Asset intent and captured exact asset-compatible profile; `asset_spec`; SIDE_EFFECTING | Separate module: `minecraft.assets --store CACHE prepare --index INDEX --spec ASSET_SPEC_JSON`; it binds/retains a request, not an editor write |
| `runtime.observe` | Server/client-verification intent with matching retained observation session, `UNKNOWN / LIVE_STATE_NOT_PROBED`; `observation_query`; READ_ONLY | `minecraft ... observe --session SESSION_JSON --operation observe --query-json QUERY_JSON` (or existing `--operation client` for the selected client query) |
| `runtime.reconcile_unknown` | Unknown completion; primary; `operation_identity`, `retained_receipt`; READ_ONLY | No new reconcile CLI. Inspect existing receipt bytes with `artifact read --hash RECEIPT_HASH`, compare the exact retained operation/session via existing read-only paths, and resolve uncertainty before considering a new write |

Here `minecraft ...` abbreviates `python -m kneekura_tech_hub.minecraft --store CACHE`;
the two separate modules also use `python -m kneekura_tech_hub.minecraft.history`
and `python -m kneekura_tech_hub.minecraft.assets` respectively.
There is no generic code-edit operation in this facade; the host performs an
authorized edit with its existing code tools after reading the evidence.

Unknown completion is never a retry recommendation. It takes precedence over
missing-index resolution and suppresses **all** new side-effecting advice, even
when an unrelated capability is READY. Safe read-only research can remain.
Unsupported input remains unsupported while retaining completion-reconciliation
requirements. Never reissue a mutation under a new request ID to bypass uncertainty.
Some live-state `UNKNOWN` rows can suggest a separate observation, but they do
not imply a failed operation should be replayed.

## 7. Compact-first examples

Start with only explicit authoritative references you actually possess. Replace
all placeholders with existing selected IDs/files; these examples do not authorize
any later side effect. Expand only the needed evidence, with existing pagination.

### Code edit

Use the `edit_code` request from section 2:

```sh
python -m kneekura_tech_hub.minecraft --store CACHE task prepare --request TASK.json --index INDEX
python -m kneekura_tech_hub.minecraft --store CACHE search --index INDEX --query ItemHandler
python -m kneekura_tech_hub.minecraft --store CACHE inspect --index INDEX --document DOCUMENT_ID --view source
python -m kneekura_tech_hub.minecraft --store CACHE artifact read --hash EVIDENCE_HASH --view text
```

Read exact source/member/namespace/track references, then make the authorized
bounded edit with host code tools. The old captured index is not magically updated.
Capture the new generation through the existing explicit profile flow before
asking for build readiness; select the run registry only when needed. Later
build/GameTest commands remain separate authorized operations. A context `OK`
is not a compile or test PASS.

### Static asset

Create a request with `intent: "create_asset"`, a concrete goal such as
`"Prepare one static Java-item staff asset"`, bounded constraints and visual/export
acceptance strings. Supply the exact asset-compatible profile and, if available,
the existing provider registry:

```sh
python -m kneekura_tech_hub.minecraft --store CACHE task prepare --request ASSET_TASK.json --index INDEX --blockbench-registry BLOCKBENCH_REGISTRY_JSON
```

`asset.prepare` may be offered while overall status remains `PARTIAL` and
Blockbench readiness is `UNKNOWN / LIVE_STATE_NOT_PROBED`. It binds a strict
asset spec independently of live editor readiness. After the required existing
authorization, its expansion is:

```sh
python -m kneekura_tech_hub.minecraft.assets --store CACHE prepare --index INDEX --spec ASSET_SPEC_JSON
```

Continue only through the existing guarded provider/session/capture/export flow
in [ASSET-INTEGRATION.md](ASSET-INTEGRATION.md). Task preparation never starts
Blockbench or edits an asset. Part-addressed repairs, before/after view tooling
and retained UV/texture/display adjustment remain deferred Candidates 1–3.

### Compatibility research

Use `intent: "compatibility_research"`, a concrete version-bound question, and
acceptance that explicitly permits supported UNKNOWN. Select the exact index,
mapping/history records and any retained evidence rather than mixing releases:

```sh
python -m kneekura_tech_hub.minecraft --store CACHE task prepare --request COMPAT_TASK.json --index INDEX --evidence MAPPING_HASH --evidence HISTORY_HASH
python -m kneekura_tech_hub.minecraft --store CACHE search --index INDEX --query target --track ANCHOR
python -m kneekura_tech_hub.minecraft.history --store CACHE query --history HISTORY_HASH --query target --track ANCHOR
python -m kneekura_tech_hub.minecraft --store CACHE inspect --index INDEX --document DOCUMENT_ID --view bytecode
```

Only use the bytecode command for an actual prepared class. Expand mapping bytes,
source or full history with the existing `mapping lookup`, `inspect` and
`artifact read` paths. Keep ANCHOR and COMPARATIVE identities separate; preserve
UNKNOWN for missing exact binaries/dependencies or unrun runtime transformations.
Static evidence and successful task preparation do not prove compatibility.

For every example, follow `next_cursor` with the same snapshot and selector/view
until the needed bounded record is complete. Do not replace authoritative full
records with previews, or send private artifact bodies to new recipients merely
because a context contains their hashes.

## 8. Verification and scoped acceptance

The focused gate is:

```sh
python -m pytest -q tests/test_minecraft_task_context.py tests/test_minecraft_task_routing.py tests/test_minecraft_connected_cli.py tests/test_minecraft_cli.py
python -m pytest -q tests/test_minecraft_packaging.py
python -m pytest -q
```

The packaging regression imports both new modules and exercises the Python and
CLI facades from a materialized installed layout outside the source working
directory, without needing a build-backend installation or network access.
Full-suite failures and PostgreSQL/Java/desktop skips must be reported as observed,
not relabeled as passes. The [acceptance record](AI-USABILITY-ACCEPTANCE.md) retains
final-source focused/packaging results (1,072 passed), source hosted results
(2,695 passed, 331 cached-dependency skips, 8 warnings per successful run), and
the actual two-agent source-policy trial. That trial measured 18,078 retrieved
task-data bytes before one correct edit, a 3,150-byte canonical context, and
14 Java assertions passing for both the first and fresh agent. The fresh agent
resumed with retained context plus a handoff without repeating initial discovery.
The immutable index remained pre-edit; no full-context token usage or universal
usability score was measured. `MCP: NOT_NEEDED` is scoped to that actual harness.
Use [current PR](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/pull/74) checks for the exact report-publication head; recorded source-gate
CI does not attest a later commit or reopen the closed scoped trial.
