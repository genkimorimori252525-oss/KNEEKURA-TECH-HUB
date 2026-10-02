# Failure / Repair History — MOD analysis workflow v1

## Purpose

When analyzing an upstream MOD, inspect how it failed and how it was repaired, not only its present code. The output connects symptom, triggering conditions, environment, affected symbols, proposed cause, causal steps, actual repair diff and a narrowly applicable lesson. Reuse this record for our own MOD development later. This is one analysis facet, not another autonomous agent or database.

## Required workflow

1. Pin the target track/revision and a justified history window (release range, subsystem or concrete query). Preserve search/list pages as an inventory, including pagination/truncation and excluded ranges. Do not imply an entire history scan from a few search hits.
2. Select relevant Issues, PRs, discussions, fix commits, reverts and release notes. Read the discussion and actual diff; follow links between reports and repairs rather than treating keyword matches as proof.
3. Read before/after source for important changes. Pin each revision independently. A fix's parent is a pre-fix state, not automatically the commit that introduced the bug. A merged PR can have multiple parents, a squash, a revert or an incomplete fix.
4. Describe symptom and trigger separately from cause. Mark author statements as AUTHOR_CLAIM and analyst deductions as INFERENCE. UNKNOWN is acceptable and carries a reason. Each positive assertion or causal-chain step cites its own evidence. Include alternatives and limitations where relevant.
5. Record repair/workaround, regression tests and remaining uncertainty. Issue closure, PR merge and a passing compile do not establish successful runtime reproduction. Retain contrary reports and subsequent regressions.
6. Produce `FAILURE-REPAIR-HISTORY.md` (readable account) and `.json` (structured case records). Preserve captured source bytes outside normal Git history and refer to immutable document/index IDs. Mutable Issue/PR text needs URL, capture timestamp and content hash; URL alone is not a snapshot.
7. Import the record with the history adapter; use query for symptom/cause/repair/symbol/lesson lookup with exact track/environment filters. Existing Hub staging/curation remains the only route to canonical knowledge. No imported record is automatically VALIDATED.

A knowledge-free investigation is an allowed result: use an empty case list plus the captured search inventory and declared scope. Do not invent a teachable case. `REVIEWED_SCOPE` means only the declared window was reviewed, not all versions, all Issues or runtime validity.

## Record format

Top-level fields:

- `format`: `kneekura.failure-history.v1`.
- `repository`: upstream origin.
- `scope`: `track`, exact `head_revision`, descriptive `history_window`, `queries` array.
- `coverage`: `status` (`NOT_ANALYZED`, `PARTIAL`, `REVIEWED_SCOPE`), `inspected_evidence_ids`, `deferred`, `unavailable` arrays. REVIEWED_SCOPE cannot retain deferred/unavailable work inside the chosen scope.
- `scope_evidence`: optional captured search-inventory evidence. Necessary to document a reviewed scope when no useful cases were found.
- `cases`: at most 1000 cases per batch; paginate the investigation instead of silently dropping cases.

Each case has `case_id`, `origin` (`UPSTREAM` or `OWN_DEVELOPMENT`), `track`, explicit `environment`, `affected_symbols`, `before_revision`, `after_revision`, `evidence`, `causal_chain`, `reproduction`, `fix_verification`, and these five assertion objects: `symptom`, `trigger_conditions`, `root_cause`, `repair`, `lesson`. Extra detail such as workaround, regression-test identity, alternate explanation or original URLs is retained rather than stripped.

An assertion is `{ "basis": "AUTHOR_CLAIM", "text": "...", "evidence_ids": ["issue-42"] }`. Allowed bases: DIRECT_OBSERVATION, AUTHOR_CLAIM, INFERENCE, UNKNOWN. UNKNOWN uses `text: null` and a nonempty `reason`; it must not smuggle in a definite cause. Missing evidence cannot be replaced by confident prose.

Evidence entries have `id`, `role`, `index_snapshot_id`, `document_id`, plus optional source URL/commit/capture metadata. Roles: issue, pull_request, commit, diff, before_code, after_code, log, experiment, release_note, discussion, search_inventory. Capture original downloaded data first with the existing profile adapter. The history adapter verifies exact document membership and retains the resulting locator/content hash; it does not execute or fetch those documents.

`reproduction` and `fix_verification` each have `state` and `evidence_ids`. States:

- NOT_RUN: not established by the supplied evidence.
- REPORTED: someone reported a result; preserve who, where and applicability.
- RECORDED_EXPERIMENT: a captured experiment artifact is cited. This is still imported research, not a new authenticated runtime assertion.

The adapter deliberately rejects PASS, REPRODUCED and VERIFIED_FIXED as top-level imported states. Real run outcomes remain in the existing run-bound verification record, linked as evidence, with their exact environment and assertions. A fixture, screenshot, merged PR or author claim must not masquerade as that execution.

## Commands

```text
python -m kneekura_tech_hub.minecraft.history --store CACHE import --record FAILURE-REPAIR-HISTORY.json
python -m kneekura_tech_hub.minecraft.history --store CACHE query --history HISTORY_HASH --query "navigation" --track ANCHOR --environment-json '{"loader":"forge","minecraft":"1.20.1"}'
```

Import freezes a CAS artifact, pins available original evidence and reports missing evidence. Query searches only recorded text; it does not invent a causal match or compatible implementation. Reusing a cursor with changed filters is rejected. If evidence becomes unavailable, readable cases remain available with a PARTIAL result and missing IDs. Full records are readable with the existing `artifact read --hash HISTORY_HASH` command. Preserve raw record files under the MOD analysis directory so normal full-source search also finds them.

## Initial implementation coverage

Implemented: bounded record/anchor validation, immutable capture, exact environment/track filtering, text query and pagination, preservation of unknown causes and missing evidence, zero canonical writes. The authoring pass added regression cases before implementation.

Not implied: an automatic GitHub harvester, verified causal inference, bulk historical analysis of Twilight Forest or Connector, or a live runtime reproduction. Those analyses are actual work for the MOD-analysis agent and remain explicitly tracked per target.
