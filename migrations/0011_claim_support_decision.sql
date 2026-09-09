BEGIN;

CREATE TABLE claim_support_decision (
    id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL REFERENCES claim(id),
    from_maturity TEXT NOT NULL,
    to_maturity TEXT NOT NULL,
    reason TEXT NOT NULL,
    reviewed_by JSONB NOT NULL,
    evidence_ids JSONB NOT NULL,
    supporting_evidence_ids JSONB NOT NULL,
    refuting_evidence_ids JSONB NOT NULL,
    qualifying_evidence_ids JSONB NOT NULL,
    distinct_source_ids JSONB NOT NULL,
    distinct_snapshot_ids JSONB NOT NULL,
    review_flags JSONB NOT NULL,
    competing_active_claim_ids JSONB NOT NULL,
    independence_assessment TEXT NOT NULL,
    independence_note TEXT,
    counterevidence_note TEXT,
    qualification_note TEXT,
    competition_note TEXT,
    policy_version TEXT NOT NULL,
    decided_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT claim_support_decision_id_prefix CHECK (id LIKE 'csd:%'),
    CONSTRAINT claim_support_decision_transition CHECK (
        from_maturity = 'CANDIDATE' AND to_maturity = 'SUPPORTED'
    ),
    CONSTRAINT claim_support_decision_reason CHECK (length(btrim(reason)) > 0),
    CONSTRAINT claim_support_decision_human CHECK (reviewed_by->>'actor_type' = 'human'),
    CONSTRAINT claim_support_decision_independence CHECK (
        independence_assessment IN ('NOT_ASSESSED', 'HUMAN_REVIEWED')
    ),
    CONSTRAINT claim_support_decision_independence_note CHECK (
        independence_assessment <> 'HUMAN_REVIEWED'
        OR (independence_note IS NOT NULL AND length(btrim(independence_note)) > 0)
    ),
    CONSTRAINT claim_support_decision_arrays CHECK (
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

CREATE UNIQUE INDEX idx_claim_support_decision_once
    ON claim_support_decision(claim_id);

CREATE INDEX idx_claim_support_decision_decided_at
    ON claim_support_decision(decided_at, id);

CREATE FUNCTION kthub_require_support_decision_for_candidate_promotion()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.maturity = 'CANDIDATE' AND NEW.maturity = 'SUPPORTED' THEN
        IF NOT EXISTS (
            SELECT 1
            FROM claim_support_decision decision
            WHERE decision.claim_id = NEW.id
              AND decision.from_maturity = 'CANDIDATE'
              AND decision.to_maturity = 'SUPPORTED'
        ) THEN
            RAISE EXCEPTION
                'claim CANDIDATE -> SUPPORTED requires matching claim support decision: %',
                NEW.id;
        END IF;
    END IF;
    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER trg_claim_candidate_support_requires_decision
AFTER UPDATE ON claim
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION kthub_require_support_decision_for_candidate_promotion();

CREATE FUNCTION kthub_require_support_decision_applied()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    current_maturity TEXT;
BEGIN
    SELECT maturity
      INTO current_maturity
      FROM claim
     WHERE id = NEW.claim_id;

    IF current_maturity IS DISTINCT FROM 'SUPPORTED' THEN
        RAISE EXCEPTION
            'claim support decision requires SUPPORTED maturity on claim % (current %)',
            NEW.claim_id,
            current_maturity;
    END IF;
    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER trg_claim_support_decision_requires_applied_maturity
AFTER INSERT ON claim_support_decision
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION kthub_require_support_decision_applied();

COMMIT;
