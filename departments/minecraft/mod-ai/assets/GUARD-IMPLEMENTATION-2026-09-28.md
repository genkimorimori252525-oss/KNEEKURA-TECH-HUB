# M2 continuation — local guard preparation, 2026-09-28

Status: **PARTIAL M2; selected-file local verification complete; published to PR #74; full repository CI and live Blockbench acceptance remain outstanding.**

Continues [the approved unified plan](../../../../docs/superpowers/plans/2026-09-28-minecraft-mod-ai-unified.md)
at PR #74 remote head `a4b195a0466ec59fb7e57a4eae1fff45e9f9603f`.
M0 and M1 remain complete at their historical revisions. M2 is **not** complete.
No existing source, observer, runtime, CAS, main or parent PR is replaced.
No new agent, scheduler, database, background process or `labs/` tree is introduced.

## What is implemented

`src/kneekura_tech_hub/minecraft/asset_guard.py` adds an offline preparation CLI.
It accepts an existing M1 request hash and explicitly supplied local upstream
plugin bytes. It revalidates the request/spec/style/profile/index/reference chain
without repairing or rewriting it. The exact Forge version remains profile-bound.
The upstream Git blob must equal `898f811f15c0bb6cb7eed08f9d994ba3b0131e74`,
from sosadly revision `028cdd76589de2e2cea51bfd79495b50a3c7d1d2`.
A different, truncated or modified plugin is refused before a package is created.

A narrow source transformation replaces the original command dispatcher rather
than putting a client-side allowlist in front of an unrestricted endpoint. Unknown
or duplicated transformation seams fail closed. The original automatic server
start block is removed, irrespective of the saved autostart setting. Manual start
in a disposable editor is required. The caller does not install, load or start it.

The generated dispatcher permits only authenticated, request-bound guard routes:

| Operation | Restricted upstream call | Scope |
|---|---|---|
| `begin` | `new_project` | Empty editor, fixed `java_block`, spec name and size |
| `texture` | `create_texture` | One solid fill from the fixed palette; no URL/path |
| `cube` | `add_cube` | At most 128 bounded, unrotated boxes with explicit UVs |
| `inspect` | `check_model` | Observation only; not a quality verdict |

All original remote action names, including `execute_script`, plugin install/
uninstall, imports, direct edits, saving and exports, are rejected. The original
GET `/ping` health endpoint remains available. This is a **different restricted
application protocol**, not drop-in compatibility with the upstream MCP tool
catalogue. The existing Python M1 probe is unchanged and remains read-only; a
Python/network mutation client is **not** added by this slice.

A session binds the actual newly created Project object and UUID, checks tab,
plugin, format, texture and cube inventories, enforces ordered operations and one
in-flight call, and expires after 15 minutes. Dedicated mutation calls begin
synchronously after checks, without a promise scheduling gap. A 10-second timeout,
partial failure or inconsistent post-state leaves the session UNKNOWN and disables
further writes. It does not cancel a running editor operation or retry it.

Operation completion, structural validation, visual review and game behavior are
separate. Even a confirmed operation has structural/visual/runtime `NOT_RUN`.
An upstream numeric score, zero return value or an empty issue list cannot promote
those outcomes. Status exposes only a bounded last-operation receipt and does not
claim an authenticated loaded source revision.

## Local files and secrets

The preparation function creates a fresh, unpredictable package directory; it
never merges, overwrites or cleans an existing destination. Names are a fixed
allowlist, links/reparse parents are refused, and POSIX uses exclusive/no-follow
file creation plus a held directory descriptor. Packages must be outside both
Git checkouts/worktrees and the evidence CAS. On POSIX the directory is mode 0700
and files mode 0600. Windows ACL guarantees and real Windows behavior are untested.

`guarded-plugin.js` and `client-private.json` contain a generated session secret.
Never commit, upload or put them into the CAS. Only a manifest of hashes and
NOT_RUN outcomes is captured in the existing Store. A mid-write failure preserves
its partial directory for inspection and will not reuse it.

This is **not an OS sandbox or protection against malicious same-user processes,
other trusted code or a human concurrently editing the model**. Inventory checks
are not a full digest of every model property. Sequence/receipt state is in-memory
and does not survive plugin/process restart. Discard the package after a run or
UNKNOWN result; do not reconnect/replay it after restart. Persistent recovery,
exclusive host ownership and actual loaded-byte attestation remain prerequisites
for later automated live integration, not guarantees of this slice.

## Source findings and fixes

Exact source review, rather than README inference, established that:

- `new_project` returns `get_status().project`, which has no UUID field. The guard
  binds the actual new Project object; a fixture regression covers that exact
  response shape.
- `create_texture` has a 400 ms fallback that may return before image loading
  actually completed. The guard separately requires complete image and matching
  natural dimensions. A response alone is not texture readiness.
- Direct export actions write caller-selected paths, and save can trigger a UI
  action before the file operation completes. They remain unavailable here;
  protected export/capture is still an M2 task.
- Original dispatch resolves `commands[action]`, and autostart is enabled by a
  persisted UI setting. Replacing dispatch and removing the autostart block are
  deliberate local changes, not claims about default upstream safety.

Source: [the pinned plugin](https://github.com/sosadly/blockbench-mcp/blob/028cdd76589de2e2cea51bfd79495b50a3c7d1d2/plugin/blockbench_mcp.js), specifically `get_status`, `new_project`, `create_texture`,
`dispatch` and `buildUI`.
The modification recipe does not redistribute the full plugin. Preserve the
upstream license/attribution when preparing the private local derivative.

## Verification and environment

- Exact selected-file baseline: unchanged `storage.py`, `asset_contract.py`, and
  79 existing M1 contract regression tests; all Git blob hashes checked.
- Fresh selected-checkout suite: **130 pytest tests passed, zero failures/skips**.
  This is 79 unchanged regressions plus 51 new tests. One new test runs the
  **52 Node guard checks**; do not add those again as independent pytest tests.
- Tests use real local CAS/file operations and a real JavaScript guard with a
  **fake editor host**. Transformation seams are small explicit source fixtures.
  CLI error handling and generated JavaScript syntax are checked.
- RED was observed before implementation and before fixes for the microtask race,
  real upstream status shape, NaN clock, autostart, invalid config error mapping,
  and secret package placement. Partial-write and late-completion cases are tested.
- Final review is **author self-review**, not an independent subagent review.

No complete source archive was available in the execution container. Positive
transformation of the full pinned plugin and loading that derivative in Blockbench
were **NOT RUN**. Wrong-pin rejection and transformation mechanics are not proof
of full upstream compatibility. Missing editor APIs fail closed.

No full-repository/PostgreSQL CI, desktop Blockbench, live Forge, screenshot,
render, Windows, network synchronization or performance result is claimed.
Historical 726-test and Forge evidence retains its old tested revision.
Container DNS prevented cloning and Durable workflow status remained unavailable.
The exact additive patch was later recovered from the conversation artifact and
published through authenticated GitHub write tools. No merge, manual workflow
dispatch, runner/visibility change or plugin installation is implied by publication.

## Reproduce and next resume

In a checkout with this additive patch applied, Python 3.11+ and pytest installed,
and Node.js available, run:

```sh
PYTHONPATH=src python -m pytest -q
```

The full repository suite (including configured PostgreSQL) must also run before
integration. The selected-file result above cannot substitute for it.
For offline preparation only, on the later host with the actual pinned source:

```sh
PYTHONPATH=src python -m kneekura_tech_hub.minecraft.asset_guard \
  --store /path/to/existing/cas --request EXISTING_REQUEST_SHA256 \
  --upstream /path/to/pinned/blockbench_mcp.js --parent /private/outside-git
```

This defaults to writes disabled. `--enable-writes` is an explicit local opt-in,
not permission to install the derivative or skip live acceptance.

Resume **M2**, not M3: first validate complete pinned-source transformation and
fresh isolated desktop lifecycle; then integrate an explicit bounded writer,
texture painting, required-view rendering and protected export/capture. Retain
native `.bbmodel`, Java item JSON, PNG and review hashes in the existing CAS.
Only after live asset acceptance proceed to Forge packaging, client verification,
and the single real-MOD repair cycle. Real providers/Core caller acceptance and
Twilight-first/Connector-next research remain on the original unified plan.
