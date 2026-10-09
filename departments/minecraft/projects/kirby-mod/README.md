# Kirby MOD — TECH-HUB product workspace

**Imported 2026-10-09.** This is the continuing product source, not a study-only example.

## Source and exact verification

- Former origin: `genkimorimori252525-oss/Kirby_mod` (private before this import).
- Pinned source: `main@620226ee8a88351dd8918f73679977a15582337c` (Forge 1.20.1 / Forge 47.4.10 / Java 17 / GeckoLib 4.8.3 / Mixins).
- Imported path: `departments/minecraft/projects/kirby-mod/`.
- Snapshot verification before new design docs: **174/174 source/project/test/resource blobs match origin Git SHA and path**; original non-cache tree had 175 candidate files.
- **Not imported:** `Kirby制作過程ボックス/kirby_mod-1.00.jar` (1,791,297 bytes). GitHub content retrieval returned empty for the large binary; importing it would have produced an invalid blob. It remains at the origin repository. Rebuild a fresh jar from source instead; never claim historical binary equivalence without its bytes.
- Intentionally not imported: `.gradle-home/`, `build-validation/` (generated caches and build outputs).
- The imported legacy `AGENTS.md`, `.agents/`, `.codex/` and `.vscode/` are **origin metadata**, not new product obligations. In particular, its instructions to update the old `/tlm` for every behavior and deploy jars to local absolute Windows paths are superseded for future TECH-HUB product work by the roadmap below.
- This import made no gameplay-source changes, has **not run Gradle / GameTest / live Minecraft**, and does not claim playable acceptance.

## Preserved gameplay foundation

- `src/main/java/com/example/kirby_mod/entity/KirbyEntity.java`: central Kirby entity and animation state.
- `entity/ai/`: inhaling, swallowing/digesting, spitting, flight, swimming, dodging, target selection.
- `client/KirbyModel.java`, `KirbyRenderer.java`: GeckoLib geometry, textures and animations.
- `src/main/resources/assets/kirby_mod/geo/kirby.geo.json` and `animations/kirby.animation.json`.
- `src/main/resources/assets/kirby_mod/texture/` (12 PNG), `sounds/` (36 OGG).
- `src/test/java/` (25 Java test files).
- Existing `debug/`, telemetry, `/tlm`: **legacy preserved-only, incomplete, not adopted as the TECH-HUB standard**. Do not expand or duplicate it per new copy ability. Preserve compatibility until a deliberate replacement is ready.

## Next production lanes

1. [Copy ability design & Blockbench workflow](docs/COPY-ABILITIES-DESIGN-2026-10-09.md) — currently proposed, not implemented.
2. Use existing TECH-HUB `mod-ai/` Blockbench pipeline and exact-profile validation to produce **editable** model sources plus GeckoLib model/texture/animation exports.
3. Game mechanic implementation in this Kirby MOD folder, not in `departments/minecraft/mods/` research reports.
4. Shared diagnostics: adopt the [common KNEEKURA MOD debug roadmap](../../design/2026-10-09-shared-mod-debug-roadmap.md) when the shared runtime contract is implemented; no new Kirby-private debugging system.

## Local build entry

From this folder in a Java 17 environment with dependencies available:

```powershell
.\gradlew.bat test build --no-daemon --console=plain
```

Source compilation, test outcomes and in-game behavior **remain unverified for this migration**. Do not silently install outputs to `.minecraft/mods`.

## Provenance / redistribution

The owner explicitly authorized migration from a private repository into public TECH-HUB. This does not itself prove that game-character artwork, audio or other third-party IP is redistributable under an open license. `mod_license=All Rights Reserved` in the imported metadata remains unchanged. Review asset provenance/licensing before any separate downstream public redistribution/release.
