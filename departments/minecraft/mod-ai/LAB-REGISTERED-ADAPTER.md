# Registered LAB adapter and retained experiment resume

This source slice adds an explicit local file bridge to KNEEKURA-LAB. It can register an already prepared request, inspect that registration, and reconcile an existing action journal. It does not launch Minecraft, install a runtime owner, dispatch actions, or convert a retained report into live evidence.

The executable surface is deliberately small:

```text
kneekura-minecraft experiment inspect-adapter --registry REGISTRY.json
kneekura-minecraft experiment register --registry REGISTRY.json --request-hash SHA256
kneekura-minecraft experiment inspect-registration --registry REGISTRY.json --request-hash SHA256
kneekura-minecraft experiment reconcile-unknown --registry REGISTRY.json --request-hash SHA256 --action-id IDEMPOTENCY_KEY
kneekura-minecraft experiment resume --result-hash SHA256
kneekura-minecraft task prepare --request TASK.json --experiment-result SHA256
```

`register` copies the exact verified request, assertion, binding, build, config and resource bytes from the existing TECH HUB CAS into the selected private LAB input directory. LAB rechecks all content hashes before committing its existing registration record. Repeating registration only returns the same record when all inputs match. An incomplete or conflicting record is never automatically repaired.

`inspect-registration` and `reconcile-unknown` invoke the fixed registered Node adapter. They may retain a TECH HUB receipt and a bounded transport input file, but cannot execute a runtime action. A missing journal, interrupted action, corrupt chain, foreign request/action key or unconfirmed local adapter completion never authorizes replay. `reconcile-unknown` reports the existing journal state; it cannot clear an unknown result or grant permission to retry.

## Private registry

The caller supplies schema version 1, enabled `true`, backend `kneekura.lab.local-bridge.v1`, a canonical LAB workspace, declared source revision, exact Node executable path and SHA-256, exact owner-config path and SHA-256, a deadline up to ten seconds, and SHA-256 values for this fixed module closure:

- `adapter-cli.mjs`
- `adapter.mjs`
- `registration.mjs`
- `materials.mjs`
- `json.mjs`
- `action-journal.mjs`
- `arena-contract.mjs`

All modules are under `debug-workspace/bridge/`. Registry fields are `schema_version`, `enabled`, `backend`, `workspace`, `source_revision`, `executable`, `executable_hash`, `module_hashes`, `owner_file`, `owner_hash`, and `timeout_seconds`. No caller-supplied arguments, shell commands, endpoint or executable can be put into an ExperimentRequest.

The Node owner config contains `schemaVersion`, `runtimeRoot`, `inputRoot`, and `run`. Both roots must already be canonical directories. `run` is null for registration-only work. Reconciliation requires an exact configured run directory and session/run/snapshot/process/experiment/request identity matching its immutable RunSnapshot. These paths stay private and are not included in public receipts.

The declared Git revision is descriptive linkage. Current executable/module byte hashes provide local tool identity; neither proves JVM loaded classes. Each invocation rechecks all registered bytes before and after running. The child process receives a minimal environment, excluding inherited Node and native-library injection hooks. Registry files, module files, output and process time are bounded; symlinks and nonregular files fail closed.

## Resume and TaskContext

`resume` verifies the retained request, raw RunSnapshot and complete referenced evidence inventory. It returns compact assertion records, action receipts, unresolved gaps, observation pointers and exact drill-down hashes. Assertions remain `IMPORTED_LAB_REPORT`; runtime attestation remains `NOT_ESTABLISHED`. The output explicitly grants no execution authority and disallows replay.

TaskContext accepts optional `--experiment-registry` and `--experiment-result` inputs. It inspects them without starting a process or writing data. Unknown completion makes reconciliation the primary read-only operation and suppresses new mutation advice. A result linked to a different supplied index/profile/source is marked for reverification. The experimental surface is implemented, while runtime execution stays blocked until loaded-runtime identity, disposable-world authority and live acceptance are established.

## Source and live gates

The hosted TECH HUB workflow pins exact LAB and MOD revisions, runs LAB source tests and portable Java contracts, exercises an actual Python-to-Node registration fixture, and compiles the bridge against the pinned MOD source. It never runs a Minecraft client/server task. The existing LAB Windows workflow remains a separate gate.

A source fixture is not a real repair cycle. Real action/camera acceptance, holding appearance, the visual-format benchmark and X7's real MOD repair loop are deferred under the user's code-first instruction. X8 same-frame multipass remains conditional on a demonstrated X3 deficiency; it is neither implemented nor declared unnecessary before that evaluation.
