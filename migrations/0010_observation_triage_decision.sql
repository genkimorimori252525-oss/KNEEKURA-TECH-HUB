BEGIN;

CREATE TABLE observation_triage_decision (
    id TEXT PRIMARY KEY,
    observation_id TEXT NOT NULL REFERENCES staged_observation(id),
    action TEXT NOT NULL,
    from_status TEXT NOT NULL,
    to_status TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_by JSONB NOT NULL,
    resulting_claim_id TEXT REFERENCES claim(id),
    policy_version TEXT NOT NULL,
    decided_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT observation_triage_decision_id_prefix CHECK (id LIKE 'otd:%'),
    CONSTRAINT observation_triage_decision_action CHECK (
        action IN ('MARK_TRIAGED', 'REJECT', 'EXPIRE', 'PROMOTE_TO_CLAIM_CANDIDATE')
    ),
    CONSTRAINT observation_triage_decision_from_status CHECK (
        from_status IN ('NEW', 'TRIAGED')
    ),
    CONSTRAINT observation_triage_decision_to_status CHECK (
        to_status IN ('TRIAGED', 'PROMOTED', 'REJECTED', 'EXPIRED')
    ),
    CONSTRAINT observation_triage_decision_reason CHECK (length(btrim(reason)) > 0),
    CONSTRAINT observation_triage_decision_transition CHECK (
        (action = 'MARK_TRIAGED' AND from_status = 'NEW' AND to_status = 'TRIAGED' AND resulting_claim_id IS NULL)
        OR
        (action = 'REJECT' AND to_status = 'REJECTED' AND resulting_claim_id IS NULL)
        OR
        (action = 'EXPIRE' AND to_status = 'EXPIRED' AND resulting_claim_id IS NULL)
        OR
        (action = 'PROMOTE_TO_CLAIM_CANDIDATE' AND from_status = 'TRIAGED' AND to_status = 'PROMOTED' AND resulting_claim_id IS NOT NULL)
    ),
    CONSTRAINT observation_triage_decision_actor CHECK (
        created_by->>'actor_type' IN ('human', 'tool', 'system')
    ),
    CONSTRAINT observation_triage_decision_actor_authority CHECK (
        created_by->>'actor_type' = 'human'
        OR action IN ('MARK_TRIAGED', 'EXPIRE')
    )
);

CREATE INDEX idx_observation_triage_decision_observation
    ON observation_triage_decision(observation_id, decided_at, id);

CREATE UNIQUE INDEX idx_observation_triage_decision_one_transition_per_state
    ON observation_triage_decision(observation_id, from_status);

COMMIT;
