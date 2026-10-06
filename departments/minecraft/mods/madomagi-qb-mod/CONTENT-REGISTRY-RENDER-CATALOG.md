# QB-MOD 1.6.4.082 — Content, registry and rendering catalog

Primary evidence: supplied QB-MOD source snapshot.

## Registration architecture

`mod_QB` performs code-driven 1.6.4-era registration:
- blocks/items through `GameRegistry`;
- localized names through `LanguageRegistry`;
- entities through both global IDs and mod entity IDs;
- selected natural spawns through `EntityRegistry.addSpawn`;
- client renderers through `PuellaMagiClientProxy`.

There are no data-pack registries, JSON recipes, modern DeferredRegister objects, Mixins or data generators in this snapshot.

ANCHOR implication: the content graph is portable as data/intent, but every registration surface must be rewritten for 1.20.1 Forge.

## Naturally spawned / encounter-gated content

### QB
Registry-level spawn:
- weight 1;
- min/max 1;
- monster creature type;
- Extreme Hills and Ice Mountains.

The entity itself adds further spawn constraints, so registry declaration is only the first gate.

### Walpurgisnacht
Registry-level spawn:
- weight 100;
- min/max 1;
- monster;
- all base 12 biomes.

This apparently broad/high-weight declaration is misleading by itself: `EntityWalpurgisnacht.getCanSpawnHere()` applies the actual calendar/time/height/global-gate constraints. This is a strong example of why registry inspection alone cannot describe encounter frequency.

### Grief Seed
Registry-level spawn:
- weight 2;
- min/max 1;
- monster;
- all base 12 biomes.

Its own light/spawn tests further narrow eligibility.

Other witches, servants and projectiles are primarily created through transformation, incubation, summoning or attacks rather than ordinary biome spawn registration.

Technique: **broad registry admission + strict entity-local encounter gate**.

ANCHOR should prefer explicit spawn placement/biome modifiers plus a separately testable encounter predicate instead of hiding most semantics in `getCanSpawnHere`.

## Recipes

All recipes are code-authored.

### Utility / ammunition
- Mami Ribbon block: 2×2 Mami Ribbon → 16 blocks.
- Kyouko Shield block: one Kyouko Ribbon → 6 blocks.
- Madoka Ribbon: red wool → ribbon.
- Light Arrow: arrow + redstone + gold nugget + lapis dye → 4.
- Bullet: iron ingot + gunpowder → 4.

### Spawn eggs
- QB egg: Incubator surrounded by eggs.
- JB egg: Incubator + eggs + Grief Seeds.

### Weapons
- Madoka Bow: Grief Seed + vanilla bow + red flower.
- Homura Desert Eagle: iron + gold + gunpowder.
- Homura Type 89: iron + diamond + gunpowder.
- Homura Bow: two Madoka Ribbons + Madoka Bow.
- Sayaka Cutlass: Grief Seed + diamond sword + jukebox.
- Sayaka Hair Clip: iron + yellow dye.
- Sayaka Bat: Hair Clip + planks.
- Mami Musket: Grief Seed + iron + flint.
- Mami Ribbon: yellow wool.
- Kyouko Spear: Grief Seed + diamond sword + gold block.
- Kyouko Ribbon: black wool + iron.
- Kirika Claw: Grief Seed + diamond sword + three iron swords.
- Yuri gun: Grief Seed + redstone block + nether quartz + iron.

Design observation: Grief Seed is used not only as a cleansing/witch-cycle item but as a **crafting catalyst for multiple signature magical weapons**, tying combat progression back into witch hunting.

## Barrier blocks

### BlockMamiRibbon

- cloth material;
- non-opaque/non-normal cube;
- drops nothing;
- no self item drop;
- largely presentation/protection geometry.

It is explicitly protected from multiple boss/world-destruction routines.

### BlockKyoukoShield

- `BlockPane` using cloth material;
- must have a solid supporting block beneath;
- breaks/drops if support is removed;
- no Silk Touch harvesting;
- uses separate side/top icon;
- likewise protected from many boss/world-destruction routines.

Technique: **player-deployed protected terrain vocabulary** shared with boss destruction exclusions.

For ANCHOR, destruction immunity should become a tag/capability/policy (for example `kneekura:boss_terrain_protected`) rather than hardcoded class/ID comparisons scattered through each boss.

## Magical-girl inventory and GUI

`InventoryMadomagi`:
- fixed 5 slots;
- persists each occupied slot to NBT list with Slot byte;
- supports class-based item lookup as well as item-id lookup;
- AI consumes items from this inventory (Grief Seeds, torches, transformation/special items);
- `dropAllItems()` ejects every stack into world;
- open/close callbacks inform the owner entity.

This means the inventory is part of AI state, not merely player storage.

Ultimate Form entry ejects inventory and UF prevents normal inventory use, matching the 2013 community update note.

`GuiMadomagi` reuses the vanilla hopper texture, giving a five-slot visual surface without a bespoke GUI texture.

Technique: **small NPC tactical inventory exposed through familiar vanilla GUI skin**.

Risk: `MadomagiGuiHandler` holds mutable shared container state and should not be recreated literally on a multiplayer modern server.

## Renderer registration map

Client proxy registers distinct renderers for:
- 8 magical-girl/contract entities;
- major witches/bosses and servants;
- staged weapon entities/projectiles;
- Grief Seed and boss hazards.

Notable visual scales supplied at renderer construction:
- Kriemhild Gretchen: 15.0×
- Walpurgisnacht: 5.0×
- Homulilly Nutcracker: 4.0×
- Gertrud: 4.0×
- Oktavia: 3.0×
- Homulilly: 3.0×
- Servant Oktavia: 3.0×
- Shadow Puella Magi: 0.7×
- Candeloro: 0.3×

These values are presentation scale arguments to Garnet renderer bases, separate from entity collision dimensions/attributes.

Technique: **simulation size and presentation scale are independent knobs**.

For ANCHOR, bounding boxes/pathfinding/reach should be designed explicitly rather than inferred from render scale.

## Magical-girl form rendering

`RenderMahoShojo` has four model slots:
- normal;
- transformed;
- Rebellion;
- Ultimate.

Before each draw, the renderer switches `mainModel` according to synchronized entity form.

A separate synchronized posture state sets `modelBipedMain.aimedBow`.

Thus:
- narrative/form state chooses model;
- posture/combat state chooses pose;
- entity texture logic chooses texture.

This separation is worth preserving in modern animation systems.

## Ambidextrous rendering

Yuri uses `RenderMahoShojoAmbidexter`.

The renderer:
- lets the normal right-hand item render through the superclass;
- then manually transforms and renders the same held ItemStack relative to the left arm;
- supports block, bow, full-3D item and flat-item transform branches.

Technique: **renderer-level mirrored second-hand presentation without changing logical inventory/held-item state**.

In 1.20.1, prefer actual equipment/animation semantics where gameplay needs two weapons; keep pure renderer duplication only when it is intentionally cosmetic.

## Charlotte phase presentation

`RenderCharlotte` couples phase state to both:
- model replacement: normal model vs second-form model;
- scale replacement: 0.5× first form vs 5× second form.

This yields a **10× visual scale jump** across the phase transition even before considering different model geometry.

Technique: **phase change communicates itself through simultaneous model-family and scale discontinuity**.

## Shadow Puella Magi presentation

`RenderShadowPuellaMagi` contains seven magical-girl model instances.

Entity type selects one model dynamically and chooses whether `aimedBow` posture should be enabled for that visual type.

For Yuri-like type, it additionally duplicates equipped-item rendering to the left arm.

Technique: **one enemy entity class as a polymorphic visual shell over multiple character silhouettes**.

## Light Arrow rendering

`RenderLightArrow` does not simply reuse vanilla Arrow rendering.

It:
- aligns a custom crossed-quad mesh to projectile yaw/pitch;
- uses translucent color alpha 128;
- obtains full/bright lightmap values from projectile;
- modulates grayscale brightness with a sine function of `tickLight`;
- rotates four side quads around the projectile axis.

Technique: **small projectile rendered as pulsing luminous crossed planes rather than geometry-heavy model**.

This is relevant to modern danmaku/beam-effect design: low-complexity billboard/plane geometry can provide visible magical projectiles without a full entity model.

## Grief Seed rendering

Grief Seed uses a similar small crossed-plane/arrow-like custom mesh, without the Light Arrow's pulsing full-bright color modulation.

This keeps world-incubation objects visually lightweight.

## Boss UI

Walpurgisnacht and Kriemhild custom renderers call legacy `BossStatus.setBossStatus(..., true)` during rendering.

The boss bar is therefore coupled to render invocation in 1.6.4.

ANCHOR rewrite must use modern server-side boss event/bar state and must not make UI state dependent on whether the entity renderer ran.

## HeightCorrection

`RenderMahoShojo.preRenderCallback` conditionally calls Garnet's pre-render scale path when `mod_QB.heightCorrection` is enabled.

It is a rendering/character-height correction toggle, not navigation, collision or spawn-height logic.

## Portability summary

High-value invariant concepts:
1. broad registry spawn + strict encounter predicate;
2. Grief Seed as progression/crafting catalyst;
3. protected barrier tag used by terrain-destructive bosses;
4. five-slot AI-owned tactical inventory;
5. state→model and posture→pose separation;
6. separate simulation dimensions and render scale;
7. model+scale discontinuity for boss phase readability;
8. polymorphic enemy visual shell;
9. crossed-plane luminous projectile renderer;
10. renderer-independent modern boss bar redesign.

Legacy APIs to rewrite:
- numeric global entity IDs;
- `LanguageRegistry`;
- code recipes;
- `RenderingRegistry`;
- GL11 immediate transforms;
- `BossStatus`;
- hopper-texture coordinates if GUI design changes;
- direct block-ID immunity tests.