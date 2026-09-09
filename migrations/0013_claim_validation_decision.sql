BEGIN;

CREATE TABLE claim_validation_decision (
    id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL REFERENCES claim(id),
    support_decision_id TEXT NOT NULL REFERENCES claim_support_decision(id),
    from_maturity TEXT NOT NULL,
    to_maturity TEXT NOT NULL,
    reason TEXT NOT NULL,
    validated_by JSONB NOT NULL,
    validation_basis TEXT NOT NULL,
    validation_note TEXT NOT NULL,
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
    validated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT claim_validation_decision_id_prefix CHECK (id LIKE 'cvd:%'),
    CONSTRAINT claim_validation_decision_transition CHECK (
        from_maturity IN ('SUPPORTED', 'CHALLENGED') AND to_maturity = 'VALIDATED'
    ),
    CONSTRAINT claim_validation_decision_reason CHECK (length(btrim(reason)) > 0),
    CONSTRAINT claim_validation_decision_human CHECK (validated_by->>'actor_type' = 'human'),
    CONSTRAINT claim_validation_decision_basis CHECK (
        validation_basis IN ('EVIDENCE_REVIEW', 'REPRODUCTION', 'EXPERIMENT', 'OTHER')
    ),
    CONSTRAINT claim_validation_decision_note CHECK (length(btrim(validation_note)) > 0),
    CONSTRAINT claim_validation_decision_independence CHECK (
        independence_assessment IN ('NOT_ASSESSED', 'HUMAN_REVIEWED')
    ),
    CONSTRAINT claim_validation_decision_independence_note CHECK (
        independence_assessment <> 'HUMAN_REVIEWED'
        OR (independence_note IS NOT NULL AND length(btrim(independence_note)) > 0)
    ),
    CONSTRAINT claim_validation_decision_arrays CHECK (
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

CREATE INDEX idx_claim_validation_decision_claim
    ON claim_validation_decision(claim_id, validated_at, id);

CREATE INDEX idx_claim_validation_decision_validated_at
    ON claim_validation_decision(validated_at, id);

CREATE FUNCTION kthub_require_validation_decision_for_validated_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.maturity = 'VALIDATED'
       AND OLD.maturity IN ('SUPPORTED', 'CHALLENGED') THEN
        IF NEW.last_verified IS NULL OR NOT EXISTS (
            SELECT 1
            FROM claim_validation_decision decision
            WHERE decision.claim_id = NEW.id
              AND decision.from_maturity = OLD.maturity
              AND decision.to_maturity = 'VALIDATED'
              AND decision.validated_at = NEW.last_verified
        ) THEN
            RAISE EXCEPTION
                'claim % -> VALIDATED requires matching claim validation decision: %',
                OLD.maturity,
                NEW.id;
        END IF;
    END IF;
    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER trg_claim_validated_requires_decision
AFTER UPDATE ON claim
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION kthub_require_validation_decision_for_validated_transition();

CREATE FUNCTION kthub_require_validation_decision_applied()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    current_maturity TEXT;
    current_last_verified TIMESTAMPTZ;
BEGIN
    SELECT maturity, last_verified
      INTO current_maturity, current_last_verified
      FROM claim
     WHERE id = NEW.claim_id;

    IF current_maturity IS DISTINCT FROM 'VALIDATED'
       OR current_last_verified IS DISTINCT FROM NEW.validated_at THEN
        RAISE EXCEPTION
            'claim validation decision requires matching VALIDATED state and last_verified on claim %',
            NEW.claim_id;
    END IF;
    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER trg_claim_validation_decision_requires_applied_state
AFTER INSERT ON claim_validation_decision
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION kthub_require_validation_decision_applied();

COMMIT;
