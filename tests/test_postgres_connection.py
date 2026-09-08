from __future__ import annotations

import os

import pytest

from kneekura_tech_hub.postgres_repository import PostgresRepository


DSN = os.getenv("KTHUB_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not DSN, reason="KTHUB_TEST_DATABASE_URL is not set")


def test_repository_connect_uses_autocommit():
    assert DSN is not None
    repository = PostgresRepository.connect(DSN)
    try:
        assert repository.connection.autocommit is True
        repository.connection.execute("SELECT 1").fetchone()
        assert repository.connection.info.transaction_status.name == "IDLE"
    finally:
        repository.close()
