BEGIN;

CREATE TABLE claim_disposition_decision (
    id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL REFERENCES claim(id),
    from_maturity TEXT NOT NULL,
    to_maturity TEXT NOT NULL,
    successor_claim_id TEXT REFERENCES claim(id),
    reason TEXT NOT NULL,
    decided_by JSONB NOT NULL,
    evidence_ids JSONB NOT NULL,
    supporting_evidence_ids JSONB NOT NULL,
    refuting_evidence_ids JSONB NOT NULL,
    qualifying_evidence_ids JSONB NOT NULL,
    distinct_source_ids JSONB NOT NULL,
    distinct_snapshot_ids JSONB NOT NULL,
    review_flags JSONB NOT NULL,
    competing_active_claim_ids JSONB NOT NULL,
    competition_note TEXT,
    policy_version TEXT NOT NULL,
    decided_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT claim_disposition_decision_id_prefix CHECK (id LIKE 'cdd:%'),
    CONSTRAINT claim_disposition_decision_reason CHECK (length(btrim(reason)) > 0),
    CONSTRAINT claim_disposition_decision_human CHECK (decided_by->>'actor_type' = 'human'),
    CONSTRAINT claim_disposition_decision_transition CHECK (
        (
            to_maturity = 'REJECTED'
            AND from_maturity IN ('SUPPORTED', 'CHALLENGED')
            AND successor_claim_id IS NULL
        )
        OR
        (
            to_maturity = 'SUPERSEDED'
            AND from_maturity IN ('VALIDATED', 'CHALLENGED')
            AND successor_claim_id IS NOT NULL
        )
    ),
    CONSTRAINT claim_disposition_decision_arrays CHECK (
        jsonb_typeof(evidence_ids) = 'array'
        AND jsonb_array_length(evidence_ids) > 0
        AND jsonb_typeof(supporting_evidence_ids) = 'array'
        AND jsonb_array_length(supporting_evidence_ids) > 0
        AND jsonb_typeof(refuting_evidence_ids) = 'array'
        AND jsonb_typeof(qualifying_evidence_ids) = 'array'
        AND jsonb_typeof(distinct_source_ids) = 'array'
        AND jsonb_array_length(distinct_source_ids) > 0
        AND jsonb_typeof(distinct_snapshot_ids) = 'array'
        AND jsonb_array_length(distinct_snapshot_ids) > 0
        AND jsonb_typeof(review_flags) = 'array'
        AND jsonb_typeof(competing_active_claim_ids) = 'array'
    )
);

CREATE UNIQUE INDEX idx_claim_disposition_decision_once
    ON claim_disposition_decision(claim_id);
CREATE INDEX idx_claim_disposition_decision_time
    ON claim_disposition_decision(decided_at, id);

CREATE FUNCTION kthub_validate_claim_disposition_evidence()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    expected_evidence_ids JSONB;
    expected_supporting_evidence_ids JSONB;
    expected_refuting_evidence_ids JSONB;
    expected_qualifying_evidence_ids JSONB;
    expected_source_ids JSONB;
    expected_snapshot_ids JSONB;
BEGIN
    SELECT
        COALESCE(jsonb_agg(actual.evidence_id ORDER BY actual.evidence_id), '[]'::jsonb),
        COALESCE(
            jsonb_agg(actual.evidence_id ORDER BY actual.evidence_id)
                FILTER (WHERE 'SUPPORTS' = ANY(actual.roles)),
            '[]'::jsonb
        ),
        COALESCE(
            jsonb_agg(actual.evidence_id ORDER BY actual.evidence_id)
                FILTER (WHERE 'REFUTES' = ANY(actual.roles)),
            '[]'::jsonb
        ),
        COALESCE(
            jsonb_agg(actual.evidence_id ORDER BY actual.evidence_id)
                FILTER (WHERE 'QUALIFIES' = ANY(actual.roles)),
            '[]'::jsonb
        ),
        COALESCE(jsonb_agg(DISTINCT actual.source_id ORDER BY actual.source_id), '[]'::jsonb),
        COALESCE(
            jsonb_agg(DISTINCT actual.source_snapshot_id ORDER BY actual.source_snapshot_id),
            '[]'::jsonb
        )
    INTO
        expected_evidence_ids,
        expected_supporting_evidence_ids,
        expected_refuting_evidence_ids,
        expected_qualifying_evidence_ids,
        expected_source_ids,
        expected_snapshot_ids
    FROM (
        SELECT
            claim_evidence.evidence_id,
            evidence.roles,
            evidence.source_id,
            evidence.source_snapshot_id
        FROM claim_evidence
        JOIN evidence ON evidence.id = claim_evidence.evidence_id
        WHERE claim_evidence.claim_id = NEW.claim_id
    ) AS actual;

    IF jsonb_array_length(expected_evidence_ids) = 0
       OR jsonb_array_length(expected_supporting_evidence_ids) = 0 THEN
        RAISE EXCEPTION
            'claim disposition decision requires actual SUPPORTS Evidence on claim %',
            NEW.claim_id;
    END IF;

    IF NEW.evidence_ids IS DISTINCT FROM expected_evidence_ids
       OR NEW.supporting_evidence_ids IS DISTINCT FROM expected_supporting_evidence_ids
       OR NEW.refuting_evidence_ids IS DISTINCT FROM expected_refuting_evidence_ids
       OR NEW.qualifying_evidence_ids IS DISTINCT FROM expected_qualifying_evidence_ids
       OR NEW.distinct_source_ids IS DISTINCT FROM expected_source_ids
       OR NEW.distinct_snapshot_ids IS DISTINCT FROM expected_snapshot_ids THEN
        RAISE EXCEPTION
            'claim disposition decision Evidence profile does not match Claim %',
            NEW.claim_id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_claim_disposition_evidence_integrity
BEFORE INSERT ON claim_disposition_decision
FOR EACH ROW
EXECUTE FUNCTION kthub_validate_claim_disposition_evidence();

CREATE TRIGGER trg_claim_disposition_competition_integrity
BEFORE INSERT ON claim_disposition_decision
FOR EACH ROW
EXECUTE FUNCTION kthub_validate_claim_decision_competition_snapshot();

CREATE FUNCTION kthub_validate_claim_disposition_successor()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    target claim%ROWTYPE;
    successor claim%ROWTYPE;
BEGIN
    SELECT * INTO target FROM claim WHERE id = NEW.claim_id;

    IF NEW.to_maturity = 'SUPERSEDED' THEN
        SELECT * INTO successor FROM claim WHERE id = NEW.successor_claim_id;

        IF successor.id IS NULL OR successor.id = target.id THEN
            RAISE EXCEPTION 'invalid successor Claim for disposition %', NEW.id;
        END IF;
        IF successor.maturity NOT IN ('SUPPORTED', 'VALIDATED') THEN
            RAISE EXCEPTION 'successor Claim must be at least SUPPORTED for disposition %', NEW.id;
        END IF;
        IF NOT (
            (
                target.entity_id IS NOT NULL
                AND successor.entity_id = target.entity_id
            )
            OR
            (
                target.entity_id IS NULL
                AND successor.entity_id IS NULL
                AND successor.relation_source_entity_id = target.relation_source_entity_id
                AND successor.relation_type = target.relation_type
                AND successor.relation_target_entity_id = target.relation_target_entity_id
            )
        ) THEN
            RAISE EXCEPTION 'successor Claim must describe the same exact subject for disposition %', NEW.id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_claim_disposition_successor_integrity
BEFORE INSERT ON claim_disposition_decision
FOR EACH ROW
EXECUTE FUNCTION kthub_validate_claim_disposition_successor();

CREATE FUNCTION kthub_require_disposition_decision_for_terminal_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF (
        OLD.maturity IN ('SUPPORTED', 'CHALLENGED')
        AND NEW.maturity = 'REJECTED'
    ) OR (
        OLD.maturity IN ('VALIDATED', 'CHALLENGED')
        AND NEW.maturity = 'SUPERSEDED'
    ) THEN
        IF NOT EXISTS (
            SELECT 1
            FROM claim_disposition_decision AS decision
            WHERE decision.claim_id = NEW.id
              AND decision.from_maturity = OLD.maturity
              AND decision.to_maturity = NEW.maturity
              AND decision.successor_claim_id IS NOT DISTINCT FROM NEW.superseded_by
        ) THEN
            RAISE EXCEPTION
                'claim % -> % requires matching human disposition decision: %',
                OLD.maturity,
                NEW.maturity,
                NEW.id;
        END IF;
    END IF;
    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER trg_claim_terminal_transition_requires_disposition
AFTER UPDATE ON claim
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION kthub_require_disposition_decision_for_terminal_transition();

CREATE FUNCTION kthub_require_claim_disposition_applied()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    current_maturity TEXT;
    current_successor TEXT;
BEGIN
    SELECT maturity, superseded_by
      INTO current_maturity, current_successor
      FROM claim
     WHERE id = NEW.claim_id;

    IF current_maturity IS DISTINCT FROM NEW.to_maturity
       OR current_successor IS DISTINCT FROM NEW.successor_claim_id THEN
        RAISE EXCEPTION
            'claim disposition decision requires matching terminal Claim state for %',
            NEW.claim_id;
    END IF;
    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER trg_claim_disposition_requires_applied_state
AFTER INSERT ON claim_disposition_decision
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION kthub_require_claim_disposition_applied();

CREATE TRIGGER trg_claim_disposition_append_only
BEFORE UPDATE OR DELETE ON claim_disposition_decision
FOR EACH ROW
EXECUTE FUNCTION kthub_reject_claim_decision_mutation();

COMMIT;
