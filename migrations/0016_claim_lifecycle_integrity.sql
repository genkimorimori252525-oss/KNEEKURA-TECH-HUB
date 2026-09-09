BEGIN;

CREATE FUNCTION kthub_require_candidate_claim_on_insert()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.maturity IS DISTINCT FROM 'CANDIDATE' THEN
        RAISE EXCEPTION 'new claims must start at CANDIDATE: %', NEW.id;
    END IF;
    IF NEW.last_verified IS NOT NULL THEN
        RAISE EXCEPTION 'new CANDIDATE claims cannot start with last_verified: %', NEW.id;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_claim_insert_lifecycle_integrity
BEFORE INSERT ON claim
FOR EACH ROW
EXECUTE FUNCTION kthub_require_candidate_claim_on_insert();

CREATE FUNCTION kthub_require_allowed_claim_lifecycle_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    transition_allowed BOOLEAN := FALSE;
BEGIN
    IF OLD.maturity IS DISTINCT FROM NEW.maturity THEN
        transition_allowed := CASE OLD.maturity
            WHEN 'CANDIDATE' THEN NEW.maturity IN ('SUPPORTED', 'REJECTED')
            WHEN 'SUPPORTED' THEN NEW.maturity IN ('VALIDATED', 'CHALLENGED', 'REJECTED')
            WHEN 'VALIDATED' THEN NEW.maturity IN ('CHALLENGED', 'SUPERSEDED')
            WHEN 'CHALLENGED' THEN NEW.maturity IN ('SUPPORTED', 'VALIDATED', 'SUPERSEDED', 'REJECTED')
            ELSE FALSE
        END;

        IF NOT transition_allowed THEN
            RAISE EXCEPTION
                'invalid claim lifecycle transition % -> % for %',
                OLD.maturity,
                NEW.maturity,
                NEW.id;
        END IF;
    END IF;

    IF NEW.last_verified IS DISTINCT FROM OLD.last_verified
       AND NOT (
            NEW.maturity = 'VALIDATED'
            AND OLD.maturity IN ('SUPPORTED', 'CHALLENGED')
       ) THEN
        RAISE EXCEPTION
            'last_verified may change only during SUPPORTED/CHALLENGED -> VALIDATED for %',
            NEW.id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_claim_update_lifecycle_integrity
BEFORE UPDATE ON claim
FOR EACH ROW
EXECUTE FUNCTION kthub_require_allowed_claim_lifecycle_transition();

COMMIT;
