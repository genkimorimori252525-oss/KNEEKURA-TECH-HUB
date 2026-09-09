from pathlib import Path


MIGRATION = Path("migrations/0019_reviewed_claim_immutability.sql")


def test_reviewed_claim_immutability_migration_contract() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")

    assert "CREATE TRIGGER trg_reviewed_claim_content_immutability" in sql
    assert "OLD.created_by IS DISTINCT FROM NEW.created_by" in sql
    assert "OLD.maturity = 'CANDIDATE' AND NEW.maturity = 'CANDIDATE'" in sql
    assert "reviewed Claim epistemic content is immutable" in sql

    assert "CREATE FUNCTION kthub_current_claim_evidence_ids" in sql
    assert "ORDER BY decision.decided_at DESC, decision.id DESC" in sql
    assert "reviewed Claim Evidence set differs from latest support decision" in sql

    assert "CREATE CONSTRAINT TRIGGER trg_reviewed_claim_evidence_insert_integrity" in sql
    assert "CREATE CONSTRAINT TRIGGER trg_reviewed_claim_evidence_update_integrity" in sql
    assert "CREATE CONSTRAINT TRIGGER trg_reviewed_claim_evidence_delete_integrity" in sql
    assert "CREATE CONSTRAINT TRIGGER trg_reviewed_claim_evidence_maturity_integrity" in sql
    assert sql.count("DEFERRABLE INITIALLY DEFERRED") >= 4

    # No new revision table is introduced in this slice; corrections use a new Claim ID.
    assert "CREATE TABLE claim_revision" not in sql
