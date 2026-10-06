#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${TMPDIR:-/tmp}/five-difficulties-core-$$"
trap 'rm -rf "$OUT"' EXIT
mkdir -p "$OUT"

mapfile -t MAIN < <(find "$ROOT/src/main/java/dev/kneekura/fivedifficulties/core" -name '*.java' -print | sort)
mapfile -t TEST < <(find "$ROOT/src/test/java" -name '*.java' -print | sort)

javac --release 17 -d "$OUT" "${MAIN[@]}" "${TEST[@]}"
java -cp "$OUT" dev.kneekura.fivedifficulties.core.LegacyPatternCoreRegression
java -cp "$OUT" dev.kneekura.fivedifficulties.core.SakuyaTimeStopCoreRegression
java -cp "$OUT" dev.kneekura.fivedifficulties.core.HomingAmuletContractRegression
java -cp "$OUT" dev.kneekura.fivedifficulties.core.SakuyaWatchContractRegression
java -cp "$OUT" dev.kneekura.fivedifficulties.core.X1WideShotGeometryRegression
java -cp "$OUT" dev.kneekura.fivedifficulties.core.X1HomingMathRegression
java -cp "$OUT" dev.kneekura.fivedifficulties.core.X1SakuyaTimePolicyRegression\n