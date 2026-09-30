"""Load authoritative Core data from a source checkout or installed package."""
from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any


def load_json_resource(relative_path: str, override_path: Path | None = None) -> dict[str, Any]:
    if override_path is not None:
        return json.loads(Path(override_path).read_text(encoding="utf-8"))

    package = Path(__file__).resolve().parent
    checkout = package.parent.parent
    if package.parent.name == "src" and (checkout / "pyproject.toml").is_file():
        # Keep checkout edits authoritative; do not require copied resource files.
        resource = checkout / relative_path
    else:
        # Never search an installed package's parent directories or the caller's
        # working directory for policy. Use the bytes included in this package.
        resource = files("kneekura_tech_hub").joinpath("resources", relative_path)
    return json.loads(resource.read_text(encoding="utf-8"))
