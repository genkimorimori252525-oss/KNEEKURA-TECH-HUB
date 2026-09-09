# Claim Support Gate v1

## Purpose

This slice governs the first canonical Claim maturity promotion:

```text
CANDIDATE
  ↓ human review only
SUPPORTED
```

`SUPPORTED` means that a human reviewer judged the current Evidence set sufficient to keep the Claim as supported knowledge. It does **not** mean validated, independently reproduced, universally applicable, or contradiction-free.

## No scalar quality score

The gate never computes a single support score. It records observable review dimensions separately:

- exact Evidence IDs considered;
- Evidence with `SUPPORTS` role;
- Evidence with `REFUTES` role;
- Evidence with `QUALIFIES` role;
- distinct Source IDs;
- distinct SourceSnapshot IDs;
- Evidence Review flags;
- active competing Claim IDs for the same exact subject;
- whether independence was assessed.

Multiple Sources are not automatically treated as independent confirmation.

## Human-only promotion

Only a human actor may create a `claim_support_decision` and promote a `CANDIDATE` Claim to `SUPPORTED`.

AI can create Claim Candidates through governed earlier stages, but cannot perform this maturity promotion.

## Minimum Evidence condition

A Claim must have at least one Evidence record whose roles include `SUPPORTS`.

The gate does not require an arbitrary minimum number of Sources or Snapshots.

## Counterevidence and qualification acknowledgement

The presence of `REFUTES` Evidence does not automatically reject a Claim. The reviewer must provide an explicit `counterevidence_note` before promotion.

Likewise, `QUALIFIES` Evidence requires an explicit `qualification_note`.

This keeps competing or limiting evidence visible instead of silently discarding it.

## Competing Claims

Claims are compared only by the existing exact stored subject key. Semantic similarity is not used to invent competition.

If another active Claim exists for the same exact subject, promotion requires a `competition_note`.

The gate does not choose a winner and does not infer contradiction from textual disagreement.

## Independence

Independence inference remains deliberately deferred.

Every support decision records one of:

- `NOT_ASSESSED`
- `HUMAN_REVIEWED`

`HUMAN_REVIEWED` requires a free-text `independence_note`. `NOT_ASSESSED` is allowed and remains visible in the audit record.

Therefore `SUPPORTED` never implies that evidence independence was established.

## Append-only decision record

Successful promotion creates `record_type: claim_support_decision` with an ID beginning `csd:`.

The decision captures the exact review state used for promotion. It is append-only and one first support decision is allowed per Claim.

## Transactional pairing

Migration `0011_claim_support_decision.sql` enforces both directions:

1. `CANDIDATE -> SUPPORTED` cannot commit without a matching `claim_support_decision`.
2. A `claim_support_decision` cannot commit unless the Claim actually reaches `SUPPORTED` in the same transaction.

This blocks direct repository/SQL maturity mutation from bypassing the review record.

The Support Gate locks the Claim row with `FOR UPDATE`, writes the decision, performs the existing Claim transition, and commits both with the existing `CLAIM_PROMOTE` curation event atomically.

## Evidence-profile binding

Migration `0012_claim_support_evidence_integrity.sql` independently re-derives the deterministic evidence profile from `claim_evidence` and `evidence` before a support decision can be inserted.

The database requires the decision's:

- complete `evidence_ids` set;
- `SUPPORTS`, `REFUTES`, and `QUALIFIES` partitions;
- distinct Source IDs;
- distinct SourceSnapshot IDs

to match the actual records attached to the Claim. A direct SQL caller therefore cannot satisfy the support pairing rule by inventing unrelated Evidence IDs or falsifying their roles/source provenance.

The database also requires `counterevidence_note` and `qualification_note` when the actual Evidence roles contain `REFUTES` or `QUALIFIES` respectively. Human interpretation itself remains in the domain layer; the database only protects deterministic integrity facts.

## CLI

Read-only context:

```bash
kneekura-claim-support context cl:...
```

Read-only decision history:

```bash
kneekura-claim-support history --claim-id cl:...
```

Governed promotion:

```bash
kneekura-claim-support promote cl:... \
  --actor-id curator \
  --reason "reviewed pinned evidence" \
  --independence-assessment NOT_ASSESSED
```

Additional notes become mandatory only when the corresponding review condition is present.

## Deliberately not included

- automatic independence inference;
- quality/support scores;
- automatic winner selection among competing Claims;
- AI promotion to `SUPPORTED`;
- automatic `SUPPORTED -> VALIDATED`;
- semantic duplicate merging;
- automatic rejection merely because counterevidence exists.
