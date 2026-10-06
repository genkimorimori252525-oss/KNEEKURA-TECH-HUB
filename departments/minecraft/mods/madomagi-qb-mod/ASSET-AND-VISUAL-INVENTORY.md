# QB-MOD 1.6.4.082 — Asset and visual inventory

Primary QB archive SHA-256:
`52b1ba0774e098795dcf1ed9a489c66414ea725235978171f48a10db7287ba4e`

Alternate texture pack SHA-256:
`2f868b66ec3d4ea9baae91c8dc601d46b3215be067a17b7ad3ed02fddb636aec`

## Shipped visual asset totals

QB-MOD contains:
- 94 PNG textures;
- 35 Model*.java model classes;
- 18 Render*.java custom renderer classes.

All 94 PNGs are under `assets/puellamagi/textures/`.

PNG dimensions:

| Dimensions | Count |
| --- | ---: |
| 16×16 | 37 |
| 128×128 | 15 |
| 64×64 | 13 |
| 128×64 | 10 |
| 32×32 | 9 |
| 64×32 | 6 |
| 256×128 | 2 |
| 192×96 | 2 |

This mix reflects:
- small item/block sprites;
- player/biped skins;
- larger witch/boss texture sheets.

## Asset families

### Blocks
3 PNGs:
- Mami Ribbon;
- Kyouko Shield side;
- Kyouko Shield top.

### Enemy / witch textures
Includes:
- Gertrud / Adelbert / Anthony;
- Charlotte first/second;
- Oktavia / Pyotr;
- Candeloro;
- Homulilly / Nutcracker;
- Clara Dolls / Liese / Lilia / Lotte / Luiselotte;
- Walpurgisnacht;
- Maid and seven Shadow Puella variants.

### Projectile / entity textures
Includes:
- Claw;
- Corno Forte;
- Cutlass;
- Fire Lance;
- Grief Seed;
- Light Arrow;
- Musket;
- Prickle;
- Spear;
- Wheel.

### Character / form textures
Character texture files cover normal and implemented transformed/special forms for:
- Madoka;
- Homura;
- Sayaka;
- Mami;
- Kyouko;
- Kirika;
- Yuri;
- QB/JB.

## Identical shipped texture pairs

SHA-256 grouping finds two deliberate/original duplicate pairs:

- `mobs/kyoukoMS.png` == `mobs/kyoukoReb.png`
- `mobs/sayakaReb.png` == `mobs/sayakaUF.png`

This means those form transitions can change AI/state without necessarily changing the texture bytes. Model/render state may still differ.

## Alternate TexturePack-01 coverage

The supplied texture pack contains 20 PNG files intended for `assets/puellamagi/textures/mobs/`.

19 filenames map exactly to existing QB mob texture paths, and every mapped override has different PNG bytes from the base archive.

They cover:
- Homura normal/MS/Rebellion/UF;
- Kirika normal/MS;
- Kyouko normal/MS/Rebellion;
- Madoka normal/MS;
- Mami normal/MS;
- Sayaka normal/MS/Rebellion/UF;
- Yuri normal/MS.

## Texture-pack filename defect: Madoka UF

The twentieth ZIP member is decoded by Python's ZIP reader as:

`.../mobs/éìadokaUF.png`

The ZIP entry does **not** set the UTF-8 filename flag (`flag_bits = 0`).

Recovering its raw CP437-decoded bytes and interpreting those bytes as CP932 gives:

`.../mobs/ｍadokaUF.png`

where the first character is **full-width U+FF4D 'ｍ'**, not ASCII `m`.

QB-MOD's entity texture convention requests:

`textures/mobs/madokaUF.png`

Therefore this alternate resource entry does not have the exact logical resource path required for Madoka Ultimate Form.

Finding:
- intended visual override is apparent from the name;
- exact filename mismatch is direct archive evidence;
- actual runtime fallback behavior was not executed, but normal resource resolution should not equate full-width `ｍ` with ASCII `m`.

Portable repair: rename the entry to exact ASCII `madokaUF.png`.

## Light Arrow visual technique

Light Arrow renderer:
- custom crossed-plane mesh;
- rotates four side quads around projectile axis;
- uses translucent alpha;
- takes projectile full-bright lightmap;
- modulates luminance with a sine wave over `tickLight`.

This is an efficient magical-projectile presentation primitive and is relevant to the future danmaku/effects library.

## Shadow visual polymorphism

One Shadow Puella entity can select seven distinct character model families.

The type byte simultaneously controls:
- texture;
- model instance;
- held weapon;
- bow posture;
- attack vocabulary.

This is a compact **simulation entity → multiple visual/combat archetypes** implementation.

## Charlotte phase readability

Charlotte first→second phase changes:
- model family;
- texture/state;
- render scale from 0.5× to 5×.

The resulting visual scale discontinuity is 10× before model geometry differences, making phase transition immediately legible.

## Boss scaling

Renderer constructor scale values include:
- Kriemhild Gretchen 15×;
- Walpurgisnacht 5×;
- Homulilly Nutcracker 4×;
- Gertrud 4×;
- Oktavia 3×;
- Homulilly 3×;
- Servant Oktavia 3×.

Render size is separate from collision/entity dimensions.

## Particle vocabulary found in source

Literal particle IDs include:
- `reddust`;
- `portal`;
- `bubble`;
- `note`;
- plus dynamically chosen mode-feedback particles such as `happyVillager`, `heart`, and `spell`.

Not all effects use custom textures; much of the spectacle is built by combining entity projectiles, vanilla particles, fireworks, TNT/explosion effects and model scale.

## Sound vocabulary found in source

Frequent literals include:
- `random.bow`;
- `mob.endermen.portal`;
- `random.fuse`;
- `random.click`;
- `random.break`;
- `random.bowhit`;
- `mob.cow.step`.

No custom audio asset set was found in the QB archive inventory.

Technique: **presentation assembled from custom visuals + stock Minecraft sound vocabulary**, reducing distribution size.

## ANCHOR notes

For 1.20.1 Forge:
- model classes require modern EntityModel/LayerDefinition or another chosen animation system;
- direct GL11 transforms must be replaced with PoseStack/render-type logic;
- exact ResourceLocation paths should be normalized and validated;
- texture overrides should be tested for case/Unicode path mismatches;
- visual scale must remain independent from collision/navigation dimensions.