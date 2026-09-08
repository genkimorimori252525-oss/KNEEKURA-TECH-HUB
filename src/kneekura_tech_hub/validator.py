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


def load_review_decision_schema(schema_path: Path | None = None) -> dict[str, Any]:
    if schema_path is None:
        schema_path = (
            Path(__file__).resolve().parents[2]
            / "schemas"
            / "v1"
            / "review-decision.schema.json"
        )
    return json.loads(schema_path.read_text(encoding="utf-8"))


def load_source_selection_decision_schema(schema_path: Path | None = None) -> dict[str, Any]:
    if schema_path is None:
        schema_path = (
            Path(__file__).resolve().parents[2]
            / "schemas"
            / "v1"
            / "source-selection-decision.schema.json"
        )
    return json.loads(schema_path.read_text(encoding="utf-8"))


def load_source_acquisition_authorization_schema(
    schema_path: Path | None = None,
) -> dict[str, Any]:
    if schema_path is None:
        schema_path = (
            Path(__file__).resolve().parents[2]
            / "schemas"
            / "v1"
            / "source-acquisition-authorization.schema.json"
        )
    return json.loads(schema_path.read_text(encoding="utf-8"))


def load_source_acquisition_execution_schema(
    schema_path: Path | None = None,
) -> dict[str, Any]:
    if schema_path is None:
        schema_path = (
            Path(__file__).resolve().parents[2]
            / "schemas"
            / "v1"
            / "source-acquisition-execution.schema.json"
        )
    return json.loads(schema_path.read_text(encoding="utf-8"))


def load_policy(policy_path: Path | None = None) -> dict[str, Any]:
    if policy_path is None:
        policy_path = Path(__file__).resolve().parents[2] / "governance" / "policy-v1.json"
    return json.loads(policy_path.read_text(encoding="utf-8"))


def _missing(locator: dict[str, Any], *fields: str) -> list[str]:
    return [field for field in fields if locator.get(field) in (None, "")]


def _evidence_locator_errors(record: dict[str, Any]) -> list[str]:
    locator = record.get("locator") or {}
    locator_type = locator.get("type")
    errors: list[str] = []

    requirements = {
        "source_lines": ("path", "line_start", "line_end", "content_hash"),
        "symbol": ("symbol",),
        "stable_url": ("url",),
    }
    required = requirements.get(locator_type, ())
    missing = _missing(locator, *required)
    if missing:
        errors.append(f"{locator_type} locator requires: {', '.join(missing)}")

    if locator_type == "document_section" and not (
        locator.get("section") or locator.get("url")
    ):
        errors.append("document_section locator requires section or url")

    if locator_type == "issue_comment" and not (
        locator.get("comment_id") or locator.get("url")
    ):
        errors.append("issue_comment locator requires comment_id or url")

    if locator_type == "experiment_artifact" and not (
        locator.get("artifact_id") or locator.get("content_hash") or locator.get("url")
    ):
        errors.append("experiment_artifact locator requires artifact_id, content_hash, or url")

    line_start = locator.get("line_start")
    line_end = locator.get("line_end")
    if isinstance(line_start, int) and isinstance(line_end, int) and line_end < line_start:
        errors.append("locator line_end must be greater than or equal to line_start")

    return errors


def _execution_errors(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    status = record.get("status")
    requested_paths = record.get("requested_paths") or []
    file_results = record.get("file_results") or []
    actor_type = (record.get("executed_by") or {}).get("actor_type")

    if actor_type not in {"tool", "system"}:
        errors.append("acquisition executions require a tool or system actor")
    if len(file_results) != len(requested_paths):
        errors.append("acquisition execution file_results must cover every requested path")
    elif [item.get("path") for item in file_results] != requested_paths:
        errors.append("acquisition execution file_results must preserve requested path order")

    for item in file_results:
        item_status = item.get("status")
        if item_status == "FETCHED":
            if not isinstance(item.get("byte_count"), int):
                errors.append("FETCHED file result requires byte_count")
            if not item.get("sha256") or not item.get("git_blob_sha"):
                errors.append("FETCHED file result requires sha256 and git_blob_sha")
            if item.get("error_code") is not None:
                errors.append("FETCHED file result cannot contain error_code")
        elif item_status == "FAILED":
            if any(item.get(field) is not None for field in ("byte_count", "sha256", "git_blob_sha")):
                errors.append("FAILED file result cannot contain fetched hashes or byte_count")
            if not item.get("error_code"):
                errors.append("FAILED file result requires error_code")

    if status == "SUCCEEDED":
        if any(item.get("status") != "FETCHED" for item in file_results):
            errors.append("SUCCEEDED acquisition execution cannot contain failed file results")
        if not record.get("manifest_sha256"):
            errors.append("SUCCEEDED acquisition execution requires manifest_sha256")
        if not record.get("storage_key"):
            errors.append("SUCCEEDED acquisition execution requires storage_key")
        if record.get("error_code") is not None:
            errors.append("SUCCEEDED acquisition execution cannot contain error_code")
        if record.get("authorization_effective_after") is not True:
            errors.append("SUCCEEDED acquisition execution requires effective authorization after fetch")
    elif status == "FAILED":
        if not record.get("error_code"):
            errors.append("FAILED acquisition execution requires error_code")
        if record.get("manifest_sha256") is not None or record.get("storage_key") is not None:
            errors.append("FAILED acquisition execution cannot publish manifest or storage_key")
        if (
            record.get("error_code")
            in {
                "AUTHORIZATION_BECAME_INEFFECTIVE",
                "AUTHORIZATION_CHANGED_DURING_EXECUTION",
                "SOURCE_CHANGED_DURING_EXECUTION",
            }
            and record.get("authorization_effective_after") is not False
        ):
            errors.append("provenance-race execution failures must mark authorization ineffective")

    return errors


def _policy_errors(record: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    record_type = record.get("record_type")

    if record_type == "knowledge_entity" and record.get("relations"):
        errors.append(
            "direct canonical relation writes are disabled by relation provenance policy; "
            "use evidence-backed relation claims"
        )

    if record_type == "claim":
        claim_type = record.get("claim_type")
        evidence_ids = record.get("evidence_ids") or []
        relation = record.get("relation")

        if claim_type in policy["required_evidence_for_claim_types"] and not evidence_ids:
            errors.append(f"{claim_type} requires at least one evidence_id")
        if relation is not None and not evidence_ids:
            errors.append("relation claims require at least one evidence_id")
        if isinstance(relation, dict) and (
            relation.get("source_entity_id") == relation.get("target_entity_id")
        ):
            errors.append("relation claim endpoints must be different entities")

    if record_type == "staged_observation":
        evidence_ids = record.get("evidence_candidate_ids") or []
        if not evidence_ids:
            errors.append("staged observations require at least one evidence_candidate_id")

    if record_type == "evidence":
        errors.extend(_evidence_locator_errors(record))

    if record_type == "source":
        license_state = (record.get("license") or {}).get("state")
        acquisition_level = (record.get("acquisition") or {}).get("level")
        if license_state == "UNKNOWN" and acquisition_level != policy["license_unknown_max_acquisition"]:
            errors.append("UNKNOWN license sources are limited to metadata-only acquisition")

    if record_type == "review_decision":
        if record.get("source_claim_id") == record.get("target_claim_id"):
            errors.append("review decision source and target Claims must be different")
        actor_type = (record.get("created_by") or {}).get("actor_type")
        if actor_type != "human":
            errors.append("review decisions require a human creator")
        if record.get("supersedes_decision_id") == record.get("id"):
            errors.append("review decision cannot supersede itself")

    if record_type == "source_selection_decision":
        actor_type = (record.get("created_by") or {}).get("actor_type")
        if actor_type != "human":
            errors.append("source selection decisions require a human creator")
        if record.get("supersedes_decision_id") == record.get("id"):
            errors.append("source selection decision cannot supersede itself")

    if record_type == "source_acquisition_authorization":
        actor_type = (record.get("created_by") or {}).get("actor_type")
        if actor_type != "human":
            errors.append("source acquisition authorizations require a human creator")
        if record.get("supersedes_authorization_id") == record.get("id"):
            errors.append("source acquisition authorization cannot supersede itself")

    if record_type == "source_acquisition_execution":
        errors.extend(_execution_errors(record))

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
    record_type = record.get("record_type")
    if record_type == "review_decision":
        schema = load_review_decision_schema(schema_path)
    elif record_type == "source_selection_decision":
        schema = load_source_selection_decision_schema(schema_path)
    elif record_type == "source_acquisition_authorization":
        schema = load_source_acquisition_authorization_schema(schema_path)
    elif record_type == "source_acquisition_execution":
        schema = load_source_acquisition_execution_schema(schema_path)
    else:
        schema = load_schema(schema_path)
    validator = Draft202012Validator(schema)
    schema_errors = sorted(validator.iter_errors(record), key=lambda error: list(error.path))

    messages = [error.message for error in schema_errors]
    messages.extend(_policy_errors(record, load_policy(policy_path)))

    if messages:
        raise HubValidationError("; ".join(messages))
