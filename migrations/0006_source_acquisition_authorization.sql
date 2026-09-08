BEGIN;

CREATE TABLE source_acquisition_authorization (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES source(id),
    decision TEXT NOT NULL,
    selection_decision_id TEXT NOT NULL REFERENCES source_selection_decision(id),
    acquisition_level TEXT NOT NULL,
    revision TEXT NOT NULL,
    allowed_paths JSONB NOT NULL,
    rationale TEXT NOT NULL,
    created_by JSONB NOT NULL,
    policy_version TEXT NOT NULL,
    decided_at TIMESTAMPTZ NOT NULL,
    supersedes_authorization_id TEXT REFERENCES source_acquisition_authorization(id),
    CONSTRAINT source_acquisition_authorization_id_prefix CHECK (id LIKE 'aa:%'),
    CONSTRAINT source_acquisition_authorization_decision CHECK (
        decision IN ('AUTHORIZE', 'REVOKE')
    ),
    CONSTRAINT source_acquisition_authorization_level CHECK (
        acquisition_level = 'selected-files'
    ),
    CONSTRAINT source_acquisition_authorization_revision CHECK (
        length(btrim(revision)) > 0
    ),
    CONSTRAINT source_acquisition_authorization_paths_array CHECK (
        jsonb_typeof(allowed_paths) = 'array' AND jsonb_array_length(allowed_paths) BETWEEN 1 AND 32
    ),
    CONSTRAINT source_acquisition_authorization_rationale CHECK (
        length(btrim(rationale)) > 0
    ),
    CONSTRAINT source_acquisition_authorization_not_self_superseding CHECK (
        supersedes_authorization_id IS NULL OR supersedes_authorization_id <> id
    )
);

CREATE INDEX idx_source_acquisition_authorization_source
    ON source_acquisition_authorization(source_id);

CREATE INDEX idx_source_acquisition_authorization_selection
    ON source_acquisition_authorization(selection_decision_id);

CREATE UNIQUE INDEX idx_source_acquisition_authorization_one_successor
    ON source_acquisition_authorization(supersedes_authorization_id)
    WHERE supersedes_authorization_id IS NOT NULL;

COMMIT;
