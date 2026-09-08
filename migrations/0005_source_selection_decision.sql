BEGIN;

CREATE TABLE source_selection_decision (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES source(id),
    decision TEXT NOT NULL,
    rationale TEXT NOT NULL,
    created_by JSONB NOT NULL,
    policy_version TEXT NOT NULL,
    decided_at TIMESTAMPTZ NOT NULL,
    supersedes_decision_id TEXT REFERENCES source_selection_decision(id),
    CONSTRAINT source_selection_decision_id_prefix CHECK (id LIKE 'sd:%'),
    CONSTRAINT source_selection_decision_allowed CHECK (
        decision IN (
            'SELECT_FOR_REVIEW',
            'DEFER',
            'REJECT_FOR_REVIEW'
        )
    ),
    CONSTRAINT source_selection_decision_nonempty_rationale CHECK (length(btrim(rationale)) > 0),
    CONSTRAINT source_selection_decision_not_self_superseding CHECK (
        supersedes_decision_id IS NULL OR supersedes_decision_id <> id
    )
);

CREATE INDEX idx_source_selection_decision_source
    ON source_selection_decision(source_id);

CREATE UNIQUE INDEX idx_source_selection_decision_one_successor
    ON source_selection_decision(supersedes_decision_id)
    WHERE supersedes_decision_id IS NOT NULL;

COMMIT;
