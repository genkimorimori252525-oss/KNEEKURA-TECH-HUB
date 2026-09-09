BEGIN;

ALTER TABLE claim
    ADD COLUMN pending_support_reviewed_at TIMESTAMPTZ,
    ADD COLUMN last_support_reviewed_at TIMESTAMPTZ;

CREATE TABLE claim_resupport_decision (
    id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL REFERENCES claim(id),
    initial_support_decision_id TEXT NOT NULL REFERENCES claim_support_decision(id),
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
    CONSTRAINT claim_resupport_decision_id_prefix CHECK (id LIKE 'crsd:%'),
    CONSTRAINT claim_resupport_decision_transition CHECK (
        from_maturity = 'CHALLENGED' AND to_maturity = 'SUPPORTED'
    ),
    CONSTRAINT claim_resupport_decision_reason CHECK (length(btrim(reason)) > 0),
    CONSTRAINT claim_resupport_decision_human CHECK (reviewed_by->>'actor_type' = 'human'),
    CONSTRAINT claim_resupport_decision_independence CHECK (
        independence_assessment IN ('NOT_ASSESSED', 'HUMAN_REVIEWED')
    ),
    CONSTRAINT claim_resupport_decision_independence_note CHECK (
        independence_assessment <> 'HUMAN_REVIEWED'
        OR (independence_note IS NOT NULL AND length(btrim(independence_note)) > 0)
    ),
    CONSTRAINT claim_resupport_decision_arrays CHECK (
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

CREATE UNIQUE INDEX idx_claim_resupport_decision_review_once
    ON claim_resupport_decision(claim_id, decided_at);

CREATE INDEX idx_claim_resupport_decision_claim
    ON claim_resupport_decision(claim_id, decided_at, id);

CREATE FUNCTION kthub_support_review_decision_exists(
    target_claim_id TEXT,
    target_maturity TEXT,
    target_decided_at TIMESTAMPTZ
)
RETURNS BOOLEAN
LANGUAGE SQL
STABLE
AS $$
    SELECT CASE target_maturity
        WHEN 'CANDIDATE' THEN EXISTS (
            SELECT 1
            FROM claim_support_decision decision
            WHERE decision.claim_id = target_claim_id
              AND decision.from_maturity = 'CANDIDATE'
              AND decision.to_maturity = 'SUPPORTED'
              AND decision.decided_at = target_decided_at
        )
        WHEN 'CHALLENGED' THEN EXISTS (
            SELECT 1
            FROM claim_resupport_decision decision
            WHERE decision.claim_id = target_claim_id
              AND decision.from_maturity = 'CHALLENGED'
              AND decision.to_maturity = 'SUPPORTED'
              AND decision.decided_at = target_decided_at
        )
        ELSE FALSE
    END;
$$;

CREATE FUNCTION kthub_guard_claim_support_review_anchor()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.pending_support_reviewed_at IS NOT NULL
           OR NEW.last_support_reviewed_at IS NOT NULL THEN
            RAISE EXCEPTION 'new CANDIDATE claims cannot start with support review anchors: %', NEW.id;
        END IF;
        RETURN NEW;
    END IF;

    IF NEW.pending_support_reviewed_at IS DISTINCT FROM OLD.pending_support_reviewed_at THEN
        IF NEW.maturity IS DISTINCT FROM OLD.maturity THEN
            RAISE EXCEPTION 'support review pending anchor must be armed before maturity transition: %', NEW.id;
        END IF;
        IF OLD.maturity NOT IN ('CANDIDATE', 'CHALLENGED') THEN
            RAISE EXCEPTION 'support review pending anchor may only be armed from CANDIDATE or CHALLENGED: %', NEW.id;
        END IF;
        IF NEW.pending_support_reviewed_at IS NULL
           OR NOT kthub_support_review_decision_exists(
                NEW.id,
                OLD.maturity,
                NEW.pending_support_reviewed_at
           ) THEN
            RAISE EXCEPTION 'support review pending anchor requires matching decision for %', NEW.id;
        END IF;
        IF NEW.pending_support_reviewed_at IS NOT DISTINCT FROM OLD.last_support_reviewed_at THEN
            RAISE EXCEPTION 'support review decision timestamp cannot be reused for %', NEW.id;
        END IF;
    END IF;

    IF OLD.maturity IN ('CANDIDATE', 'CHALLENGED')
       AND NEW.maturity = 'SUPPORTED' THEN
        IF OLD.pending_support_reviewed_at IS NULL
           OR NOT kthub_support_review_decision_exists(
                NEW.id,
                OLD.maturity,
                OLD.pending_support_reviewed_at
           ) THEN
            RAISE EXCEPTION '% -> SUPPORTED requires a fresh armed support review decision: %',
                OLD.maturity,
                NEW.id;
        END IF;
        IF OLD.pending_support_reviewed_at IS NOT DISTINCT FROM OLD.last_support_reviewed_at THEN
            RAISE EXCEPTION 'support review decision timestamp cannot be reused for %', NEW.id;
        END IF;
        NEW.last_support_reviewed_at := OLD.pending_support_reviewed_at;
        NEW.pending_support_reviewed_at := NULL;
    ELSE
        IF NEW.last_support_reviewed_at IS DISTINCT FROM OLD.last_support_reviewed_at THEN
            RAISE EXCEPTION 'last_support_reviewed_at may change only while entering SUPPORTED: %', NEW.id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_claim_support_review_anchor_insert
BEFORE INSERT ON claim
FOR EACH ROW
EXECUTE FUNCTION kthub_guard_claim_support_review_anchor();

CREATE TRIGGER trg_claim_support_review_anchor_update
BEFORE UPDATE ON claim
FOR EACH ROW
EXECUTE FUNCTION kthub_guard_claim_support_review_anchor();

CREATE FUNCTION kthub_require_resupport_decision_applied()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    current_maturity TEXT;
    current_last_support_reviewed_at TIMESTAMPTZ;
BEGIN
    SELECT maturity, last_support_reviewed_at
      INTO current_maturity, current_last_support_reviewed_at
      FROM claim
     WHERE id = NEW.claim_id;

    IF current_maturity IS DISTINCT FROM 'SUPPORTED'
       OR current_last_support_reviewed_at IS DISTINCT FROM NEW.decided_at THEN
        RAISE EXCEPTION
            'claim resupport decision requires matching SUPPORTED state and support review timestamp on claim %',
            NEW.claim_id;
    END IF;
    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER trg_claim_resupport_decision_requires_applied_state
AFTER INSERT ON claim_resupport_decision
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION kthub_require_resupport_decision_applied();

COMMIT;
