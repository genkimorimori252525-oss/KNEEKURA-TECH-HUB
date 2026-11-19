"""Target profiles and block registries (PLAN P2).

A profile separates three things the plan requires to be managed independently:
file format (Sponge version), DataVersion, and the block/state registry. The registry is
Mojang data and is never committed; it is generated locally and pinned by SHA-256.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .blockstate import BlockState

PROFILE_DIR = Path(__file__).resolve().parent.parent / "profiles"


class ProfileError(ValueError):
    pass


@dataclass(frozen=True)
class Registry:
    """block id -> {property: allowed values}. Built from Minecraft's own data-generator report."""

    blocks: dict[str, dict[str, frozenset[str]]]
    sha256: str
    source: str

    def check(self, state: BlockState) -> str | None:
        """Return None when legal, else a reason code. Name-only matching is never enough."""
        props = self.blocks.get(state.block_id)
        if props is None:
            return "UNKNOWN_BLOCK_ID" if state.namespace == "minecraft" else "UNKNOWN_MOD_BLOCK"
        for key, value in state.properties:
            allowed = props.get(key)
            if allowed is None:
                return f"INVALID_PROPERTY:{key}"
            if value not in allowed:
                return f"INVALID_PROPERTY_VALUE:{key}={value}"
        return None


def load_registry(path: Path, expected_sha256: str | None) -> Registry:
    data = Path(path).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        raise ProfileError(f"REGISTRY_SHA256_MISMATCH: expected {expected_sha256}, got {digest}")
    doc = json.loads(data)
    if not isinstance(doc, dict) or not doc:
        raise ProfileError("INVALID_REGISTRY")
    blocks: dict[str, dict[str, frozenset[str]]] = {}
    for block_id, entry in doc.items():
        # Vanilla `--reports` blocks.json: {"minecraft:x": {"properties": {k: [v...]}, "states": [...]}}
        if not isinstance(entry, dict) or "states" not in entry:
            raise ProfileError(f"UNSUPPORTED_REGISTRY_FORMAT: {block_id}")
        props = entry.get("properties", {})
        if not isinstance(props, dict) or not all(isinstance(v, list) for v in props.values()):
            raise ProfileError(f"INVALID_REGISTRY_PROPERTIES: {block_id}")
        blocks[block_id] = {k: frozenset(map(str, v)) for k, v in props.items()}
    return Registry(blocks=blocks, sha256=digest, source=str(path))


@dataclass(frozen=True)
class TargetProfile:
    profile_id: str
    minecraft: str
    loader: str
    worldedit: str
    schematic_version: int
    data_version: int
    registry_path: str
    registry_sha256: str | None
    registry_generator: dict
    status: str
    build_height: int = 384

    def registry(self, root: Path, override: Path | None = None) -> Registry:
        path = override or (root / self.registry_path)
        if not Path(path).exists():
            raise ProfileError(f"REGISTRY_NOT_AVAILABLE: {path} (run `fetch-registry` explicitly)")
        # An override must still match the pin; an unpinned profile only accepts an explicit override.
        if self.registry_sha256 is None and override is None:
            raise ProfileError("REGISTRY_NOT_PINNED")
        return load_registry(Path(path), self.registry_sha256)


def load_profile(profile_id: str) -> TargetProfile:
    if not isinstance(profile_id, str) or not profile_id.replace("-", "").replace(".", "").isalnum():
        raise ProfileError("INVALID_PROFILE_ID")
    path = PROFILE_DIR / f"{profile_id}.json"
    if not path.is_file():
        raise ProfileError(f"UNKNOWN_PROFILE: {profile_id}")
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("profile_id") != profile_id or doc.get("schema_version") != 1:
        raise ProfileError("PROFILE_IDENTITY_MISMATCH")
    missing = [k for k in ("minecraft", "loader", "worldedit", "schematic_version", "data_version", "registry", "status") if k not in doc]
    if missing or "path" not in doc.get("registry", {}):
        raise ProfileError(f"PROFILE_FIELDS_MISSING: {missing or ['registry.path']}")
    if doc["schematic_version"] != 2:
        raise ProfileError("ONLY_SPONGE_V2_TARGETS_IMPLEMENTED")
    reg = doc["registry"]
    return TargetProfile(
        profile_id=profile_id, minecraft=doc["minecraft"], loader=doc["loader"], worldedit=doc["worldedit"],
        schematic_version=doc["schematic_version"], data_version=doc["data_version"],
        registry_path=reg["path"], registry_sha256=reg.get("sha256"), registry_generator=reg.get("generator", {}),
        status=doc["status"], build_height=int(doc.get("build_height", 384)),
    )
