# Kirby MOD — copy abilities & Blockbench authoring roadmap

**Status:** design entry, not an implemented gameplay feature. Target is the imported Forge 1.20.1 product at `../` (GeckoLib 4.8.3).

## Design premise

Copy abilities should be specified before implementing their art or mechanics. The existing Kirby inhale → held → digest/spit lifecycle is retained; gaining an ability must be an explicit, server-authoritative transition after an eligible completed swallow, not an accidental consequence of targeting or animation.

A copy ability comprises four independent yet linked contracts:

1. **Source/rules:** which mobs, traits or custom NBT conditions grant it, exclusions, multi-mob priority, inability to copy, loss/replacement behavior.
2. **Gameplay:** action inputs, charge/cooldown, attack area/projectiles, movement modifications, damage semantics, and AI ability decisions.
3. **Presentation:** Kirby costume/hat/weapon, particle/FX, sound, exact bone placements, animation clips, client sync and visibility.
4. **Validation:** ability ownership on server, state persistence/reload, packet synchronization, animations and performance, failure cases.

## Visual design worksheet (per ability)

- `ability_id`, ability name, 1-sentence fantasy, visual silhouette at gameplay distance.
- Color palette and permitted contrast; recognizable main accent; copyability source.
- Headwear/body overlay/accessory geometry and geometric attachment bone; dimensions relative to the source Kirby rig, not just an isolated illustration.
- Action poses: neutral, attack start, peak, recovery, hover, hurt; distinguishing effects and impact cue.
- Camera readability: front, side, back, 3/4; silhouette recognizability at low pixel density; distance/occlusion.
- Gameplay: attack range, active frames, hit window, projectiles and collision ownership (server vs client).
- Limits: no persistent mesh reallocation per tick, no all-entity scans, no unrestricted particle counts.
- Explicit asset references and provenance; human sign-off on a single 3D preview before game integration.

## Suggested data identity, not yet an accepted schema

```json
{
  "ability_id": "kirby_mod:fire",
  "copy_source": {"entity_tags": ["example:fire_copy_sources"]},
  "visual": {
    "geckolib_geometry": "kirby_mod:geo/copy/fire.geo.json",
    "texture": "kirby_mod:textures/copy/fire.png",
    "animation": "kirby_mod:animations/copy/fire.animation.json"
  },
  "moves": ["fire_breath", "flame_dash"],
  "status": "DESIGN_ONLY"
}
```

Do not treat this illustrative JSON as a runnable datapack definition. Agree the state machine and asset lookup first.

## TECH-HUB Blockbench sequence

1. Pin the exact Tech-Hub Blockbench tool revision and imported Kirby geometry/animation source; import existing `kirby.geo.json` as a baseline.
2. Reconstruct and retain a **native editable `.bbmodel`** master. The imported Kirby tree contains exported geometry/animation JSON, but no verified editable `.bbmodel` master.
3. Build each ability as a constrained accessory/body overlay on Kirby's existing head/body bone vocabulary; if a full geometry swap is required, explicitly map the affected bones and preserve existing animations.
4. Export GeckoLib-compatible geometry, texture and animation; keep `.bbmodel`, export bytes, content hashes and front/side/back/3/4 captures.
5. Use TECH-HUB's part-specific modification/repair checks to prove **unrelated Kirby parts do not change**; verify UV, animation keyframe and renderer compatibility.
6. Integrate server-authoritative ability state and client visual selection; account for swapping, death, saving, reload, multiplayer and entity unloading.
7. Test compile, isolated ability logic, server GameTest, client visuals, synchronization and performance; classify each as TESTED / NOT_RUN instead of treating export as runtime proof.

Existing TECH-HUB documents: `../../../../mod-ai/ASSET-INTEGRATION.md` is *not* an established relative link: use the canonical `departments/minecraft/mod-ai/ASSET-INTEGRATION.md` and `BLOCKBENCH-REPAIR-ACCEPTANCE-2026-10-01.md`.

## Candidate first abilities (not selected)

- **Fire:** unmistakable burning crown, cone of flame / short burst and continuous fire breath.
- **Sword:** distinct sharp silhouette and two-phase swipe with readable melee arc.
- **Ice:** crystalline blue crown, short frost jet and on-hit slow with transparent ice projectiles.

One ability should be the vertical-slice pilot. Preserve capability to create radically different later powers without requiring a universal canned projectile or AI behavior pattern.

## Debug constraint

Do **not** create a new `/kirby-debug` or expand old `/tlm` as the common answer. Copy-ability observability must be designed against the future [shared KNEEKURA MOD debug contract](../../../design/2026-10-09-shared-mod-debug-roadmap.md). Until that exists, use bounded existing logs and tests, and mark missing live observability rather than faking it.
