BEGIN;

CREATE FUNCTION kthub_validate_claim_support_decision_evidence()
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

    IF jsonb_array_length(expected_evidence_ids) = 0 THEN
        RAISE EXCEPTION
            'claim support decision requires actual Evidence on claim %',
            NEW.claim_id;
    END IF;

    IF jsonb_array_length(expected_supporting_evidence_ids) = 0 THEN
        RAISE EXCEPTION
            'claim support decision requires actual SUPPORTS Evidence on claim %',
            NEW.claim_id;
    END IF;

    IF NEW.evidence_ids IS DISTINCT FROM expected_evidence_ids THEN
        RAISE EXCEPTION
            'claim support decision evidence_ids do not match claim Evidence for %',
            NEW.claim_id;
    END IF;

    IF NEW.supporting_evidence_ids IS DISTINCT FROM expected_supporting_evidence_ids THEN
        RAISE EXCEPTION
            'claim support decision supporting_evidence_ids do not match Evidence roles for %',
            NEW.claim_id;
    END IF;

    IF NEW.refuting_evidence_ids IS DISTINCT FROM expected_refuting_evidence_ids THEN
        RAISE EXCEPTION
            'claim support decision refuting_evidence_ids do not match Evidence roles for %',
            NEW.claim_id;
    END IF;

    IF NEW.qualifying_evidence_ids IS DISTINCT FROM expected_qualifying_evidence_ids THEN
        RAISE EXCEPTION
            'claim support decision qualifying_evidence_ids do not match Evidence roles for %',
            NEW.claim_id;
    END IF;

    IF NEW.distinct_source_ids IS DISTINCT FROM expected_source_ids THEN
        RAISE EXCEPTION
            'claim support decision distinct_source_ids do not match claim Evidence for %',
            NEW.claim_id;
    END IF;

    IF NEW.distinct_snapshot_ids IS DISTINCT FROM expected_snapshot_ids THEN
        RAISE EXCEPTION
            'claim support decision distinct_snapshot_ids do not match claim Evidence for %',
            NEW.claim_id;
    END IF;

    IF jsonb_array_length(expected_refuting_evidence_ids) > 0
       AND (NEW.counterevidence_note IS NULL OR length(btrim(NEW.counterevidence_note)) = 0) THEN
        RAISE EXCEPTION
            'claim support decision with REFUTES Evidence requires counterevidence_note for %',
            NEW.claim_id;
    END IF;

    IF jsonb_array_length(expected_qualifying_evidence_ids) > 0
       AND (NEW.qualification_note IS NULL OR length(btrim(NEW.qualification_note)) = 0) THEN
        RAISE EXCEPTION
            'claim support decision with QUALIFIES Evidence requires qualification_note for %',
            NEW.claim_id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_claim_support_decision_evidence_integrity
BEFORE INSERT ON claim_support_decision
FOR EACH ROW
EXECUTE FUNCTION kthub_validate_claim_support_decision_evidence();

COMMIT;
