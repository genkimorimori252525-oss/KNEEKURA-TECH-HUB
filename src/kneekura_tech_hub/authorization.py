from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import re
from uuid import uuid4

from .repository import Record, RecordRepository
from .selection import active_source_selection_decisions
from .validator import validate_record


class AcquisitionAuthorizationError(ValueError):
    """Raised when a bounded Source acquisition authorization is invalid or unsafe."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _decision_time(record: Record) -> datetime:
    raw = record.get("decided_at")
    if not isinstance(raw, str) or not raw:
        raise AcquisitionAuthorizationError(
            f"acquisition authorization has invalid decided_at: {record.get('id')}"
        )
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AcquisitionAuthorizationError(
            f"acquisition authorization has invalid decided_at: {record.get('id')}"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise AcquisitionAuthorizationError(
            f"acquisition authorization decided_at must include timezone: {record.get('id')}"
        )
    return parsed.astimezone(timezone.utc)


def _source(repository: RecordRepository, source_id: str) -> Record:
    record = repository.get(source_id)
    if record is None:
        raise AcquisitionAuthorizationError(f"missing source: {source_id}")
    if record.get("record_type") != "source":
        raise AcquisitionAuthorizationError(
            f"expected source for {source_id}, got {record.get('record_type')!r}"
        )
    return record


def _selection(repository: RecordRepository, selection_id: str) -> Record:
    record = repository.get(selection_id)
    if record is None:
        raise AcquisitionAuthorizationError(f"missing source selection decision: {selection_id}")
    if record.get("record_type") != "source_selection_decision":
        raise AcquisitionAuthorizationError(
            f"expected source_selection_decision for {selection_id}, "
            f"got {record.get('record_type')!r}"
        )
    validate_record(record)
    return record


def _authorization(repository: RecordRepository, authorization_id: str) -> Record:
    record = repository.get(authorization_id)
    if record is None:
        raise AcquisitionAuthorizationError(
            f"missing source acquisition authorization: {authorization_id}"
        )
    if record.get("record_type") != "source_acquisition_authorization":
        raise AcquisitionAuthorizationError(
            f"expected source_acquisition_authorization for {authorization_id}, "
            f"got {record.get('record_type')!r}"
        )
    return record


def _validate_paths(paths: object) -> list[str]:
    if not isinstance(paths, list) or not 1 <= len(paths) <= 32:
        raise AcquisitionAuthorizationError("allowed_paths must contain between 1 and 32 paths")
    if len(paths) != len(set(paths)):
        raise AcquisitionAuthorizationError("allowed_paths must be unique")

    normalized: list[str] = []
    for path in paths:
        if not isinstance(path, str) or not path:
            raise AcquisitionAuthorizationError("allowed_paths entries must be non-empty strings")
        if "\x00" in path:
            raise AcquisitionAuthorizationError("allowed_paths must not contain NUL")
        if "\\" in path:
            raise AcquisitionAuthorizationError("allowed_paths must use repository-relative POSIX paths")
        if path.startswith("/") or ":" in path:
            raise AcquisitionAuthorizationError("allowed_paths must be repository-relative paths")
        parts = path.split("/")
        if any(part in {"", ".", ".."} for part in parts):
            raise AcquisitionAuthorizationError(
                "allowed_paths must not contain empty, dot, or parent traversal segments"
            )
        if any(part.lower() == ".git" for part in parts):
            raise AcquisitionAuthorizationError("allowed_paths must not target repository control data")
        normalized.append(path)
    return normalized


def _validate_revision(source: Record, revision: object) -> str:
    if not isinstance(revision, str) or not revision:
        raise AcquisitionAuthorizationError("revision must be a non-empty string")
    provider = (source.get("origin") or {}).get("provider")
    if provider == "github" and re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise AcquisitionAuthorizationError(
            "GitHub acquisition authorization requires an exact lowercase 40-hex commit SHA"
        )
    return revision


def _license_is_resolved(source: Record) -> bool:
    license_record = source.get("license") or {}
    expression = license_record.get("declared_expression")
    return (
        license_record.get("state") == "KNOWN"
        and isinstance(expression, str)
        and bool(expression.strip())
    )


def _validate_license_for_authorization(source: Record) -> None:
    if not _license_is_resolved(source):
        raise AcquisitionAuthorizationError(
            "AUTHORIZE requires license.state=KNOWN with a declared license expression"
        )


def _validate_stored_authorization(repository: RecordRepository, record: Record) -> None:
    if record.get("record_type") != "source_acquisition_authorization":
        raise AcquisitionAuthorizationError(
            f"expected source_acquisition_authorization, got {record.get('record_type')!r}"
        )
    validate_record(record)
    _decision_time(record)
    source = _source(repository, record["source_id"])
    selection = _selection(repository, record["selection_decision_id"])
    if selection["source_id"] != source["id"]:
        raise AcquisitionAuthorizationError(
            f"authorization selection belongs to another Source: {record['id']}"
        )
    _validate_revision(source, record["revision"])
    _validate_paths(record["allowed_paths"])


def acquisition_authorization_history(
    repository: RecordRepository,
    *,
    source_id: str | None = None,
) -> list[Record]:
    if source_id is not None:
        _source(repository, source_id)

    records = repository.list("source_acquisition_authorization")
    for record in records:
        _validate_stored_authorization(repository, record)

    if source_id is not None:
        records = [record for record in records if record["source_id"] == source_id]
    return sorted(records, key=lambda item: (_decision_time(item), item["id"]))


def active_acquisition_authorizations(
    repository: RecordRepository,
    *,
    source_id: str | None = None,
) -> list[Record]:
    history = acquisition_authorization_history(repository, source_id=source_id)
    all_records = acquisition_authorization_history(repository)
    superseded_ids = [
        record["supersedes_authorization_id"]
        for record in all_records
        if record.get("supersedes_authorization_id") is not None
    ]
    duplicates = [item for item, count in Counter(superseded_ids).items() if count > 1]
    if duplicates:
        raise AcquisitionAuthorizationError(
            f"acquisition authorization has multiple successors: {sorted(duplicates)!r}"
        )
    superseded = set(superseded_ids)
    active = [record for record in history if record["id"] not in superseded]

    by_source = Counter(record["source_id"] for record in active)
    conflicts = sorted(source for source, count in by_source.items() if count > 1)
    if conflicts:
        raise AcquisitionAuthorizationError(
            f"Source has multiple active acquisition authorizations: {conflicts!r}"
        )
    return active


def authorization_effectiveness(
    repository: RecordRepository,
    authorization_id: str,
) -> Record:
    """Evaluate whether an active AUTHORIZE remains safe to consume *now*.

    Historical authorization is not permanent authority. Current Source depth, license state,
    and Source selection are rechecked so stale grants fail closed before a future executor can
    consume them.
    """

    authorization = _authorization(repository, authorization_id)
    _validate_stored_authorization(repository, authorization)
    source = _source(repository, authorization["source_id"])
    blockers: list[str] = []

    active = active_acquisition_authorizations(repository, source_id=source["id"])
    if len(active) != 1 or active[0]["id"] != authorization["id"]:
        blockers.append("NOT_ACTIVE_AUTHORIZATION")
    if authorization["decision"] != "AUTHORIZE":
        blockers.append("NOT_AUTHORIZE_DECISION")
    if (source.get("acquisition") or {}).get("level") != "metadata-only":
        blockers.append("SOURCE_NO_LONGER_METADATA_ONLY")
    if not _license_is_resolved(source):
        blockers.append("LICENSE_NO_LONGER_RESOLVED")

    selections = active_source_selection_decisions(repository, source_id=source["id"])
    if (
        len(selections) != 1
        or selections[0]["id"] != authorization["selection_decision_id"]
        or selections[0]["decision"] != "SELECT_FOR_REVIEW"
    ):
        blockers.append("SELECTION_NO_LONGER_CURRENT")

    return {
        "authorization": deepcopy(authorization),
        "source": deepcopy(source),
        "effective": not blockers,
        "blockers": blockers,
    }


def authorized_acquisition_requests(repository: RecordRepository) -> list[Record]:
    """Read-only view of currently effective AUTHORIZE records.

    The view rechecks live prerequisites and never fetches a file. Stale authorizations remain
    in history but disappear from this effective-authority view until a new valid grant exists.
    """

    result: list[Record] = []
    for authorization in active_acquisition_authorizations(repository):
        if authorization["decision"] != "AUTHORIZE":
            continue
        status = authorization_effectiveness(repository, authorization["id"])
        if status["effective"]:
            result.append(
                {
                    "authorization": status["authorization"],
                    "source": status["source"],
                }
            )
    return result


class AcquisitionAuthorizationEngine:
    """Human-gated authorization for an exact, bounded selected-file acquisition scope.

    AUTHORIZE requires a current human SELECT_FOR_REVIEW and resolved license metadata.
    REVOKE remains available even if selection/license state later changes. Neither operation
    mutates Source.acquisition or performs retrieval.
    """

    def __init__(self, repository: RecordRepository, *, policy_version: str = "1.0.0") -> None:
        self.repository = repository
        self.policy_version = policy_version

    def create(self, record: Record, *, actor: Record) -> Record:
        if record.get("record_type") != "source_acquisition_authorization":
            raise AcquisitionAuthorizationError(
                f"expected source_acquisition_authorization, got {record.get('record_type')!r}"
            )
        if actor.get("actor_type") != "human":
            raise AcquisitionAuthorizationError("acquisition authorizations require a human actor")
        if record.get("created_by") != actor:
            raise AcquisitionAuthorizationError(
                "acquisition authorization created_by must match the acting identity"
            )
        if record.get("policy_version") != self.policy_version:
            raise AcquisitionAuthorizationError(
                "acquisition authorization policy_version must match the active policy"
            )

        source = _source(self.repository, record["source_id"])
        before = deepcopy(source)
        selection = _selection(self.repository, record["selection_decision_id"])
        if selection["source_id"] != source["id"]:
            raise AcquisitionAuthorizationError(
                "acquisition authorization selection must concern the same Source"
            )

        _validate_revision(source, record.get("revision"))
        _validate_paths(record.get("allowed_paths"))

        active = active_acquisition_authorizations(self.repository, source_id=source["id"])
        predecessor_id = record.get("supersedes_authorization_id")
        decision = record.get("decision")

        if decision == "AUTHORIZE":
            if (source.get("acquisition") or {}).get("level") != "metadata-only":
                raise AcquisitionAuthorizationError(
                    "AUTHORIZE v1 applies only while the Source remains metadata-only"
                )
            _validate_license_for_authorization(source)

            active_selections = active_source_selection_decisions(
                self.repository,
                source_id=source["id"],
            )
            if len(active_selections) != 1:
                raise AcquisitionAuthorizationError(
                    "AUTHORIZE requires exactly one active Source selection decision"
                )
            current_selection = active_selections[0]
            if current_selection["id"] != selection["id"]:
                raise AcquisitionAuthorizationError(
                    "AUTHORIZE must reference the current active Source selection decision"
                )
            if current_selection["decision"] != "SELECT_FOR_REVIEW":
                raise AcquisitionAuthorizationError(
                    "AUTHORIZE requires an active SELECT_FOR_REVIEW decision"
                )

            if active:
                if predecessor_id != active[0]["id"]:
                    raise AcquisitionAuthorizationError(
                        "Source already has an active authorization; supersede it explicitly"
                    )
            elif predecessor_id is not None:
                raise AcquisitionAuthorizationError(
                    "supersedes_authorization_id must reference the active authorization"
                )

            if predecessor_id is not None:
                previous = _authorization(self.repository, predecessor_id)
                _validate_stored_authorization(self.repository, previous)
                if previous["source_id"] != source["id"]:
                    raise AcquisitionAuthorizationError(
                        "superseding authorization must concern the same Source"
                    )

        elif decision == "REVOKE":
            if predecessor_id is None:
                raise AcquisitionAuthorizationError("REVOKE requires supersedes_authorization_id")
            if len(active) != 1 or active[0]["id"] != predecessor_id:
                raise AcquisitionAuthorizationError(
                    "REVOKE must supersede the current active authorization"
                )
            previous = _authorization(self.repository, predecessor_id)
            _validate_stored_authorization(self.repository, previous)
            if previous["decision"] != "AUTHORIZE":
                raise AcquisitionAuthorizationError("REVOKE must supersede an AUTHORIZE record")

            scope_fields = (
                "source_id",
                "selection_decision_id",
                "acquisition_level",
                "revision",
                "allowed_paths",
            )
            mismatched = [field for field in scope_fields if record.get(field) != previous.get(field)]
            if mismatched:
                raise AcquisitionAuthorizationError(
                    "REVOKE must preserve the exact authorized scope: " + ", ".join(mismatched)
                )
        else:
            raise AcquisitionAuthorizationError(f"unsupported authorization decision: {decision!r}")

        validate_record(record)
        _decision_time(record)
        self.repository.put(record)

        after = _source(self.repository, source["id"])
        if after != before:
            raise AcquisitionAuthorizationError(
                "Source changed while recording authorization; acquisition execution is forbidden"
            )
        return deepcopy(record)

    def authorize_from_fields(
        self,
        *,
        source_id: str,
        selection_decision_id: str,
        revision: str,
        allowed_paths: list[str],
        rationale: str,
        actor: Record,
        authorization_id: str | None = None,
        supersedes_authorization_id: str | None = None,
    ) -> Record:
        record: Record = {
            "record_type": "source_acquisition_authorization",
            "id": authorization_id or f"aa:{uuid4()}",
            "source_id": source_id,
            "decision": "AUTHORIZE",
            "selection_decision_id": selection_decision_id,
            "acquisition_level": "selected-files",
            "revision": revision,
            "allowed_paths": allowed_paths,
            "rationale": rationale,
            "created_by": actor,
            "policy_version": self.policy_version,
            "decided_at": _now(),
        }
        if supersedes_authorization_id is not None:
            record["supersedes_authorization_id"] = supersedes_authorization_id
        return self.create(record, actor=actor)

    def revoke(
        self,
        authorization_id: str,
        *,
        rationale: str,
        actor: Record,
        revocation_id: str | None = None,
    ) -> Record:
        previous = _authorization(self.repository, authorization_id)
        record: Record = {
            "record_type": "source_acquisition_authorization",
            "id": revocation_id or f"aa:{uuid4()}",
            "source_id": previous["source_id"],
            "decision": "REVOKE",
            "selection_decision_id": previous["selection_decision_id"],
            "acquisition_level": previous["acquisition_level"],
            "revision": previous["revision"],
            "allowed_paths": deepcopy(previous["allowed_paths"]),
            "rationale": rationale,
            "created_by": actor,
            "policy_version": self.policy_version,
            "decided_at": _now(),
            "supersedes_authorization_id": authorization_id,
        }
        return self.create(record, actor=actor)
