from __future__ import annotations

from copy import deepcopy

import pytest

from kneekura_tech_hub.repository import MemoryRepository


# These pre-existing adversarial tests deliberately simulate corruption that is
# no longer reachable through the supported repository API now that governance
# history is append-only. Keep their downstream fingerprint/race assertions,
# but inject the impossible state through MemoryRepository's private test state
# rather than weakening production immutability.
_IMPOSSIBLE_AUTHORIZATION_CORRUPTION_TESTS = frozenset(
    {
        "tests/test_authorized_acquisition_execution.py::test_authorization_record_change_midflight_fails_closed",
        "tests/test_selected_file_extraction.py::test_historical_authorization_mutation_is_detected_by_fingerprint",
        "tests/test_verified_acquisition_commit.py::test_authorization_change_after_success_is_detected_by_execution_fingerprint",
    }
)


@pytest.fixture(autouse=True)
def _inject_impossible_authorization_corruption(request, monkeypatch):
    if request.node.nodeid not in _IMPOSSIBLE_AUTHORIZATION_CORRUPTION_TESTS:
        return

    original_put = MemoryRepository.put

    def put_with_test_corruption(self, record, *, replace: bool = False):
        current = self._records.get(record["id"])
        if (
            replace
            and current is not None
            and current.get("record_type") == "source_acquisition_authorization"
        ):
            self._records[record["id"]] = deepcopy(record)
            return
        return original_put(self, record, replace=replace)

    monkeypatch.setattr(MemoryRepository, "put", put_with_test_corruption)
