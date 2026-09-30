# Failure / Repair History — two M2 own-development cases

Recorded 2026-09-30. This is a bounded research record using the existing `minecraft.history`, `Store`, `capture_profile` and index adapters. It is not a new knowledge platform or canonical entry.

## Scope and result

- Exact reviewed scope: renderer repair `ddc11a0c3cb8fc1b3314c18fc9935bd86ad93e3d` → `f5651fe5ebbaf4df9526f4644054705d74f0215f`, then staff repair `f5651fe5ebbaf4df9526f4644054705d74f0215f` → `a14f4ed7940236fc6c5493a0cb67835c878191a0`. `c6bbe10e76be0f2806ae2e770bad3914d60b6b8e` corroborates identical repaired asset bytes only.
- Repository head recorded: `9224c8709dc2f174ceb55f61866cd7a0b5f07166`. These are pre-fix observations, not proven bug-introducing commits.
- Adapter import: **OK**, 2 OWN_DEVELOPMENT cases; original-evidence membership/hash checks: 48. Query tests include positive symptom/repair lookups and exact wrong-track/wrong-environment negatives.
- History SHA-256: `4abaa63aa724be619293fbcfd8143f0676c4fa5f01d03a2cfcc4093fb2074971`
- Profile SHA-256: `477167fe9ae142d5c5054327ca0c01718d80ddab7249d8dc9bb42cc77322c839`
- Index snapshot SHA-256: `61a01b3598069012702d4f537fafb283f1af015db720b34021c7084b1b3fe03a`
- Every imported reproduction/fix state is `RECORDED_EXPERIMENT`; canonical writes = **0**; runtime attestation = **false**. All original live session gates remain unchanged (`NOT_RUN`, loaded revision `UNATTESTED`).

## 1. Plugin API readiness did not establish a complete renderer

**Observed:** [failed run 36682264552](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36682264552), artifact 11081404332, had a success-looking plugin/bridge snapshot, GPU adapter warnings, then null editor globals. Its complete six-file ZIP is retained byte-for-byte. The pre-fix workflow used `--disable-gpu`; the harness selected the first page and tested only Plugin/Plugins globals. The local regression transcript records three failures, followed by a separate 13-pass transcript.

**Root-cause inference:** combined evidence supports incomplete WebGL setup and possible selection of the secondary `chrome://gpu` page. Pinned upstream source shows that page is opened after WebGL renderer construction throws, but the artifact lacks the exact thrown native exception and target URL inventory. Those causal details remain INFERENCE.

**Repair:** `f5651fe5ebbaf4df9526f4644054705d74f0215f` requires one unique file-backed editor, `Blockbench.setup_successful`, and a non-lost render context. The workflow enables ANGLE OpenGL with `LIBGL_ALWAYS_SOFTWARE=1` instead of disabling GPU. The [next run](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36683367656) retains successful setup and six editor assets. It also exposes the independent design defects below; transport success did not mean the whole asset was correct.

## 2. First real staff capture missed legacy-format and visual requirements

**Observed before:** native and model bytes contain 26.3 rather than target-compatible legacy 1.9.0, no display transforms, 12 elements, and an all-gold head without a distinct purple accent. The exact front PNG was inspected.

**Root-cause inference:** the guard inherited the editor's latest project settings, while a single gold fill and crowded geometry explain the exported and visible defects. Pinned upstream project source maps the latest default to 26.3. This does not prove any in-game failure.

**Repair:** `a14f4ed7940236fc6c5493a0cb67835c878191a0` pins the owned project to 1.9.0, applies seven exact display slots, bounds palette-paint rectangles, awaits changed bitmap decode, and creates 16 elements with a separate purple star and open gold halo. [Repaired run](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36685697463) front, left and back PNGs were directly inspected. Both serialized formats equal the exact committed display policy. Its separate export result records structural PASS only; original session verification remains untouched. The exported model, texture and three view files from [later capture](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/36686342010) are byte-identical; native .bbmodel bytes differ in elements/textures/outliner and are not declared identical.

## Evidence and portability

The publication keeps two authored history records and derived import/query/verification summaries. The raw evidence archive is retained locally, not published. Paths and hashes in these records refer to that local closure; a checkout alone cannot replay or independently reverify it. The archive contains the `raw/`, profile, index, Store and manifest files described below.

- The archive’s `raw/` preserves exact allowlisted raw captures, the original failed ZIP, first-party before/after files and focused diffs, local experiment logs, and short upstream excerpts. `raw/analysis/evidence-inventory.json` lists source paths/URLs, exact revisions, SHA-256 values, copy time and scope exclusions. Upstream excerpt bytes were compared with pinned local Git files; whole upstream source, installers and provider packages are intentionally omitted.
- `FAILURE-REPAIR-HISTORY.json` contains assertions with their own evidence IDs and immutable document/index anchors. The archive’s `profile.json` gives all raw document hashes. `raw/analysis/observations.json` records derived exact-format/display/asset-byte comparisons without mutating original receipts.
- `portable-evidence.tar.gz` contains this bounded evidence set and only the CAS closure generated from it. No existing CAS, private configuration or token-bearing package was copied. The archive’s `MANIFEST.sha256` covers every bundle member except itself; archive digest is outside the archive in `portable-evidence.tar.gz.sha256`.
- `verification.json` records import/query and fresh-extraction replay results. `query-roundtrip.json` gives positive and negative filter results. History adapter tests: **16 passed**; this is not the complete repository suite. The bare system Python had no pytest; the existing `../venv/bin/python` ran the recorded test command.

### Replay with the existing package

Only with separately authorized access to the original local archive, from the repository root with this package importable:

```sh
H=departments/minecraft/mod-ai/history/2026-09-30
mkdir -p "$H/replay"
tar -xzf "$H/portable-evidence.tar.gz" -C "$H/replay"
(cd "$H/replay" && sha256sum -c MANIFEST.sha256)
PYTHONPATH=src python -m kneekura_tech_hub.minecraft.history --store "$H/replay/store" import --record "$H/replay/FAILURE-REPAIR-HISTORY.json"
PYTHONPATH=src python -m kneekura_tech_hub.minecraft.history --store "$H/replay/store" query --history 4abaa63aa724be619293fbcfd8143f0676c4fa5f01d03a2cfcc4093fb2074971 --query WebGL --track ANCHOR --environment-json '{"blockbench":"5.2.1"}'
PYTHONPATH=src python -m kneekura_tech_hub.minecraft.history --store "$H/replay/store" query --history 4abaa63aa724be619293fbcfd8143f0676c4fa5f01d03a2cfcc4093fb2074971 --query purple --track ANCHOR --environment-json '{"minecraft":"1.20.1","loader":"forge"}'
```

## Limits and remaining work

This reviewed scope is only the two cases and their captured evidence. Broader history, M4/M5 and Forge acceptance are excluded, not complete. Editor screenshots and structural export checks do not validate inventory, held-item, multiplayer or runtime behavior. Local historical test logs lack embedded exact revision/command metadata. No issue closure, commit, green test, or screenshot is promoted to a canonical or game-runtime claim.

## Publication note

The portable archive is retained locally at SHA-256 `268ae42b3aef311dd9187572ad83efa661ce3a578eb0e143cdbbc810bb8ced79`. It is deliberately excluded from public publication. The JSON record, hashes and roundtrip verification remain published; full raw-byte replay requires that local archive. Do not treat a repository checkout alone as the complete portable evidence store.
