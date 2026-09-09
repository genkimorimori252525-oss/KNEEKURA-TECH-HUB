BEGIN;

CREATE FUNCTION kthub_reject_governance_history_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION '% is append-only; % is forbidden', TG_TABLE_NAME, TG_OP;
END;
$$;

CREATE TRIGGER trg_curation_event_append_only
BEFORE UPDATE OR DELETE ON curation_event
FOR EACH ROW
EXECUTE FUNCTION kthub_reject_governance_history_mutation();

CREATE TRIGGER trg_review_decision_append_only
BEFORE UPDATE OR DELETE ON review_decision
FOR EACH ROW
EXECUTE FUNCTION kthub_reject_governance_history_mutation();

CREATE TRIGGER trg_source_selection_decision_append_only
BEFORE UPDATE OR DELETE ON source_selection_decision
FOR EACH ROW
EXECUTE FUNCTION kthub_reject_governance_history_mutation();

CREATE TRIGGER trg_source_acquisition_authorization_append_only
BEFORE UPDATE OR DELETE ON source_acquisition_authorization
FOR EACH ROW
EXECUTE FUNCTION kthub_reject_governance_history_mutation();

CREATE TRIGGER trg_source_acquisition_execution_append_only
BEFORE UPDATE OR DELETE ON source_acquisition_execution
FOR EACH ROW
EXECUTE FUNCTION kthub_reject_governance_history_mutation();

CREATE TRIGGER trg_source_acquisition_commit_append_only
BEFORE UPDATE OR DELETE ON source_acquisition_commit
FOR EACH ROW
EXECUTE FUNCTION kthub_reject_governance_history_mutation();

CREATE TRIGGER trg_observation_triage_decision_append_only
BEFORE UPDATE OR DELETE ON observation_triage_decision
FOR EACH ROW
EXECUTE FUNCTION kthub_reject_governance_history_mutation();

COMMIT;
