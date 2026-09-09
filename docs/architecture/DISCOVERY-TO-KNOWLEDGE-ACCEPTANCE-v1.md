# Discovery-to-Knowledge Acceptance v1

## Purpose

The Hub now has many individually tested governance boundaries. This acceptance slice proves that those boundaries also compose into one usable path from public OSS discovery to reviewed knowledge.

This is deliberately an integration contract, not a new canonical model or promotion shortcut.

## Accepted path

```text
GitHub Search metadata
  -> metadata-only Source
  -> human SELECT_FOR_REVIEW
  -> human license resolution
  -> human exact acquisition Authorization
  -> bounded tool Execution
  -> Verified Acquisition Commit
  -> immutable SourceSnapshot
  -> Hub-controlled Evidence extraction from committed bytes
  -> AI-created NEW StagedObservation
  -> bounded tool triage
  -> human canonical Knowledge Entity creation
  -> human Observation -> Claim CANDIDATE promotion
  -> human Support decision
  -> human Validation decision
  -> Evidence Explanation back to SourceSnapshot and Source
```

Every arrow keeps the existing authority boundary. The test does not add a convenience API that jumps across stages.

## Discovery remains discovery

The acceptance starts with the existing GitHub Discovery Adapter fixture.

The adapter emits both a seven-star relevant repository and a much larger-star repository. Provider order is preserved and neither popularity value is converted into a quality score.

GitHub Search license metadata remains a hint. The discovered Source starts with `license.state = REVIEW_REQUIRED`, and acquisition authorization is expected to fail until a human resolves the license metadata.

## Selection is not authorization

A human `SELECT_FOR_REVIEW` decision only records that a Source is worth deeper examination. It does not change acquisition depth or bypass license policy.

The acceptance explicitly attempts Authorization before license resolution and expects failure.

## Authorization is not acquisition

After human license resolution, the Authorization pins one exact commit SHA and one exact path.

A successful acquisition Execution still leaves the Source at `metadata-only` and creates no SourceSnapshot.

Only Verified Acquisition Commit re-verifies stored bytes, updates the Source to `selected-files`, and creates the immutable SourceSnapshot.

## Extraction is not knowledge promotion

The AI supplies only an untrusted extraction proposal. Hub code derives exact Evidence and a NEW StagedObservation from the committed bytes.

At this point there is still no Claim and no Knowledge Entity created automatically.

A tool may perform the bounded mechanical `NEW -> TRIAGED` transition. Canonical Knowledge Entity creation and Observation promotion remain human-only.

Observation promotion creates only a `CANDIDATE` Claim and inherits the exact Observation Evidence.

## Candidate is not trusted knowledge

The acceptance then uses the normal human Claim Support and Claim Validation gates.

The validation is intentionally narrow: a human verifies that the pinned source line says what the Claim says. The test records `independence_assessment = NOT_ASSESSED` and does not pretend that one Source is independent corroboration.

## Provenance closure

The final assertion uses Evidence Explanation to reconstruct:

```text
VALIDATED Claim
  -> Evidence
  -> immutable SourceSnapshot at exact revision
  -> originally discovered Source
```

The unselected high-star Source remains metadata-only throughout.

## What this acceptance does not do

- no automatic canonical entity creation;
- no automatic Observation promotion;
- no automatic Support or Validation;
- no popularity ranking;
- no license inference from GitHub Search metadata;
- no full-source acquisition;
- no semantic deduplication;
- no new global score;
- no new production persistence model.

A failure in this test should be treated as an integration pressure on an existing boundary rather than as justification to add a shortcut around that boundary.
