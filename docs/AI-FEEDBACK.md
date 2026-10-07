# KNEEKURA TECH HUB — AI Feedback Ledger

Created/revised: 2026-10-07. English compression requested by the user; existing AF IDs, observations, decisions and verification history are preserved below.

Record failures, missing information and useful repairs so future AI work avoids repetition. This is an operational ledger, not automatic implementation approval or canonical Evidence/Claim/Review Decision. Follow [guide](PROJECT-GUIDE.md), [Constitution](../governance/CONSTITUTION.md), the knowledge-core [feature freeze](architecture/CORE-FEATURE-FREEZE-v1.md), and the selected department/tool design. Correct rejections and intentional omissions are not defects. Core freeze is not a project-wide ban on approved department work.

## Record and review

Record reproducible failures, repeated research/operation friction, documentation drift, unmet required workflows, regressions, or evidenced license/provenance/authority/integrity weaknesses. Label speculative ideas explicitly; never invent failures or causes.

1. Read related open, verified and rejected entries before work.
2. Append a unique increasing `AF-NNNN`; link duplicates instead of erasing prior observations.
3. Separate facts, hypotheses and proposals. Include minimal reproduction, exact error/exit, revision/path, expected vs actual result and unverified scope.
4. Preserve dated corrections, rejection reasons and recurrence history. Update the index to the latest state; resolve concurrent ID conflicts before combining changes.
5. Prefer an existing tool, corrected docs/procedure or test-only proof before production changes. Recording an idea does not authorize code/policy/config/migration changes.
6. After a repair, append relevant regression/DB/runtime results and rollback conditions. Keep secrets, credential-bearing DSNs, personal data and full third-party content out of the ledger. Record only known actor IDs/versions.

States: `RECORDED` -> `INVESTIGATING` -> `PROPOSED` -> `APPROVED` -> `IMPLEMENTED` -> `VERIFIED`; `DEFERRED`/`REJECTED` retain reasons and reconsideration conditions. These describe work, not mandatory transitions. PROPOSED is not approval; APPROVED requires actual authorization; IMPLEMENTED is not verified; VERIFIED is limited to recorded checks.

Impact: `BLOCKING` = required workflow blocked; `QUALITY` = authority/integrity/regression/wrong-decision risk; `FRICTION` = workflow/discovery cost. These are not truth scores.

## Adoption gate

Require an observed need consistent with the applicable design (and core freeze for core changes); reproduction/evidence; affected invariant; why existing paths are insufficient; the smallest repair and explicit non-goals; expected results and regression checks; costs/risks and rollback/reconsideration conditions.

Preserve revision/locator/hash/authorship, Evidence roles, counterevidence, applicability, ambiguity and history. Do not add unnecessary public API/schema/dependencies or a second canonical store. Prefer docs -> procedure -> verification -> narrow code repair. Test-only proof that the existing path works is a valid resolution. If evidence is insufficient, defer or reject.

Reject improvements that:

- impersonate human reviewers or automate canonical merge/support/validation;
- choose a winner by stars/score or hide competing Claims/counterevidence;
- replace NO_MATCH with fuzzy recommendations or turn uncertainty/errors into success;
- remove guards/audit/license checks to satisfy tests;
- overwrite Evidence/reviewed Claims with current upstream facts;
- claim skipped DB tests or pure-Java/static checks prove Minecraft runtime behavior.

Measure the original failure and protected behavior, not speed/test count alone. Legitimate rejection must remain rejection after a repair.

## Entry template

```markdown
### AF-NNNN — Short title

- Date/actor: ISO timestamp with timezone; known ID/version or unknown
- Kind/impact/state: FAILURE | GAP | IDEA / BLOCKING | QUALITY | FRICTION / RECORDED
- Context: task/PR/AF links; commit and dirty scope; OS/tool versions; DB/runtime use
- Facts: expected, actual, impact and unknowns
- Reproduction/evidence: minimal input, command, exit/error, stable path/locator
- Hypothesis: possible cause and contrary/unconfirmed evidence
- Existing paths: alternatives checked; why sufficient/insufficient
- Minimal proposal/non-goals: docs-only option first
- Quality: protected invariants/authority/provenance/history; added risks
- Adoption checks: reproduction/regression/DB/runtime; expected outcomes/metrics
- Rollback/reconsideration: trigger and history-preserving method
- History (append): date / state / decision-maker / evidence / command+result / limits
```

## Index

| ID | Issue | Latest state | Impact |
| --- | --- | --- | --- |
| AF-0001 | Shared AI workflow and feedback entry point | VERIFIED | FRICTION |
| AF-0002 | Historical ambiguous guidance JSON acceptance | VERIFIED | QUALITY |
| AF-0003 | Dedicated read-like CLIs apply migrations | RECORDED | QUALITY |
| AF-0004 | Local-only analysis policy exceeds Git exclusions | RECORDED | QUALITY |
| AF-0005 | Incorrect standalone overlay preflight example | VERIFIED | QUALITY |
| AF-0006 | Remote handoffs reference tools absent from this checkout | RECORDED | QUALITY |
| AF-0007 | Local core mistaken for project-wide feature coverage | VERIFIED (docs only) | QUALITY |
| AF-0008 | NaturalGhast requirements exceed current Tank fixture coverage | RECORDED | QUALITY |
| AF-0009 | Private observer omitted resource-pack metadata | VERIFIED (observer loading) | FRICTION |
| AF-0010 | Arena receipt hashing mistaken for Node action serialization | VERIFIED (scoped owner) | QUALITY |
| AF-0011 | Opt-in mob POV with explicit image retrieval | VERIFIED (scoped camera) | FRICTION |

## Light audit — 2026-10-07

Read AF0001..0011 and checked relevant source contracts; this is not a new DB/runtime or whole-Hub audit. AF0001/0002/0005/0007 retain their original limited verification; AF0009/0010 remain scoped native results, not full flight PASS. AF0003/0004 are unobserved operational risks, not reproduced accidents. No entry warrants weakening rejection, authority, provenance or quality checks.

Keep AF0006 open for cross-checkout availability: this camera work selects an isolated TANK_CORE source at `6b7456278b25e1f8ac3fbeb416ee7ee9a525c542`; it does not synchronize every remote research/danmaku branch into the old user checkout. Current PR96 head matches that base; previous LAB inspection `c369953` remains historical evidence. Existing Tank rotation already supports a custom bounded geometry recipe; geometry generation requires its separate pre-experiment maintenance registration, not implicit expansion of the experimental action grant.

AF0008 corrections remain applicable: physical size, MOD profile, action bounds, player acquisition and mob motion testing are separate. AF0011 is now authorized for the first implementation slice; it remains unimplemented/unverified until checks are recorded below. Feedback suggestions do not authorize unrelated core, dependency or policy changes.

## Records

### AF-0008 — NaturalGhast requirements exceed current Tank fixture coverage

2026-10-07; GAP/QUALITY; RECORDED. User approved the initial NaturalGhast flight/perception/frontal-anchor slice and identified `TANK_CORE` as the Tank. Source: NaturalGhastmod redesign v0.5 and `docs/CODEX-HANDOFF-2026-10-07.md` at `4e6f1bdd9b9869c516a487f1e3ca35729e7bb4bf`; implementation/repair `8d6d839` in the isolated `C:/Users/genki/Documents/Codex/NaturalGhastmod` checkout. LAB source `c3699539388af68495ff1529af3576ff4926e9bc` in the private profile checkout.

Facts: original Tank interior 19×19×11 cannot contain a 4×4 boss at the specified 22–34 block frontal distance. `debug-workspace/bridge/owner-grant.mjs` excludes Player subjects; `KneekuraDebugArenaController` permits wait, teleport-subject and set-block operations. These are intentional authority limits, not defective rejection. Initial registered launch correctly rejected a host/target source revision mismatch; an actual Forge47.2.0 host failed loading the Forge47.4.10 target with `NoSuchMethodException: SoutouGhastMod.<init>()`. Original85file hashes remained unchanged; the failed owned process was stopped. A clean-source build of the repaired target passed (18s); pure-core22 and mapped swept-AABB3 assertions passed. These checks do not prove native player perception or full flight.

Existing path: opt-in NaturalGhast tools register its own source identity/materials, select the LAB host separately, override only the new private launch to Forge47.4.10, and use a fresh original-save copy. Limited native idle/clearance/render evidence is distinct from full combat verification. No production LAB dependency, original-world resize, existing-config overwrite, shortened combat range or reduced entity size.

Proposal: before the next native movement slice, define a bounded registered player-observation fixture and sufficiently large private Tank using existing owner-managed maintenance where applicable. Seal the player/camera operations, source/world identity, owner lifetime and budgets; measure declared scenarios and retain raw/canonical evidence. The current registered owner cannot be bypassed by an unregistered probe that sets targets or camera input. This proposal is not implementation approval for new LAB operations.

Adoption gate: verify takeoff from floor, wall departure, acceleration/braking/turn, frontal recovery, jitter vs sustained turn, LOS loss and subject change; include negative permission/identity/expiry tests and cleanup/original-world hashes. Group coherent scenarios into one bounded window when geometry and authority allow it. Reuse original rejection evidence and record PASS/FAIL/INCONCLUSIVE/NOT_RUN separately. Reject fixes that weaken owner gates, hide incomplete native coverage or infer visual quality from READY.

Reconsider after an approved fixture/owner extension or an existing adequate path is evidenced. Append actual native outcomes and retained run locators; do not replace historical failures. Full-host compatibility, multiplayer, final balance and danmaku remain outside this initial slice.

History, 2026-10-07: `foundation-0ZDlpd` at NaturalGhast `9b19f53e8895eb0d3784b60f4bc10d31cfe79c88` passed scoped idle/clearance/render: preflight READY with CURRENT freshness,40active idle ticks,4×4collision-free body, actual renderer/raw frame,29canonical observations, clean shutdown and EVIDENCE_COMPLETE finalization. Original85files/hashes unchanged. Earlier `foundation-47Z5xJ` remains a rejected preflight: explicit brightness=false contradicted the bright resource and newest client sample could be later than the owner file's clock. Corrected the display profile and used a preceding unchanged retained sample, preserving the age/identity/lease guards. Native player-facing/flight coverage remains NOT_RUN; this entry stays RECORDED for the fixture gap.

Correction, 2026-10-07, after user clarification: 19×19×11 describes the retained fixture, not a universal Tank size limit. `TANK_CORE` selects a MOD profile, not geometry. LAB `SimScenario.FloorSpec`/`SimArena` expose `floor.radius` and `wallHeight`; a fresh private fixture can be enlarged and registered with its actual new baseline. The owner action scope is separate: `owner-grant.mjs` currently limits each edge to64 and volume to4096 and excludes Player action subjects. These limits do not prohibit a larger physical world or read-only player observation. Do not enlarge authority implicitly when changing geometry.

Correction, 2026-10-07: NaturalGhast's `SoutouGhastAnchorGoal` operates on visible `LivingEntity` targets; normal `SoutouGhast.registerGoals` acquisition selects Player. A registered development-only mob target fixture can cover motion/facing/LOS behavior without a fake-player MOD, but does not validate normal player acquisition or the player's visual experience. Prefer existing fixtures/instrumentation; add dependencies only after a demonstrated gap. Mob POV proposal: AF-0011.

### AF-0001 — Shared AI workflow and feedback entry point

2026-10-07; GAP/FRICTION; initial RECORDED. [README](../README.md) covered common operations but lacked a consolidated 14-CLI guide, side-effect warnings and continuous AI feedback workflow. Sources: [entry points](../pyproject.toml), [CLI code](../src/kneekura_tech_hub/) and pre-task document inventory.

Repair: add this ledger and guide, linked from README; no CLI/policy/schema changes. Keep detailed contracts authoritative. Checks: help/entry-point consistency, links/whitespace, sample preflight.

History, 2026-10-07: IMPLEMENTED -> VERIFIED. All 14 executable `--help` calls exited 0; base preflight exited 0; 25 related tests passed. AF-0005 corrected the overlay example. DB/runtime/external acquisition were not verified in that work.

Correction, 2026-10-07: this verification covered the local knowledge core only. The first guide did not sufficiently inventory the wider remote Hub. See AF-0007; preserve those valid core checks without treating them as full-project coverage.

### AF-0002 — Historical ambiguous guidance JSON acceptance

2026-10-07; FAILURE/QUALITY; initial IMPLEMENTED. Past acceptance recorded duplicate object keys and NaN/Infinity reaching DB open; this was not a new failure in this task. Sources: [acceptance](architecture/CONTEXT-GUIDANCE-QUERY-SURFACE-v1.md), [parser](../src/kneekura_tech_hub/guidance_cli.py), [adversarial tests](../tests/test_context_guidance_cli_adversarial_json.py).

Existing repair: `_reject_duplicate_object_pairs` and `_reject_non_finite_number` reject before DB access. Preserve exact JSON types/matching; do not normalize ambiguous input.

History, 2026-10-07: IMPLEMENTED -> VERIFIED. `.venv/Scripts/python.exe -m pytest -q tests/test_context_guidance_cli.py tests/test_context_guidance_cli_adversarial_json.py tests/test_validator.py tests/test_bundle.py tests/test_minecraft_department_contract.py`: 25 passed, exit 0. Real DB path untested.

### AF-0003 — Dedicated read-like CLIs apply migrations

2026-10-07; GAP/QUALITY; RECORDED. Nine dedicated CLIs call `apply_migrations` when opening repositories, including history/context/check. Evidence: [selection](../src/kneekura_tech_hub/selection_cli.py), [support](../src/kneekura_tech_hub/claim_support_cli.py), [extraction](../src/kneekura_tech_hub/selected_file_extraction_cli.py); [guidance](../src/kneekura_tech_hub/guidance_cli.py) does not.

No actual migration accident/permission failure reproduced; initialized DBs need not change schema every call. Mitigation: document side effects and confirm destination/authority. Only consider separating reads/initialization after a real operational failure, preserving write workflows and drift protection. Reproduce on a disposable DB with pending/no-pending migrations and varying permissions before proposing API changes.

History, 2026-10-07: static behavior confirmed; warnings added. No DB reproduction or core-change adoption.

### AF-0004 — Local-only analysis policy exceeds Git exclusions

2026-10-07; GAP/QUALITY; RECORDED. [Minecraft policy](../departments/minecraft/README.md) keeps raw checkouts/JARs/decompiled trees/full assets local; [.gitignore](../.gitignore) does not exclude every analysis destination. No license violation or leak was established.

Mitigation: use workspace-external raw storage, inspect Git additions, avoid unrelated `git add .`. A future narrow exclusion change requires actual storage paths and user permission for settings changes. Do not hide derived inventories/runtime evidence/distributable outputs. Check representative raw and derived paths with `git check-ignore -v <path>`; reconsider on concrete mis-addition or required storage standardization.

History, 2026-10-07: warnings added; `.gitignore` unchanged.

### AF-0005 — Incorrect standalone overlay preflight example

2026-10-07; FAILURE/QUALITY; initial RECORDED. The guide draft incorrectly listed standalone overlay checks. `kneekura-hub bundle-check pilots/incremental-computation-relations-v1.json` exited 1:

`INVALID BUNDLE: cl:salsa:query-incremental:narrower-than:incremental:e021c01d references missing record: ev:salsa:readme:query-model:e021c01d`

Cause: [CLI](../src/kneekura_tech_hub/cli.py) calls [preflight_bundle](../src/kneekura_tech_hub/bundle.py) without a repository; overlays depend on base Evidence/entities. Correct rejection, not a core bug. Repair only the example and explain base-first ingestion/repository-backed offline preflight; do not weaken validation or duplicate canonical base records.

History, 2026-10-07: IMPLEMENTED -> VERIFIED. In-memory preflight exited 0: base 18 records, base-backed relations 1, then problems 4. Both overlays were rejected alone as expected. No persistent DB writes.

### AF-0006 — Remote handoffs reference tools absent from this checkout

2026-10-07; GAP/QUALITY; RECORDED. NaturalGhast's current handoff references Tech Hub JavaFX authoring, Youkai Homecoming and JujutsuCraft research. Local HEAD `379c6b372522f744acc4698f5396787c9f056dbb` lacks these paths; remote main/draft branches have different coverage. Treating the local 14-CLI guide as all current remote tooling would mislead later AI work.

Evidence/mitigation: the [guide feature map](PROJECT-GUIDE.md#availability-and-feature-map) pins main/draft source documents and distinguishes local availability. No source synchronization or runtime launch was performed. Before future use, select the required reviewed revision and isolate any import from dirty work; verify paths/help/identity without claiming unmerged drafts are the main baseline. Remains RECORDED for local tool acquisition/integration; documentation mitigation does not install tools.

### AF-0007 — Local core mistaken for project-wide feature coverage

2026-10-07; FAILURE/QUALITY; initial RECORDED. Actor: this coding agent; model version not established. The user requested a reusable project/tool guide and later identified missing Kobun and danmaku capabilities. Expected: route future work across the actual multifunctional Hub. Actual: the initial guide concentrated on the stale local checkout's 14 core CLIs and two MOD targets, then focused remote follow-up on one consumer project. That scope could hide existing tools or cause duplicate implementation.

Reproduction/evidence: local HEAD `379c6b372522f744acc4698f5396787c9f056dbb` lacks MOD-AI/LAB/JavaFX/Kobun paths. GitHub main `c9145ec5376aeeff59995b8c20f7b839f810ab6e` adds the 15th console entry `kneekura-minecraft` and integrated LAB; draft PR90/93 and PR97 contain Kobun and JavaFX Score authoring. The revised [feature map](PROJECT-GUIDE.md#availability-and-feature-map) pins these source documents and their limits. User correction, not a production crash, exposed this documentation failure.

Cause: local availability was allowed to define project coverage; branch/PR discovery was not performed before presenting the first inventory. Source files and a current local catalog were insufficient because they predated department integration and later independent branches.

Repair: inventory main, all branch refs and open PRs before choosing relevant entrypoints; route knowledge core, MOD-AI/assets, LAB/Tank/Motion/Decision, Vanilla maps/AI, Kobun, optimization, danmaku, Airborne, aircraft physics and preservation/research separately. Read current handoff/acceptance and source when README checkpoints conflict. Remove the consumer-specific README link as requested; do not expand that separate write-up. No production code, settings, source synchronization or runtime changes.

Quality/adoption checks: links resolve at their pinned commits; PR draft/base/head status matches the reviewed listing; executable examples match parser/script contracts; local and remote commands are labeled separately. Never promote an offline prototype, source Atlas, compile receipt, scoped pilot or branch presence into runtime/full-project PASS. Branch stacks do not merge independent work. Prefer compact routing and authoritative links to copied manuals.

Rollback/reconsideration: correct the affected row when a head/interface/status changes; append evidence and retain prior failure history. Remove unsupported claims, not authority/identity/validation guards. A new lane or user correction triggers another scoped inventory.

History, 2026-10-07: RECORDED -> IMPLEMENTED. Inventoried 126 branch refs and 54 open PRs; inspected relevant main/draft documents, Python parser routes and LAB package scripts. Broader guide and README navigation corrected. Not an audit of every branch/file; remote applications were not installed or launched.

History, 2026-10-07: IMPLEMENTED -> VERIFIED (documentation scope only). Checked 18 pinned remote source paths against non-truncated Git trees, 50 local link occurrences/anchors, Markdown references/fences/whitespace and English guide/ledger prose: no failures. Ten listed PR-stack relationships match the retained open-PR base/head records. JavaFX launcher inspection additionally confirmed hash-pinned dependency downloads and unsupported Score smoke. `git diff --check -- README.md docs/PROJECT-GUIDE.md docs/AI-FEEDBACK.md` exited 0; explicit content checks covered the untracked documents. `.venv/Scripts/python.exe -m pytest -q tests/test_context_guidance_cli.py tests/test_context_guidance_cli_adversarial_json.py tests/test_validator.py tests/test_bundle.py tests/test_minecraft_department_contract.py`: 25 passed, exit 0. These core tests do not exercise the remote department tools, DB or Minecraft; AF-0006's installation/integration gap remains open.

### AF-0009 — Private observer omitted resource-pack metadata

2026-10-07; FAILURE/FRICTION; IMPLEMENTED. NaturalGhast `tools/tank/run-foundation-tank.mjs` initially packaged the private observer with `mods.toml` but no `pack.mcmeta`. Forge47.4.10 loaded the target mod, then stopped at `LoadingErrorScreen`; raw private-client frame text identified `observer.jar failed to load a valid ResourcePackInfo`. Earlier run `foundation-qTKGQS` recorded `READY timeout after 180000ms`; finite read-only UI diagnostics in `foundation-6EraWM` identified the cause. These failures were integration-tool mistakes, not authority failures or evidence of target combat behavior. Retained local artifacts are under `C:/Users/genki/Documents/Codex/NaturalGhastmod/build/tank/`.

Repair `883f9f0`: add required pack-format15 metadata to the new private observer artifact and assert it is present before launch. No loading-warning suppression, GUI auto-approval, owner bypass or original-world changes. Preserve the clean target/source build, exact registration, bounded runs and separate producer identities. Future disposable observer JARs need both Forge mod metadata and Minecraft resource metadata before native launch; compile alone is insufficient.

Verification: native outcome pending at this entry's creation; do not mark VERIFIED merely because the ZIP member check exists. Reconsider if a metadata-bearing observer still reaches the warning screen; retain its actual frame, loader error, source/artifact identities and owned cleanup result.

History, 2026-10-07: IMPLEMENTED -> VERIFIED (observer loading only). `foundation-0ZDlpd` passed the declared native pilot and produced a raw SoutouGhast frame; owner/preflight READY, clean stop and EVIDENCE_COMPLETE. The original warning was removed by valid metadata, not suppression. Full target behavior remains outside this entry's verification scope.

### AF-0010 — Arena receipt hashing mistaken for Node action serialization

2026-10-07; FAILURE/QUALITY; IMPLEMENTED. The NaturalGhast offline Tank adapter initially assumed Node `stableJson` was interchangeable with `KneekuraDebugActionJournal.canonical` for an arena baseline. Run `foundation-w0UWGp` reached DEBUG_READY, then correctly rejected owner installation with `ARENA_BASELINE_MISMATCH`; canonical evidence shutdown acknowledged clean, and original85file hashes matched. Java's typed Gson pose numbers retain `0.0`; JSON parsing and Node serialization produced `0`. The two contracts are not interchangeable. The same journal's comment explicitly distinguishes internal receipts from exact Node action-sidecar bytes.

Repair `3d99b6c`: place the offline preparation adapter in the LAB package and reuse its package-private typed-Gson canonical/sha256 functions, as the existing private fixture adapter does. Only development preparation changes; no production dependency, canonical implementation fork, hash normalization, baseline replacement after observation, relaxed owner gate or reflection. Keep Node registration/request byte hashing separate from Java arena receipt hashing.

Before native use, inspect the exact producer/consumer serialization contract and test representative typed numeric values, arrays and poses. Native owner acceptance, exact subject/geometry checks and cleanup remain required; a plausible predicted hash is not measured authority. Verification pending at entry creation. If rejection recurs, inspect real geometry/pose/source before proposing further changes; do not manufacture the observed baseline into the registered request to force PASS.

History, 2026-10-07: IMPLEMENTED -> VERIFIED (scoped owner installation). `foundation-0ZDlpd` installed ACTIVE_SCOPED_CONTROL against the exact predicted Java baseline, passed READY/preflight with finite lease, and finalized canonical evidence after clean stop. Native owner verification, not the helper hash alone, supports this result; original85file hashes remained equal. This does not validate unregistered player actions or larger flight scenarios.

### AF-0011 — Opt-in mob POV with explicit image retrieval

2026-10-07; IDEA/FRICTION; VERIFIED (scoped camera). User requests a Tech Hub mob-eye camera based on spectator viewing, with retrieval only when requested and no continuous recording/data growth. Purpose: inspect orientation and scene composition during bounded Tank behavior work. The following proposal/source notes retain their original historical context; current implementation and measured scope are appended below.

Inspected source: LAB `c3699539388af68495ff1529af3576ff4926e9bc`, `debug-workspace/forge-bridge/.../KneekuraDebugCardinalCapture.java`, `KneekuraDebugCaptureRestoration.java`, and `debug-workspace/evidence/visual-capture.mjs`. Existing cardinal capture already owns client camera takeover/restoration and durable PNG delivery, but freezes the server and requires the exact `cardinal-4-snapshot-v1` rig/four sequential views. It cannot be relabeled as a live mob-eye camera. No native mob-POV trial was performed in this proposal work.

Recommended first slice:

- Opt-in live view of one exact, loaded mob UUID in the owned private Tank. Preserve the running AI/server ticks; observer remains a spectator. Do not turn, move, retarget or possess the mob through camera input.
- Explicit attach/return plus bounded lifetime; no automatic startup activation. Resolve the actual eye pose/orientation through Minecraft's render camera, not a guessed body pose. Document species-specific rendering/effects and interpolation.
- View-only mode writes no images, frame telemetry or video buffers. A finite control receipt may record attach/return/failure for restoration accountability; do not persist per-frame view data.
- Explicit snapshot request writes one bounded PNG and compact metadata: target UUID/type, run/source identity, dimension, observed camera pose/FOV/viewport, client render tick/partial tick and independently available server observation references. Missing/unpaired time stays UNKNOWN; do not claim same-tick state from proximity.
- Reuse the existing owner/identity, budget, evidence delivery and restoration mechanisms where their contracts apply. Give mob POV a distinct request/artifact contract; preserve cardinal capture unchanged. Serialize camera ownership so simultaneous capture/view requests cannot overwrite each other's state.
- Return on request, expiry, target unload/death, world change, owner loss or disconnect. Restore only the still-owned client presentation fields and a valid previous camera; otherwise use the current local player's camera when available and record uncertain restoration. Never restore stale entity/world objects or write entity transforms back.

Non-goals: automatic recording, rolling pre-roll, background image export, fake-player MOD acquisition, production target-selection changes, video encoding/new dependencies, replay reconstruction or evidence that the AI perceived everything rendered. Mob-eye RGB is a visualization; LOS, sensing, targets and decision evidence remain separate.

Alternatives: manual vanilla spectator switching has the lowest implementation cost and is suitable for immediate inspection, but lacks UUID-bound automation and capture/restoration receipts; extending the current frozen cardinal rig would confuse live behavior evidence and is rejected. Prefer manual viewing until the new operation is implemented and verified. Short bounded image sequences/video can be considered later only on explicit request and with duration/frame/byte limits; do not add them by default.

Adoption checks, grouped into one work unit: attach/snapshot/return; default view produces zero frame files; exact UUID and runtime identity rejection; repeated request and camera-ownership conflict handling; expiry/death/unload/disconnect restoration; no server tick hold or mob transform/AI writes; moving/rotating mob camera tracking; raw image/metadata correspondence; finite artifact budget and original-world preservation. Static/compile tests do not establish real-client behavior. Record actual camera-induced presentation/state changes rather than claiming zero observer effect.

Risks/costs: new client operation/artifact contract, species-dependent camera effects, observer influence and restoration races. If state isolation, pairing or restore ownership cannot be established, stop automatic viewing and retain the failed receipt; use manual inspection while correcting the smallest affected seam. Keep finalized evidence immutable.

History, 2026-10-07: user intent recorded; source contracts inspected; design proposal only. Implementation and native acceptance NOT_RUN. Written design/implementation approval remains pending.

History, 2026-10-07: APPROVED by user: implement this camera work after a light feedback audit, before NaturalGhast. Scope is opt-in live view plus explicitly requested single PNG, no constant recording; implementation design/plan saved under `docs/superpowers/`. Native acceptance is still NOT_RUN. No repeated intermediate approval is inferred necessary after the explicit instruction to enter implementation.

History, 2026-10-07: IMPLEMENTED -> VERIFIED (scoped). Local `codex/mob-pov-camera-20261007` adds `mob-eye-live-v1`, `MOB_POV_CAMERA`, immutable attach/snapshot/return indices0..31, shared camera ownership, finite lease/capture limits, durable PNG retrieval/finalization and bounded restoration receipts. Python/LAB must come from that branch; the original dirty checkout is not upgraded. No extra MOD/dependency, automatic activation, frame history or server tick hold. Read the branch's `departments/minecraft/lab/debug-workspace/bridge/MOB-POV.md`.

Verification: Python rig/contracts97 PASS; control147 PASS/3 Windows symlink cases deselected after the full run exposed missing1314 privilege. Related Node99/99 PASS; broad Node515 =511 PASS/3 FAIL/1 SKIP (two Windows symlink EPERM, one existing inherited-pipe expectation). Genuine-Gson Java lifecycle/ownership/overlay18 and commands8 PASS; ordinary/Tank/mob-POV Node-Java interoperability and actual Forge47.2 compile PASS. Full portable JVM runner remains blocked by its earlier Windows symlink fixture. Preserve those limitations; do not weaken guards or call every suite green.

One independent whole-branch review found two Important issues, both repaired with RED->GREEN regressions: exclude derived motion overlays from a pending raw snapshot, and retrieve/seal a late canonical PNG under OUTCOME_UNKNOWN without rewriting its immutable receipt. A native clock race also required sampling default owner-validation time after asynchronous inputs/status reads; explicit supplied clocks and lease gates remain unchanged.

Native acceptance: frozen saved Reimu, exact private TANK_CORE copy; LAB `546ebfe6d645904f7d2c178ac68d44a3a508d4d2`, host `7f14960999bc2955d85ae9d3619090ad37817c38`. `C:/temp/kneekura-mob-pov-20261007/mob-pov-4k50LD/sealed-audit.json` is PASS: default imageCount0; server ticks141->161/gameTime40448->40468; exactly one requested640x480 PNG (47598 bytes, SHA256 `3cdf3ce1bdd37046f0181ced9835757991937d30db01288892d90426d63473e8`); explicit return and EXPIRED both RESTORED; clean evidence shutdown/dropped0; EVIDENCE_COMPLETE; original85 files unchanged. PNG visually inspected at the raw scene stage, without derived labels/HUD. Server reference remains asynchronous, not same-tick or AI-perception evidence. Observed class-resource/container linkage is not resident transformed-class attestation.

Keep the original pilot report FAIL: its final assertion read a cached prior-return status before the expiry observation arrived. The independent read-only auditor verifies the later immutable sealed observation and image; it does not rewrite reports/receipts/finalization. Pilot report SHA256 `b01642131cc307e0dda1c76ea1cffbaf3d1cdffcf5ac688b40cb0a8745a52d2e`; finalization SHA256 `41fdff2556b4cec6fdbe002445059bb9c6163c7a04682c776777375e0069e773`. Future pilot waits for the actual EXPIRED row and fresh command-index4 inactive status; that corrected end-to-end waiting sequence was not rerun. Earlier failed trials remain retained: absent heartbeat field, declared640x360 vs actual640x480, asynchronous clock race, cached pre-attach status. Correct the affected harness/reader; never alter sealed inputs or replay uncertain commands to manufacture PASS.

Remaining scope: moving/dead/unloaded mobs, external camera/screen/world interruptions and species-specific presentation require separate bounded native checks. Pure lifecycle coverage is not client acceptance. Deferred minor: numeric `validatedAtNanos` rejects negative JVM clock origins or JavaScript-unsafe values (~104 days uptime); future string/relative-time artifact revision, not relaxed authority. Late UNKNOWN lookup is bounded to16MiB canonical observations. NaturalGhast/player acquisition, AI perception and flight remain outside this camera result. Roll back automatic use if ownership/restoration/source binding cannot be established, preserving failed receipts and finalized evidence.
