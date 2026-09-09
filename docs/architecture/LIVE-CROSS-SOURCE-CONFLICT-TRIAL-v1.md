# Live Cross-Source Conflict Trial v1

## Status

Accepted as an evidence/acceptance contract after real PostgreSQL CI.

This slice changes no production code, schema, or migration. It proves that the existing comparison, competition-review, validation, provenance, and explanation machinery can preserve two real ecosystem-specific design choices without inventing a global winner.

## Why this trial exists

Synthetic conflict fixtures already proved that the Hub can expose disagreeing Claims without automatically declaring contradiction or choosing a winner. The remaining question was whether the same behavior holds when the evidence comes from real, recognisable upstream projects whose popularity and authority signals differ substantially.

The trial deliberately chooses a topic where different answers can both be correct in context:

> Which indentation character policy does the ecosystem's canonical style authority use or prefer?

This is not a universal truth question. It is a comparison theme containing contextual design choices.

## Live sources

### Go / gofmt

Observed from live GitHub and then frozen for reproducible CI:

```text
repository  golang/go
commit      5d12b248d5520ff5adafeb9be9acc2148399ca49
tree        73a4ee55f515fa641e4edc21ab89e6d4ead693a4
path        src/cmd/gofmt/doc.go
blob        8ac9c6a931711df3c65b58611d77fc000578175d
stars       137991
license     BSD-3-Clause
```

The pinned documentation states that gofmt uses tabs for indentation and blanks for alignment.

### Python / PEP 8

Observed from live GitHub and then frozen for reproducible CI:

```text
repository  python/peps
commit      3b6032df5a42825474e00b75a4b1a8e9c7af459b
tree        ece03897c8329d793b51ec7b07bb583ae537533f
path        peps/pep-0008.rst
blob        d14c9e97b120daecadcd4afe742af69ddc07a34c
stars       5003
license     REVIEW_REQUIRED in Hub capture
```

The pinned PEP 8 section prefers spaces for indentation and limits tabs to consistency with code already indented using tabs.

GitHub repository metadata did not provide a repository license value for `python/peps`. This trial therefore does not infer or promote a license expression. The Source remains `REVIEW_REQUIRED` in the Hub acceptance data.

## Frozen evidence contract

CI does not depend on live GitHub availability. The live observation is frozen as:

```text
tests/fixtures/live-cross-source-conflict/indentation-policy/go-gofmt.txt
tests/fixtures/live-cross-source-conflict/indentation-policy/python-pep8.txt
tests/fixtures/live-cross-source-conflict/indentation-policy/capture.json
```

The test verifies the SHA-256 of each frozen excerpt before database work. The capture also records exact upstream commit, tree, path, Git blob SHA, repository metadata, and the observed narrow statement.

The Evidence locator preserves the real upstream Git blob identity. The frozen excerpt hash is an additional local fixture-integrity check; it does not replace the upstream provenance anchor.

## Claim model

A human creates one comparison theme:

```text
Source-code indentation character policy
```

Both Claims share the same exact comparison subject and scope:

```json
{
  "decision": "indentation-character",
  "comparison": "language-style-policy",
  "question": "tabs-or-spaces"
}
```

Their applicability remains distinct:

```text
Go Claim      -> ecosystem=Go, authority=gofmt
Python Claim  -> ecosystem=Python, authority=PEP 8
```

This separation is essential. The Hub exposes that the statements differ while retaining the context that makes both statements valid.

## Accepted lifecycle

The acceptance path is:

```text
Go Evidence
  -> Go Candidate
  -> human Support
  -> human Validation
  -> Go VALIDATED

Python Evidence arrives later
  -> Python Candidate
  -> comparison exposes both active Claims
  -> Support without competition_note is refused
  -> human Support with explicit competition awareness
  -> Validation without competition_note is refused
  -> human Validation with explicit contextual review
  -> Python VALIDATED

Final state:
  Go     VALIDATED
  Python VALIDATED
```

Neither Claim is challenged, rejected, or superseded.

## Comparison contract

With both Claims active, comparison must expose:

```text
MULTIPLE_ACTIVE_CLAIMS
STATEMENTS_DIFFER
needs_review = true
```

It must not infer:

```text
CONTRADICTION
winner
preferred_claim_id
```

The final state remains review-visible even though both Claims are Validated. `VALIDATED` means the narrow contextual Claim was human-reviewed against its evidence; it does not mean competing contextual design choices disappear.

## Popularity is not epistemic authority

At capture time the Go repository had far more GitHub stars than the PEP repository.

That metadata is intentionally preserved because it is useful source context. It is not transformed into:

- Claim confidence;
- Claim maturity;
- source quality score;
- truth ranking;
- winner selection;
- preferred design recommendation.

A larger audience does not make tabs a universal winner over spaces.

## License handling remains independent

The Go Source has a known declared repository license in the live GitHub metadata used for this trial.

The Python PEP Source remains `REVIEW_REQUIRED` because the repository metadata did not provide a license value and this acceptance slice is not a license-resolution workflow.

The Hub must not launder licensing uncertainty merely because:

- the Source is official;
- the evidence is useful;
- the Claim is human-validated;
- another Source has a known license.

Epistemic review and acquisition/license authority remain separate concerns.

## Proven provenance

`explain_claim()` independently reconstructs both paths:

```text
Go Claim
  -> Go Evidence
  -> golang/go Snapshot
  -> golang/go Source

Python Claim
  -> Python Evidence
  -> python/peps Snapshot
  -> python/peps Source
```

The exact pinned blob identity remains visible for each side.

## CI result

The first real PostgreSQL CI run passed against the existing production implementation:

```text
323 passed
```

No production implementation, schema, or migration change was required.

## Deliberately excluded

This acceptance does not add:

- automatic semantic contradiction inference;
- automatic source ranking;
- popularity-weighted truth;
- a global indentation recommendation;
- automatic Challenge because statements differ;
- automatic winner or preferred Claim;
- automatic Claim merge;
- a conflict table;
- a scalar source-quality score;
- automatic license resolution;
- live-network dependency in CI.

A new canonical mechanism should be introduced only if later operating pressure proves that the existing comparison, review, provenance, or lifecycle surfaces are insufficient.

## Governing lesson

Different evidence-backed design choices are not defects merely because they differ.

The Hub should preserve:

```text
context + evidence + provenance + review state
```

before attempting any global conclusion.

For contextual engineering knowledge, truthful disagreement can be a stable final state.
