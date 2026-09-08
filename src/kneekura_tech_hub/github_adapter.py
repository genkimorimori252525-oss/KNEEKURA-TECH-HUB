from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .discovery import DiscoveryIntakeError, github_source_id, preflight_discovery_intake
from .repository import Record


_ALLOWED_SORTS = {"stars", "forks", "help-wanted-issues", "updated"}
_ALLOWED_ORDERS = {"asc", "desc"}


class GitHubDiscoveryAdapterError(ValueError):
    """Raised when GitHub discovery metadata cannot be converted safely."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_time(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise GitHubDiscoveryAdapterError(
            "discovered_at must be a timezone-aware ISO timestamp"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise GitHubDiscoveryAdapterError("discovered_at must include a timezone")
    return parsed.isoformat()


def _actor(actor: Record) -> Record:
    actor_type = actor.get("actor_type")
    if actor_type not in {"human", "ai", "tool", "system"}:
        raise GitHubDiscoveryAdapterError(f"unsupported actor_type: {actor_type!r}")
    allowed = {"actor_type", "actor_id", "version"}
    extra = sorted(set(actor) - allowed)
    if extra:
        raise GitHubDiscoveryAdapterError(f"unsupported actor fields: {extra!r}")
    return dict(actor)


def _validate_sort_order(search_sort: str | None, search_order: str | None) -> None:
    if search_sort is not None and search_sort not in _ALLOWED_SORTS:
        raise GitHubDiscoveryAdapterError(f"unsupported GitHub search sort: {search_sort!r}")
    if search_order is not None and search_order not in _ALLOWED_ORDERS:
        raise GitHubDiscoveryAdapterError(f"unsupported GitHub search order: {search_order!r}")


def _repository_name(item: dict[str, Any]) -> str:
    value = item.get("full_name")
    if not isinstance(value, str):
        raise GitHubDiscoveryAdapterError("GitHub search item requires full_name")
    parts = value.strip().split("/")
    if len(parts) != 2 or not all(parts):
        raise GitHubDiscoveryAdapterError(f"invalid GitHub full_name: {value!r}")
    return f"{parts[0]}/{parts[1]}"


def _clean_string(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _license_hint(item: dict[str, Any]) -> dict[str, str | None] | None:
    value = item.get("license")
    if not isinstance(value, dict):
        return None
    hint = {
        "key": _clean_string(value.get("key")),
        "name": _clean_string(value.get("name")),
        "spdx_id": _clean_string(value.get("spdx_id")),
        "url": _clean_string(value.get("url")),
    }
    if not any(hint.values()):
        return None
    return hint


def _is_nonpublic(item: dict[str, Any]) -> bool:
    if item.get("private") is True:
        return True
    visibility = item.get("visibility")
    if isinstance(visibility, str):
        return visibility.lower() != "public"
    # OSS discovery fails closed when public visibility is not established.
    return item.get("private") is not False


def _metadata_source(item: dict[str, Any]) -> Record:
    repository = _repository_name(item)
    html_url = item.get("html_url")
    if not isinstance(html_url, str) or not html_url.startswith("https://github.com/"):
        raise GitHubDiscoveryAdapterError(
            f"GitHub search item {repository} requires a github.com html_url"
        )

    origin: dict[str, Any] = {
        "provider": "github",
        "repository": repository,
        "url": html_url,
    }

    optional_fields = {
        "github_repository_id": item.get("id"),
        "node_id": item.get("node_id"),
        "default_branch": item.get("default_branch"),
        "description": item.get("description"),
        "language": item.get("language"),
        "fork": item.get("fork"),
        "archived": item.get("archived"),
        "disabled": item.get("disabled"),
        "visibility": item.get("visibility"),
        "stargazers_count": item.get("stargazers_count"),
        "forks_count": item.get("forks_count"),
        "open_issues_count": item.get("open_issues_count"),
        "pushed_at": item.get("pushed_at"),
        "updated_at": item.get("updated_at"),
        "topics": item.get("topics"),
    }
    origin.update({key: value for key, value in optional_fields.items() if value is not None})

    hint = _license_hint(item)
    if hint is not None:
        # Search API license metadata is a discovery hint, not a verified license conclusion.
        origin["github_license_hint"] = hint

    return {
        "record_type": "source",
        "id": github_source_id(repository),
        "kind": "repository",
        "origin": origin,
        "acquisition": {"level": "metadata-only"},
        "license": {
            "state": "REVIEW_REQUIRED",
            "declared_expression": None,
            "handling_policy": "DISCOVERY_METADATA_ONLY",
        },
    }


def _batch_id(
    query: str,
    source_ids: list[str],
    page: int,
    search_sort: str | None,
    search_order: str | None,
) -> str:
    material = json.dumps(
        {
            "query": query,
            "page": page,
            "sort": search_sort,
            "order": search_order,
            "source_ids": source_ids,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = sha256(material.encode("utf-8")).hexdigest()[:20]
    return f"discovery:github-search:{digest}"


def build_metadata_discovery_batch(
    search_payload: dict[str, Any],
    *,
    query: str,
    discovered_by: Record,
    discovered_at: str | None = None,
    page: int = 1,
    max_records: int = 1000,
    search_sort: str | None = None,
    search_order: str | None = None,
) -> dict[str, Any]:
    """Convert GitHub repository-search items into a metadata-only discovery batch.

    Provider ordering is preserved. Stars, forks, language and license fields remain metadata;
    none of them is converted into a quality judgment or canonical knowledge record. Non-public
    repositories are omitted from this OSS discovery adapter even when an authenticated GitHub
    token could see them. API sort/order are retained as discovery provenance rather than
    interpreted as a quality score.
    """

    if not isinstance(query, str) or not query.strip():
        raise GitHubDiscoveryAdapterError("query must be a non-empty string")
    if not isinstance(page, int) or page < 1:
        raise GitHubDiscoveryAdapterError("page must be a positive integer")
    if not isinstance(max_records, int) or not 1 <= max_records <= 1000:
        raise GitHubDiscoveryAdapterError("max_records must be between 1 and 1000")
    _validate_sort_order(search_sort, search_order)

    actor = _actor(discovered_by)
    timestamp = _parse_time(discovered_at or _now())
    items = search_payload.get("items")
    if not isinstance(items, list):
        raise GitHubDiscoveryAdapterError("GitHub search response requires an items array")

    records: list[Record] = []
    seen: set[str] = set()
    duplicate_count = 0
    skipped_nonpublic_count = 0
    for raw in items:
        if not isinstance(raw, dict):
            raise GitHubDiscoveryAdapterError("GitHub search items must be objects")
        if _is_nonpublic(raw):
            skipped_nonpublic_count += 1
            continue
        source = _metadata_source(raw)
        if source["id"] in seen:
            duplicate_count += 1
            continue
        seen.add(source["id"])
        records.append(source)
        if len(records) >= max_records:
            break

    if not records:
        raise GitHubDiscoveryAdapterError(
            "GitHub search response produced no usable public repositories"
        )

    source_ids = [record["id"] for record in records]
    batch: dict[str, Any] = {
        "intake_version": "1.0",
        "batch_id": _batch_id(query.strip(), source_ids, page, search_sort, search_order),
        "discovered_by": actor,
        "discovered_at": timestamp,
        "scope": {
            "provider": "github",
            "query": query.strip(),
            "selection_basis": (
                "GitHub repository search provider order; discovery metadata is not a quality rank"
            ),
            "filters": {
                "adapter": "github-discovery-adapter-v1",
                "metadata_only": True,
                "public_only": True,
                "page": page,
                "api_sort": search_sort,
                "api_order": search_order,
                "input_item_count": len(items),
                "output_source_count": len(records),
                "duplicate_source_count": duplicate_count,
                "skipped_nonpublic_count": skipped_nonpublic_count,
                "api_total_count": search_payload.get("total_count"),
                "api_incomplete_results": search_payload.get("incomplete_results"),
            },
        },
        "records": records,
    }

    try:
        preflight_discovery_intake(batch)
    except DiscoveryIntakeError as exc:
        raise GitHubDiscoveryAdapterError(f"adapter produced invalid discovery batch: {exc}") from exc
    return batch


def fetch_repository_search_page(
    query: str,
    *,
    token: str | None = None,
    per_page: int = 100,
    page: int = 1,
    sort: str | None = None,
    order: str | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Fetch one GitHub repository-search page without writing any Hub data."""

    if not isinstance(query, str) or not query.strip():
        raise GitHubDiscoveryAdapterError("query must be a non-empty string")
    if not isinstance(per_page, int) or not 1 <= per_page <= 100:
        raise GitHubDiscoveryAdapterError("per_page must be between 1 and 100")
    if not isinstance(page, int) or page < 1:
        raise GitHubDiscoveryAdapterError("page must be a positive integer")
    _validate_sort_order(sort, order)

    params: dict[str, Any] = {"q": query.strip(), "per_page": per_page, "page": page}
    if sort is not None:
        params["sort"] = sort
    if order is not None:
        params["order"] = order

    request = Request(
        "https://api.github.com/search/repositories?" + urlencode(params),
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "KNEEKURA-TECH-HUB/github-discovery-adapter-v1",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed GitHub host
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise GitHubDiscoveryAdapterError(f"GitHub search HTTP error: {exc.code}") from exc
    except URLError as exc:
        raise GitHubDiscoveryAdapterError(f"GitHub search transport error: {exc.reason}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GitHubDiscoveryAdapterError("GitHub search returned invalid JSON") from exc

    if not isinstance(payload, dict):
        raise GitHubDiscoveryAdapterError("GitHub search response must be an object")
    return payload


def load_search_payload(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GitHubDiscoveryAdapterError(f"cannot read GitHub search payload: {path}") from exc
    if not isinstance(payload, dict):
        raise GitHubDiscoveryAdapterError("GitHub search payload must be an object")
    return payload
