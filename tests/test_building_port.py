"""Building port (PLAN-2026-11-14-CROSS-VERSION) — fixtures T01–T08, no network, no world.

Runs under pytest (CI) and also as a plain script: ``python tests/test_building_port.py``.
The registry used here is a tiny hand-written subset in the vanilla report format; it is a
synthetic fixture, not the authoritative 1.20.1 registry. The real-registry test at the end runs
only when the locally generated, SHA-pinned report exists, and is skipped otherwise.
"""

from __future__ import annotations

import contextlib
import gzip
import json
import re
import struct
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "departments" / "minecraft" / "building" / "portable"))

from schematic_port import cli, compat, ir, nbt, sponge_v2  # noqa: E402
from schematic_port.blockstate import BlockState, BlockStateError, decode_varints, encode_varints, parse_state  # noqa: E402
from schematic_port.profile import ProfileError, Registry, load_profile, load_registry  # noqa: E402

PROFILE = load_profile("minecraft-java-1.20.1-forge")
DATA_TAG = bytes([7, 0, 4]) + b"Data"  # ByteArray tag named "Data" (a bare b"Data" also matches "DataVersion")


@contextlib.contextmanager
def raises(exc, match: str):
    try:
        yield
    except exc as e:  # noqa: PERF203
        assert re.search(match, str(e)), f"{e!r} does not match {match!r}"
    else:
        raise AssertionError(f"{exc.__name__} matching {match!r} not raised")


def registry() -> Registry:
    facing = ["north", "south", "west", "east"]
    tf = ["true", "false"]
    doc = {
        "minecraft:air": {"states": [{"id": 0, "default": True}]},
        "minecraft:stone": {"states": [{"id": 1, "default": True}]},
        "minecraft:oak_planks": {"states": [{"id": 2, "default": True}]},
        "minecraft:glass": {"states": [{"id": 3, "default": True}]},
        "minecraft:oak_stairs": {"properties": {"facing": facing, "half": ["top", "bottom"],
                                                "shape": ["straight", "inner_left", "inner_right", "outer_left", "outer_right"],
                                                "waterlogged": tf}, "states": []},
        "minecraft:oak_door": {"properties": {"facing": facing, "half": ["upper", "lower"], "hinge": ["left", "right"],
                                              "open": tf, "powered": tf}, "states": []},
        "minecraft:oak_fence": {"properties": {"east": tf, "north": tf, "south": tf, "west": tf, "waterlogged": tf}, "states": []},
        "minecraft:water": {"properties": {"level": [str(i) for i in range(16)]}, "states": []},
        "minecraft:cobblestone": {"states": [{"id": 9, "default": True}]},
    }
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "blocks.json"
        p.write_text(json.dumps(doc), encoding="utf-8")
        return load_registry(p, None)


def sparse(cells, **extra) -> bytes:
    return json.dumps({"format": ir.SPARSE_FORMAT, "mcbuild_commit": "0" * 40, "blueprint_sha256": "1" * 64,
                       "seed": 0, "data_version": 3953, "cells": cells, **extra}).encode()


def v3(width, height, length, palette: dict[str, int], indices, offset=(0, 0, 0), extras=None) -> bytes:
    blocks = {"Palette": (nbt.COMPOUND, {k: (nbt.INT, v) for k, v in palette.items()}),
              "Data": (nbt.BYTE_ARRAY, encode_varints(indices)),
              "BlockEntities": (nbt.LIST, (nbt.COMPOUND, extras or []))}
    schematic = {"Version": (nbt.INT, 3), "DataVersion": (nbt.INT, 3953), "Width": (nbt.SHORT, width),
                 "Height": (nbt.SHORT, height), "Length": (nbt.SHORT, length), "Offset": (nbt.INT_ARRAY, list(offset)),
                 "Blocks": (nbt.COMPOUND, blocks), "Entities": (nbt.LIST, (nbt.COMPOUND, []))}
    return nbt.dumps({"Schematic": (nbt.COMPOUND, schematic)})


def roundtrip(building, policy=sponge_v2.SKIP_AIR, reg=None):
    reg = reg or registry()
    result = compat.check(building, reg)
    assert result.status in ("LOSSLESS", "SUBSTITUTED"), result.issues
    data, info = sponge_v2.write_v2(result.ir, PROFILE, policy)
    back = sponge_v2.read_v2(data)
    verdict = sponge_v2.verify_readback(result.ir, back, PROFILE, reg, policy)
    return data, info, back, verdict


# --- primitives -------------------------------------------------------------------------------

def test_block_state_parsing_is_strict_and_canonical():
    s = parse_state("minecraft:oak_stairs[half=top,facing=east]")
    assert str(s) == "minecraft:oak_stairs[facing=east,half=top]"
    for bad in ["oak_stairs", "minecraft:Stone", "minecraft:a[b=c,b=d]", "minecraft:a[b]", "minecraft:a[b=c]x",
                "minecraft:../x", "minecraft:a[ b=c]", "minecraft:a[b=c]]"]:
        with raises(BlockStateError, "INVALID|DUPLICATE"):
            parse_state(bad)


def test_varint_rejects_overlong_truncated_trailing_and_out_of_palette():
    assert list(decode_varints(encode_varints([0, 127, 128, 300]), 4, 300)) == [0, 127, 128, 300]
    with raises(BlockStateError, "OVERLONG"):
        decode_varints(b"\x80\x80\x80\x80\x80\x01", 1, 10)
    with raises(BlockStateError, "NON_MINIMAL"):
        decode_varints(b"\x81\x00", 1, 10)
    with raises(BlockStateError, "TRUNCATED"):
        decode_varints(b"\x81", 1, 10)
    with raises(BlockStateError, "TRAILING"):
        decode_varints(b"\x01\x01", 1, 10)
    with raises(BlockStateError, "OUTSIDE_PALETTE"):
        decode_varints(b"\x05", 1, 4)
    with raises(BlockStateError, "COUNT_EXCEEDS"):
        decode_varints(b"\x01", 10_000_000, 4)


# --- T01–T08 -------------------------------------------------------------------------------------

def test_t01_simple_box_round_trips_with_zero_diff():
    cells = [[x, y, z, "minecraft:stone" if y == 0 else "minecraft:oak_planks"] for x in range(3) for y in range(2) for z in range(3)]
    cells.append([1, 2, 1, "minecraft:glass"])
    building = ir.from_sparse_json(sparse(cells))
    data, info, back, verdict = roundtrip(building)
    assert verdict["status"] == "ZERO_DIFF" and verdict["solid_cells"] == 19
    assert back["data_version"] == 3465 and info["dimensions"] == [3, 3, 3]
    assert sponge_v2.write_v2(compat.check(building, registry()).ir, PROFILE)[0] == data  # reproducible bytes


def test_t02_states_and_orientation_are_preserved():
    states = ["minecraft:oak_stairs[facing=east,half=top]", "minecraft:oak_door[facing=north,half=lower,hinge=left,open=false,powered=false]",
              "minecraft:oak_fence[east=true,north=false,south=false,west=true,waterlogged=false]", "minecraft:water[level=0]"]
    building = ir.from_sparse_json(sparse([[i, 0, 0, s] for i, s in enumerate(states)]))
    _, _, back, verdict = roundtrip(building)
    assert verdict["status"] == "ZERO_DIFF"
    assert str(back["cells"][(0, 0, 0)]) == "minecraft:oak_stairs[facing=east,half=top]"


def test_t03_negative_coordinates_origin_and_l_shape_keep_positions():
    cells = [[-5, -2, 7, "minecraft:stone"], [-4, -2, 7, "minecraft:stone"], [-5, -2, 9, "minecraft:cobblestone"], [-5, 1, 9, "minecraft:glass"]]
    building = ir.from_sparse_json(sparse(cells))
    building.paste_origin = (-5, -2, 7)
    _, info, back, verdict = roundtrip(building)
    assert verdict["status"] == "ZERO_DIFF"
    assert info["offset"] == [-5, -2, 7] and info["we_offset"] == [0, 0, 0] and back["origin"] == [-5, -2, 7]
    assert info["dimensions"] == [2, 4, 3]
    assert back.state_at((-4, -2, 9)).is_air and building.cell_kind((-4, -2, 9)) == ir.ABSENT  # L-shape gap stays empty


def test_t04_explicit_air_vs_absent_and_air_policies():
    cells = [[0, 0, 0, "minecraft:stone"], [2, 0, 0, "minecraft:stone"], [1, 0, 0, "minecraft:air"], [5, 0, 0, "minecraft:air"]]
    building = ir.from_sparse_json(sparse(cells))
    assert building.cell_kind((1, 0, 0)) == ir.EXPLICIT_AIR and building.cell_kind((3, 0, 0)) == ir.ABSENT
    _, info, _, verdict = roundtrip(building, sponge_v2.SKIP_AIR)
    assert verdict["status"] == "ZERO_DIFF" and info["dimensions"] == [3, 1, 1]
    assert any(w.startswith("EXPLICIT_AIR_NOT_APPLIED_WITH_SKIP_AIR:2") for w in info["warnings"])
    _, info, back, verdict = roundtrip(building, sponge_v2.FULL_REPLACE)
    assert verdict["status"] == "ZERO_DIFF" and info["dimensions"] == [6, 1, 1] and back.state_at((5, 0, 0)).is_air
    # A v3 file cannot tell air from unplaced: intent is UNKNOWN and air is not carried.
    unknown = ir.from_sponge_v3(v3(3, 1, 1, {"minecraft:stone": 0, "minecraft:air": 1}, [0, 1, 0]))
    assert unknown.air_intent == ir.AIR_UNKNOWN and len(unknown.cells) == 2
    _, info, _, _ = roundtrip(unknown, sponge_v2.FULL_REPLACE)
    assert "AIR_INTENT_UNKNOWN_ABSENT_CELLS_WILL_BECOME_AIR" in info["warnings"]


def test_t05_newer_blocks_are_refused_never_turned_into_air():
    building = ir.from_sparse_json(sparse([[0, 0, 0, "minecraft:stone"], [1, 0, 0, "minecraft:trial_spawner"]]))
    result = compat.check(building, registry())
    assert result.status == "BLOCKED" and result.ir is None
    assert result.issues[0]["reason"] == "UNKNOWN_BLOCK_ID" and result.issues[0]["positions"] == [[1, 0, 0]]
    reg = registry()
    with raises(compat.SubstitutionError, "TO_AIR_FORBIDDEN"):
        compat.load_substitutions(b'{"minecraft:trial_spawner": "minecraft:air"}', reg)
    table = compat.load_substitutions(b'{"minecraft:trial_spawner": "minecraft:cobblestone"}', reg)
    first = compat.check(building, reg, table)
    assert first.status == "SUBSTITUTED" and first.substitutions[0]["count"] == 1
    assert compat.check(building, reg, table).ir.cells == first.ir.cells  # deterministic


def test_t06_invalid_state_id_and_mod_blocks_are_refused_with_positions():
    cells = [[0, 0, 0, "minecraft:oak_stairs[facing=up]"], [1, 0, 0, "minecraft:oak_stairs[color=red]"],
             [2, 0, 0, "minecraft:not_a_block"], [3, 0, 0, "somemod:machine"]]
    result = compat.check(ir.from_sparse_json(sparse(cells)), registry())
    reasons = {i["reason"] for i in result.issues}
    assert reasons == {"INVALID_PROPERTY_VALUE:facing=up", "INVALID_PROPERTY:color", "UNKNOWN_BLOCK_ID", "UNKNOWN_MOD_BLOCK"}
    stairs = next(i for i in result.issues if i["reason"] == "INVALID_PROPERTY:color")
    assert stairs["candidates"] == ["minecraft:oak_stairs"]
    with raises(compat.SubstitutionError, "TARGET_INVALID"):
        compat.load_substitutions(b'{"somemod:machine": "minecraft:oak_stairs[facing=up]"}', registry())


def test_t07_hostile_inputs_fail_before_large_allocation():
    huge_dims = v3(1, 1, 1, {"minecraft:stone": 0}, [0])
    raw = bytearray(gzip.decompress(huge_dims))
    i = raw.index(b"Width") + len(b"Width")
    raw[i:i + 2] = struct.pack(">h", 30000)
    with raises(ir.IRError, "VOLUME_LIMIT"):
        ir.from_sponge_v3(gzip.compress(bytes(raw)))
    with raises(nbt.NBTError, "NOT_GZIP|TRUNCATED|CORRUPT"):
        ir.from_sponge_v3(huge_dims[:-9])
    bomb = gzip.compress(b"\x00" * (2 * 1024 * 1024))
    with raises(nbt.NBTError, "DECOMPRESSED_SIZE_LIMIT"):
        nbt.loads(bomb, max_bytes=1024 * 1024)
    lying = bytearray(gzip.decompress(huge_dims))
    j = lying.index(DATA_TAG) + len(DATA_TAG)
    lying[j:j + 4] = struct.pack(">i", 2**30)
    with raises(nbt.NBTError, "LENGTH_EXCEEDS_INPUT"):
        ir.from_sponge_v3(gzip.compress(bytes(lying)))
    with raises(BlockStateError, "OVERLONG|TRUNCATED|TRAILING|NON_MINIMAL"):
        good = v3(2, 1, 1, {"minecraft:stone": 0, "minecraft:air": 1}, [0, 1])
        r = bytearray(gzip.decompress(good)); k = r.index(DATA_TAG) + len(DATA_TAG) + 4
        r[k:k + 2] = b"\x80\x80"
        ir.from_sponge_v3(gzip.compress(bytes(r)))
    with raises(ir.IRError, "DUPLICATE_PALETTE_STATE|INVALID_PALETTE"):
        ir.from_sponge_v3(v3(1, 1, 1, {"minecraft:stone": 0, "minecraft:stone[]": 1}, [0]))
    with raises(ir.IRError, "BLOCK_ENTITIES"):
        ir.from_sponge_v3(v3(1, 1, 1, {"minecraft:stone": 0}, [0], extras=[{"Id": (nbt.STRING, "minecraft:chest")}]))
    # Bounds are recomputed from what remains, so a cleared far corner never inflates the export.
    building = ir.from_sparse_json(sparse([[0, 0, 0, "minecraft:stone"]]))
    assert building.bounds() == ((0, 0, 0), (0, 0, 0))
    with raises(ir.IRError, "EXTENT_LIMIT"):
        ir.from_sparse_json(sparse([[0, 0, 0, "minecraft:stone"], [600, 0, 0, "minecraft:stone"]]))


def test_t08_readback_detects_tampering_and_target_illegal_palette():
    building = ir.from_sparse_json(sparse([[0, 0, 0, "minecraft:stone"], [1, 0, 0, "minecraft:glass"]]))
    reg = registry()
    mapped = compat.check(building, reg).ir
    data, _ = sponge_v2.write_v2(mapped, PROFILE)
    root_name, (_, root) = nbt.loads(data)
    root["Palette"] = (nbt.COMPOUND, {"minecraft:air": (nbt.INT, 0), "minecraft:stone": (nbt.INT, 1), "minecraft:glass": (nbt.INT, 2)})
    tampered = sponge_v2.read_v2(nbt.dumps(root, root_name=root_name))
    verdict = sponge_v2.verify_readback(mapped, tampered, PROFILE, reg, sponge_v2.SKIP_AIR)
    assert verdict["status"] == "DIFF" and verdict["counts"]["BLOCK_MISMATCH"] == 2
    root["Palette"] = (nbt.COMPOUND, {"minecraft:air": (nbt.INT, 0), "minecraft:glass": (nbt.INT, 1), "minecraft:trial_spawner": (nbt.INT, 2)})
    illegal = sponge_v2.read_v2(nbt.dumps(root, root_name=root_name))
    assert "PALETTE_NOT_LEGAL_IN_TARGET" in sponge_v2.verify_readback(mapped, illegal, PROFILE, reg, sponge_v2.SKIP_AIR)["counts"]
    root["PaletteMax"] = (nbt.INT, 9)
    with raises(ir.IRError, "PALETTE_MAX_MISMATCH"):
        sponge_v2.read_v2(nbt.dumps(root, root_name=root_name))


# --- CLI -------------------------------------------------------------------------------------------

def test_we_offset_and_block_data_bytes_match_worldedit_formulas_independently():
    """Checks raw NBT against WorldEdit's own formulas, not against our reader (review M1)."""
    cells = [[2, 1, 3, "minecraft:stone"], [3, 1, 3, "minecraft:glass"], [2, 3, 6, "minecraft:oak_planks"]]
    building = ir.from_sparse_json(sparse(cells))
    building.paste_origin = (1, 0, 0)
    data, _ = sponge_v2.write_v2(compat.check(building, registry()).ir, PROFILE)
    _, (_, root) = nbt.loads(data)
    meta = root["Metadata"][1]
    assert [meta[k][1] for k in ("WEOffsetX", "WEOffsetY", "WEOffsetZ")] == [1, 1, 3]  # min (2,1,3) - origin (1,0,0)
    assert list(root["Offset"][1]) == [2, 1, 3]
    w, h, l = (root[k][1] for k in ("Width", "Height", "Length"))
    assert (w, h, l) == (2, 3, 4)
    pal = {k: v[1] for k, v in root["Palette"][1].items()}
    expected = [pal["minecraft:air"]] * (w * h * l)
    for x, y, z, st in cells:  # WorldEdit 7.2.15: index = y*W*L + z*W + x, relative to Offset
        expected[(y - 1) * w * l + (z - 3) * w + (x - 2)] = pal[st]
    assert root["BlockData"][1] == encode_varints(expected)


def test_cell_bombs_are_refused_before_building_cells():
    old = ir.MAX_CELLS
    ir.MAX_CELLS = sponge_v2.MAX_CELLS = 100
    try:
        with raises(ir.IRError, "CELL_LIMIT"):
            ir.from_sponge_v3(v3(10, 2, 10, {"minecraft:stone": 0}, [0] * 200))
        building = ir.from_sparse_json(sparse([[0, 0, 0, "minecraft:stone"]]))
        _, (_, root) = nbt.loads(sponge_v2.write_v2(compat.check(building, registry()).ir, PROFILE)[0])
        root["Width"] = (nbt.SHORT, 20)
        root["Length"] = (nbt.SHORT, 10)
        root["Palette"] = (nbt.COMPOUND, {"minecraft:stone": (nbt.INT, 0)})
        root["PaletteMax"] = (nbt.INT, 1)
        root["BlockData"] = (nbt.BYTE_ARRAY, bytes(200))
        with raises(ir.IRError, "CELL_LIMIT"):
            sponge_v2.read_v2(nbt.dumps(root, root_name="Schematic"))
    finally:
        ir.MAX_CELLS = sponge_v2.MAX_CELLS = old


def test_full_replace_of_v3_input_clears_the_original_box_and_air_variants_survive():
    src = ir.from_sponge_v3(v3(4, 1, 1, {"minecraft:stone": 0, "minecraft:air": 1}, [1, 0, 1, 1], offset=(10, 0, 0)))
    _, info, _, verdict = roundtrip(src, sponge_v2.FULL_REPLACE)
    assert info["dimensions"] == [4, 1, 1] and info["offset"] == [10, 0, 0] and verdict["status"] == "ZERO_DIFF"
    assert "FULL_REPLACE_REGION_IS_SOURCE_V3_BOX" in info["warnings"]
    doc = {"minecraft:air": {"states": []}, "minecraft:cave_air": {"states": []}, "minecraft:stone": {"states": []}}
    with tempfile.TemporaryDirectory() as d:
        rp = Path(d) / "r.json"
        rp.write_text(json.dumps(doc), encoding="utf-8")
        reg = load_registry(rp, None)
    cave = ir.from_sparse_json(sparse([[0, 0, 0, "minecraft:stone"], [1, 0, 0, "minecraft:cave_air"]]))
    _, _, back, verdict = roundtrip(cave, sponge_v2.FULL_REPLACE, reg)
    assert verdict["status"] == "ZERO_DIFF" and str(back.state_at((1, 0, 0))) == "minecraft:cave_air"


def test_duplicate_substitution_keys_are_rejected():
    with raises(compat.SubstitutionError, "DUPLICATE_SUBSTITUTION_KEY"):
        compat.load_substitutions(b'{"minecraft:a": "minecraft:stone", "minecraft:a": "minecraft:glass"}', registry())
    with raises(compat.SubstitutionError, "DUPLICATE_SUBSTITUTION_KEY"):
        compat.load_substitutions(b'{"minecraft:oak_stairs[facing=east,half=top]": "minecraft:stone", '
                                  b'"minecraft:oak_stairs[half=top,facing=east]": "minecraft:glass"}', registry())


def test_cli_convert_success_overwrite_blocked_and_confirmation():
    """Runs the real CLI paths end to end with a profile pinned to a temporary registry (review M2)."""
    import dataclasses
    import hashlib
    original = cli.load_profile
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        reg = d / "blocks.json"
        reg.write_text(json.dumps({"minecraft:air": {"states": []}, "minecraft:stone": {"states": []}}), encoding="utf-8")
        pinned = dataclasses.replace(PROFILE, registry_sha256=hashlib.sha256(reg.read_bytes()).hexdigest())
        src = d / "b.json"
        src.write_bytes(sparse([[0, 0, 0, "minecraft:stone"], [1, 0, 0, "minecraft:stone"]]))
        out = d / "out.schem"
        base = ["convert", str(src), "--target", PROFILE.profile_id, "--registry", str(reg), "--out", str(out)]
        # The real profile pin does not match this temporary registry: refused before anything is written.
        assert cli.main(base) == 2 and not out.exists()
        cli.load_profile = lambda _id: pinned
        try:
            assert cli.main(base) == 0 and out.exists()
            report = json.loads((d / "out.schem.report.json").read_text(encoding="utf-8"))
            assert report["gates"]["P3_FILE_READBACK"] == "PASS" and report["gates"]["P4_PASTE_IN_TEST_WORLD"] == "NOT_RUN"
            assert report["out_schem_sha256"] == hashlib.sha256(out.read_bytes()).hexdigest()
            before = out.read_bytes()
            assert cli.main(base) == 2 and out.read_bytes() == before  # never overwritten
            assert not list(d.glob("*.tmp"))
            bad = d / "bad.json"
            bad.write_bytes(sparse([[0, 0, 0, "minecraft:trial_spawner"]]))
            out2 = d / "out2.schem"
            assert cli.main(["convert", str(bad), "--target", PROFILE.profile_id, "--registry", str(reg), "--out", str(out2)]) == 3
            assert not out2.exists()
            out3 = d / "out3.schem"
            replace = base[:-1] + [str(out3), "--air-policy", "full_region_replace"]
            assert cli.main(replace) == 2 and not out3.exists()
            assert cli.main(replace + ["--confirm-full-replace"]) == 0 and out3.exists()
        finally:
            cli.load_profile = original


def test_profile_pins_format_data_version_and_registry_separately():
    assert (PROFILE.schematic_version, PROFILE.data_version) == (2, 3465)
    assert re.fullmatch(r"[0-9a-f]{64}", PROFILE.registry_sha256)
    with raises(ProfileError, "INVALID_PROFILE_ID|UNKNOWN_PROFILE"):
        load_profile("../../etc/passwd")
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "blocks.json"
        p.write_text("{}", encoding="utf-8")
        with raises(ProfileError, "SHA256_MISMATCH"):
            load_registry(p, PROFILE.registry_sha256)


def test_real_registry_when_generated_locally():
    path = ROOT / PROFILE.registry_path
    if not path.exists():
        try:
            import pytest
            pytest.skip("official registry not generated locally (run fetch-registry explicitly)")
        except ImportError:
            return "SKIPPED"
    reg = PROFILE.registry(ROOT)
    assert reg.check(parse_state("minecraft:oak_stairs[facing=east,half=top]")) is None
    assert reg.check(parse_state("minecraft:trial_spawner")) == "UNKNOWN_BLOCK_ID"
    assert reg.check(parse_state("minecraft:cherry_planks")) is None  # 1.20 block exists


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = skipped = 0
    for name, fn in tests:
        try:
            if fn() == "SKIPPED":
                skipped += 1
                print("skip", name)
                continue
            print("ok  ", name)
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print("FAIL", name, repr(exc))
    print(f"{len(tests) - failed - skipped}/{len(tests)} passed, {skipped} skipped, {failed} failed")
    sys.exit(1 if failed else 0)
