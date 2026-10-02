# KNEEKURA-LAB monorepo migration — 2026-10-02

Status: **SOURCE MIGRATION COMPLETE; MONOREPO WIRING INTEGRATED ON THE CURRENT BRANCH**

## Decision

KNEEKURA-LAB is no longer treated as a required separate source repository for Minecraft MOD-AI work.
Its source, contracts, tests, Viewer/SimLab history and current Debug Workspace/Tank implementation now live under:

`departments/minecraft/lab/`

The architectural boundary remains logical rather than repository-level:

- Tech Hub knowledge/Core/TaskContext decides what is known, what evidence exists and what verification is needed.
- The LAB subtree owns bounded Minecraft experiment control, observation, capture, restoration and evidence production.
- Target MOD repositories remain separate products and are not absorbed into the LAB subtree.

## Exact import provenance

- source repository: `genkimorimori252525-oss/KNEEKURA-LAB`
- source revision: `f2d6165b16587672ac56f83c001c65bc2fa6d06a`
- raw Tech Hub import commit: `c7461ef2da1dbfe137b73fa16b6c26b225bc427f`
- imported Git-managed source blobs: **348 / 348 non-.github blobs**
- deliberately not imported: the two repository-specific LAB GitHub workflow files under `.github/workflows/`

The raw import commit precedes monorepo-specific edits so the migration boundary can be audited independently.

## What remains outside Git

The old LAB data policy is retained. Generated runtime directories, Minecraft worlds, local configuration, credentials, private logs and machine-specific evidence are not made repository source merely because LAB moved into Tech Hub.

The legacy KNEEKURA-LAB repository is not deleted by this migration. It remains a historical/source-origin reference until the user chooses otherwise.

## CI and source identity

Tech Hub CI now reads LAB directly from `departments/minecraft/lab`. A separate private LAB checkout and its deploy key are no longer required. The still-separate target MOD checkout retains its own repository-scoped read-only credential where needed.

`departments/minecraft/mod-ai/verification/lab-source-pin.json` schema v2 records the in-repository path plus the original LAB import repository/revision and the separately pinned target MOD revision.

## AI usability

The Minecraft TaskContext inspects the vendored LAB source automatically. Therefore a coding agent can discover that the experimental verification surface exists without being handed an external LAB checkout or registry merely to locate source.

This does **not** grant execution authority. A same-repository LAB source is still distinct from:

- a live owner/session;
- a disposable verification world;
- loaded-runtime identity;
- an authorized experiment/control registry;
- successful Minecraft/GameTest/client evidence.

Task routing keeps those states BLOCKED/UNKNOWN until their existing explicit contracts are satisfied.

## Migration boundary

Historical documents can continue to mention the standalone KNEEKURA-LAB repository when describing past runs and source pins. Current implementation and new work should use the monorepo path as the canonical source location.
