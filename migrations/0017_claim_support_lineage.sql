BEGIN;

ALTER TABLE claim
    ADD COLUMN last_support_reviewed_at TIMESTAMPTZ;

ALTER TABLE claim_support_decision
    DROP CONSTRAINT claim_support_decision_transition;

ALTER TABLE claim_support_decision
    ADD CONSTRAINT claim_support_decision_transition CHECK (
        from_maturity IN ('CANDIDATE', 'CHALLENGED')
        AND to_maturity = 'SUPPORTED'
    );

DROP INDEX idx_claim_support_decision_once;

CREATE UNIQUE INDEX idx_claim_support_decision_review_once
    ON claim_support_decision(claim_id, decided_at);

-- Before this migration each Claim could have at most one support decision.
-- Backfill the current support-lineage anchor from that historical decision.
UPDATE claim AS target
   SET last_support_reviewed_at = decision.decided_at
  FROM claim_support_decision AS decision
 WHERE decision.claim_id = target.id;

CREATE FUNCTION kthub_guard_claim_support_lineage_insert()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.last_support_reviewed_at IS NOT NULL THEN
        RAISE EXCEPTION
            'new CANDIDATE claims cannot start with last_support_reviewed_at: %',
            NEW.id;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_claim_support_lineage_insert
BEFORE INSERT ON claim
FOR EACH ROW
EXECUTE FUNCTION kthub_guard_claim_support_lineage_insert();

CREATE FUNCTION kthub_guard_claim_support_lineage_update()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    review_timestamp TIMESTAMPTZ;
BEGIN
    IF OLD.maturity IN ('CANDIDATE', 'CHALLENGED')
       AND NEW.maturity = 'SUPPORTED' THEN
        SELECT decision.decided_at
          INTO review_timestamp
          FROM claim_support_decision AS decision
         WHERE decision.claim_id = NEW.id
           AND decision.from_maturity = OLD.maturity
           AND decision.to_maturity = 'SUPPORTED'
           AND (
                OLD.last_support_reviewed_at IS NULL
                OR decision.decided_at > OLD.last_support_reviewed_at
           )
         ORDER BY decision.decided_at DESC, decision.id DESC
         LIMIT 1;

        IF review_timestamp IS NULL THEN
            RAISE EXCEPTION
                '% -> SUPPORTED requires a fresh claim support decision: %',
                OLD.maturity,
                NEW.id;
        END IF;

        NEW.last_support_reviewed_at := review_timestamp;
    ELSIF NEW.last_support_reviewed_at IS DISTINCT FROM OLD.last_support_reviewed_at THEN
        RAISE EXCEPTION
            'last_support_reviewed_at may change only while entering SUPPORTED: %',
            NEW.id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_claim_support_lineage_update
BEFORE UPDATE ON claim
FOR EACH ROW
EXECUTE FUNCTION kthub_guard_claim_support_lineage_update();

DROP TRIGGER trg_claim_support_decision_requires_applied_maturity
    ON claim_support_decision;
DROP FUNCTION kthub_require_support_decision_applied();

CREATE FUNCTION kthub_require_support_decision_applied()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    current_maturity TEXT;
    current_support_reviewed_at TIMESTAMPTZ;
BEGIN
    SELECT maturity, last_support_reviewed_at
      INTO current_maturity, current_support_reviewed_at
      FROM claim
     WHERE id = NEW.claim_id;

    IF current_maturity IS DISTINCT FROM 'SUPPORTED'
       OR current_support_reviewed_at IS DISTINCT FROM NEW.decided_at THEN
        RAISE EXCEPTION
            'claim support decision requires matching SUPPORTED state and support-lineage timestamp on claim %',
            NEW.claim_id;
    END IF;
    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER trg_claim_support_decision_requires_applied_maturity
AFTER INSERT ON claim_support_decision
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION kthub_require_support_decision_applied();

CREATE FUNCTION kthub_require_latest_support_decision_for_validation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    latest_support_decision_id TEXT;
BEGIN
    SELECT decision.id
      INTO latest_support_decision_id
      FROM claim_support_decision AS decision
     WHERE decision.claim_id = NEW.claim_id
     ORDER BY decision.decided_at DESC, decision.id DESC
     LIMIT 1;

    IF latest_support_decision_id IS NULL
       OR NEW.support_decision_id IS DISTINCT FROM latest_support_decision_id THEN
        RAISE EXCEPTION
            'claim validation decision must reference latest support decision for %',
            NEW.claim_id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_claim_validation_requires_latest_support_decision
BEFORE INSERT ON claim_validation_decision
FOR EACH ROW
EXECUTE FUNCTION kthub_require_latest_support_decision_for_validation();

COMMIT;
