BEGIN;

CREATE FUNCTION kthub_reject_provenance_anchor_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION '% is immutable; % is forbidden', TG_TABLE_NAME, TG_OP;
END;
$$;

CREATE TRIGGER trg_source_snapshot_immutable
BEFORE UPDATE OR DELETE ON source_snapshot
FOR EACH ROW
EXECUTE FUNCTION kthub_reject_provenance_anchor_mutation();

CREATE TRIGGER trg_evidence_immutable
BEFORE UPDATE OR DELETE ON evidence
FOR EACH ROW
EXECUTE FUNCTION kthub_reject_provenance_anchor_mutation();

COMMIT;
