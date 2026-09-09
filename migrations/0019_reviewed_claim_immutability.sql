BEGIN;

-- A Claim's epistemic payload may be edited only while it remains a Candidate.
-- The transition that leaves CANDIDATE must use the payload that was actually
-- present during review; changing content in the same UPDATE is forbidden.
CREATE FUNCTION kthub_guard_reviewed_claim_content_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.created_by IS DISTINCT FROM NEW.created_by THEN
        RAISE EXCEPTION 'claim created_by is immutable: %', OLD.id;
    END IF;

    IF (
        OLD.entity_id IS DISTINCT FROM NEW.entity_id
        OR OLD.relation_source_entity_id IS DISTINCT FROM NEW.relation_source_entity_id
        OR OLD.relation_type IS DISTINCT FROM NEW.relation_type
        OR OLD.relation_target_entity_id IS DISTINCT FROM NEW.relation_target_entity_id
        OR OLD.claim_type IS DISTINCT FROM NEW.claim_type
        OR OLD.statement IS DISTINCT FROM NEW.statement
        OR OLD.scope IS DISTINCT FROM NEW.scope
        OR OLD.applicability IS DISTINCT FROM NEW.applicability
        OR OLD.confidence IS DISTINCT FROM NEW.confidence
        OR OLD.reasoning_basis IS DISTINCT FROM NEW.reasoning_basis
        OR OLD.alternative_interpretations IS DISTINCT FROM NEW.alternative_interpretations
        OR OLD.policy_version IS DISTINCT FROM NEW.policy_version
    ) AND NOT (OLD.maturity = 'CANDIDATE' AND NEW.maturity = 'CANDIDATE') THEN
        RAISE EXCEPTION
            'reviewed Claim epistemic content is immutable; create a new Claim for revisions: %',
            OLD.id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_reviewed_claim_content_immutability
BEFORE UPDATE ON claim
FOR EACH ROW
EXECUTE FUNCTION kthub_guard_reviewed_claim_content_mutation();

-- Return the exact current Evidence IDs for one Claim in stable JSON order.
CREATE FUNCTION kthub_current_claim_evidence_ids(target_claim_id TEXT)
RETURNS JSONB
LANGUAGE SQL
STABLE
AS $$
    SELECT COALESCE(jsonb_agg(ce.evidence_id ORDER BY ce.evidence_id), '[]'::jsonb)
      FROM claim_evidence AS ce
     WHERE ce.claim_id = target_claim_id;
$$;

-- A reviewed Claim must keep the Evidence set captured by its latest support
-- decision. The check is deferred so the normalized repository may replace
-- identical claim_evidence rows inside a transaction without false failures.
CREATE FUNCTION kthub_require_reviewed_claim_evidence_snapshot(target_claim_id TEXT)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    latest_support_evidence_ids JSONB;
    current_evidence_ids JSONB;
BEGIN
    SELECT decision.evidence_ids
      INTO latest_support_evidence_ids
      FROM claim_support_decision AS decision
     WHERE decision.claim_id = target_claim_id
     ORDER BY decision.decided_at DESC, decision.id DESC
     LIMIT 1;

    -- No support decision means this is still cheap Candidate material.
    IF latest_support_evidence_ids IS NULL THEN
        RETURN;
    END IF;

    current_evidence_ids := kthub_current_claim_evidence_ids(target_claim_id);
    IF current_evidence_ids IS DISTINCT FROM latest_support_evidence_ids THEN
        RAISE EXCEPTION
            'reviewed Claim Evidence set differs from latest support decision: %',
            target_claim_id;
    END IF;
END;
$$;

CREATE FUNCTION kthub_check_reviewed_claim_evidence_change()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    target_claim_id TEXT;
BEGIN
    target_claim_id := COALESCE(NEW.claim_id, OLD.claim_id);
    PERFORM kthub_require_reviewed_claim_evidence_snapshot(target_claim_id);
    RETURN COALESCE(NEW, OLD);
END;
$$;

CREATE CONSTRAINT TRIGGER trg_reviewed_claim_evidence_insert_integrity
AFTER INSERT ON claim_evidence
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION kthub_check_reviewed_claim_evidence_change();

CREATE CONSTRAINT TRIGGER trg_reviewed_claim_evidence_update_integrity
AFTER UPDATE ON claim_evidence
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION kthub_check_reviewed_claim_evidence_change();

CREATE CONSTRAINT TRIGGER trg_reviewed_claim_evidence_delete_integrity
AFTER DELETE ON claim_evidence
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION kthub_check_reviewed_claim_evidence_change();

-- Also check when a Claim crosses lifecycle boundaries. This closes the case
-- where a support decision is written, Candidate Evidence links are changed,
-- and then the Claim is promoted without another claim_evidence row event.
CREATE FUNCTION kthub_check_reviewed_claim_evidence_on_maturity()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.maturity IS DISTINCT FROM NEW.maturity THEN
        PERFORM kthub_require_reviewed_claim_evidence_snapshot(NEW.id);
    END IF;
    RETURN NEW;
END;
$$;

CREATE CONSTRAINT TRIGGER trg_reviewed_claim_evidence_maturity_integrity
AFTER UPDATE OF maturity ON claim
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION kthub_check_reviewed_claim_evidence_on_maturity();

COMMIT;
