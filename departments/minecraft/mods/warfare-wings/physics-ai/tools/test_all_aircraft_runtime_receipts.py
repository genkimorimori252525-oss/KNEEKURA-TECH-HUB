#!/usr/bin/env python3
"""Synthetic 24-airframe receipt acceptance/rejection; not Minecraft measurements."""

from pathlib import Path
import tempfile

from test_tactical_runtime_receipts import fixture, write
from verify_all_aircraft_runtime_receipts import verify
from verify_tactical_runtime_receipts import (
    ReceiptError, source_airframe_retention,
)


def expect_fail(directory: Path, fragment: str) -> None:
    try:
        verify(directory)
    except ReceiptError as error:
        if fragment not in str(error):
            raise AssertionError(f"Wrong rejection: {error}, expected {fragment}") from error
    else:
        raise AssertionError(f"Broken 24-aircraft fixture passed: {fragment}")


def main() -> None:
    roster = source_airframe_retention()
    checks = 0
    with tempfile.TemporaryDirectory(prefix="ww-24-aircraft-receipt-test-") as temporary:
        path = Path(temporary)
        for aircraft in sorted(roster):
            scenario = "roster-" + aircraft.split(":", 1)[1]
            # 41 real-sample equivalent mock records with the canonical per-model
            # input decay and >4 blocks movement, but NO game entity data.
            mock = fixture(scenario, aircraft)[:41]
            for i, row in enumerate(mock):
                row["pos_z"] = str(i * .2)
                row["yaw_deg"] = str(i * .1)
            write(path, scenario, mock)
        result = verify(path)
        assert result["plane_count"] == 24
        assert result["status"] == "ALL_24_SEQUENTIAL_RUNTIME_SMOKES_VERIFIED"
        checks += 2

        roster_aircraft = sorted(roster)[0]
        name = "roster-" + roster_aircraft.split(":", 1)[1]
        file = path / f"{name}-forge-controls.csv"
        original = file.read_bytes()
        file.unlink()
        expect_fail(path, "trace missing")
        checks += 1
        file.write_bytes(original)

        with file.open("a", encoding="utf-8") as handle:
            handle.write("CORRUPTED EXTRA SAMPLE\n")
        expect_fail(path, "expected 41 data samples")
        checks += 1
        file.write_bytes(original)

        from csv import DictReader, DictWriter
        with file.open(encoding="utf-8", newline="") as handle:
            reader = DictReader(handle)
            fieldnames = reader.fieldnames
            records = list(reader)
        records[6]["smooth_x"] = "-0.8"
        with file.open("w", encoding="utf-8", newline="") as handle:
            writer = DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
        expect_fail(path, "input smoothing failed")
        checks += 1
    print(f"AllAircraftRuntimeReceiptSelfTest passed: {checks} synthetic assertions;"
          " actual 24-plane measurements NOT_RUN in this fixture")


if __name__ == "__main__":
    main()
