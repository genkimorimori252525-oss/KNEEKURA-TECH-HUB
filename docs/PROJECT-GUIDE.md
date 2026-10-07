# KNEEKURA TECH HUB — Project Guide

Reviewed: 2026-10-07. Scope: local knowledge core plus GitHub main, all 126 branch refs and 54 open PRs inventoried; relevant feature docs and entry-point source inspected. This is a routing guide, not an exhaustive code audit or fresh runtime certification. Recheck heads, PR states, current acceptance and `--help` before use.

The Hub includes knowledge curation, Minecraft source intelligence, asset tooling, real-game experiments/observation, historical MOD studies, optimization research and offline authoring/simulation tools. **14 local core CLIs are not the full tool inventory.**

## Availability and feature map

Local HEAD: `379c6b372522f744acc4698f5396787c9f056dbb`, with unrelated dirty Twilight R2 work. GitHub main: `c9145ec5376aeeff59995b8c20f7b839f810ab6e` (2026-10-02). Main adds `kneekura-minecraft` as a **15th console entry**, plus separate Python modules, Node tools and Forge adapters absent from this checkout. Later features live in separate unmerged branches. Documentation links do not install them; select an isolated, reviewed revision before running a missing tool. Never pull/reset over existing work.

Those local availability statements describe the original guide checkout. Mob POV is implemented in `C:/Users/genki/.codex/worktrees/mob-pov-camera/KNEEKURA-TECH-HUB`, branch `codex/mob-pov-camera-20261007`, based on PR96 `6b7456278b25e1f8ac3fbeb416ee7ee9a525c542`; it is not merged into main or installed in the original checkout. Use that worktree's Python (`PYTHONPATH=src`) and LAB together; repin its complete32-module control source closure. Check the working directory/source before applying either inventory.

| Task / feature | Entry and capability | Reviewed availability / limit |
| --- | --- | --- |
| OSS knowledge / discovery | 14 core CLIs below; revision-backed Evidence, Claims, contextual guidance | Local and main; core v1 frozen |
| MOD-AI / Source Intelligence | [MOD-AI][mod-ai]; `kneekura-minecraft`: profile/classpath capture, source/bytecode inspection, mappings, intervention candidates, Core staging | Main; exact identity and coverage required |
| Compact AI task preparation | [TaskContext][task-context]; `task prepare` / `task capabilities`, existing evidence and bounded next actions | Main; read-only, no automatic execution; 12 capability rows |
| Model / texture / export workflow | [Asset integration][asset-integration]; static Java-item spec, registered Blockbench editing/capture, verified resource export | Main; scoped Linux/X11 staff cycle accepted; general model/animation/armor authoring not established |
| Build / GameTest / live observation | Registered Gradle/Java, disposable worlds, authenticated Forge observer, paired client/server observation and native input | Main; Windows MOD-AI native input unsupported; registered operations and budgets required |
| LAB / Arena / Tank | [Current main handoff][main-handoff], [LAB][lab]; owned process/world, bounded Arena actions, Cardinal capture/restoration, finalized evidence/export, Tank presentation | Main; canonical home is `departments/minecraft/lab`, not the old standalone LAB repository |
| Trace / network / animation analysis | LAB `simlab`: JSONL schemas, replay/analysis, packet companion, YSM graph/Molang probes, render/golden regression tools | Main; derived/Web views do not replace real Minecraft acceptance |
| Vanilla discovery / AI research | [Foundation Map][foundation], [Vanilla AI][vanilla-ai]; exact captured classes, inheritance/reference candidates; Goal/Brain/pathfinding/control research | Main; generated CAS map, incomplete semantic inventory; structural references are not a dynamic call graph |
| Motion Trace / Decision Observatory | [Current continuation][decision-handoff]; UUID-bound retained/native views, Goal/Brain/memory/path/control/result stages, terrain/Boss adapters | Draft PR79/80; bounded source/runtime evidence, full original acceptance still open |
| Tank Workbench / iteration | [Workbench][tank-workbench]; status/preflight, tick cursor, standalone HTML, experiment digest/comparison/reproduction/guidance; [lean MOD profile][tank-core] | Draft PR94/95/96 stacked above PR80; measured diagnostics do not establish universal non-degradation |
| Kobun / historical MOD studies | [Ancient MOD lane][kobun]; ORIGINAL / ERA-CONTEXT / DESCENDANT / MODERN-EXTRACTION; [Five Difficulties X1 ecosystem][kobun-x1] | Draft PR90/93; historical API/mapping/runtime isolated; X1 static evidence, original runtime NOT_RUN |
| Optimization research | [Optimization lane][optimization]; renderer/tick/memory/GC/I/O/cache/threading mechanisms and benchmarks | Draft PR91; mechanism evidence alone is PERFORMANCE_NOT_VERIFIED; correctness/compatibility tested separately |
| Danmaku creation / preview | [JavaFX 3D sketch][danmaku]; FAN/RING/SPIRAL, multitrack Score v2, live editing, Player POV, JSON save/load and timeline controls | Draft PR97; authoring preview, Minecraft collision/damage/networking/performance not implemented |
| Airborne AI research / prototype | [Offline prototype][airborne]; Hero/Common flight contracts, landing/route/LOS/recovery, read-only model observation | Draft PR84/86/87; deterministic offline model, Minecraft runtime NOT_RUN |
| Aircraft Physics AI / Atlas | [Warfare Wings laboratory][warfare]; Java 17 microkernel, 24-aircraft Atlas v2, trace comparison/calibration bridge | Draft PR102/103; SOURCE_MICROKERNEL; same-artifact real-game calibration NOT_RUN |
| Preservation / reconstruction code | [Five Difficulties 1.20.1 port][x1-port]; pure-Java core + Forge Homing/Sakuya slice; Bedrock Wither PR75/81 | Separate unmerged work; X1 README records P6 server scenarios, P7 branch adds client-smoke source; complete content/client parity not established |
| Model / animation engineering research | [YSM research][ysm]; Molang/controller/render/network seams and exact-binary semantic maps | Separate research branch, no matching open PR in reviewed listing; whole-target IN_PROGRESS, runtime unmeasured |

**Branch stack matters.** PR97 → PR96 → PR95 → PR94 → PR80 → PR79 → main; PR93 → PR90; PR87 → PR86 → PR84; PR100 → PR99; PR81 → PR75. A later date does not make independent research branches a combined baseline. PR102 and PR103 have separate main-based heads. Before porting findings, compare the actual branch/base and accepted source generation.

**Research shelves, not installed plugins.** Open research includes Youkai Homecoming danmaku (#92), JujutsuCraft combat (#99), Jujutsu Verse domain/VFX (#100), Kimetsu combat/VFX (#98), Goofy Critters locomotion (#89), Liberty Villagers habits (#88), Invasion siege (#85), Ages of Dominion RTS/UI (#83), Chronoclones replay (#82), and cross-MOD flight (#84). PR85 is open/non-draft; the other listed PRs are draft. Chronoclones explicitly lacks exact binary/source acquisition. Separate YSM, FatePhantasms VFX and Madomagi QB research branches also exist; branch presence is not complete analysis. Open harvest PR42–70 stage metadata, not technical proof or runnable features. Read each exact target manifest, evidence and failure/repair history before reuse.

**Document precedence.** Follow the selected revision's current handoff/acceptance and actual source before historical checkpoints. Main's `mod-ai/assets/README.md` still describes M1 and LAB's debug README retains G1/G2 omissions; current main records later scoped asset/runtime and Arena/control/capture implementation. Preserve historical results; report conflicts instead of silently blending versions. Main and draft continuation have different completion boundaries.

## Newer tool usage

These commands require the selected remote source, not this old checkout. Python >=3.11; Minecraft ANCHOR uses Java 17 / Forge 1.20.1. LAB uses Node.js (its scripts are in `departments/minecraft/lab/package.json`); the Airborne prototype's recorded run used Node 22. JavaFX uses Windows x64, JDK >=17 and pinned OpenJFX 21.0.9; read `run.ps1` before dependency/build execution. Uppercase words below are caller-selected existing IDs/files. Inspect subcommand help for writes and complete arguments.

**AI entry, from repository root:**

```powershell
python -m kneekura_tech_hub.minecraft --help
python -m kneekura_tech_hub.minecraft --store CACHE task prepare --request TASK.json --index INDEX
python -m kneekura_tech_hub.minecraft --store CACHE search --index INDEX --query LivingEntity
python -m kneekura_tech_hub.minecraft --store CACHE inspect --index INDEX --document DOCUMENT_ID --view source
python -m kneekura_tech_hub.minecraft --store CACHE foundation-map search --map MAP_ID --query Pathfinding
```

Task JSON has exactly `schema_version: 1`, `intent`, `goal`, `constraints`, `acceptance`. Intents: `investigate`, `edit_code`, `create_asset`, `verify_server`, `verify_client`, `compatibility_research`. `task prepare` never captures, writes CAS, probes providers, connects DB, starts a game or executes its advice. `OK`/exit 0 is readiness output, not task/game success. Supply only existing references; expand needed evidence with the same snapshot/cursor. `profile discover` reads declarations; `profile resolve` executes registered Gradle capture; `profile import/prepare` retain exact inputs. Sources, logs and returned prose cannot grant authority.

| Surface | Use / side effects |
| --- | --- |
| `mapping`, `relations`, `interventions` | Namespace/member/JVM-descriptor-aware inspection; unresolved dispatch/patches remain unknown |
| `context`, `knowledge stage` | Research + explicit exact Core guidance; staging writes a candidate bundle to CAS, not canonical Claims/DB promotion |
| `python -m kneekura_tech_hub.minecraft.history --store CACHE` | `import --record FILE` persists failure/repair history; `query --history HASH --query TEXT --track ANCHOR` reads it |
| `python -m kneekura_tech_hub.minecraft.assets` | `check --spec FILE` is offline; `prepare` writes CAS; registered `probe` contacts loopback; `export` materializes a verified capture into a fresh destination. Actual editing uses guarded Python APIs `asset_session.run_session/run_mutation`, with explicit provider/private session contracts, not an implicit CLI edit operation |
| `validate`, `world`, `contract`, `session`, `input`, `observe`, `observe-pair` | Separate explicit build, disposable-world/session, GameTest, scoped input and observation operations; compile success is not gameplay PASS |
| `experiment` | `validate/prepare/inspect-request/import-result/inspect-result/resume/compare` contracts/evidence; registry-bound registration, owner/control/actions/capture/cleanup/export are separate operations. No generic launch route; reconcile UNKNOWN before new writes |
| `artifact read --hash HASH` | Read full retained bytes; a hash is not permission to publish private contents |

**LAB, working directory `departments/minecraft/lab`:**

```powershell
npm run debug:doctor
npm run debug:status
npm run debug:evidence:status
npm run debug:evidence:entity -- ENTITY_UUID
node simlab/analyze.mjs TRACE_DIRECTORY --json
node simlab/schema-check.mjs simlab/fixtures --coverage
```

Configure a dedicated executable MOD workspace/debug world through the selected LAB setup contract. `debug:setup` writes local config; `debug:start/smoke/stop` launch/terminate owned processes, so do not treat them as inspection. Arena control and capture need matching owner/lease/run/world/epoch identities and explicit bounds. Finalized evidence stays read-only; drop/gap/unknown completion remains visible. Actual server state, client state, sampled transitions and derived explanations stay separate. Do not compile into a live mutable runtime classpath.

For PR94/96 use `node debug-workspace/cli.mjs tank-status --arena-epoch N --config CONFIG`; `tank-view UUID` additionally needs revision/tick-window/output selectors. `experiment-summary/compare/reproduction/guidance` follow the [Workbench contract][tank-workbench]. Emit HTML/manifests outside finalized runs. Missing world/observer/presentation bindings yield INCONCLUSIVE; matching declarations alone do not prove A/B comparability. `TANK_CORE` vs `FULL_COMPAT` is a registered experiment-input change, not evidence for compatibility with removed MODs.

**Mob POV, implemented on the local camera branch:** [AF-0011](AI-FEEDBACK.md#af-0011--opt-in-mob-pov-with-explicit-image-retrieval) records scoped real-client acceptance: UUID-bound live viewing, zero default images, one requested PNG, explicit/expiry return and original-world preservation. Read `departments/minecraft/lab/debug-workspace/bridge/MOB-POV.md` in the worktree above for permissions, CLI, budgets, source pins and retrieval. No recording buffer or additional MOD. Moving/dead/unloaded targets and external-camera native cases remain NOT_RUN; lifecycle tests do not establish them. Existing cardinal capture retains its frozen four-view contract. Rendered eye view does not certify AI perception. `TANK_CORE` controls the MOD profile, not Tank dimensions; physical fixture geometry and bounded action authority are separate (AF-0008).

**Native flight fixture:** [AF-0012](AI-FEEDBACK.md#af-0012--bounded-flight-fixture-and-acceptance-repairs) records NaturalGhast's scoped static Player acquisition/flight acceptance in a fresh56×16×56 room. Offline preparation, actual world baseline, Player observation and the small action grant are separate. One registered seal-cell opening activates observation; 600 read-only server samples and one explicit raw PNG, no target setter, fake-player dependency or automatic recording. The target's `docs/FLIGHT-MOBILITY-VERIFICATION.md` and `tools/tank/run-flight-tank.mjs` hold exact source/host/runtime identities and limitations. Journal completion does not by itself prove owner idle/next-action readiness. Keep supported block palettes and class anchors; unknown filesystem errors remain unknown (AF-0013).

**Fixture subjects and preservation:** NaturalGhast preparation now excludes exact saved seed Reimu roots in its bounded room; Reimu is not a mandatory `TANK_CORE` resident. Explicit Reimu-subject MOB_POV experiments remain intentional (AF-0014). The2026-10-08 user observation requires a broad persistent boss-owned region and physical swimming, superseding camera-following assumptions; old static-player PASS is not acceptance of that corrected behavior (AF-0015). Inspect NBT only in a disposable copy: Minecraft `RegionFile` can write padding even during inspection. Original preservation requires byte hashes/counts, not semantic readback (AF-0016).

**Danmaku, working directory `departments/minecraft/danmaku-preview` at PR97:**

```powershell
./run.ps1 -JavaHome 'C:/Program Files/Java/jdk-17' -Score
./run.ps1 -Score -ScoreFile 'C:/path/to/score.json'
./run.ps1 -Test
```

Without `-Score`, use single Pattern v1. Score v2 composes tracks with start/end ticks, WORLD/PLAYER_VIEW, forward speed, phase, hue/radius and FAN/RING/SPIRAL. Old scores lacking `phaseDeg` default to 0. Bounds: 60 seconds, 32 tracks, 3000 combined live bullets; invalid inputs are rejected rather than silently dropped. Player POV/top/side/free camera, play/pause/single tick/seek and counts support visual iteration. Keep boss-origin emission and intended safe gaps; preview success does not prove runtime feasibility. `-CompileOnly` and `-Smoke` are additional source/UI checks, not Minecraft tests; `-Score -Smoke` is unsupported. The launcher writes build/cache files and downloads missing hash-pinned JavaFX JARs; `-Test` uses pure Java without JavaFX download.

**Choose a research lane.** Normal targets use ANCHOR/FRONTIER; Kobun preserves era-specific ORIGINAL names, mappings and artifacts, then derives modern extraction separately. Five Difficulties X1 includes spell-card/normal-danmaku/action-variant/addon atlases; do not infer modern parity from them. Optimization separates mechanism, measured workload, semantic correctness and compatibility. Airborne runs `npm test` in its prototype directory and emits an explicitly non-runtime schema. Warfare Wings must complete same-artifact trace calibration before source Atlas ranks become measured performance or autonomous-combat acceptance.

### Pinned source references

[mod-ai]: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/c9145ec5376aeeff59995b8c20f7b839f810ab6e/departments/minecraft/mod-ai/README.md
[task-context]: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/c9145ec5376aeeff59995b8c20f7b839f810ab6e/departments/minecraft/mod-ai/TASK-CONTEXT.md
[asset-integration]: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/c9145ec5376aeeff59995b8c20f7b839f810ab6e/departments/minecraft/mod-ai/CURRENT-ACCEPTANCE-2026-09-30.md
[main-handoff]: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/c9145ec5376aeeff59995b8c20f7b839f810ab6e/departments/minecraft/CURRENT-HANDOFF-2026-10-02.md
[lab]: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/c9145ec5376aeeff59995b8c20f7b839f810ab6e/departments/minecraft/lab/README.md
[foundation]: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/c9145ec5376aeeff59995b8c20f7b839f810ab6e/departments/minecraft/vanilla-foundation/README.md
[vanilla-ai]: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/c9145ec5376aeeff59995b8c20f7b839f810ab6e/departments/minecraft/vanilla-ai/README.md
[decision-handoff]: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/6b7456278b25e1f8ac3fbeb416ee7ee9a525c542/departments/minecraft/CURRENT-HANDOFF-2026-10-04.md
[tank-workbench]: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/6b7456278b25e1f8ac3fbeb416ee7ee9a525c542/departments/minecraft/lab/docs/KNEEKURA_TANK_WORKBENCH.md
[tank-core]: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/6b7456278b25e1f8ac3fbeb416ee7ee9a525c542/departments/minecraft/lab/docs/KNEEKURA_TANK_CORE_PROFILE.md
[kobun]: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/7fd9919b0397cfa2bf97efba8fb547627bedbb6e/departments/minecraft/kobun/README.md
[kobun-x1]: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/cb83cee43c241b45e473f01e00263adf4d1c188f/departments/minecraft/kobun/mods/itutu-no-nandai-plus/README.md
[optimization]: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/b1ba6493f463f0b70bb9c94cf78700ed35b5e064/departments/minecraft/optimization/README.md
[danmaku]: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/ef1fe6180bafedd98bd21181b08a034d241098c7/departments/minecraft/danmaku-preview/README.md
[airborne]: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/210acdf2715be767e3ab83752385de3da7d1ea47/departments/minecraft/mod-ai/airborne-ai/prototype/README.md
[warfare]: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/2c0cf1329ec8a75edf91d4cde0622f513eb2c181/departments/minecraft/mods/warfare-wings/physics-ai/README.md
[x1-port]: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/a73a71d54b0e8916d33ee340d143244b42060f2d/departments/minecraft/mods/five-difficulties/port-1.20.1/README.md
[ysm]: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/blob/a6abc37e39db9b25ad643abf074215064b206199/departments/minecraft/mods/yes-steve-model/README.md

## Start here

Read applicable task/`AGENTS.md` instructions, [README](../README.md), [Constitution](../governance/CONSTITUTION.md), [policy](../governance/policy-v1.json), relevant schemas/designs/tests, and [AI feedback](AI-FEEDBACK.md). Check existing work:

```powershell
git status --short
git branch --show-current
```

Keep unrelated dirty files intact. If `.codegraph/` exists, use CodeGraph before locating/understanding code; otherwise use `rg`. No CodeGraph index existed at review time.

The Hub's knowledge core discovers OSS technology and curates evidence-backed knowledge. [Core v1 is frozen](architecture/CORE-FEATURE-FREEZE-v1.md): reopen only for a reproduced defect, unmet original-purpose workflow, operational failure, evidenced governance/integrity weakness, or breaking platform change. Missing fuzzy search, embeddings, rankings, universal scores, automatic merge/validation, or default mass crawling is intentional. This core freeze does not declare department tools complete or cancel their separate approved designs.

| Path | Purpose |
| --- | --- |
| `src/kneekura_tech_hub/` | Domain logic, persistence and CLIs |
| `tests/` | Authority, provenance, history, race and DB checks |
| `schemas/v1/`, `governance/` | Record contracts and knowledge-quality policy |
| `migrations/` | Ordered SQL; applied-history SHA-256 drift protection |
| `pilots/`, `docs/pilots/`, `docs/research/` | Pinned OSS examples and research records |
| `docs/architecture/` | Invariants, gates and acceptance criteria |
| `departments/minecraft/` | Whole-target analysis and portability |
| `.github/workflows/` | Python tests and Minecraft execution lanes |

## Knowledge and authority

```text
Metadata -> Source -> human Selection + license/Authorization
-> bounded Execution -> verified Commit -> immutable SourceSnapshot
-> Evidence -> NEW StagedObservation -> human triage -> Claim CANDIDATE
-> human SUPPORTED -> human VALIDATED -> contextual reads + explanation
```

Curated bundles and Minecraft full-tree research have separate governed paths. The selected-file executor is not a full-clone tool.

- **Source:** search metadata/popularity is not technical evidence.
- **SourceSnapshot:** immutable revision anchor; new upstream revisions never overwrite history.
- **Evidence:** stable locator/content with `SUPPORTS`, `REFUTES`, `QUALIFIES` roles.
- **StagedObservation:** lower-trust candidate; starts `NEW`. AI cannot mutate its lifecycle.
- **Claim:** exactly one entity or relation subject. Inference remains inference.
- **Knowledge Entity:** immutable identity; no automatic canonical merge.
- **Relation Projection:** rebuilt from Claims, never a second canonical graph.
- **Review Decision:** append-only human judgment, separate from Claim mutation/promotion.

AI may extract, propose, compare and supply review material. Canonical entity creation/merge, Claim support/validation, and terminal disposition of reviewed Claims require the corresponding human authority. Preserve authorship and audit trails.

**Actor trap:** `kneekura-hub` defaults to `human`; selection/auth/support/validation/disposition CLIs construct human actors. This is not authentication. AI must not impersonate a reviewer by supplying an actor ID. Use explicit `--actor-type ai` and actual ID/version only on permitted paths. Multiple Sources do not imply independent evidence; `VALIDATED` does not imply universal applicability, no counterevidence, or permanent freshness.

## Environment and safe checks

Requirements: Python `>=3.11`, `jsonschema`; DB uses `psycopg`; dev extras include `pytest`/`psycopg`. [pyproject.toml](../pyproject.toml) defines dependencies and entry points. Reviewed local Python: 3.13.14; test CI: 3.12.

For a new environment only; reuse an existing `.venv`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\kneekura-hub.exe --help
```

Examples below assume `.venv/Scripts` is on PATH. Replace `<...>` placeholders before execution.

```powershell
kneekura-hub bundle-check pilots/incremental-computation-v1.json
kneekura-hub validate <record.json>
```

These need no DB/network and write no records. Schema/preflight success is not semantic human validation. `bundle-check` requires a self-contained bundle: relations/problems overlays depend on base Evidence/entities and correctly fail alone. Ingest base first; offline overlay preflight can use `preflight_bundle(..., repository=...)` with base records in `MemoryRepository`.

**DB side effects:** `KTHUB_DATABASE_URL` supplies normal connections; guidance and supported hub subcommands also accept `--dsn`. `init-db` applies migrations. Nine dedicated CLIs—selection, auth, execution, commit, extraction, triage, support, validation, disposition—call `apply_migrations` on connection, including history/context/check commands. A business-record read may therefore alter schema. Verify destination and authority first. Guidance and hub read paths do not auto-migrate; their DB must already be initialized. Never store credentials/tokens in docs or logs. Use [README examples](../README.md#quick-start) and each gate's specification for authorized writes.

## Local knowledge-core CLI map

All 14 local knowledge-core entry points support `--help`; inspect subcommand help for exact arguments. Newer Minecraft/Node/Java tools are mapped above. Read-like operations still have the migration caveat above.

| Command | Main surface / purpose | Contract |
| --- | --- | --- |
| `kneekura-hub` | validate/bundle/discovery checks; ingest, relations, problem queries, explanations, reviews, comparisons, decisions, transitions, merge | [CLI](../src/kneekura_tech_hub/cli.py) |
| `kneekura-hub-validate` | Validate one JSON record | [CLI](../src/kneekura_tech_hub/cli.py) |
| `kneekura-github-discover` | `--query` or saved `--input-json`; one metadata page; no DB writes | [Adapter](architecture/GITHUB-DISCOVERY-ADAPTER-v1.md) |
| `kneekura-discovery-run` | `--spec`, optional `--responses`, `--output`; bounded multi-query search; no DB writes | [Run](architecture/BOUNDED-DISCOVERY-RUN-v1.md) |
| `kneekura-source-selection` | `decide/history/active/selected`; human review selection, not acquisition permission | [Selection](architecture/METADATA-REVIEW-SELECTION-GATE-v1.md) |
| `kneekura-acquisition-auth` | `authorize/revoke/history/active/authorized`; human revision/path permission, no fetching | [Auth](architecture/ACQUISITION-AUTHORIZATION-v1.md) |
| `kneekura-acquisition-exec` | `execute/history`; authorized GitHub Contents fetch; tool/system executor | [Execution](architecture/AUTHORIZED-ACQUISITION-EXECUTION-v1.md) |
| `kneekura-acquisition-commit` | `verify/commit/history`; recheck bytes/provenance and commit Snapshot | [Commit](architecture/VERIFIED-ACQUISITION-COMMIT-v1.md) |
| `kneekura-selected-file-extract` | `snapshot-check/check/ingest`; verified selected files -> Evidence + NEW observations | [Extraction](architecture/CANONICAL-SELECTED-FILE-EVIDENCE-EXTRACTION-v1.md) |
| `kneekura-observation-triage` | `queue/show/duplicates/history/transition`; human candidate promotion; no auto-merge | [Triage](architecture/STAGED-OBSERVATION-TRIAGE-v1.md) |
| `kneekura-claim-support` | `context/history/promote`; human CANDIDATE -> SUPPORTED | [Support](architecture/CLAIM-SUPPORT-GATE-v1.md) |
| `kneekura-claim-validation` | `context/history/validate`; human validation/revalidation with review basis | [Validation](architecture/CLAIM-VALIDATION-GATE-v1.md) |
| `kneekura-claim-disposition` | `context/history/decide`; human reviewed-Claim rejection/supersession | [Disposition](architecture/CLAIM-DISPOSITION-GATE-v1.md) |
| `kneekura-guidance` | entity ID, optional `--context-json`; read-only VALIDATED selection and provenance | [Guidance](architecture/CONTEXT-GUIDANCE-QUERY-SURFACE-v1.md) |

Discovery caps: 32 queries, 10 pages/query, 100 requests/run, 1000 unique Sources. Execution caps: 32 paths, 1 MiB/file, 8 MiB/run. Do not evade bounds by widening permissions.

## Workflows

**Reuse knowledge.** Find IDs via `list --type knowledge_entity`; query `relations`, `solutions`, `solved-problems`, `requirements`. `research` includes CANDIDATE/SUPPORTED/VALIDATED/CHALLENGED; choose `validated`, `challenged` or `history` deliberately. Pilot IDs exist only after ingestion.

```powershell
kneekura-hub solutions ke:problem:repeated-recomputation-after-input-change --view research
kneekura-hub requirements ke:query-based-incremental-computation --view research
kneekura-hub explain-claim <claim-id>
kneekura-hub review-claim <claim-id>
kneekura-hub review-claims --needs-review
kneekura-hub compare-claims --multiple-only
kneekura-guidance <entity-id> --context-json '{"minecraft_version":"1.20.1","loader":"Forge"}'
```

Context is a format example, not a promised match. Match actual applicability keys, values and JSON types. If Windows shell quoting corrupts JSON, fix argument passing rather than weakening validation.

Guidance outcomes: `ONE_MATCH` -> inspect scope/evidence; `MULTIPLE_MATCHES` -> preserve alternatives; `CONTEXT_REQUIRED` -> obtain context; `NO_MATCH` -> preserve mismatch; `NO_VALIDATED_CLAIMS` -> return to review. Never invent a winner or fallback.

**Research new technology.** Define problem/application; inspect existing records; bounded metadata discovery + `discovery-check`; human selection/license/authorization; exact authorized fetch + separate verified commit; extraction check/ingest; human triage to an existing subject's CANDIDATE; support/validation review; contextual retrieval. Missing entities require governed human creation. For upstream changes, add Snapshots/Claims and re-verification history; do not rewrite reviewed statements/Evidence. Diagnose rejected input before changing guards.

**Minecraft.** Read the selected revision's department, analysis spec/workflow, catalog and target README/manifest. Local [department](../departments/minecraft/README.md), [analysis spec](../departments/minecraft/ANALYSIS-SPEC-v1.md) and [catalog](../departments/minecraft/catalog/MODS.md) are older: Twilight Forest IN_PROGRESS; Connector QUEUED/NOT_PINNED. Remote main records both IN_PROGRESS and pins Connector source tracks, with binary/runtime unresolved. Use the feature map for newer lanes; do not overwrite old status with a different revision's evidence.

- ANCHOR = 1.20.1 Forge adaptation; FRONTIER = useful current upstream. Keep version/loader evidence separate.
- Full-tree inventory -> mapping -> evidence. A few search hits are not whole-target completion.
- Raw checkouts/JARs/decompiled trees/full third-party assets stay local, preferably outside the workspace; `.gitignore` does not cover every analysis path. Commit derived inventories, hashes, maps, locators and portability notes.
- Facets: NOT_ANALYZED / INVENTORIED / MAPPED / EVIDENCE_BACKED / NOT_APPLICABLE. Inventory or static success does not prove runtime behavior.
- Portability separates concept, upstream implementation, platform/API differences, backport strategy and risks.

[Twilight tools](../departments/minecraft/mods/twilight-forest/tools/): `verify_anchor_jar.py` (resource correspondence, not compiled-class identity), `build_render_asset_graph.py`, `compare_render_asset_graphs.py`, `run_runtime_r1.py`, `run_runtime_r2.py`. Inspect `--help`, [runtime spec](../departments/minecraft/mods/twilight-forest/RUNTIME-EVIDENCE-SPEC.md), [R1 evidence](../departments/minecraft/mods/twilight-forest/RUNTIME-R1-VERIFICATION.md) and workflow before Gradle/Java/world-producing runs. R2 had unrelated dirty work during review; this guide does not certify its completion.

## Verification and maintenance

### Quality and speed

Implement and verify **coherent work units**, not every tiny edit. Define each unit's scope, acceptance criteria and relevant checks first; complete its related changes, then run one combined verification pass. Batch expensive builds, broad suites and Tank launches at meaningful integration boundaries. Reuse valid results until later changes affect their scope; do not repeat unrelated checks by habit.

Use engineering judgment to balance feedback speed, defect risk and execution cost. Run an earlier focused check when an uncertain interface, regression, high-risk change or unsafe state could invalidate later work. Keep regression coverage and required design/CI gates; batching changes timing, not acceptance standards. Do not enlarge a batch until failures become difficult to locate, skip checks to meet a deadline, or weaken guards to obtain success.

For Minecraft, establish static/unit and compile readiness before a bounded Tank session. Exercise the completed behavior in a disposable world with exact source/build/runtime identities; inspect observations and visible results, then record failures and repairs. Keep visual correctness, gameplay, cleanup and performance conclusions separate. Improve preparation, reuse and batching to deliver both quality and speed; do not trade quality for fewer test runs. The agent chooses an appropriate batch size and escalates uncertainty with evidence.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest -q tests/test_context_guidance_cli.py tests/test_context_guidance_cli_adversarial_json.py tests/test_validator.py tests/test_bundle.py tests/test_minecraft_department_contract.py
```

**DB fixtures TRUNCATE tables with CASCADE.** Set `KTHUB_TEST_DATABASE_URL` only to a confirmed disposable test DB. Without it, DB tests skip; report that limitation. Local [CI](../.github/workflows/test.yml) uses self-hosted Windows, Python 3.12 and PostgreSQL 16 in Docker; remote main's MOD-AI docs record hosted Linux/Java 17/PostgreSQL 16. Inspect workflows at the selected head. The local workflow's destructive Git line-ending normalization is not a local repair recipe; investigate fixture bytes/hashes first. No dedicated lint/type-check command is configured in local `pyproject.toml`.

Remote-source checks: MOD-AI task/context/packaging tests listed in its contract; LAB `npm run test:ci`; draft Motion/Decision `npm run test:motion-decision`; JavaFX `./run.ps1 -Test/-CompileOnly/-Smoke`; Airborne `npm test`; Warfare microkernel/calibration checks in its status docs. Run only the relevant selected lane; separate static/unit, provider/UI, Forge compile and exact-runtime results. Historical CI/test counts in linked documents are not new results for this guide.

For docs, verify links, CLI arguments, source consistency and whitespace (`git diff --check`; also check untracked files). Report changes/files, commands and pass/skip/fail, plus assumptions and unverified scope. Log relevant failures in [AI-FEEDBACK.md](AI-FEEDBACK.md). Update this guide when interfaces, authority, dependencies, tests/CI or workflows change; link detailed specs instead of duplicating them.
