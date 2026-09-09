BEGIN;

CREATE FUNCTION kthub_reject_audit_event_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'curation_event is append-only; % is forbidden', TG_OP;
END;
$$;

CREATE TRIGGER trg_curation_event_append_only
BEFORE UPDATE OR DELETE ON curation_event
FOR EACH ROW
EXECUTE FUNCTION kthub_reject_audit_event_mutation();

COMMIT;
