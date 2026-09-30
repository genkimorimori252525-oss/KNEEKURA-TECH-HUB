# Local AI handoff — Minecraft MOD-AI asset/runtime integration

> Historical handoff. The current executable/environment state is in
> [the 2026-09-30 continuation](CONTINUATION-2026-09-30.md). The native-capture
> RED below was resolved before that continuation; retain it as history, not
> as the current resume task.

Date: 2026-09-28  
Repository: `genkimorimori252525-oss/KNEEKURA-TECH-HUB`  
Draft PR: #74  
Working branch: `jolly/minecraft-mod-ai-assets-2026-09-28`  
Latest executable-code head reviewed for this handoff: `824a2365a0ac945620f26a15339b352ac0de35f6`

This file is the resume point for a local coding agent. Read it together with the
authoritative unified plan and spec. Do not reconstruct the project from chat history.

## Authoritative documents

1. Plan: `docs/superpowers/plans/2026-09-28-minecraft-mod-ai-unified.md`
2. Scope/spec: `departments/minecraft/mod-ai/ASSET-INTEGRATION.md`
3. M1 checkpoint: `departments/minecraft/mod-ai/assets/IMPLEMENTATION-2026-09-28.md`
4. M2 guard checkpoint: `departments/minecraft/mod-ai/assets/GUARD-IMPLEMENTATION-2026-09-28.md`
5. Hosted M2 guard evidence: `departments/minecraft/mod-ai/assets/GUARD-HOSTED-VERIFICATION-2026-09-28.md`
6. This handoff: `departments/minecraft/mod-ai/LOCAL-AI-HANDOFF-2026-09-28.md`

The plan is visible on the PR branch even though #74 is still a Draft and is not merged
into main. Work on this branch unless the human explicitly chooses a different branch.

## Product intent

Build a Minecraft MOD-development AI environment that can investigate the exact target
environment, learn from upstream source/bytecode and failure/repair history, generate
code and assets, build them, operate the real game, observe the result, repair failures,
and retain evidence for later work.

Do not replace the existing KNEEKURA knowledge core. This work lives in the existing
Minecraft MOD-AI application/research layer and reuses its Store/CAS, ProjectProfile,
source intelligence, Forge execution, Observer, GameTest oracle, and history.

Selected asset backend: `sosadly/blockbench-mcp` pinned at
`028cdd76589de2e2cea51bfd79495b50a3c7d1d2`.
Vibecraft remains reference-only, not an accepted Forge 1.20.1 runtime dependency.

## Current progress

### M0 — plan fusion
Complete.

The previous MOD-AI plan and the Blockbench/runtime plan are fused into one ordered plan.
No duplicate `labs/` platform, scheduler, database, or autonomous Mod Agent service was added.

### M1 — strict asset request + read-only sosadly preflight
Complete at its recorded scope.

Implemented:
- strict static Java-item asset spec and StyleProfile;
- exact Forge 1.20.1 / Forge 47.x / Java 17 profile binding;
- existing-CAS retention;
- read-only loopback provider probe;
- strict response IDs/envelopes/deadlines/size bounds;
- no retry, redirect, mutation, arbitrary script, plugin install, or source-attestation claim;
- CLI check/prepare/probe.

Historical hosted proof for the M1 branch recorded 726 passing tests. Do not reinterpret
that as Blockbench desktop or Minecraft client acceptance.

### M2 — guarded disposable editor/write/capture path
Partially implemented and currently at a deliberate RED checkpoint.

Implemented before the current RED:
- `asset_guard.py` pins exact upstream plugin bytes before generating a guarded derivative;
- raw Blockbench routes are closed behind `kneekura_asset` / `kneekura_asset_status`;
- `execute_script`, plugin install/uninstall, raw save/export/load/close and raw geometry routes
  cannot bypass the guard;
- write permission is explicit and disabled by default;
- fresh/isolated editor state and project object identity are enforced;
- sequencing, single in-flight operation, lease expiry, project switching and unknown completion
  fail closed;
- no blind retry after an uncertain write;
- private token-bearing package output is prohibited inside Git/CAS and refuses overwrite;
- model/texture/view capture was moved toward an inline, no-filesystem-authority evidence path;
- `asset_session.py` now drives one guarded session and only writes captured evidence to CAS
  after the expected session finishes.

The last green hosted checkpoint before the newer capture/session work was the guard-preparation
slice at `f0194b55c51ea8c1af651673c985bb4a82ace398`: 777 tests passed, 0 failed.

## Current RED / exact next bug

Latest executable-code head:
`824a2365a0ac945620f26a15339b352ac0de35f6`

GitHub Actions run:
`36398566854`

Synthetic PR test merge recorded by the artifact:
`d500634a9c05b9186db71ec74e24b0559de3dcff`

Observed result:
- **787 passed**
- **2 failed**
- **8 pre-existing warnings**

Artifact:
`10959037802`
(`hub-tests-d500634a9c05b9186db71ec74e24b0559de3dcff`)

The two failures describe one unfinished interface:

1. `tests/test_minecraft_asset_guard.py::test_node_guard_contract_suite`
   - Node subtest: `capture native returns inline bbmodel JSON without filesystem authority`
   - current guard rejects `kind: "native"` with `INVALID_CAPTURE`.

2. `tests/test_minecraft_asset_session.py::test_successful_session_captures_inline_artifacts_to_existing_cas`
   - test expects artifacts:
     `model, native, texture, front, left, back`
   - current `run_session()` captures only:
     `model, texture, front, left, back`.

This is the first resume task. The intended direction is **not** to weaken the tests or fall
back to filesystem paths. The unified plan requires the editable native `.bbmodel` artifact.
Extend the same bounded inline capture contract to `native`, then make the session collect,
validate, hash, and retain it in the existing CAS.

## Immediate implementation order

1. Stay on #74's working branch and re-run the focused tests before editing:
   `python -m pytest -q tests/test_minecraft_asset_guard.py tests/test_minecraft_asset_session.py`
   Confirm the two failures above rather than assuming this handoff is still current.

2. Complete RED→GREEN for pathless native capture:
   - guard accepts exactly `{kind:"native", view:null}`;
   - host capture produces bounded UTF-8 `.bbmodel` JSON without caller-supplied path;
   - capture envelope has a fixed kind/MIME/encoding contract;
   - guard validates bounded JSON before CONFIRMED;
   - `asset_session._capture_bytes` validates native bytes separately from exported Java model;
   - session capture order includes native;
   - CAS artifact metadata preserves the distinction between exported Java model JSON and
     editable Blockbench native source.

3. Keep raw `save_project`, `export_project`, `export_model`, arbitrary paths,
   `execute_script`, plugin install and load-project routes blocked. Do not solve native
   capture by granting filesystem authority.

4. Run focused tests, then the full repository suite. Only move on when green.

5. After the no-path model/native/texture/view capture interface is green, continue M2:
   - use the exact pinned source to prepare the guarded package;
   - exercise it in a disposable real Blockbench desktop instance;
   - create only the first Celestial Staff fixture;
   - capture required views;
   - keep structural / visual / runtime verdicts separate;
   - do not call fixture tests or screenshot existence a visual PASS.

6. Only after live desktop acceptance, decide the narrow final export/write boundary needed to
   materialize `.bbmodel`, Java item JSON and PNG into a disposable Forge workspace.
   Preserve no-overwrite and path-scope invariants.

Then continue M3→M5 exactly as the unified plan states.

## Important invariants / do not redo

- Do not rebuild Source Intelligence, Observer, GameTest, Store/CAS, ProjectProfile, or history.
- Do not reapply older conversation ZIPs or patches.
- Do not merge main/#71/#72/#73 unless the human explicitly requests it.
- Do not introduce a second MOD-AI database, scheduler, runtime authority, or `labs/` product.
- Do not silently upgrade Forge or Java.
- Do not trust README claims as compatibility evidence.
- Do not treat loopback connectivity as plugin-source attestation.
- Do not expose the private guard token to CAS, Git, logs, or provider error text.
- Do not retry a write whose completion is uncertain.
- Do not turn upstream numeric scores, `check_model`, screenshots, or build success into an
  automatic aesthetic/runtime PASS.
- Keep Twilight Forest before Sinytra Connector for the planned upstream research sequence.
- Keep actual Vineflower/tiny-remapper execution and Core caller acceptance on the remaining list.

## Local-agent startup checklist

Suggested resume commands:

```bash
git fetch origin
git switch jolly/minecraft-mod-ai-assets-2026-09-28
git pull --ff-only

python -m pytest -q tests/test_minecraft_asset_guard.py tests/test_minecraft_asset_session.py
# after the focused RED→GREEN fix:
python -m pytest -q
```

Node is also required by `test_node_guard_contract_suite`; it runs the real guard factory
against a fake editor host and is not live Blockbench evidence.

Before claiming M2 complete, perform the real desktop acceptance named in the plan. If the local
environment cannot launch/operate Blockbench, leave that item NOT_RUN/BLOCKED rather than
substituting unit tests.

## Evidence discipline

Every future checkpoint should state separately:
- exact repository head tested;
- exact external source revision;
- whether evidence is fixture/local desktop/Minecraft;
- test counts and failures;
- structural, visual, runtime verdicts;
- anything still NOT_RUN.

Do not erase the current RED history. It records why native capture was added and gives the next
agent a concrete failing contract to satisfy.
