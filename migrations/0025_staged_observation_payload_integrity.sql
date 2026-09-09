BEGIN;

-- A StagedObservation ID denotes one stable extracted payload. Lifecycle status
-- remains governed separately by the Triage Gate, but the source, summary,
-- candidate names, creator, and Evidence set must not drift underneath that ID.
CREATE TABLE staged_observation_payload_anchor (
    observation_id TEXT PRIMARY KEY REFERENCES staged_observation(id) ON DELETE RESTRICT,
    evidence_candidate_ids TEXT[] NOT NULL
);

-- Existing observations become anchored at their currently committed payload.
INSERT INTO staged_observation_payload_anchor(observation_id, evidence_candidate_ids)
SELECT observation.id,
       ARRAY(
           SELECT link.evidence_id
             FROM staged_observation_evidence link
            WHERE link.observation_id = observation.id
            ORDER BY link.evidence_id
       )
  FROM staged_observation observation;

-- New observations are anchored at transaction commit, after their Evidence
-- links have been inserted. This deliberately treats the first committed form
-- as the identity payload while still allowing normal multi-row creation.
CREATE FUNCTION kthub_anchor_new_staged_observation_payload()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO staged_observation_payload_anchor(observation_id, evidence_candidate_ids)
    VALUES (
        NEW.id,
        ARRAY(
            SELECT link.evidence_id
              FROM staged_observation_evidence link
             WHERE link.observation_id = NEW.id
             ORDER BY link.evidence_id
        )
    )
    ON CONFLICT (observation_id) DO NOTHING;
    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER trg_staged_observation_create_payload_anchor
AFTER INSERT ON staged_observation
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION kthub_anchor_new_staged_observation_payload();

-- Status is intentionally excluded: Triage owns that lifecycle field. Every
-- other persisted field that participates in Observation meaning is immutable.
CREATE FUNCTION kthub_guard_staged_observation_payload_update()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.id IS DISTINCT FROM NEW.id
       OR OLD.source_id IS DISTINCT FROM NEW.source_id
       OR OLD.summary IS DISTINCT FROM NEW.summary
       OR OLD.candidate_names IS DISTINCT FROM NEW.candidate_names
       OR OLD.created_by IS DISTINCT FROM NEW.created_by THEN
        RAISE EXCEPTION
            'staged observation payload is immutable; only governed status changes are allowed: %',
            OLD.id;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_staged_observation_payload_immutable
BEFORE UPDATE ON staged_observation
FOR EACH ROW
EXECUTE FUNCTION kthub_guard_staged_observation_payload_update();

-- The repository currently rewrites the link rows when status changes. Use a
-- deferred final-state comparison instead of forbidding intermediate DELETE /
-- INSERT operations, so an unchanged Evidence set remains compatible while any
-- committed semantic change is rejected.
CREATE FUNCTION kthub_require_staged_observation_evidence_anchor()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    target_observation_id TEXT;
    anchored_ids TEXT[];
    current_ids TEXT[];
BEGIN
    target_observation_id := COALESCE(NEW.observation_id, OLD.observation_id);

    SELECT anchor.evidence_candidate_ids
      INTO anchored_ids
      FROM staged_observation_payload_anchor anchor
     WHERE anchor.observation_id = target_observation_id;

    -- During the initial creation transaction the deferred anchor may not have
    -- been inserted yet. The creation trigger will anchor the final committed
    -- set. Every later transaction has an anchor and must compare equal.
    IF anchored_ids IS NULL THEN
        RETURN NULL;
    END IF;

    SELECT ARRAY(
        SELECT link.evidence_id
          FROM staged_observation_evidence link
         WHERE link.observation_id = target_observation_id
         ORDER BY link.evidence_id
    ) INTO current_ids;

    IF current_ids IS DISTINCT FROM anchored_ids THEN
        RAISE EXCEPTION
            'staged observation Evidence set is immutable: %',
            target_observation_id;
    END IF;
    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER trg_staged_observation_evidence_matches_anchor
AFTER INSERT OR UPDATE OR DELETE ON staged_observation_evidence
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION kthub_require_staged_observation_evidence_anchor();

CREATE FUNCTION kthub_reject_staged_observation_anchor_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'staged_observation_payload_anchor is immutable; % is forbidden', TG_OP;
END;
$$;

CREATE TRIGGER trg_staged_observation_payload_anchor_immutable
BEFORE UPDATE OR DELETE ON staged_observation_payload_anchor
FOR EACH ROW
EXECUTE FUNCTION kthub_reject_staged_observation_anchor_mutation();

COMMIT;
