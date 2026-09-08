BEGIN;

ALTER TABLE source_acquisition_execution
    ADD COLUMN source_fingerprint_sha256 TEXT,
    ADD COLUMN authorization_fingerprint_sha256 TEXT;

ALTER TABLE source_acquisition_execution
    ADD CONSTRAINT source_acquisition_execution_source_fingerprint CHECK (
        source_fingerprint_sha256 IS NULL
        OR source_fingerprint_sha256 ~ '^[0-9a-f]{64}$'
    ),
    ADD CONSTRAINT source_acquisition_execution_authorization_fingerprint CHECK (
        authorization_fingerprint_sha256 IS NULL
        OR authorization_fingerprint_sha256 ~ '^[0-9a-f]{64}$'
    );

COMMIT;
