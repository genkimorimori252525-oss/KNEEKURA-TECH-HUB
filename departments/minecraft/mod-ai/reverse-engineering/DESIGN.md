# Opt-in reverse-engineering toolkit — design and implementation plan

## User intent
Add CFR, Vineflower and REA to TECH HUB, reusing a similar existing department.
Do not make unrelated AI tasks read these documents, inspect installations,
install dependencies, start providers or register MCP servers.

## Placement and existing implementation
Baseline: `e5149661a696cded69f6f7dd6db9bfbdeea06337` (main, 2026-10-17).
`src/kneekura_tech_hub/minecraft/providers.py` already implements an explicit,
hash-verified Vineflower adapter with captured classpaths and CAS provenance.
Its blob is `6a75753f898567fd944cba590e9498db66a1272d`. Keep it unchanged.
Place this optional tool shelf under the same MOD-AI department. No competing
top-level department, no global AGENTS/skills/MCP configuration, no new Core
imports or package dependencies. Non-Minecraft REA investigations can reuse
this shelf, but their findings remain in the owning project's research lane.

## Interfaces
- `toolkit.py catalog`: static tool descriptions; no installation checks.
- `toolkit.py install TOOL`: explicit acquisition of only the selected tool.
- `toolkit.py decompile TOOL INPUT --run NAME`: isolated local Java comparison.
- `toolkit.py provider-config`: emit config for the EXISTING Vineflower adapter.
- `toolkit.py rea -- ...`: explicit pinned CLI, never automatic setup/MCP.
All runtime files live in this directory's ignored `.local` by default.
REA itself may maintain upstream-owned user cache/state after explicit use;
this wrapper does not change that undocumented internal storage contract.

## Trust and resource boundaries
Use exact versions, verified Java tool bytes and immutable copies of inputs.
The Java comparison never launches the target application. REA is an explicit
CLI passthrough; operations that execute targets need their own authorization.
Record input/tool/library/output hashes, command, exit status and limitations.
Outputs are derived candidates, not original source or runtime proof. No
third-party binaries, full decompiled trees, node_modules or private paths
belong in Git. Installation is NOT a sandbox for untrusted native providers.

## Implementation plan
1. Write cold-start/selection/integrity/argv/receipt tests; observe RED.
2. Implement dependency-free Python CLI and pinned local installation recipe.
3. Keep detailed instructions scoped; expose only a short optional shelf link.
4. Run the local source contract suite. Add path-filtered CI with no tool
   installation, plus explicit manual real-tool smoke verification.
5. Inspect diff, publish an isolated branch/PR, and distinguish source tests,
   hosted tool tests and owner-PC verification in the final report.

## Review focus
Missing or corrupt selected tools must fail without automatic downloads.
Paths with spaces must stay single argv elements; no shell expressions.
An existing run directory or input must never be overwritten.
Provider failure, timeout and empty Java output must not produce a success claim.
An unrelated task or catalog/help request must never probe Java/Node/REA.

## Execution evidence
Local shared-PC connection was unavailable; work uses a standalone change set
against the observed main, not a claim of access to uncommitted owner work.
Test and publication results are recorded in VERIFICATION.md after execution.
