BEGIN;

CREATE TABLE source_acquisition_execution (
    id TEXT PRIMARY KEY,
    authorization_id TEXT NOT NULL REFERENCES source_acquisition_authorization(id),
    source_id TEXT NOT NULL REFERENCES source(id),
    revision TEXT NOT NULL,
    requested_paths JSONB NOT NULL,
    status TEXT NOT NULL,
    file_results JSONB NOT NULL,
    manifest_sha256 TEXT,
    storage_key TEXT,
    error_code TEXT,
    executed_by JSONB NOT NULL,
    policy_version TEXT NOT NULL,
    executed_at TIMESTAMPTZ NOT NULL,
    authorization_effective_after BOOLEAN NOT NULL,
    CONSTRAINT source_acquisition_execution_id_prefix CHECK (id LIKE 'ax:%'),
    CONSTRAINT source_acquisition_execution_status CHECK (status IN ('SUCCEEDED', 'FAILED')),
    CONSTRAINT source_acquisition_execution_requested_paths CHECK (
        jsonb_typeof(requested_paths) = 'array' AND jsonb_array_length(requested_paths) BETWEEN 1 AND 32
    ),
    CONSTRAINT source_acquisition_execution_file_results CHECK (
        jsonb_typeof(file_results) = 'array' AND jsonb_array_length(file_results) <= 32
    ),
    CONSTRAINT source_acquisition_execution_success_fields CHECK (
        (status = 'SUCCEEDED' AND manifest_sha256 IS NOT NULL AND storage_key IS NOT NULL AND error_code IS NULL)
        OR
        (status = 'FAILED' AND manifest_sha256 IS NULL AND storage_key IS NULL AND error_code IS NOT NULL)
    )
);

CREATE INDEX idx_source_acquisition_execution_authorization
    ON source_acquisition_execution(authorization_id);

CREATE INDEX idx_source_acquisition_execution_source
    ON source_acquisition_execution(source_id);

CREATE UNIQUE INDEX idx_source_acquisition_execution_one_success
    ON source_acquisition_execution(authorization_id)
    WHERE status = 'SUCCEEDED';

COMMIT;
