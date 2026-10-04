# MOD analysis: practical entry guide

Use this guide with [ANALYSIS-SPEC-v1.md](ANALYSIS-SPEC-v1.md) and the target's own
README. If the target's primary purpose is performance optimization, also use
[optimization/ANALYSIS-SPEC.md](optimization/ANALYSIS-SPEC.md) and
[optimization/BENCHMARK-SPEC.md](optimization/BENCHMARK-SPEC.md); do not promote a source-level
fast path into an empirical performance claim without workload-bound benchmark evidence. It turns the existing specification into a repeatable research pass; it
does not introduce a crawler, another knowledge graph, or new CLI commands.

## 1. Resume the right work

1. Read the target README, current analysis plan, immutable evidence receipts and
   remaining coverage. Historical checkpoints remain historical: a completed
   tooling trial is not an unfinished task, or proof that a MOD works.
2. Fix ANCHOR / FRONTIER / optional COMPARATIVE separately. Record repository,
   commit, release association, Minecraft, loader, declared dependencies, license
   and acquisition date. A branch name or `latest` URL is only a discovery pointer.
3. Obtain the complete available source tree before whole-target interpretation.
   Verify inventory and bytes; retain unacquired files, unavailable dependencies,
   submodules and truncation explicitly. Full acquisition is not full analysis.
4. Use separate profiles/indexes per track. Preserve the existing CAS snapshot
   identity as well as Git revision; a Git HEAD alone does not describe binaries,
   mappings, dependency closure, side, configuration or observed runtime.

## 2. Required reconnaissance, performed by the analyst

Check useful external sources early: official site/manual/wiki/release notes,
established community guides/wikis, modpack docs, forum/Reddit reports and
precisely locatable videos. This is required discovery work when suitable sources
are available, not a promise that the adapter automatically fetches websites.

- Start from official project links and versioned docs. Log redirects: a 1.20.1
  project link can land on a current NeoForge page.
- Use community material to discover symptoms, conditions, terminology and
  overlooked features. Likes, repeated reports and agreement do not establish truth.
- For video claims record the actual timestamp and version evidence. A title or
  search snippet is discovery metadata; without viewed content/transcript, record
  `DISCOVERED_NOT_REVIEWED` or the exact access failure. Never invent timestamps.
- Record contradictory reports, missing versions, inaccessible pages and an
  unhelpful/no-source result. Do not silently replace them with current docs.
- Keep captured bytes/extracted text outside normal Git history. Record what was
  captured (original API response, extracted page text, transcript, etc.), when,
  the URL and hash. A hash of extracted text is not an original HTML/video hash.
- Publish only rights-appropriate, minimized summaries, hashes and locators.
  Links do not authorize uploading private logs, credentials or licensed assets.

## 3. Make a small Feature Map, then follow the evidence

For a content MOD, group visible mechanics by bosses, progression, worldgen,
items, rendering and integration. For Connector, use discovery/dependencies,
aliases, mappings, transformation, Mixins, classloading, caches and compatibility.
This map is a navigation aid, not a second canonical knowledge graph.

Each row follows this route:

`BehaviorHint → track-scoped search → Source/Bytecode/mappings → Issue/PR/commit
failure/repair → runtime only if needed → evidence-backed review`

1. Convert names, exact config keys, triggers and symptoms into literal searches.
2. Follow returned locators through full readback, including pagination. Read the
   callers, boundary conditions and relevant dependency implementation, not just a
   snippet. Retain a miss; refine names or namespaces explicitly rather than
   pretending search is semantic reasoning.
3. Keep original source, distribution bytecode, decompiled/remapped source and
   loaded/transformed runtime classes distinct. Record hashes and transformation
   provenance. Searchable text is not necessarily all acquired text: unsupported
   extensions and binary/service records may need byte-view/manual inspection.
4. Follow bug reports to actual repair diffs and before/after revisions using
   [FAILURE-REPAIR-HISTORY-v1.md](FAILURE-REPAIR-HISTORY-v1.md). A fix's parent is
   not automatically the introducing commit. Check follow-up regressions and
   whether the repair still exists, moved, or was reverted at the selected head.
5. If source cannot answer the question, record the exact missing observation.
   Runtime requires an authorized bounded environment/configuration, dependency
   and binary identities, assertions and cleanup. Do not launch because a guide
   recommends it, or reuse an unrelated completed run's permission.
6. Review each finding with its evidence and counterevidence. A guide alone cannot
   promote a facet to `EVIDENCE_BACKED`; static retrieval/compile success cannot
   become runtime compatibility, performance or canonical knowledge.

## 4. Lightweight authoring templates

These are document conventions, not a built-in BehaviorHint/FeatureMap schema.
Use a small table or JSON beside the target's analysis; do not invent adapter IDs.

```text
SourceRef: id; URL; author/source type; retrieved_at; published_at if known;
  claimed Minecraft/MOD/loader version; assigned track or UNKNOWN;
  captured representation + SHA-256 (or unavailable reason); license/access note
BehaviorHint: id; source_ref + heading/line/time; reported behavior/trigger;
  source version certainty; track applicability; conflicts; search terms
FeatureMap row: hint_id; subsystem; source/bytecode/history locators;
  inspected revision + profile/index/document IDs; result and basis;
  unavailable/deferred evidence; next question; facet state
Finding: precise claim; DIRECT_OBSERVATION / AUTHOR_CLAIM / INFERENCE / UNKNOWN;
  supporting and contrary evidence; applicability; runtime state; review state
```

Keep `DIRECT_OBSERVATION` of source bytes distinct from a game observation.
For history records use the existing exact JSON format, not this shorthand.

## 5. Existing tools and their limits

Run from the TECH HUB root; set `PYTHONPATH=src` if not installed. All uppercase
IDs below must be replaced with real returned IDs. The manifest points to already
acquired local inputs and explicitly declares origin/namespace/track.

```text
python -m kneekura_tech_hub.minecraft --store CACHE profile prepare --manifest MANIFEST.json
python -m kneekura_tech_hub.minecraft --store CACHE search --index INDEX --query globalModAliases --track ANCHOR
python -m kneekura_tech_hub.minecraft --store CACHE inspect --index INDEX --document DOCUMENT_ID --view source
python -m kneekura_tech_hub.minecraft --store CACHE inspect --index INDEX --document DOCUMENT_ID --view bytes
python -m kneekura_tech_hub.minecraft.history --store CACHE import --record FAILURE-REPAIR-HISTORY.json
python -m kneekura_tech_hub.minecraft.history --store CACHE query --history HISTORY_HASH --query "nested" --track ANCHOR
```

`search` is case-insensitive literal text/path retrieval. Pass a returned cursor
with the same snapshot/query/filters to retrieve subsequent pages. `inspect`
also pages; use byte view when source representation is unsupported.

Acquisition uses the analyst's authorized browser/connectors or explicit local
acquisition. `profile prepare` captures local data; it does not fetch web pages.
The current tools do not have first-class BehaviorHint/FeatureMap commands,
automatic web cross-reference, or a whole-target completion gate. These review
steps are an analyst checklist. Existing `knowledge stage` prepares a reviewed
source/license-bound candidate for the existing Core; it does not create or
promote a canonical Claim. See [the adapter README](mod-ai/README.md).

## 6. Before handing off

- [ ] Exact tracks, acquisition coverage and CAS identities are recorded
- [ ] Suitable external sources were checked, or the specific absence is recorded
- [ ] Feature Map connects hints to inspected code/history, with contrary evidence
- [ ] Unsupported search surfaces and unavailable dependencies remain visible
- [ ] Facet status uses NOT_ANALYZED / INVENTORIED / MAPPED / EVIDENCE_BACKED /
  NOT_APPLICABLE; the scope and evidence justify each promotion
- [ ] Runtime, performance, source-binary equivalence and canonical status are separate
- [ ] Remaining work says what evidence to obtain and why; no fabricated PASS
- [ ] Changed documents link back to originals; raw/private inputs are excluded

Worked continuation: [Sinytra Connector](mods/sinytra-connector/ANALYSIS-CONTINUATION-2026-10-01.md).
