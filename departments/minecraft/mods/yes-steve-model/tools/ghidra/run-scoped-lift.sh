#!/usr/bin/env bash
# Explicit opt-in static analysis. Requires approved official Ghidra/JDK installations.
set -euo pipefail
: "${GHIDRA_HOME:?Set approved Ghidra 12.1.4 installation path}"
: "${JAVA_HOME:?Set a full JDK 21 installation path}"
[[ $# == 2 ]] || { echo 'Usage: run-scoped-lift.sh exact-ysm.jar NEW-output-directory' >&2; exit 2; }
JAR=$(realpath "$1"); OUT=$(realpath -m "$2")
[[ ! -e "$OUT" ]] || { echo 'Use a new output directory; existing output is preserved.' >&2; exit 2; }
[[ -x "$JAVA_HOME/bin/javac" && -x "$GHIDRA_HOME/support/analyzeHeadless" ]]
grep -qx 'application.version=12.1.4' "$GHIDRA_HOME/Ghidra/application.properties"
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
D=$(cd "$SCRIPT_DIR/../.." && pwd)
mkdir -p "$OUT"
if git -C "$OUT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then echo 'Output must be outside Git.' >&2; exit 2; fi
mkdir -p "$OUT/projects" "$OUT/home/"{config,cache,data}
python - "$JAR" "$OUT/libysm-core.so" <<'PY'
import sys,hashlib,zipfile
from pathlib import Path
p=Path(sys.argv[1]);assert hashlib.sha256(p.read_bytes()).hexdigest()=='25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f'
with zipfile.ZipFile(p) as z:b=z.read('META-INF/native/libysm-core.so')
assert hashlib.sha256(b).hexdigest()=='15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22'
Path(sys.argv[2]).write_bytes(b)
PY
export PATH="$JAVA_HOME/bin:$PATH" HOME="$OUT/home" XDG_CONFIG_HOME="$OUT/home/config" XDG_CACHE_HOME="$OUT/home/cache" XDG_DATA_HOME="$OUT/home/data"
export JAVA_TOOL_OPTIONS="-Duser.home=$OUT/home" GHIDRA_HEADLESS_MAXMEM=2G
"$GHIDRA_HOME/support/analyzeHeadless" "$OUT/projects" YsmStatic \
 -import "$OUT/libysm-core.so" -loader ElfLoader -loader-applyRelocations false \
 -loader-loadLibraries false -loader-linkExistingProjectLibraries false -loader-imagebase 0 \
 -noanalysis -max-cpu 2 -scriptPath "$SCRIPT_DIR" -postScript YsmScopedLift.java \
 "$D/NATIVE-GHIDRA-MANIFEST-2026-10-18.tsv" "$OUT/lift.tsv" "$D/NATIVE-GHIDRA-MEMORY-2026-10-18.tsv" > "$OUT/console.log" 2>&1
python "$D/tools/native_ghidra_crosscheck_ysm_265.py" --jar "$JAR" --lift "$OUT/lift.tsv" \
 --manifest "$D/NATIVE-GHIDRA-MANIFEST-2026-10-18.tsv" --memory "$D/NATIVE-GHIDRA-MEMORY-2026-10-18.tsv" --out "$OUT/crosscheck.json"
