BEGIN;

CREATE TABLE source_acquisition_commit (
    id TEXT PRIMARY KEY,
    execution_id TEXT NOT NULL UNIQUE REFERENCES source_acquisition_execution(id),
    authorization_id TEXT NOT NULL REFERENCES source_acquisition_authorization(id),
    source_id TEXT NOT NULL REFERENCES source(id),
    snapshot_id TEXT NOT NULL UNIQUE REFERENCES source_snapshot(id),
    revision TEXT NOT NULL,
    acquisition_level TEXT NOT NULL,
    manifest_sha256 TEXT NOT NULL,
    source_fingerprint_sha256 TEXT NOT NULL,
    authorization_fingerprint_sha256 TEXT NOT NULL,
    committed_by JSONB NOT NULL,
    policy_version TEXT NOT NULL,
    committed_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT source_acquisition_commit_id_prefix CHECK (id LIKE 'vc:%'),
    CONSTRAINT source_acquisition_commit_level CHECK (acquisition_level = 'selected-files'),
    CONSTRAINT source_acquisition_commit_manifest CHECK (
        manifest_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT source_acquisition_commit_source_fingerprint CHECK (
        source_fingerprint_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT source_acquisition_commit_authorization_fingerprint CHECK (
        authorization_fingerprint_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT source_acquisition_commit_actor CHECK (
        committed_by->>'actor_type' IN ('tool', 'system')
    )
);

CREATE INDEX idx_source_acquisition_commit_source
    ON source_acquisition_commit(source_id);

CREATE INDEX idx_source_acquisition_commit_authorization
    ON source_acquisition_commit(authorization_id);

COMMIT;
