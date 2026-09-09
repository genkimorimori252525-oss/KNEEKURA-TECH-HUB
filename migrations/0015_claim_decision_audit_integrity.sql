BEGIN;

CREATE FUNCTION kthub_expected_competing_active_claim_ids(target_claim_id TEXT)
RETURNS JSONB
LANGUAGE SQL
STABLE
AS $$
    SELECT COALESCE(jsonb_agg(candidate.id ORDER BY candidate.id), '[]'::jsonb)
    FROM claim AS target
    JOIN claim AS candidate
      ON candidate.id <> target.id
     AND candidate.maturity NOT IN ('SUPERSEDED', 'REJECTED')
     AND (
        (
            target.entity_id IS NOT NULL
            AND candidate.entity_id = target.entity_id
        )
        OR
        (
            target.entity_id IS NULL
            AND candidate.entity_id IS NULL
            AND candidate.relation_source_entity_id = target.relation_source_entity_id
            AND candidate.relation_type = target.relation_type
            AND candidate.relation_target_entity_id = target.relation_target_entity_id
        )
     )
    WHERE target.id = target_claim_id;
$$;

CREATE FUNCTION kthub_validate_claim_decision_competition_snapshot()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    expected_competing_active_claim_ids JSONB;
BEGIN
    expected_competing_active_claim_ids :=
        kthub_expected_competing_active_claim_ids(NEW.claim_id);

    IF NEW.competing_active_claim_ids IS DISTINCT FROM expected_competing_active_claim_ids THEN
        RAISE EXCEPTION
            '% competing_active_claim_ids do not match active exact-subject Claims for %',
            TG_TABLE_NAME,
            NEW.claim_id;
    END IF;

    IF jsonb_array_length(expected_competing_active_claim_ids) > 0
       AND (NEW.competition_note IS NULL OR length(btrim(NEW.competition_note)) = 0) THEN
        RAISE EXCEPTION
            '% with competing active Claims requires competition_note for %',
            TG_TABLE_NAME,
            NEW.claim_id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_claim_support_decision_competition_integrity
BEFORE INSERT ON claim_support_decision
FOR EACH ROW
EXECUTE FUNCTION kthub_validate_claim_decision_competition_snapshot();

CREATE TRIGGER trg_claim_validation_decision_competition_integrity
BEFORE INSERT ON claim_validation_decision
FOR EACH ROW
EXECUTE FUNCTION kthub_validate_claim_decision_competition_snapshot();

CREATE FUNCTION kthub_reject_claim_decision_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION '% is append-only; % is forbidden', TG_TABLE_NAME, TG_OP;
END;
$$;

CREATE TRIGGER trg_claim_support_decision_append_only
BEFORE UPDATE OR DELETE ON claim_support_decision
FOR EACH ROW
EXECUTE FUNCTION kthub_reject_claim_decision_mutation();

CREATE TRIGGER trg_claim_validation_decision_append_only
BEFORE UPDATE OR DELETE ON claim_validation_decision
FOR EACH ROW
EXECUTE FUNCTION kthub_reject_claim_decision_mutation();

COMMIT;
