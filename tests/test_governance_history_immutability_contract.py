from pathlib import Path


MIGRATION = Path("migrations/0021_governance_history_immutability.sql")

PROTECTED_TABLES = (
    "curation_event",
    "review_decision",
    "source_selection_decision",
    "source_acquisition_authorization",
    "source_acquisition_execution",
    "source_acquisition_commit",
    "observation_triage_decision",
)


def test_declared_governance_history_is_append_only_without_freezing_state_records() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")

    assert "kthub_reject_governance_history_mutation" in sql
    for table in PROTECTED_TABLES:
        assert f"BEFORE UPDATE OR DELETE ON {table}" in sql

    # State-bearing canonical records keep their governed update paths.
    assert "BEFORE UPDATE OR DELETE ON source\n" not in sql
    assert "BEFORE UPDATE OR DELETE ON staged_observation" not in sql
    assert "BEFORE UPDATE OR DELETE ON claim\n" not in sql
