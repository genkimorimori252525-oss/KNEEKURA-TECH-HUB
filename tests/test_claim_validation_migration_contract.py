from pathlib import Path


def test_validation_migration_allows_one_decision_per_verification_timestamp() -> None:
    migration = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "0013_claim_validation_decision.sql"
    ).read_text(encoding="utf-8")

    assert "CREATE UNIQUE INDEX idx_claim_validation_decision_verification_once" in migration
    assert "ON claim_validation_decision(claim_id, validated_at)" in migration
