from pathlib import Path


MIGRATION = Path("migrations/0020_provenance_anchor_immutability.sql")


def test_provenance_anchor_migration_freezes_snapshot_and_evidence_only() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")

    assert "BEFORE UPDATE OR DELETE ON source_snapshot" in sql
    assert "BEFORE UPDATE OR DELETE ON evidence" in sql
    assert "kthub_reject_provenance_anchor_mutation" in sql

    # Source remains deliberately mutable because governed acquisition/license
    # state changes are legitimate elsewhere in the Hub.
    assert "BEFORE UPDATE OR DELETE ON source\n" not in sql
    assert "BEFORE UPDATE OR DELETE ON source " not in sql
