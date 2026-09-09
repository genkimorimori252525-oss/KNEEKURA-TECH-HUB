BEGIN;

CREATE TABLE staged_observation_evidence_anchor (
    observation_id TEXT PRIMARY KEY REFERENCES staged_observation(id),
    evidence_ids TEXT[] NOT NULL
);

INSERT INTO staged_observation_evidence_anchor(observation_id, evidence_ids)
SELECT
    observation.id,
    COALESCE(
        array_agg(link.evidence_id ORDER BY link.evidence_id)
            FILTER (WHERE link.evidence_id IS NOT NULL),
        ARRAY[]::TEXT[]
    )
FROM staged_observation observation
LEFT JOIN staged_observation_evidence link
  ON link.observation_id = observation.id
GROUP BY observation.id;

CREATE FUNCTION kthub_guard_staged_observation_identity_update()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.id IS DISTINCT FROM NEW.id
       OR OLD.source_id IS DISTINCT FROM NEW.source_id
       OR OLD.summary IS DISTINCT FROM NEW.summary
       OR OLD.candidate_names IS DISTINCT FROM NEW.candidate_names
       OR OLD.created_by IS DISTINCT FROM NEW.created_by
       OR OLD.created_at IS DISTINCT FROM NEW.created_at THEN
        RAISE EXCEPTION
            'staged_observation identity payload is immutable; only governed status changes are allowed';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_staged_observation_identity_payload
BEFORE UPDATE ON staged_observation
FOR EACH ROW
EXECUTE FUNCTION kthub_guard_staged_observation_identity_update();

CREATE FUNCTION kthub_reject_staged_observation_delete()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'staged_observation is retained history; DELETE is forbidden';
END;
$$;

CREATE TRIGGER trg_staged_observation_delete_forbidden
BEFORE DELETE ON staged_observation
FOR EACH ROW
EXECUTE FUNCTION kthub_reject_staged_observation_delete();

CREATE FUNCTION kthub_capture_staged_observation_evidence_anchor()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    current_evidence_ids TEXT[];
BEGIN
    SELECT COALESCE(array_agg(evidence_id ORDER BY evidence_id), ARRAY[]::TEXT[])
      INTO current_evidence_ids
      FROM staged_observation_evidence
     WHERE observation_id = NEW.id;

    INSERT INTO staged_observation_evidence_anchor(observation_id, evidence_ids)
    VALUES (NEW.id, current_evidence_ids);
    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER trg_staged_observation_capture_evidence_anchor
AFTER INSERT ON staged_observation
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION kthub_capture_staged_observation_evidence_anchor();

CREATE FUNCTION kthub_validate_staged_observation_evidence_identity()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    target_observation_id TEXT;
    expected_evidence_ids TEXT[];
    current_evidence_ids TEXT[];
BEGIN
    target_observation_id := COALESCE(NEW.observation_id, OLD.observation_id);

    SELECT evidence_ids
      INTO expected_evidence_ids
      FROM staged_observation_evidence_anchor
     WHERE observation_id = target_observation_id;

    -- During the creation transaction the deferred Observation INSERT trigger
    -- may not have materialized the anchor yet. That trigger captures the final
    -- Evidence set before commit. Every previously committed Observation has an
    -- anchor because existing rows are backfilled above.
    IF expected_evidence_ids IS NULL THEN
        RETURN NULL;
    END IF;

    SELECT COALESCE(array_agg(evidence_id ORDER BY evidence_id), ARRAY[]::TEXT[])
      INTO current_evidence_ids
      FROM staged_observation_evidence
     WHERE observation_id = target_observation_id;

    IF current_evidence_ids IS DISTINCT FROM expected_evidence_ids THEN
        RAISE EXCEPTION
            'staged_observation Evidence identity is immutable for %',
            target_observation_id;
    END IF;
    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER trg_staged_observation_evidence_identity
AFTER INSERT OR UPDATE OR DELETE ON staged_observation_evidence
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION kthub_validate_staged_observation_evidence_identity();

CREATE FUNCTION kthub_reject_staged_observation_anchor_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'staged_observation evidence anchor is immutable; % is forbidden', TG_OP;
END;
$$;

CREATE TRIGGER trg_staged_observation_evidence_anchor_immutable
BEFORE UPDATE OR DELETE ON staged_observation_evidence_anchor
FOR EACH ROW
EXECUTE FUNCTION kthub_reject_staged_observation_anchor_mutation();

COMMIT;
