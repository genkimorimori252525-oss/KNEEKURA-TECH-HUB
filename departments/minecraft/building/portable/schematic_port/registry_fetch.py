"""Explicit, opt-in generation of the official block-state report for a target version.

Downloads Mojang's server jar (SHA-1 pinned by Mojang's own version manifest), then runs the
vanilla data generator ``--reports`` (the server itself is never started, no world is created).
Output stays under ``departments/minecraft/local-artifacts/`` and is never committed.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
ALLOWED_HOSTS = {"piston-meta.mojang.com", "piston-data.mojang.com", "launcher.mojang.com"}
MAX_JAR_BYTES = 128 * 1024 * 1024


def _get(url: str, max_bytes: int) -> bytes:
    if urlparse(url).scheme != "https" or urlparse(url).hostname not in ALLOWED_HOSTS:
        raise RuntimeError(f"REFUSED_HOST: {url}")
    with urllib.request.urlopen(url, timeout=60) as r:  # noqa: S310 - https + host allowlist above
        data = r.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise RuntimeError("DOWNLOAD_SIZE_LIMIT")
    return data


def fetch(minecraft: str, out_dir: Path, expected_server_sha1: str | None = None, java: str = "java") -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(_get(MANIFEST_URL, 4 * 1024 * 1024))
    version = next((v for v in manifest["versions"] if v["id"] == minecraft), None)
    if version is None:
        raise RuntimeError(f"UNKNOWN_MINECRAFT_VERSION: {minecraft}")
    meta_bytes = _get(version["url"], 4 * 1024 * 1024)
    if hashlib.sha1(meta_bytes).hexdigest() != version["sha1"]:  # noqa: S324 - Mojang publishes SHA-1
        raise RuntimeError("VERSION_METADATA_SHA1_MISMATCH")
    server = json.loads(meta_bytes)["downloads"]["server"]
    if expected_server_sha1 and server["sha1"] != expected_server_sha1:
        raise RuntimeError(f"SERVER_SHA1_PIN_MISMATCH: manifest={server['sha1']}")
    jar = out_dir / "server.jar"
    if not jar.exists() or hashlib.sha1(jar.read_bytes()).hexdigest() != server["sha1"]:  # noqa: S324
        data = _get(server["url"], MAX_JAR_BYTES)
        if hashlib.sha1(data).hexdigest() != server["sha1"]:  # noqa: S324
            raise RuntimeError("SERVER_JAR_SHA1_MISMATCH")
        jar.write_bytes(data)
    generated = out_dir / "generated"
    if generated.exists():
        shutil.rmtree(generated)
    subprocess.run([java, "-DbundlerMainClass=net.minecraft.data.Main", "-jar", str(jar), "--reports",
                    "--output", str(generated)], cwd=out_dir, check=True, timeout=600,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    blocks = generated / "reports" / "blocks.json"
    if not blocks.is_file():
        raise RuntimeError("BLOCKS_REPORT_NOT_GENERATED")
    return {"minecraft": minecraft, "server_sha1": server["sha1"], "server_url": server["url"],
            "blocks_json": str(blocks), "blocks_sha256": hashlib.sha256(blocks.read_bytes()).hexdigest()}
