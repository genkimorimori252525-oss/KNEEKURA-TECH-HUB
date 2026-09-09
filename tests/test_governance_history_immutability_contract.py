from pathlib import Path


MIGRATION = Path("migrations/0024_governance_history_immutability.sql")

PROTECTED = {
    "review_decision": "trg_review_decision_append_only",
    "source_selection_decision": "trg_source_selection_decision_append_only",
    "source_acquisition_authorization": "trg_source_acquisition_authorization_append_only",
    "source_acquisition_execution": "trg_source_acquisition_execution_append_only",
    "source_acquisition_commit": "trg_source_acquisition_commit_append_only",
    "observation_triage_decision": "trg_observation_triage_decision_append_only",
}


def test_governance_history_migration_targets_exact_unprotected_history_set() -> None:
    text = MIGRATION.read_text(encoding="utf-8")

    for table, trigger in PROTECTED.items():
        assert f"ON {table}" in text
        assert trigger in text

    assert "BEFORE UPDATE OR DELETE" in text
    assert "kthub_reject_governance_history_mutation" in text

    # Already protected elsewhere; this migration must not duplicate those gates.
    assert "trg_curation_event_append_only" not in text
    assert "ON curation_event" not in text
    assert "ON claim_support_decision" not in text
    assert "ON claim_validation_decision" not in text
    assert "ON claim_disposition_decision" not in text
