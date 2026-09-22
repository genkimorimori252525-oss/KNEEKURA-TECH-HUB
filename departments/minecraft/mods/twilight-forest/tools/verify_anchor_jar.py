#!/usr/bin/env python3
"""Verify the distributed Twilight Forest 4.3.2508 JAR against pinned TECH HUB evidence.

This does not claim that matching resources prove compiled-class identity. It produces
machine evidence for the binary hash, metadata, JAR inventory, and exact Git-blob
matches for resources present in the pinned source candidate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

PROJECT_ID = "227639"
FILE_ID = "5468648"
RELEASE = "4.3.2508"
SOURCE_COMMIT = "a7dd8f13c653e137f977f5ffaa870fcb20fc1625"
DEFAULT_URL = "https://cursemaven.com/curse/maven/the-twilight-forest-227639/5468648/the-twilight-forest-227639-5468648.jar"


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha1_file(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "KNEEKURA-TECH-HUB/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response, destination.open('wb') as out:
        shutil.copyfileobj(response, out)


def load_expected_resources(inventory_path: Path) -> dict[str, set[str]]:
    document = json.loads(inventory_path.read_text(encoding='utf-8'))
    expected: dict[str, set[str]] = defaultdict(set)
    prefixes = ('src/main/resources/', 'src/generated/resources/')
    for entry in document.get('entries', []):
        if entry.get('type') != 'blob':
            continue
        path = entry.get('path', '')
        for prefix in prefixes:
            if path.startswith(prefix):
                relative = path[len(prefix):]
                if relative.startswith('.cache/'):
                    break
                expected[relative].add(entry['sha'])
                break
    return dict(expected)


def decode_optional(zf: zipfile.ZipFile, name: str) -> str | None:
    try:
        return zf.read(name).decode('utf-8', errors='replace')
    except KeyError:
        return None


def analyze(jar_path: Path, inventory_path: Path) -> dict:
    expected = load_expected_resources(inventory_path)
    matched = []
    mismatched = []
    expected_present = set()

    with zipfile.ZipFile(jar_path) as zf:
        infos = [info for info in zf.infolist() if not info.is_dir()]
        class_entries = [info.filename for info in infos if info.filename.endswith('.class')]
        resource_entries = [info for info in infos if not info.filename.endswith('.class')]

        for info in resource_entries:
            candidate_shas = expected.get(info.filename)
            if not candidate_shas:
                continue
            expected_present.add(info.filename)
            data = zf.read(info)
            actual_git_sha = git_blob_sha(data)
            record = {
                'path': info.filename,
                'jar_size': info.file_size,
                'jar_git_blob_sha': actual_git_sha,
                'source_candidate_blob_shas': sorted(candidate_shas),
            }
            if actual_git_sha in candidate_shas:
                matched.append(record)
            else:
                mismatched.append(record)

        expected_missing = sorted(set(expected) - expected_present)
        manifest = decode_optional(zf, 'META-INF/MANIFEST.MF')
        mods_toml = decode_optional(zf, 'META-INF/mods.toml')
        pack_mcmeta = decode_optional(zf, 'pack.mcmeta')

    denominator = len(matched) + len(mismatched)
    ratio = (len(matched) / denominator) if denominator else None
    return {
        'evidence_version': '1.0',
        'target': 'The Twilight Forest',
        'distributed_release': RELEASE,
        'curseforge_project_id': PROJECT_ID,
        'curseforge_file_id': FILE_ID,
        'source_candidate_commit': SOURCE_COMMIT,
        'binary': {
            'path': str(jar_path),
            'size': jar_path.stat().st_size,
            'sha256': sha256_file(jar_path),
            'sha1': sha1_file(jar_path),
            'zip_entry_count': len(infos),
            'class_entry_count': len(class_entries),
            'resource_entry_count': len(resource_entries),
        },
        'metadata': {
            'manifest_mf': manifest,
            'mods_toml': mods_toml,
            'pack_mcmeta': pack_mcmeta,
        },
        'resource_correspondence': {
            'source_inventory_path': str(inventory_path),
            'expected_resource_paths': len(expected),
            'compared_paths_present_in_both': denominator,
            'exact_git_blob_matches': len(matched),
            'git_blob_mismatches': len(mismatched),
            'match_ratio_on_compared_paths': ratio,
            'expected_source_paths_missing_from_jar': expected_missing,
            'mismatches': mismatched,
        },
        'identity_conclusion': (
            'RESOURCE_CORRESPONDENCE_STRONG' if denominator and not mismatched else 'RESOURCE_CORRESPONDENCE_PARTIAL'
        ),
        'identity_limit': (
            'Resource equality does not prove compiled-class identity. Exact source-to-binary provenance remains '
            'separate unless build/revision metadata or reproducible class-level evidence closes that gap.'
        ),
    }


def main() -> int:
    script = Path(__file__).resolve()
    target_root = script.parents[1]
    minecraft_root = script.parents[3]
    default_inventory = target_root / 'inventory' / 'anchor-a7dd8f13-files.json'
    default_local = minecraft_root / 'local-artifacts' / 'twilight-forest'

    parser = argparse.ArgumentParser()
    parser.add_argument('--jar', type=Path, help='Use an already-downloaded 4.3.2508 JAR')
    parser.add_argument('--url', default=DEFAULT_URL, help='Download URL when --jar is omitted')
    parser.add_argument('--inventory', type=Path, default=default_inventory)
    parser.add_argument('--output', type=Path, default=default_local / 'anchor-4.3.2508-evidence.json')
    args = parser.parse_args()

    jar_path = args.jar
    if jar_path is None:
        jar_path = default_local / 'twilightforest-1.20.1-4.3.2508-universal.jar'
        if not jar_path.exists():
            print(f'Downloading CurseMaven file {FILE_ID} -> {jar_path}')
            download(args.url, jar_path)

    if not jar_path.is_file():
        raise SystemExit(f'JAR not found: {jar_path}')
    if not args.inventory.is_file():
        raise SystemExit(f'Source inventory not found: {args.inventory}')

    evidence = analyze(jar_path, args.inventory)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({
        'sha256': evidence['binary']['sha256'],
        'size': evidence['binary']['size'],
        'resource_matches': evidence['resource_correspondence']['exact_git_blob_matches'],
        'resource_mismatches': evidence['resource_correspondence']['git_blob_mismatches'],
        'output': str(args.output),
    }, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
