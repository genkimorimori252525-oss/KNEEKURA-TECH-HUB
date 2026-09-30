# Disposable Celestial Staff pilot

This is a small application fixture under the existing MOD-AI home, not a new
runner, service, scheduler, or gameplay framework. `pilot.py` calls the existing
registered `minecraft.execution.execute` compile/export adapters, captures the
resolved ProjectProfile, and prepares the existing index after all asset changes.
It cannot launch a game or accept an EULA.

## Fixed assertions

`assertions.json` was written before implementation. Minecraft **1.20.1**, exact
Forge **47.4.6**, Java **17**, item `kneekura:celestial_staff`:

- Server use grants the invoking player Glowing I for **60 ticks** (3 seconds at
  the normal 20 TPS) and a **100-tick** (5-second) item cooldown
- Repeated handler use during cooldown fails without refreshing either value
- No ability damage, item consumption, or durability cost
- Client-side use acknowledges without applying effects or changing cooldown
- `StaffGameTests` invokes `Item.use` directly and explicitly advances a fake
  player's real effect/cooldown subsystem ticks. It does **not** establish physical right-click input,
  wall-clock timing, client display, networking, or performance
- Three optional negative controls deliberately refresh an effect, shorten the
  cooldown to 99 ticks, or attempt damage. They use the same assertions as the
  positive tests and must remain reported FAIL results

The pure `StaffUsePolicy` is independently compiled and executed by the pytest
suite with a supplied Java 17 JDK. That check does not start Minecraft. Actual
handler assertions remain NOT_RUN until an authorized GameTest launch produces
same-run authenticated receipts through the existing observer.

## Fresh workspace only

Use the official MDK URL and SHA-1 already pinned by
`.github/workflows/mod-ai-forge.yml`:

- `https://maven.minecraftforge.net/net/minecraftforge/forge/1.20.1-47.4.6/forge-1.20.1-47.4.6-mdk.zip`
- SHA-1 `1a1c045f235262ff617e285ea2156571ea93bfbe`

Extract into a new disposable directory with `src/` omitted at extraction.
Do not delete or replace source in an existing MOD project. `--configure` refuses
an existing source tree and wrong target, writes only the fixture source and
resources, and changes the fresh MDK's documented identity/build resource options.
Keep `GRADLE_USER_HOME` in an explicitly writable disposable directory.

## Asset boundary

Supply the materialized asset directory, original CAS root, and immutable export
manifest hash. The importer revalidates the original capture with the existing
asset exporter, checks the exact manifest and all three captured byte streams,
and copies only the named model JSON and PNG. It rejects edited packages, changed
resource/target identity, missing/duplicate entries, symlink ancestors, traversal,
and existing destination files. The native `.bbmodel` remains in the asset CAS
and export package, not in the distributable JAR.

For hosted evidence, `--capture-bundle` imports the bounded base64 bundle of
original `store.read()` bytes into `--asset-store`. Every content hash and the exact
required record closure are checked before the first CAS write. Missing, edited,
invalid-base64, and unrelated records fail closed; no receipt is reconstructed.

A successful import returns new source fingerprints but makes no compile/runtime
claim. Build and export must run again after any code or resource edit. The build
helper records registered receipts, resolved profile/index IDs, input hashes, and
JAR entry hashes. Build validation requires the original immutable asset CAS and
manifest hash before and after execution, and packaged assets must equal those
original captured hashes, even if workspace resources and the JAR are edited together.

## Commands

Run from the repository root (substitute explicit local paths):

```
PYTHONPATH=src python tools/ci/mod_ai_staff/pilot.py \
  --workspace /disposable/mdk --configure
PYTHONPATH=src python tools/ci/mod_ai_staff/pilot.py \
  --workspace /disposable/mdk --asset-store /evidence/asset-cas \
  --asset-manifest CAPTURED_EXPORT_MANIFEST_HASH \
  --asset-directory /evidence/asset-export --evidence /evidence/staff
PYTHONPATH=src python tools/ci/mod_ai_staff/pilot.py \
  --workspace /disposable/mdk --evidence /evidence/staff \
  --jdk /explicit/jdk17 --gradle-home /disposable/gradle-home \
  --asset-store /evidence/asset-cas --asset-manifest CAPTURED_EXPORT_MANIFEST_HASH
pytest -q tools/ci/mod_ai_staff/test_pilot.py
```

New receipts are required after fixing a known failed process. Unknown completion
is never retried blindly. No CI workflow or launch budget is changed by this pilot.
The compile receipt captures both the reobfuscated distribution JAR and the
Mojmap `build/classes/java/main` inventory. Forge userdev run contracts bind the
latter because those are the actual classes loaded in userdev; the observer
class-hash guard must never be weakened to accept a namespace mismatch.
A separately authorized launch must use existing `prepare_world`,
`contracts.prepare_contract`, and registered execution with a bounded budget.
