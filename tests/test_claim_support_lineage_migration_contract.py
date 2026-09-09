from pathlib import Path


def test_claim_support_lineage_migration_keeps_one_support_decision_vocabulary() -> None:
    migration = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "0017_claim_support_lineage.sql"
    ).read_text(encoding="utf-8")

    assert "from_maturity IN ('CANDIDATE', 'CHALLENGED')" in migration
    assert "DROP INDEX idx_claim_support_decision_once" in migration
    assert "ON claim_support_decision(claim_id, decided_at)" in migration
    assert "ADD COLUMN last_support_reviewed_at TIMESTAMPTZ" in migration
    assert "requires a fresh claim support decision" in migration
    assert "claim validation decision must reference latest support decision" in migration
    assert "CREATE TABLE claim_resupport_decision" not in migration
