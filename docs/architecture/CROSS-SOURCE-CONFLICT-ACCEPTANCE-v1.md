# Cross-Source Conflict Acceptance v1

## Purpose

KNEEKURA TECH HUB must preserve disagreement between independently sourced Claims without silently converting popularity, recency, or automation into truth authority.

The v1 conflict rule is deliberately conservative:

```text
same exact Claim subject
+ different active Claim statements

        ↓

expose the difference
require review
preserve both provenance chains

        ≠

automatically declare contradiction
choose a winner
reject the lower-ranked Source
merge the Claims
```

This contract composes existing governance boundaries. It does not introduce a new canonical conflict record.

## Why this is acceptance-only

PR #32 already proves the full two-Source path from discovery through separate acquisition, immutable SourceSnapshots, extraction, and reviewed cross-source knowledge.

This slice begins with two immutable Source/Snapshot/Evidence chains so that failures isolate conflict semantics rather than repeat acquisition plumbing.

## Comparison semantics

Claims are grouped by the existing exact immutable Claim subject key.

When more than one active Claim exists for that subject and statements differ, comparison exposes at least:

- `MULTIPLE_CLAIMS`;
- `MULTIPLE_ACTIVE_CLAIMS`;
- `STATEMENTS_DIFFER`;
- maturity-specific review flags where applicable;
- `needs_review = true`.

Statement difference is not sufficient evidence to label the Claims contradictory. Scope, terminology, versioning, interpretation, and other context may explain the difference.

Therefore comparison does not emit:

- a contradiction verdict;
- a winner;
- a preferred Claim ID;
- an automatic maturity transition.

## Popularity is not authority

Source metadata such as stars may remain available for discovery context, but it is not a Claim maturity or truth signal.

A newly discovered high-popularity Source does not automatically demote, supersede, reject, or replace an older reviewed Claim.

Likewise, an older low-popularity reviewed Claim does not automatically suppress a new Candidate from a larger Source.

## Human acknowledgement at trust boundaries

When another active Claim exists for the exact subject, the existing Support and Validation gates require an explicit human `competition_note`.

The note does not resolve the disagreement. It proves only that the reviewer did not cross the trust boundary while hiding the competing active Claim.

Support and Validation decisions preserve their exact `competing_active_claim_ids` snapshot.

## Challenge is a warning, not a verdict

Automation may move a reviewed Claim to `CHALLENGED` when new conflicting or concerning material appears.

This is intentionally asymmetric authority:

```text
AI/tool may lower trust for re-verification
AI/tool may not restore VALIDATED trust
AI/tool may not terminally erase reviewed knowledge
```

Challenge preserves the reviewed Claim's immutable epistemic payload and historical validation lineage. It also preserves `last_verified`; the timestamp records the last successful validation rather than the time of the warning.

A later return to `SUPPORTED` or `VALIDATED` remains governed by the existing human review gates.

## Terminal protection

`CHALLENGED` is not a bypass around terminal governance.

Automation cannot convert a reviewed `CHALLENGED` Claim directly into terminal `REJECTED` or `SUPERSEDED` state without the existing matching human Claim Disposition decision.

Thus discovery of a competing Claim can surface doubt but cannot erase the earlier reviewed record.

## Unresolved state is valid

The Hub is allowed to end a review cycle with two active Claims still present, for example:

```text
Claim A: CHALLENGED
Claim B: SUPPORTED
```

or another lifecycle-valid combination.

That state is not a failure of the knowledge model. It is an explicit representation of unresolved evidence.

Both Claims remain independently explainable through:

```text
Claim
  -> Evidence
  -> SourceSnapshot
  -> Source
```

until a later human review legitimately supports, validates, rejects, or supersedes one side under the normal gates.

## Deliberately not included

- automatic semantic contradiction inference;
- source popularity ranking as truth authority;
- a scalar global source-quality score;
- automatic winner selection;
- automatic rejection or supersession;
- automatic Claim merge;
- a new conflict table;
- a new Challenge decision vocabulary.

New canonical conflict machinery should be introduced only if later real operating pressure proves that the existing comparison, append-only audit trail, and Claim lifecycle cannot preserve the required evidence and authority semantics.