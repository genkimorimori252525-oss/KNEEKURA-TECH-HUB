BEGIN;

CREATE TABLE review_decision (
    id TEXT PRIMARY KEY,
    source_claim_id TEXT NOT NULL REFERENCES claim(id),
    target_claim_id TEXT NOT NULL REFERENCES claim(id),
    decision TEXT NOT NULL,
    rationale TEXT NOT NULL,
    created_by JSONB NOT NULL,
    policy_version TEXT NOT NULL,
    decided_at TIMESTAMPTZ NOT NULL,
    supersedes_decision_id TEXT REFERENCES review_decision(id),
    CONSTRAINT review_decision_id_prefix CHECK (id LIKE 'rd:%'),
    CONSTRAINT review_decision_distinct_claims CHECK (source_claim_id <> target_claim_id),
    CONSTRAINT review_decision_allowed CHECK (
        decision IN (
            'CONTRADICTS',
            'COMPATIBLE',
            'QUALIFIES',
            'DUPLICATE',
            'SUPERSEDES',
            'UNRESOLVED'
        )
    ),
    CONSTRAINT review_decision_nonempty_rationale CHECK (length(btrim(rationale)) > 0),
    CONSTRAINT review_decision_not_self_superseding CHECK (
        supersedes_decision_id IS NULL OR supersedes_decision_id <> id
    )
);

CREATE INDEX idx_review_decision_source_claim
    ON review_decision(source_claim_id);

CREATE INDEX idx_review_decision_target_claim
    ON review_decision(target_claim_id);

CREATE UNIQUE INDEX idx_review_decision_one_successor
    ON review_decision(supersedes_decision_id)
    WHERE supersedes_decision_id IS NOT NULL;

COMMIT;
