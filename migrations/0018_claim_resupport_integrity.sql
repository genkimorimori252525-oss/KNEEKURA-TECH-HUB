BEGIN;

CREATE FUNCTION kthub_validate_claim_resupport_decision_lineage()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    support_claim_id TEXT;
BEGIN
    SELECT claim_id
      INTO support_claim_id
      FROM claim_support_decision
     WHERE id = NEW.initial_support_decision_id;

    IF support_claim_id IS DISTINCT FROM NEW.claim_id THEN
        RAISE EXCEPTION
            'claim resupport decision initial_support_decision_id does not belong to claim %',
            NEW.claim_id;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_claim_resupport_decision_lineage
BEFORE INSERT ON claim_resupport_decision
FOR EACH ROW
EXECUTE FUNCTION kthub_validate_claim_resupport_decision_lineage();

CREATE TRIGGER trg_claim_resupport_decision_evidence_integrity
BEFORE INSERT ON claim_resupport_decision
FOR EACH ROW
EXECUTE FUNCTION kthub_validate_claim_support_decision_evidence();

CREATE TRIGGER trg_claim_resupport_decision_competition_integrity
BEFORE INSERT ON claim_resupport_decision
FOR EACH ROW
EXECUTE FUNCTION kthub_validate_claim_decision_competition_snapshot();

CREATE TRIGGER trg_claim_resupport_decision_append_only
BEFORE UPDATE OR DELETE ON claim_resupport_decision
FOR EACH ROW
EXECUTE FUNCTION kthub_reject_claim_decision_mutation();

COMMIT;
