from __future__ import annotations

from copy import deepcopy
from typing import Any, Protocol


Record = dict[str, Any]


class RecordRepository(Protocol):
    def get(self, record_id: str) -> Record | None:
        ...

    def put(self, record: Record, *, replace: bool = False) -> None:
        ...

    def list(self, record_type: str | None = None) -> list[Record]:
        ...


class DuplicateRecordError(ValueError):
    pass


class MemoryRepository:
    """Small in-memory repository used by the curation domain layer and tests."""

    def __init__(self) -> None:
        self._records: dict[str, Record] = {}

    def get(self, record_id: str) -> Record | None:
        record = self._records.get(record_id)
        return deepcopy(record) if record is not None else None

    def put(self, record: Record, *, replace: bool = False) -> None:
        record_id = record["id"]
        if record_id in self._records and not replace:
            raise DuplicateRecordError(f"record already exists: {record_id}")
        self._records[record_id] = deepcopy(record)

    def list(self, record_type: str | None = None) -> list[Record]:
        records = self._records.values()
        if record_type is not None:
            records = [record for record in records if record.get("record_type") == record_type]
        return [deepcopy(record) for record in records]
