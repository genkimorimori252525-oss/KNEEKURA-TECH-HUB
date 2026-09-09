# Claim Validation Gate v1

## Purpose

This slice governs Claim promotion and revalidation into `VALIDATED`:

```text
SUPPORTED ── human validation ──> VALIDATED
VALIDATED ── challenge ──> CHALLENGED ── human revalidation ──> VALIDATED
```

`VALIDATED` means that a human reviewer explicitly validated the Claim, using a declared validation basis, against the current Evidence attached to the Claim.

It does **not** mean:

- universally true;
- independently reproduced unless that was actually assessed;
- free of counterevidence or qualifications;
- applicable outside the Claim's recorded scope;
- permanently fresh.

## Human-only authority

Only a human actor may promote or re-promote a Claim to `VALIDATED`.

AI may discover, extract, propose, challenge, or supply review material, but cannot perform the validation decision itself.

## Validation basis

Every validation decision records one explicit basis:

- `EVIDENCE_REVIEW`
- `REPRODUCTION`
- `EXPERIMENT`
- `OTHER`

The basis is categorical, not a quality score. A non-empty `validation_note` records what the human actually did or checked.

The gate deliberately does not require every Claim type to use an experiment or reproduction. Claim-type-specific stronger validation policies can be added only when real corpus pressure justifies them.

## Evidence snapshot at validation time

A `claim_validation_decision` captures the current deterministic Evidence profile:

- all Evidence IDs attached to the Claim;
- Evidence whose roles include `SUPPORTS`;
- Evidence whose roles include `REFUTES`;
- Evidence whose roles include `QUALIFIES`;
- distinct Source IDs;
- distinct SourceSnapshot IDs;
- current Evidence Review flags;
- active competing Claim IDs for the same exact stored subject.

No global support or validation score is computed.

## Counterevidence, qualifications, and competing Claims

A Claim is not automatically rejected merely because counterevidence, qualification, or a competing Claim exists.

Instead:

- actual `REFUTES` Evidence requires a fresh `counterevidence_note` at validation time;
- actual `QUALIFIES` Evidence requires a fresh `qualification_note`;
- active competing Claims for the exact same stored subject require a `competition_note`.

A note recorded at the earlier Support Gate is not silently reused as a later validation acknowledgement.

## Independence

Evidence independence remains explicit and conservative:

- `NOT_ASSESSED`
- `HUMAN_REVIEWED`

`HUMAN_REVIEWED` requires an `independence_note`.

Multiple Source IDs are not automatically counted as independent confirmation. Unknown lineage therefore never silently becomes independent evidence.

## Link to the Support Gate

Every validation decision records the prior `claim_support_decision` as `support_decision_id`.

This preserves the maturity lineage:

```text
CANDIDATE
  ↓ claim_support_decision
SUPPORTED
  ↓ claim_validation_decision
VALIDATED
```

The database verifies that the referenced Support Decision belongs to the same Claim.

## Revalidation and freshness

Validation decisions are append-only and **not unique per Claim**.

This is necessary because the lifecycle permits:

```text
VALIDATED → CHALLENGED → VALIDATED
```

Each validation or revalidation creates a new `claim_validation_decision` with a fresh `validated_at` timestamp.

The Claim's `last_verified` must equal that decision's `validated_at` exactly. Therefore an old validation decision cannot be reused to satisfy a later revalidation.

A unique `(claim_id, validated_at)` database index enforces one validation decision per verification timestamp while still permitting later revalidation decisions with new timestamps.

Historical validation decisions remain visible after a challenge or later revalidation.

## Transactional pairing

Migration `0013_claim_validation_decision.sql` enforces both directions at commit time:

1. `SUPPORTED -> VALIDATED` or `CHALLENGED -> VALIDATED` cannot commit without a matching validation decision whose `validated_at` equals the Claim's new `last_verified`.
2. A validation decision cannot commit unless the Claim reaches `VALIDATED` with the same `last_verified` timestamp in the same transaction.

The domain gate locks the Claim row, writes the decision, performs the existing Claim transition, writes the existing curation event, and commits atomically.

## Evidence-profile integrity

Migration `0014_claim_validation_evidence_integrity.sql` independently re-derives the deterministic Evidence profile from canonical `claim_evidence` and `evidence` records.

A direct SQL caller cannot satisfy the pairing rule by inventing unrelated Evidence IDs, falsifying Evidence roles, or substituting Source/SourceSnapshot provenance.

The database also requires acknowledgement notes when the actual Evidence roles contain `REFUTES` or `QUALIFIES`.

## Decision audit integrity

Migration `0015_claim_decision_audit_integrity.sql` closes two shared audit gaps for both the Support Gate and Validation Gate:

1. it re-derives active competing Claim IDs using the same **exact stored subject** definition as Claim Comparison and rejects a decision that hides or invents competitors;
2. it rejects direct SQL `UPDATE` or `DELETE` on `claim_support_decision` and `claim_validation_decision`.

Therefore a successful promotion decision cannot later be erased or rewritten to change reviewer metadata, Evidence provenance, acknowledgement notes, or the recorded competition snapshot.

The competition check remains structural only. It does not infer semantic contradiction, choose a winner, or compare statement meaning.

Human identity authentication and semantic interpretation remain domain/application responsibilities; PostgreSQL protects deterministic state integrity rather than pretending that a JSON actor field proves a real person's identity.

## Public API compatibility

Existing calls remain valid:

```python
engine.transition_claim(
    claim_id,
    "VALIDATED",
    actor=human,
    reason="reviewed",
)
```

They now route through the Validation Gate and record:

- `validation_basis = EVIDENCE_REVIEW`
- `validation_note = reason`
- `independence_assessment = NOT_ASSESSED`

Callers needing richer review metadata may pass `validation_review` or use the dedicated CLI.

## CLI

Read-only context:

```bash
kneekura-claim-validation context cl:...
```

Read-only history:

```bash
kneekura-claim-validation history --claim-id cl:...
```

Governed validation:

```bash
kneekura-claim-validation validate cl:... \
  --actor-id curator \
  --reason "reproduced pinned behavior" \
  --validation-basis REPRODUCTION \
  --validation-note "Repeated the documented sequence against the pinned fixture." \
  --independence-assessment NOT_ASSESSED
```

## Deliberately not included

- scalar validation/quality scores;
- automatic Evidence independence inference;
- automatic semantic contradiction detection;
- automatic winner selection among competing Claims;
- AI-only validation;
- mandatory experiments for every Claim type;
- fixed minimum Source count;
- a claim that `VALIDATED` means permanent or universal truth.
