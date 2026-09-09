from pathlib import Path


def test_staged_observation_identity_integrity_migration_contract() -> None:
    sql = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "0025_staged_observation_identity_integrity.sql"
    ).read_text(encoding="utf-8")

    assert "CREATE TABLE staged_observation_evidence_anchor" in sql
    assert "trg_staged_observation_identity_payload" in sql
    assert "OLD.source_id IS DISTINCT FROM NEW.source_id" in sql
    assert "OLD.summary IS DISTINCT FROM NEW.summary" in sql
    assert "OLD.candidate_names IS DISTINCT FROM NEW.candidate_names" in sql
    assert "OLD.created_by IS DISTINCT FROM NEW.created_by" in sql
    assert "trg_staged_observation_delete_forbidden" in sql
    assert "DEFERRABLE INITIALLY DEFERRED" in sql
    assert "trg_staged_observation_evidence_identity" in sql
    assert "staged_observation Evidence identity is immutable" in sql
    assert "trg_staged_observation_evidence_anchor_immutable" in sql

    # Status deliberately remains outside the identity-payload trigger. Lifecycle
    # authority is already governed by migration 0010's triage pairing.
    payload_guard = sql.split(
        "CREATE FUNCTION kthub_guard_staged_observation_identity_update()", 1
    )[1].split("CREATE TRIGGER trg_staged_observation_identity_payload", 1)[0]
    assert "OLD.status" not in payload_guard
    assert "NEW.status" not in payload_guard
