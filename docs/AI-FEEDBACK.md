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
| AF-0012 | Bounded flight fixture and acceptance repairs | VERIFIED (static flight) | QUALITY |
| AF-0013 | Native filesystem error loses operation location | RECORDED | FRICTION |
| AF-0014 | Unintended saved Reimu retained in NaturalGhast Tank | VERIFIED (offline preparation) | QUALITY |
| AF-0015 | Camera-relative anchor mistaken for boss-owned region | VERIFIED (scoped motion); visual pending | QUALITY |
| AF-0016 | Original-save inspection performs sector-padding writes | VERIFIED (recovery/mitigation) | QUALITY |
| AF-0017 | Selected-subject observation mistaken for whole-Tank coverage | APPROVED scope; written design review pending | QUALITY |
| AF-0018 | Tank operating guide omits existing end-to-end procedures | VERIFIED (documentation) | FRICTION |
| AF-0019 | Camera usability and moving-Boss POV acceptance | APPROVED scope; written design review pending | FRICTION |

## Light audit — 2026-10-07

Read AF0001..0011 and checked relevant source contracts; this is not a new DB/runtime or whole-Hub audit. AF0001/0002/0005/0007 retain their original limited verification; AF0009/0010 remain scoped native results, not full flight PASS. AF0003/0004 are unobserved operational risks, not reproduced accidents. No entry warrants weakening rejection, authority, provenance or quality checks.

Keep AF0006 open for cross-checkout availability: this camera work selects an isolated TANK_CORE source at `6b7456278b25e1f8ac3fbeb416ee7ee9a525c542`; it does not synchronize every remote research/danmaku branch into the old user checkout. Current PR96 head matches that base; previous LAB inspection `c369953` remains historical evidence. Existing Tank rotation already supports a custom bounded geometry recipe; geometry generation requires its separate pre-experiment maintenance registration, not implicit expansion of the experimental action grant.

AF0008 corrections remain applicable: physical size, MOD profile, action bounds, player acquisition and mob motion testing are separate. AF0011 is now authorized for the first implementation slice; it remains unimplemented/unverified until checks are recorded below. Feedback suggestions do not authorize unrelated core, dependency or policy changes.

## Records

### AF-0012 — Bounded flight fixture and acceptance repairs

2026-10-07; actor coding agent, exact model version unestablished; FAILURE/GAP, QUALITY, VERIFIED for static-flight scope only. User authorized continuing NaturalGhast and prioritizing evidenced tooling problems. Follow AF0008: TANK_CORE is a MOD profile; physical geometry, observation target and bounded mutation authority are separate. No authority/config/dependency expansion.

Expected: actual Player acquisition, visible frontal arrival, inertial braking and compact drift. Initial private preparation exposed several correct rejections: `flight-RzdfJx` LAB-only fixture test under product test sources; `flight-ynfKNZ` UNSUPPORTED_CLASS_ANCHOR; `flight-d2a0jq` UNCONTROLLED_BLOCK_STATE; `flight-VPYIdi` OWNER_ACTION_ORDER_MISMATCH after its first VERIFIED journal; `flight-pxuVE6` two verified operations then OUTCOME_UNKNOWN / AccessDeniedException:null. The I/O operation is unreported; its cause remains unconfirmed (AF0013). `flight-pN18hN` acquired a real Player and accelerated, but its narrow wall aperture occluded the distant eye ray; AI correctly decelerated and held. Keep all failures, not retroactive PASS.

Repairs: developer-only mapped tests under `tools/tank`; supported MOD-class/container plus whole artifact binding (other compiled hashes are declarations); STONE inside the registered Arena; bounded owner idle+next-ID wait rather than replay; offline prepared aperture with one sealed-cell activation and lower eye-ray clearance. Whole-unit review additionally caught inward annulus chords, unsampled diagonals and acceptance false positives. Regressions now require full drift chord feasibility, actual candidate body sweeps and measured LOS/frontal arrival/continuous braking/moving drift. Do not relax palette/identity/order/lease checks or infer observed behavior from a primitive label.

History, 2026-10-07: Native trial `C:/Users/genki/Documents/Codex/NaturalGhastmod/build/tank/flight-92WZ2m`, target `b9938e6d017b9764bd460d2b4ce62c9889c9283c`, LAB `57bd4e011b1072bf143c9643a1b50ef0a5531954`, clean host `7f14960999bc2955d85ae9d3619090ad37817c38` with private Forge47.4.10 override. PASS_STATIC_PLAYER_ACQUISITION_FLIGHT_MOBILITY: room56x16x56, one action VERIFIED,600 contiguous samples/556 Player-target samples/531 visible frontal comfortable samples; maximum speed0.65/displacement22.9201956, gradual braking and actual drift. Static survival Player pose was measured; all600 ghast bodies4x4/collision-free/NoAI=false/health10. Preflight READY CURRENT;217 canonical observations, clean stop/dropped0/EVIDENCE_COMPLETE, original85files unchanged. One explicitly requested640x480 raw PNG visually inspected; no production observer/recording dependency. Report SHA256 `0216e4746d742f849e53dc7894aa6474e21aa72d83625a9c8d50a4b8708b91ee`. Exact run paths/frame/finalization hashes and commands are in target `docs/FLIGHT-MOBILITY-VERIFICATION.md` and `docs/FLIGHT-FOUNDATION.md`.

Grouped verification: pure Java22+25, mapped body-sweep5, mapped fixture8, Node acceptance/owner-wait6 PASS; exact target compileJava/build PASS. One independent review Critical0/Important3/Minor0; Important repairs retained RED->GREEN. Failed native launches all stopped cleanly/finalized EVIDENCE_COMPLETE/original85unchanged. This is not full-host compatibility, full AI or full-Hub acceptance.

Remaining limits/costs: static fixture only; moving/facing-changing Player, subject replacement, deliberate LOS recovery, ground scuttling/landing, tactics/attacks/danmaku, multiplayer/performance/external impulses and full-room lighting/boundary readback remain unverified. Conservative clearance may reject ambiguous narrow paths. Artifact/class-resource linkage is not resident transformed-class proof. Reconsider fixtures or stop automatic use when actual scope/source/owner/cleanup cannot be established; preserve evidence and repair only the affected seam. Next target unit is tactics/repetition/Commit Points. AF0008 remains open for broader coverage, with this dated static-flight mitigation.

### AF-0013 — Native filesystem error loses operation location

2026-10-07; GAP/FRICTION; RECORDED. `flight-pxuVE6` owner status became OUTCOME_UNKNOWN/unsafe with `error=AccessDeniedException:null`; it retained two VERIFIED operations and an uncompleted next action. Clean shutdown/finalization/original preservation succeeded. No repeatability or exact failing I/O path was established; do not claim a generic filesystem defect is fixed by the next successful run.

Source fact: `KneekuraDebugOwnerConnection.reason(Throwable)` renders a FileSystemException as class plus `getReason()`, losing its operation/file location when reason is null. This hinders choosing between publication, journal reading, permission failure and another stage. A transient Windows read/replace conflict is only a hypothesis.

Proposal: on an evidenced recurrence, add a bounded stage/operation label and safe run-relative basename to diagnostic receipts/logs, preserving terminal UNKNOWN and the original cause. Avoid secrets/full external paths, automatic retries of mutations, broad access/permission changes or weakening guards. Before adoption, reproduce a denial at a known operation, verify useful bounded diagnostics plus existing authority/privacy tests, and measure its native cost. No implementation approved solely by this entry; diagnosis first. Reconsider if a reproducible native I/O failure blocks the next required unit.

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

### AF-0014 — Unintended saved Reimu retained in NaturalGhast Tank

2026-10-08; QUALITY/FRICTION; VERIFIED (offline fixture preparation only). The user observed Reimu in the NaturalGhast manual Tank and requested its exclusion. Neither `TANK_CORE` nor the generic Tank contract requires Reimu; the target's foundation/flight preparers had retained, frozen and repositioned a saved seed entity. An unrelated resident could interfere with later experiments.

Repair: both NaturalGhast preparers use `tools/tank/TankSeedEntities.java` to remove exact root `touhou_little_maid:reimu` entries only in bounded room chunks of a newly created, exclusively locked private save. Record `seedReimuRemoved`; preserve other IDs/NBT. Do not remove TLM instrumentation, rewrite live/finalized saves, or strip an explicit subject fixture such as AF-0011. This is consumer fixture policy, not a universal species prohibition.

Verification: mapped helper compilation and5 seed-filter/8 geometry checks PASS; launcher syntax checks PASS; related owner/result Node6 PASS. Fresh flight/foundation readback removes1 Reimu each, preserves3/2 other root entity NBT respectively, and adds one active NaturalGhast. No new client launch or visual acceptance claimed; previously prepared/live Tank copies still contain their original fixtures. Evidence: NaturalGhast `build/tank-seed-work/` logs and `docs/FLIGHT-FOUNDATION.md`. Original-preservation inspection failed initially and was recovered as recorded separately in AF-0016.

### AF-0015 — Camera-relative anchor mistaken for boss-owned combat region

2026-10-08; FAILURE/QUALITY; RECORDED. The user reports missing Ghast floating, excessive attempts to enter the Player's view, and jerky movement. Clarified requirement: retain a broad boss-selected world-space region during combat; reselect only when necessary; allow free swimming rather than a roughly10-block home. Numerical tuning is delegated.

Evidence: v0.5 current code recomputes the anchor from Player position/smoothed facing, HOLD converges to zero velocity, and drift uses8-tick commitments with quiet intervals. These establish a design/implementation mismatch; they do not prove every cause of visible jitter. The earlier static-player600-sample acceptance remains valid only for its declared v0.5 scope. It cannot establish facing-changing behavior or desired visual quality.

Documentation mitigation: NaturalGhast redesign v0.6/handoff now specify a retained region, camera invariance and soft range preference. `docs/superpowers/specs/2026-10-08-combat-region-swimming-design.md` proposes open-space40×16×40, sustained physical3D swimming, reasoned reselection/hysteresis, preserved clearance/observation gates and grouped deterministic/native checks. Product movement rewrite awaits written-design review; this entry remains RECORDED. Prioritize this correction before tactics/danmaku. Do not fix presentation by removing collision checks, tracking hidden targets, adding a second velocity writer or replacing motion with renderer bobbing. Reconsider sizes/commitment tuning using bounded real motion and client inspection, preserving failed evidence.

History,2026-10-08: AF-0015 RECORDED -> IMPLEMENTED -> VERIFIED (math/lifecycle and static-player physical swimming only). User approved the design and inline continuation, reserving visual judgment. NaturalGhast product `340e315a948228ef9723e13c173dbba0f4a50bae`, finite Tank/analyzer `e91fcbf02173d9db558a5f1a1e077ab1b647a672`: persistent world-space20/8/20 radii, no Player-look reads for region ownership, observable-only target geometry, soft range,40–120-tick swimming commitments and eased intent. Keep one physical velocity owner and swept4×4 safety. Identical blocked region proposals do not restart the encounter. Broad-waypoint interior margin fixed a simulated inertial boundary overrun, without shrinking the region.

Checks:12034 region/swimming+22 controller/orientation+25mobility, mapped clearance5 and fixture5seed/10geometry, Node13 PASS; Forge build successful.4000 simulated physical ticks span31.03 horizontal/10.48 vertical with rest0. Native `flight-e3CRdb` target JAR SHA256 `cd86f7c0ee8b4e8b21de3320d466b0b1554006a4b295b0bdf40e290519d1e1d8`, LAB `17bed2d161824f3e1b682ea3f1ff9e5714f1d684`, host `7f14960999bc2955d85ae9d3619090ad37817c38`, Forge47.4.10:600 samples, retained generation1,508 swimming samples span19.31 horizontal/8.77 vertical, stopped0,maxspeed0.44;391 canonical, clean/EVIDENCE_COMPLETE, original85 hashes/count unchanged. Separate stopped-native-save copy confirms Reimu0/Ghast1 (AF-0014 scoped follow-up); original/finalized NBT was not opened.

Native camera-turn/moving-Player/LOS and subjective smoothness remain PENDING_USER/NOT_RUN; pure lifecycle assertions do not certify them. Fresh manual-only52×24×52 Tank uses the same verified JAR, no observer, recording disabled, wall omitted offline and a small raised observation platform. Read the target's `docs/COMBAT-REGION-SWIMMING-VERIFICATION.md` for exact scope, preserved RED/failure evidence and manual path. Prioritize newly observed bugs before adding tactics or danmaku; retain old static-frontal receipts as historical v0.5 evidence.

History,2026-10-08 (reviewed artifact): one fresh review found0 Critical/2 Important/0 Minor. Both reproduced and fixed: persistent blocked RETURN now falls back to a feasible local broad region; analyzer includes stopped BRAKE/HOLD tails and rejects changing region generations. Final core12036/22/25, mapped clearance5, fixture5seed/10geometry, Node15 and Forge build PASS. Source `182fcb7ee88084c5dc1aecaba6cfa870cefa13b0`.

Final native receipts remain immutable FAIL: `flight-kPfHZB` stopped before movement acceptance with `OWNER_OUTCOME_UNKNOWN:AccessDeniedException:null` (AF-0013); `flight-5jC8dG` rejected changed camera angles under its static-look condition. User later confirms occasionally moving the camera; do not repeat the same static trial or rewrite its result. The latter's separate `final-measured-audit.json` passes measured motion only:600 samples, generation1,560 swimming samples, spans24.68/6.44, stopped0,maxspeed0.44; Player position fixed, observed yaw/pitch spans12.30/16.80. Both clean/EVIDENCE_COMPLETE/original85 preserved. Latest exact JAR SHA256 `6c5d2156e9ad83d437d3106721221c13e5221531c1518a069274564364ab3bca` is running in the fresh manual Tank with DEBUG0/no observer. Controlled camera/moving-Player/LOS and visual acceptance remain pending. Source/paths/hashes and scope: NaturalGhast `docs/COMBAT-REGION-SWIMMING-VERIFICATION.md`. AF-0017 records the separate whole-room coverage gap.

History,2026-10-08 (human observation): user reports the current Ghast looks very good. Record positive qualitative movement feedback for the current manual build, rather than treating all visual judgment as absent. No explicit controlled camera-turn/moving-Player/LOS protocol, combat balance or complete Boss acceptance was supplied; those scopes remain unverified. NaturalGhast also serves as a Tank trial; successful movement does not close camera/roster usability gaps (AF-0017/0019).

History,2026-10-08 (explicit movement acceptance): user is very satisfied with current retained-region movement and requests Tank improvements before continuing the MOD. Protect that movement as accepted qualitative behavior; do not shrink the region, stop swimming or alter combat targets to accommodate camera tooling. Controlled scenario/complete Boss acceptance remains separate.

### AF-0016 — Original-save inspection API performs sector-padding writes

2026-10-08; FAILURE/PRESERVATION; VERIFIED (recovery and workflow mitigation). Actor: this coding agent. Expected original-save read-only audit; actual Java `RegionFile` inspection appended zero padding to two original entity region files. Hash checks detected the mistake immediately. `entities/r.-1.0.mca` grew46003→49152 bytes; `entities/r.0.0.mca` grew25347→28672. All pre-existing bytes matched exact-hash backups; appended tails were entirely zero. Semantic NBT equality does not excuse violating preservation.

Recovery: secured exact pre-session-SHA256 copies, requested human authorization to overwrite the two files, received approval, checked unchanged incident hashes and an exclusive save lock, retained padded copies, then restored. All85 original file hashes and file count now match the pre-session inventory. No live/finalized run rewritten. Do not describe this as uninterrupted original preservation. Evidence: NaturalGhast `build/tank-seed-work/original-padding-incident.json`, `restore-original-entities/`, `restoration-result.txt` and prior `build/tank/flight-92WZ2m/original-hashes.json`.

Mitigation: inspect Minecraft NBT through a separate disposable baseline copy; verify original preservation using raw filesystem hashes/counts only. Subsequent foundation readback used that private baseline, not the original. Never assume a library constructor/close is read-only because no explicit save call was made. Before using a new reader on protected artifacts, test its byte-level side effects on a copy. This failure strengthens preservation checks; it must not justify relaxing them.

### AF-0017 — Selected-subject observation mistaken for whole-Tank coverage

2026-10-08; GAP/QUALITY; RECORDED. User asks whether this agent knows every Tank mob's x/y/z relative to room bounds and uses existing fixed cameras, after an unintended Reimu was missed. Facts: NaturalGhast's finite server supplement observes one fixed Ghast UUID plus Player/target data; movement conclusions use measured coordinates, velocity and collisions, not image estimates. However, earlier operation did not reconcile all room residents or use cardinal capture. Missing Reimu was incomplete fixture/coverage inspection (AF-0014), not evidence that all measurements were camera-derived. Current manual launch has DEBUG0/no observer; historical telemetry cannot be presented as current live coordinates.

Existing paths inspected on `codex/mob-pov-camera-20261007`: LAB `cli.mjs` evidence-entity/tank-status/tank-view; `evidence/tank-map.mjs` X/Z plus tick-vs-Y; `evidence/decision-view.mjs` also has fixed-isometric derived projection; Forge `KneekuraDebugForgeArenaBackend.inspectSupportedState` bounded action-AABB occupant guard; `KneekuraDebugCaptureSession.pose` and `KneekuraDebugCardinalCapture`; `bridge/MOB-POV.md`; NaturalGhast `ObserveFlightTank.java` and private manual preparer. Cardinal capture uses one detached camera, sequential north/east/south/west poses around registered Arena bounds, temporary pause/server hold, explicit delivery and restoration. It is not continuous four-camera monitoring, not necessarily whole-room coverage, and its poses may be occluded by the physical shell. Mob POV is another opt-in view, not a roster or AI perception. `tank-status` exposes presentation observations, not an entity enumerator; `tank-view` is selected-subject retained evidence, not live room discovery.

Minimal mitigation implemented: guide separates physical room/action Arena/grid/combat region, world/local coordinates, position/AABB, tick/freshness, selected/all-resident coverage, fixed snapshot/live POV/Player camera. Documentation/source checks verify these distinctions only. Whole-room on-demand live roster remains RECORDED: consider a bounded server-thread read-only request returning UUID/type/base position/AABB, dimension/room bounds/tick and loaded/truncated/unknown status; include nested passengers and boundary-crossing entities explicitly. No automatic history/images, chunk force-loading, entity mutation or authority enlargement. Reuse existing evidence/identity routes; do not create a second canonical store.

Adoption requires a written scoped design and tests distinguishing known subjects from unexpected residents (including Reimu), boundary overlap, unloaded scope and result limits. Useful follow-up: spatial map linked to one roster sample, with explicit timestamps and no invented walls. Reconsider if an existing pinned department route already exports the required roster; prefer that route and documentation over duplicate functionality. Rollback unsupported coverage claims while preserving failure history. Full Tech Hub runtime/tool coverage is not claimed.

History,2026-10-08: documentation mitigation verified against LAB source024973e and NaturalGhast source182fcb7. Existing Node Tank-map/status/cardinal-frame/decision-view checks32/32 PASS; `git diff --check` and local Markdown-link/fence checks pass. These are contract/presentation checks, not another native camera trial or implemented live roster. Original85 raw hashes/count remain equal; the user's open manual game was not paused or modified.

History,2026-10-08: user authorizes implementing feedback before further NaturalGhast work. Scope APPROVED; [written observation/camera design](superpowers/specs/2026-10-08-tank-observation-usability-design.md) is REVIEW_PENDING, not runtime implementation. Separate sealed room-read scope from unchanged action authority; roster samples are finite explicit requests. Current source has no such scope; Python/Node/JVM exact interfaces need coordinated changes. No original world or camera has been operated during this design preparation.

### AF-0018 — Tank operating guide omits existing end-to-end procedures

2026-10-08; GAP/FRICTION; IMPLEMENTED (documentation). User supplies an older MD and [matching Page](https://chatgpt.com/space/page_83f4ca35a65c81919f1b0b9eca36ff76), requesting missing instructions and AI-originated feedback. MD SHA256 `e42296a4295260bc1eefa85fe68d3a9f46ad78f8f7befc1561df87bb12580c43`; historical sourcec369953/PR96head6b745627. Existing common guide routed selected telemetry and cameras but omitted practical capsule generation/preflight, grid/native-bright semantics, rotation handoff, capture/control calls, legacy Viewer separation, cleanup/exit/finalization/export and comparison/handoff conditions. Missing use instructions do not imply missing source functionality.

Repair: compact English [Tank Operating Guide](TANK-OPERATING-GUIDE.md), linked from the mandatory Project Guide. Reconcile older facts against camera-branch source97a130f, current presentation/rotation/fast-iteration/MOB-POV contracts and Python/Node parsers. Preserve source availability, failure history, no default images, current52×24×52 offline/manual differences and AF-0017 whole-room roster gap. The legacy `/api/entities` source returns summonable-type catalog bytes, not resident UUID/position inventory; its presence does not resolve that gap. Do not launch a legacy controller alongside a scoped experiment to fill missing evidence.

Quality: documentation only; no config/owner/material/source pin changes, live-game operation, new dependency or camera activation. Require command/options/link checks and relevant existing contract tests before VERIFIED. Correct stale rows or examples if source changes; retain older Page/reference generations. Explicit improvements/failure notes after each coherent work unit are part of the AI handoff, including successful MOD work that reveals Tank limitations. This does not mandate a launch/test after every small edit.

History,2026-10-08: IMPLEMENTED -> VERIFIED (documentation scope). Page/export bodies match after reference-list blank-line normalization. Existing Tank CLI/resource/preflight/reproduction/guidance tests16/16 PASS; Python experiment/request-capture/mob-pov help confirms the published routes/options.55 local link occurrences, fences, unique feedback IDs,6 pinned source paths and diff whitespace pass. References use verified PR96 source paths so the original checkout need not install newer LAB for navigation; MOB-POV stays explicitly camera-worktree-local. No new native trial, fixed-camera or moving-Ghast POV acceptance claimed.

### AF-0019 — Camera usability and moving-Boss POV acceptance

2026-10-08; IDEA/FRICTION; PROPOSED. User invites more practical fixed-camera and spectator mob-eye options, with NaturalGhast as a Tank trial. Observed friction: fixed capture was not used during movement work; its deterministic poses bind the small registered Arena rather than necessarily framing the physical room, and opaque shells can obstruct a view (source-based risk, not a measured Cardinal failure). Scoped mob-POV native evidence uses frozen Reimu; current moving Ghast usability was not established. Preserve AF-0011's cached-expiry assertion failure and limited sealed audit; do not claim a new camera defect solely from an untested case.

Candidates, not implemented features:

- Read-only camera plan/preflight: summarize rig, subject, physical/presentation/Arena bounds, each fixed pose/FOV/viewport, declared capture slots, remaining budget and likely occlusion/coverage. Mark predicted visibility as predicted; actual per-view images/metadata establish visibility. Reuse prepared identities; planning grants no execution authority.
- Compact explicit capture workflow: select a predeclared slot, wait for durable completion and observed restoration, then return raw-frame references with synchronized frozen-state coordinates and an optional derived contact sheet. Keep originals/hashes and PARTIAL/UNKNOWN visible. Avoid forcing AI to reconstruct the operation from scattered files, without inventing a universal unregistered capture command or automatic screenshots.
- If deterministic poses cannot frame an opaque room, design a separately registered, bounded rig with feasible observation positions; keep v1's frozen four-image contract unchanged. Separate read-only observation volume from mutation authority. A live fixed view would need its own ownership/timing contract; do not relabel paused Cardinal as live monitoring.
- Validate existing mob POV on a moving NaturalGhast: camera motion/interpolation and actual viewport, advancing server ticks, zero default images, one requested snapshot, explicit/expiry return, death/unload/world change and external camera/input ownership. Diagnose sampled server-reference latency rather than claiming same-tick AI sight. These are grouped native scenarios, not constant recording or full Boss acceptance.
- Improve practical diagnostics around stale status, window/framebuffer mismatch, lost subject and camera ownership; inspect immutable operation index/late canonical frame before any retry. Preserve unknown outcomes and external-camera replacements. Reuse AF-0017 roster/spatial context rather than another entity store.

Adoption: prioritize one reproducible high-value friction point, use existing routes first, declare measurable completion/visibility/restoration/zero-history criteria, preserve failed evidence, and compare observer effect separately. Camera/input theft, entity teleport/AI freezing for live POV, hidden-target acquisition, lease renewal or bypassed validation are unacceptable shortcuts. New rig/schema or runtime behavior needs its own reviewed scoped implementation; this request records ideas, not deployment. Roll back a camera option if ownership/restoration/coverage cannot be established. Optional artifacts consume a declared finite budget; successful usability claims require native evidence on the intended moving species.

History,2026-10-08: user now authorizes implementation scope, superseding the preceding request's idea-only status. Read source7006c51 and NaturalGhast06686d9 before changing code. Two concrete limitations: `KneekuraDebugMobPovOwner.mob` restricts base position to the small action Arena; `KneekuraDebugMobPovCamera` requires spectator, while `KneekuraDebugScopedOwnerGate` rejects published integrated servers. The only real Player cannot simultaneously remain the combat target and become that observer. Do not solve this by modifying accepted Ghast behavior, adding a fake Player or removing owner checks.

Source-formula probe (not native capture): current action Arena min[7,224,6]/max[13,235,13] produces north[10,232.25,-3] and west[-2.5,232.25,9.5], both outside physical room[0,224,0]..[52,248,52). Proposed versioned fixed-eye poses stay inside an explicitly sealed read scope; proposed mob-eye observer mode preserves real Player game mode. Existing v1 modes/authority remain distinct. [Written design](superpowers/specs/2026-10-08-tank-observation-usability-design.md) covers roster/plan/bundle/v2 modes and grouped acceptance; written review and implementation plan are pending. No new rig, native result or camera practicality PASS is claimed yet.


### AF-0020 — External review tightens observation contracts

2026-10-08; REVIEW/QUALITY; IMPLEMENTED, native acceptance pending. Actor: this coding agent; input: human-supplied independent review (conditional approval). Independently checked local Node/Python/JVM source rather than adopting the review's unavailable GitHub commit claim. Adopted all seven amendments: separate half-open interior/physical/action semantics; immutable owner-wide sample budget; PARTIAL missing-not-absent and subset-order warning; discover then explicitly register/trace; retained prediction/native/unknown provenance; detached input-safe eye presentation requirement; structured/raw-reference/derived artifact roles. Qualifications: current owner already binds one request hash, and mapped MouseHandler turns Player; do not describe either as a proven exploit. Existing85-file audit is fixture-specific.

Implementation: sealed read scope, finite TANK_ROOM_ROSTER native reads/receipts/raw proof, camera-plan and original-slot inspect/capture-bundle, inward fixed rig v2 and v2 visual-packet lineage. Existing action authority/v1 behavior and accepted Ghast source/JAR are unchanged. Source tests exposed and fixed optional observation geometry initialization order and extra CLI index requirements; both have regressions. No continuous capture or implicit resident tracing.

History AF-0017: whole-room discovery is now IMPLEMENTED; prior omission/failure history remains valid. History AF-0019: A–D are IMPLEMENTED; E is BLOCKED/not released because real Player attack/use/hitResult and external-camera safety proof is NOT_RUN. Existing frozen-Reimu v1 acceptance does not certify moving survival-target Ghast POV. Prefer this partial verified capability to a camera option that might alter input or product behavior.

Verification (source scope): affected Node36/36; Python observation/Mob13/13 and explicit Python/Node36-file paired closure1/1 PASS. Genuine scope JVM7 checks PASS; final Forge compilation/pose/native results recorded below after execution. Full pure JVM runner and two broader Python tests encounter Windows symlink privilege1314; no assertions removed or false PASS. New finite native pilot uses the exact accepted JAR, fresh copies, requested two samples/four-frame set and raw original audit, without rebuilding product or adding observer MOD.

Reconsider E after a dedicated detached render-lifecycle implementation and native input/death/unload/world/external-camera tests. Protected quality: unchanged accepted swimming, real Player target, finite owner budgets, honest unknowns, exact evidence/source preservation. Adoption cost: one focused camera safety unit; no new library required. Further idea: combine one explicit roster sample with a derived spatial map showing coverage gaps and sample age, without turning it into live history.


History AF-0017/0019/0020,2026-10-08: A–D VERIFIED in a bounded fresh native fixture; [acceptance](superpowers/reports/2026-10-08-tank-observation-acceptance.md). Room samples67/86 record Player/Ghast with exact world/local coordinates, complete loaded scope and no Reimu row. Fixed v2 four-frame set COMPLETE/RESTORED, clean shutdown/VERIFIED_EXIT/EVIDENCE_COMPLETE; post-seal bundle/derived HTML read succeeds. Original85 historic raw hashes/count and exact accepted JAR unchanged. Ghast displacement0 during this fixture window: do not label it moving-subject acceptance. E remains BLOCKED/not released. Final affected Node38 and compatibility67 PASS; Python focused/paired14 PASS; wider78 PASS/2 SKIP/2 Windows symlink setup failures. JVM scope7/poses6 PASS. Fresh reviewer found two Important issues (UUID sort semantics and premature native PASS), both reproduced/fixed; no Critical/Minor. No re-review or product edits.

### AF-0021 — Build output readiness and useful camera coverage

2026-10-08; FAILURE/FRICTION/IDEA; MITIGATED in native A–D scenario. Actor: this coding agent. Initial finite trials exposed source-workspace/artifact provenance confusion, empty incremental bridge output after source-root transition, and private Gradle script syntax/task-creation order. A BUILD SUCCESSFUL/UP-TO-DATE line alone did not prove bootstrap classes existed; READY timeout followed. Preserve all failed trial reports/original audits. Repair: actual clean workspace registration distinct from accepted artifact source/hash; canonical bridge source root; actual class existence check; one reasoned forced build; real Gradle configuration check and lazy task matching; bounded explicit debug environment. Successful fresh trialgYNOOY records source and actual complete shutdown. Avoid routine clean/rebuild, broad Java termination, stale source pins or relaxed READY checks.

Images also reveal useful follow-up ideas: current inward fixed views cover the room, but a single Ghast near one corner is outside two views, and the one-block grid is visually dense. Neither is incomplete capture. Consider opt-in, retained-state subject-framing candidates and adjustable grid contrast in a separately reviewed presentation unit. Keep exact one-block geometry metadata, raw unmodified images, declared image budgets and UNKNOWN occlusion; do not silently auto-reshoot or infer absent residents from an image. Reconsider only after a concrete task shows the current two useful angles insufficient. Accepted broad-region swimming stays protected; improving Tank preparation/diagnostics is preferable to constraining the boss for observation.

### AF-0022 — Astra-guided prerequisites before non-danmaku development

2026-10-08; REVIEW/IDEA/QUALITY; IMPLEMENTED, verification recorded below. Actor: this coding agent; consultant: existing gpt-6-astra observation reviewer, one compact packet/response. User authorizes adopting its recommendations and keeping GitHub history. [Decision table](superpowers/plans/2026-10-08-astra-tank-followup.md): implement a retained roster spatial map and explicit bridge class readiness now; defer detached mob-eye E until native input/restoration proof; defer framing/grid changes until measured need; retain privileged symlink checks as blocked without weakened assertions. Initial NaturalGhast work does not require E. Preserve accepted broad swimming, real Player target, original saves/JAR and bounded private trials.

Map uses the existing canonical/raw-proof reader at the original sample index, derives X/Z/elevation/body and exact coordinate tables, displays tick/hash/PARTIAL gaps, and exclusively creates one requested HTML outside retained runs. Zero new world reads/images/registration or live history. Class readiness bounds selection to64 resources, rejects missing/invalid/mismatched bytes against selected output, and rechecks native pilot pins immediately before launch. It does not establish source freshness; no stale fallback/build suppression or routine rebuild. Source/native-owner provenance remains independently required.

Verification: new contracts first failed (missing implementations), then5/5 new checks PASS; affected observation compatibility18/18 PASS. Derived map successfully verifies the sealed native sample67 (`f3a934f7a263b8026d997e8ac5d5bc26551c4eb635a6747cf4f04420e9d552d0`) and writes outside its run. Genuine existing Forge output supplies11 valid selected resources; no new Minecraft launch/product build is needed for these read/derived helpers. This does not repeat moving-Boss acceptance or resolve the Windows privilege limitations. Original native receipt and accepted movement remain the baseline; no source/runtime upgrade is implied for the dirty original TechHub checkout.

History,2026-10-08: fresh whole-followup Astra review found one Important issue: the generic roster inspector can ingest pending raw evidence on an unfinalized run. Added an early read-only finalization requirement and direct retained canonical-row reading; no EvidenceRuntime initialization/ingestion in map export. RED→GREEN unfinalized rejection regression; final affected Node19/19 and Python13/13 PASS. Corrected map export from sealed sample67 leaves all38 retained run files byte-identical. The wider11-resource readiness check is separate from the unchanged eight-member native owner-linkage contract. No new native gameplay claim. Decisions/source will be published under the user's explicit GitHub-history authorization; no merge.
