from pathlib import Path


MIGRATION = Path("migrations/0018_claim_disposition_decision.sql")


def test_claim_disposition_migration_pins_protected_terminal_authority() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")

    assert "CREATE TABLE claim_disposition_decision" in sql
    assert "decided_by->>'actor_type' = 'human'" in sql
    assert "to_maturity = 'REJECTED'" in sql
    assert "from_maturity IN ('SUPPORTED', 'CHALLENGED')" in sql
    assert "to_maturity = 'SUPERSEDED'" in sql
    assert "from_maturity IN ('VALIDATED', 'CHALLENGED')" in sql

    assert "CREATE CONSTRAINT TRIGGER trg_claim_terminal_transition_requires_disposition" in sql
    assert "DEFERRABLE INITIALLY DEFERRED" in sql
    assert "CREATE CONSTRAINT TRIGGER trg_claim_disposition_requires_applied_state" in sql
    assert "CREATE TRIGGER trg_claim_disposition_append_only" in sql

    # Candidate rejection remains deliberately outside the protected terminal gate.
    protected_function = sql.split(
        "CREATE FUNCTION kthub_require_disposition_decision_for_terminal_transition()", 1
    )[1].split("CREATE CONSTRAINT TRIGGER", 1)[0]
    assert "OLD.maturity IN ('CANDIDATE'" not in protected_function
