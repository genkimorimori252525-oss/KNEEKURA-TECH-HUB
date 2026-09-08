from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


class HubValidationError(ValueError):
    """Raised when a Hub record violates schema or v1 governance rules."""


def load_schema(schema_path: Path | None = None) -> dict[str, Any]:
    if schema_path is None:
        schema_path = Path(__file__).resolve().parents[2] / "schemas" / "v1" / "hub.schema.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


def load_policy(policy_path: Path | None = None) -> dict[str, Any]:
    if policy_path is None:
        policy_path = Path(__file__).resolve().parents[2] / "governance" / "policy-v1.json"
    return json.loads(policy_path.read_text(encoding="utf-8"))


def _policy_errors(record: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    record_type = record.get("record_type")

    if record_type == "claim":
        claim_type = record.get("claim_type")
        maturity = record.get("maturity")
        actor_type = (record.get("created_by") or {}).get("actor_type")
        evidence_ids = record.get("evidence_ids") or []

        if claim_type in policy["required_evidence_for_claim_types"] and not evidence_ids:
            errors.append(f"{claim_type} requires at least one evidence_id")
        if actor_type == "ai" and maturity == "VALIDATED" and not policy["ai_may_promote_to_validated"]:
            errors.append("AI-created claims cannot be VALIDATED under policy v1")

    if record_type == "source":
        license_state = (record.get("license") or {}).get("state")
        acquisition_level = (record.get("acquisition") or {}).get("level")
        if license_state == "UNKNOWN" and acquisition_level != policy["license_unknown_max_acquisition"]:
            errors.append("UNKNOWN license sources are limited to metadata-only acquisition")

    if record_type == "curation_event":
        actor_type = (record.get("actor") or {}).get("actor_type")
        operation = record.get("operation")
        if operation == "ENTITY_MERGE" and actor_type != "human" and not policy["automatic_entity_merge"]:
            errors.append("Canonical entity merge requires a human actor")

    return errors


def validate_record(
    record: dict[str, Any],
    *,
    schema_path: Path | None = None,
    policy_path: Path | None = None,
) -> None:
    schema = load_schema(schema_path)
    validator = Draft202012Validator(schema)
    schema_errors = sorted(validator.iter_errors(record), key=lambda error: list(error.path))

    messages = [error.message for error in schema_errors]
    messages.extend(_policy_errors(record, load_policy(policy_path)))

    if messages:
        raise HubValidationError("; ".join(messages))
