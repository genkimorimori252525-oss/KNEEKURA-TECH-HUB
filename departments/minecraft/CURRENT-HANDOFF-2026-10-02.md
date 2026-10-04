# KNEEKURA Minecraft — Current Handoff

Date: **2026-10-02**  
Status: **CURRENT ENTRY POINT — supersedes older files that call themselves "current"**  
Canonical development line: **`main`**  
Confirmed implementation merge: **`8e73ddc23b133e5a075cf58e3c7b850274f21017`**

## Local execution handoff

For the complete remaining-work sequence from the 2026-10-02 Water Tank / Vanilla AI session, use:

- [LOCAL-EXECUTION-HANDOFF-2026-10-02.md](LOCAL-EXECUTION-HANDOFF-2026-10-02.md)

It includes the real local Vanilla Foundation Map generation, unfinished Vanilla AI research, the **still-unimplemented On-Demand Sampled Motion Trace plan**, Entity Decision Observatory implementation, MOD adapter proofs, and final integrated verification.

## Read this first

This file is the current entry point for a fresh human or AI working on the Minecraft lane.

Older handoff, status, plan and acceptance documents remain intentionally preserved as historical evidence. Their original claims are not rewritten. If an older document says a feature is still deferred, unimplemented or located in a separate KNEEKURA-LAB repository, treat that statement as historical unless it is repeated here or in a newer dated acceptance record.

## Repository layout

The Minecraft engineering system is now one Tech Hub monorepo:

```text
departments/minecraft/
├─ mod-ai/       knowledge, TaskContext, evidence contracts and MOD-making AI interfaces
├─ lab/          bounded experiment/observation apparatus, Tank, capture and retained SimLab/Viewer history
├─ mods/         modern analyzed MOD technology (ANCHOR / FRONTIER)
├─ kobun/        historically isolated ancient MOD analysis (ORIGINAL-first)
└─ design/       architecture and acceptance design records
```

`departments/minecraft/lab/` is the canonical LAB source for new work. The old standalone `KNEEKURA-LAB` repository is retained only as source-origin/history unless explicitly needed for historical evidence.

The raw LAB migration boundary is commit `c7461ef2da1dbfe137b73fa16b6c26b225bc427f`, imported from `KNEEKURA-LAB@f2d6165b16587672ac56f83c001c65bc2fa6d06a`. The import was verified 348/348 by Git blob SHA and file mode with missing 0, mismatch 0 and extra 0.

## Current architecture

- **Tech Hub / MOD-AI** owns knowledge, target identity, provenance, TaskContext, experiment contracts and retained result interpretation.
- **LAB subtree** owns bounded runtime control, Arena/Tank observation, capture, restoration and evidence production.
- **Target MOD repositories** remain separate products and retain their own exact source/build identity.
- Same-repository LAB source discovery is **not execution authority**. Experiment registry, owner/session, disposable-world authority and loaded-runtime attestation remain explicit gates.
- UNKNOWN/PARTIAL/NOT_RUN/BLOCKED/INCONCLUSIVE are valid outcomes and must never be rounded into PASS.
- Restoration and cleanup evidence remain first-class verification, not postscript bookkeeping.

## Current LAB capability

The current source includes the bounded Arena/action path, owner lifetime/control, Cardinal capture/restoration, trigger capture, finalized evidence/export, Tank presentation, Forge bridge/runtime observation and retained Viewer/SimLab regression infrastructure.

Historical G1/G2 documents under `lab/docs/` and `lab/debug-workspace/README.md` still contain earlier milestone wording. Use them for history and contracts, not as the current implementation checklist.

## AI usability

`task prepare` remains the compact AI-facing entrance. It can expose the vendored LAB capability without requiring an external LAB checkout, while preserving existing research/asset/build/GameTest routing priority.

Source presence alone does not add a side-effecting `experiment.prepare` action. That path appears only when the explicit experiment adapter/registry prerequisites are supplied.

## Verification baseline

The LAB integration merge on PR #74 reached `04d2923a638db406c033a27e94ace41bf8a6ba81`.

At that head:

- complete Tech Hub suite: **3,142 passed / 332 skipped / 8 warnings**;
- push and PR Tech Hub workflows: SUCCESS;
- push and PR monorepo LAB source workflows: SUCCESS;
- LAB source gate covered the complete LAB source suite, portable Java bridge/owner/camera contracts, Python↔Node registration, scoped-control/export roundtrip, actual Forge compilation against the pinned MOD source, dependency source contracts and pinned MOD unit/resource regressions.

A follow-up monorepo audit identified and repairs the observer Git-scope issue: observer identity must describe the `departments/minecraft/lab` subtree, not unrelated Tech Hub working-tree changes.

## Canonical branch and historical PRs

`main` is now the single authoritative implementation line.

The former stacked Minecraft development lineage has been consolidated:

- PR #71 is contained in main and recorded as merged;
- PR #72 and PR #73 are closed as historical review checkpoints, superseded by the final integrated line;
- PR #74 was retargeted directly to main and merged as `8e73ddc23b133e5a075cf58e3c7b850274f21017`.

A fresh agent must start from `main`, not from the former #71–#74 branch stack.

The Bedrock Wither artifact work remains separate in PR #75 and is now based directly on `main`. It is not part of the confirmed general Tech Hub/MOD-AI/LAB baseline until separately accepted.

## Data and publication boundary

The GitHub repository is currently **public**, even though the project is private/internal in purpose. Never interpret public repository visibility as permission to publish runtime/private data.

Do not commit:

- Minecraft worlds or production saves;
- `debug-runtime/` or generated `run/` data;
- local `config.local.json`;
- credentials, tokens, deploy keys or owner secrets;
- private machine paths/log bundles unless deliberately minimized and reviewed.

The relevant ignore rules remain under the repository root and `departments/minecraft/lab/.gitignore`.

## Do not redo

Do not recreate the LAB as another repository, add a second MOD-AI database, weaken evidence/authority gates, retry uncertain mutations, merge version/loader tracks, or treat historical RED/UNKNOWN records as obsolete mistakes.

Start from `main`, inspect this handoff, then use the specific dated evidence/acceptance document for the subsystem being changed.
