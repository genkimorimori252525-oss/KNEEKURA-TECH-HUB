BEGIN;

CREATE TABLE IF NOT EXISTS staged_observation_evidence (
    observation_id TEXT NOT NULL REFERENCES staged_observation(id) ON DELETE CASCADE,
    evidence_id TEXT NOT NULL REFERENCES evidence(id),
    PRIMARY KEY (observation_id, evidence_id)
);

CREATE INDEX IF NOT EXISTS idx_staged_observation_evidence_evidence
    ON staged_observation_evidence(evidence_id);

COMMIT;
