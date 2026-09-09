# Cross-Source Knowledge Acceptance v1

## Purpose

Discovery-to-Knowledge Acceptance v1 proved that one governed Source can travel from metadata-only discovery to a human-validated Claim without bypassing selection, license review, acquisition authorization, verified Snapshot creation, Observation triage, Claim support, or Claim validation.

The next real use pressure is cross-source aggregation: two independently acquired Sources may describe the same technique, and their immutable Evidence should be able to support one Claim without leaving provenance or staging state inconsistent.

## The integration gap

A StagedObservation is intentionally Source-local. Its Evidence identity resolves to exactly one SourceSnapshot.

The existing `PROMOTE_TO_CLAIM_CANDIDATE` path creates a new Claim Candidate from one TRIAGED Observation and inherits that Observation's Evidence set.

A later independent Observation could be manually added to the still-editable Candidate Evidence set, because Candidate epistemic edits are deliberately allowed. However, that would leave the second Observation in `TRIAGED` even though its Evidence had already entered the Claim.

That state is misleading:

```text
Claim Candidate
  Evidence: Source A + Source B

Observation A: PROMOTED
Observation B: TRIAGED   <- actually consumed, but still in review queue
```

Cross-source acceptance therefore needs a governed way to consume a second TRIAGED Observation into an existing Claim Candidate.

## v1 operation

`attach_observation_to_candidate_claim()` is deliberately narrow.

It atomically:

1. requires a human actor;
2. locks the source Observation;
3. requires the Observation to be `TRIAGED`;
4. locks the target Claim;
5. requires the target Claim to be `CANDIDATE`;
6. verifies the Observation's immutable Evidence records and Source ownership;
7. requires that the Observation contribute at least one new Evidence ID;
8. unions those Evidence IDs into the Candidate;
9. marks the Observation `PROMOTED`;
10. appends the existing `PROMOTE_TO_CLAIM_CANDIDATE` Observation triage decision with `resulting_claim_id` set to the existing Claim.

No new canonical record type or lifecycle action is needed. The existing decision already means that a TRIAGED Observation was promoted into a Claim Candidate; v1 simply permits the resulting Candidate to pre-exist.

## Authority boundary

AI may create extraction proposals and StagedObservations, but it cannot perform this attachment.

The operation requires a human because it asserts a semantic judgment that the second Observation belongs in the same Claim Candidate.

This does not make the Candidate trusted. The Claim remains `CANDIDATE` until the existing human Support Gate reviews the exact resulting Evidence set.

## Independence

Multiple distinct Source IDs are evidence topology, not proof of independence.

Support and Validation continue to record:

- `distinct_source_ids`
- `distinct_snapshot_ids`
- `independence_assessment`
- optional `independence_note`

The system does not infer independence merely because two Sources exist. `HUMAN_REVIEWED` remains an explicit human assessment.

## Reviewed-content boundary

Cross-source aggregation is allowed only while the Claim is `CANDIDATE`.

Once the Claim becomes `SUPPORTED`, the existing Reviewed Claim Immutability contract freezes the exact Evidence set captured by the support decision. A later attempt to remove one Source, add another Source, or silently replace Evidence under the same reviewed Claim ID is rejected.

Corrections after review therefore continue to require the existing new-Claim / supersession model rather than in-place epistemic rewriting.

## Acceptance contract

The PostgreSQL acceptance test proves:

```text
GitHub Search
  -> Source A + Source B
  -> separate Selection
  -> separate human license resolution
  -> separate exact Authorization
  -> separate bounded Execution
  -> separate Verified Commit
  -> immutable Snapshot A + Snapshot B
  -> AI extraction A + B
  -> TRIAGED Observation A + B
  -> human creates one Entity
  -> human promotes Observation A to new Claim Candidate
  -> AI attachment attempt rejected
  -> human attaches Observation B to existing Candidate
  -> both Observations PROMOTED
  -> one Claim with exact Evidence A + B
  -> human SUPPORTED with explicit independence review
  -> Evidence set frozen
  -> human VALIDATED with explicit independence review
  -> explanation reconstructs both Source/Snapshot chains
```

## Deliberately not included

- automatic semantic equivalence detection;
- automatic Observation attachment;
- automatic independence inference;
- popularity-based truth ranking;
- automatic conflict resolution;
- new cross-source canonical tables;
- new Observation lifecycle vocabulary;
- mutation of reviewed Claim Evidence.
