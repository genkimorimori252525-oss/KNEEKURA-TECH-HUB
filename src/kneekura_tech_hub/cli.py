from __future__ import annotations

import argparse
import json
from pathlib import Path

from .validator import HubValidationError, validate_record


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a KNEEKURA TECH HUB v1 JSON record")
    parser.add_argument("record", type=Path)
    args = parser.parse_args()

    data = json.loads(args.record.read_text(encoding="utf-8"))
    try:
        validate_record(data)
    except HubValidationError as exc:
        print(f"INVALID: {exc}")
        return 1

    print("VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
