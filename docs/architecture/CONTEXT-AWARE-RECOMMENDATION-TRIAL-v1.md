# Context-Aware Recommendation Trial v1

Status: acceptance contract proven on PR #38

## Purpose

Live Cross-Source Conflict Trial v1 proved that KNEEKURA Tech Hub can preserve two independently reviewed, simultaneously `VALIDATED` design choices without inventing a global winner:

```text
Go / gofmt       -> tabs for indentation
Python / PEP 8   -> spaces preferred for indentation
```

That preservation property is necessary but not sufficient for a useful knowledge system. A later reader also needs a safe way to ask:

```text
What applies in Go?
What applies in Python?
```

without converting context into a hidden ranking system.

This trial establishes the smallest read-only bridge between preserved applicability and contextual guidance.

## Proven gap

The Hub already stored Claim `applicability` as reviewed epistemic content, but the query layer had no API that could select trusted entity Claims by explicit applicability context.

The test-first PR reproduced the gap as an import failure:

```text
ImportError: cannot import name 'contextual_claims_for_entity'
```

This is the Defect Proof for this slice. It is a read-path gap, not a failure of Claim lifecycle, PostgreSQL provenance, or review governance.

## Minimal query contract

The production addition is:

```python
contextual_claims_for_entity(repository, entity_id, context=...)
```

It considers only:

```text
record_type = claim
entity_id   = resolved subject
relation    = absent
maturity    = VALIDATED
```

A `CANDIDATE`, `SUPPORTED`, `CHALLENGED`, `SUPERSEDED`, or `REJECTED` Claim cannot become trusted contextual guidance merely because its applicability matches.

## Exact subset matching

A supplied context is an exact subset constraint on the Claim's immutable `applicability` mapping.

Example:

```text
Claim applicability:
{
  "domain": "source-code",
  "ecosystem": "Go",
  "authority": "gofmt"
}

context {"ecosystem": "Go"}
    -> match

context {"ecosystem": "Go", "authority": "gofmt"}
    -> match

context {"ecosystem": "go"}
    -> no match

context {"ecosystem": "Go", "authority": "PEP 8"}
    -> no match
```

The matcher performs no normalization, stemming, synonym expansion, vector similarity, language-model inference, or fallback.

## Typed exactness

Python considers `True == 1` true. That language behavior is unsafe for a contract described as exact JSON-shaped context matching.

The matcher therefore also requires value types to agree recursively.

```text
applicability typed_marker = true

context true -> match
context 1    -> no match
```

Nested dictionaries and lists are compared recursively with the same typed exactness.

## Resolution states

The query returns a candidate set and an explicit resolution. It does not return a winner.

### Supplied context

```text
0 matches -> NO_MATCH
1 match   -> ONE_MATCH
>1 match  -> MULTIPLE_MATCHES
```

### No context / empty context

```text
0 validated Claims -> NO_VALIDATED_CLAIMS
1 validated Claim  -> ONE_MATCH
>1 validated Claims -> CONTEXT_REQUIRED
```

For the Go/Python indentation example:

```text
{"ecosystem":"Go"}
    -> ONE_MATCH
    -> Go/gofmt Claim

{"ecosystem":"Python"}
    -> ONE_MATCH
    -> Python/PEP 8 Claim

no context
    -> CONTEXT_REQUIRED
    -> both Claims remain visible

{"domain":"source-code"}
    -> MULTIPLE_MATCHES
    -> both Claims remain visible
```

## No hidden recommendation authority

The result intentionally contains no:

```text
winner
preferred_claim_id
score
rank
confidence-derived preference
popularity-derived preference
freshness-derived preference
```

Context narrows applicability. It does not create authority.

A one-match result means:

> exactly one already-VALIDATED Claim satisfied the explicit context constraint.

It does **not** mean:

> the Hub proved this is universally best.

## Fail-closed behavior

The query layer rejects malformed context rather than guessing:

- context must be a mapping;
- context keys must be strings;
- unknown Knowledge Entity IDs surface as `QueryError` at the query boundary;
- no result causes no semantic fallback.

The query is read-only. It creates no CurationEvent, review decision, Claim mutation, or authority transition.

## Relationship to Live Cross-Source Conflict Trial v1

The two trials form one preservation-to-use path:

```text
real Source A -> immutable Evidence -> VALIDATED Claim A --\
                                                        +--> exact context query
real Source B -> immutable Evidence -> VALIDATED Claim B --/
```

Live Cross-Source Conflict Trial v1 proves that different valid choices survive together.

Context-Aware Recommendation Trial v1 proves that a caller can select the applicable reviewed choice without destroying that coexistence.

## Deliberate non-goals

This trial does not add:

- fuzzy context matching;
- semantic similarity search;
- an ontology of all possible context keys;
- automatic context inference from user prose;
- global recommendation scoring;
- popularity weighting;
- freshness weighting;
- source-authority scoring;
- a recommendation table;
- a new database schema or migration;
- a CLI;
- automatic Claim promotion or disposition.

Those features require separate evidence and pressure before they can justify additional authority or complexity.

## Acceptance evidence

The initial test-only head failed because the query API did not exist.

After the minimal query-layer implementation, the first functional run reached:

```text
326 passed, 1 failed
```

The remaining failure exposed a query-boundary integration detail: unknown entity resolution leaked `ProjectionError` instead of the query layer's `QueryError`. The query boundary was normalized accordingly.

Adversarial review then identified Python's `True == 1` coercion as a potential violation of exact matching, so typed recursive equality was added and locked by regression tests.

Final CI result before this architecture note:

```text
327 passed in 24.83s
```

No schema or migration change was required.
