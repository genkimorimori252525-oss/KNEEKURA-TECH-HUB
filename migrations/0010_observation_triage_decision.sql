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

-- Creation is the only unaudited lifecycle edge. New observations must therefore
-- enter through NEW; every later state requires an append-only triage decision.
CREATE FUNCTION kthub_require_new_observation_on_insert()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status <> 'NEW' THEN
        RAISE EXCEPTION 'new staged observations must start at NEW';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_staged_observation_insert_new
BEFORE INSERT ON staged_observation
FOR EACH ROW
EXECUTE FUNCTION kthub_require_new_observation_on_insert();

-- Status mutation and its audit decision are a transaction-level pair. The check
-- is deferred so service code may write either side first, but commit cannot
-- publish an unaudited status change.
CREATE FUNCTION kthub_require_triage_decision_for_status_change()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        IF NOT EXISTS (
            SELECT 1
            FROM observation_triage_decision decision
            WHERE decision.observation_id = NEW.id
              AND decision.from_status = OLD.status
              AND decision.to_status = NEW.status
        ) THEN
            RAISE EXCEPTION
                'staged observation status change % -> % requires matching triage decision',
                OLD.status,
                NEW.status;
        END IF;
    END IF;
    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER trg_staged_observation_status_requires_decision
AFTER UPDATE ON staged_observation
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION kthub_require_triage_decision_for_status_change();

-- The inverse check prevents an append-only decision from claiming a lifecycle
-- change that never actually reached the Observation row.
CREATE FUNCTION kthub_require_triage_decision_applied()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    current_status TEXT;
BEGIN
    SELECT status
      INTO current_status
      FROM staged_observation
     WHERE id = NEW.observation_id;

    IF current_status IS DISTINCT FROM NEW.to_status THEN
        RAISE EXCEPTION
            'triage decision target status % is not applied to observation % (current %)',
            NEW.to_status,
            NEW.observation_id,
            current_status;
    END IF;
    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER trg_observation_triage_decision_requires_applied_status
AFTER INSERT ON observation_triage_decision
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION kthub_require_triage_decision_applied();

COMMIT;
