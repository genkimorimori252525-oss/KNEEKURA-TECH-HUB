from pathlib import Path


MIGRATIONS = Path(__file__).resolve().parents[1] / "migrations"


def test_validation_migration_allows_one_decision_per_verification_timestamp() -> None:
    migration = (MIGRATIONS / "0013_claim_validation_decision.sql").read_text(encoding="utf-8")

    assert "CREATE UNIQUE INDEX idx_claim_validation_decision_verification_once" in migration
    assert "ON claim_validation_decision(claim_id, validated_at)" in migration


def test_decision_audit_hardening_pins_competition_and_append_only_history() -> None:
    migration = (MIGRATIONS / "0015_claim_decision_audit_integrity.sql").read_text(
        encoding="utf-8"
    )

    assert "kthub_expected_competing_active_claim_ids" in migration
    assert "trg_claim_support_decision_competition_integrity" in migration
    assert "trg_claim_validation_decision_competition_integrity" in migration
    assert "BEFORE UPDATE OR DELETE ON claim_support_decision" in migration
    assert "BEFORE UPDATE OR DELETE ON claim_validation_decision" in migration
