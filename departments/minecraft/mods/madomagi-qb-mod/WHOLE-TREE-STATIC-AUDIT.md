# QB-MOD / Garnet-MOD 1.6.4.082 — Whole-tree static surface audit receipt

Date: 2026-10-07

Purpose: provide a **retrieval-completeness check** after the manual whole-target analysis.

This audit does not infer behavior from keyword counts. It asks a narrower question:

> Across all 193 shipped Java files, which files contain high-risk or special legacy APIs/patterns that deserve semantic review, and have those surfaces been classified somewhere in the analysis?

Primary archives:
- QB-MOD SHA-256: `52b1ba0774e098795dcf1ed9a489c66414ea725235978171f48a10db7287ba4e`
- Garnet-MOD SHA-256: `5f778c8949dcce95dcd56dacd9242f117bc17f03879bab48cb667ba2a3c82778`

Regenerator:
- `tools/audit-static-surfaces.py`

The script scans only Java text and emits JSON. It does not fetch source, decompile classes or make semantic claims.

## Scan universe

- QB Java files: 156
- Garnet Java files: 37
- total: **193**
- parse/search scope: every `*.java` under the two supplied MCP source roots

## Aggregate literal-hit inventory

| Surface | Occurrences | Files |
| --- | ---: | ---: |
| TODO | 6 | 5 |
| System.out print/println | 4 | 3 |
| createExplosion | 10 | 6 |
| EntityTNTPrimed | 25 | 11 |
| setHealth | 6 | 4 |
| setDead | 38 | 20 |
| setBlock-family writes | 16 | 13 |
| addPotionEffect | 19 | 10 |
| setPosition | 20 | 12 |
| getEntitiesWithinAABB | 18 | 12 |
| writeEntityToNBT | 14 | 8 |
| readEntityFromNBT | 14 | 8 |
| Packet250CustomPayload | 4 | 2 |
| DataWatcher references | 83 | 11 |
| lightning/weather-effect literal | 1 | 1 |
| EntityFireworkRocket | 6 | 2 |

Counts are literal source occurrences and are not normalized by overload, branch reachability or generated/dead code.

## TODO coverage

All six TODO hits are classified:

- `EntityOktavia` ×2 — common servant path TODO-disabled; Wheel AI is the active pressure system.
- `EntityGarnetThrowable` ×1 — commented TNT special interaction.
- `BlockMamiRibbon` ×1 — commented connected-surface appearance idea.
- `EntityGriefSeed` ×1 — commented block-update experiment.
- `ItemMamiRibbon` ×1 — commented future pull/tether mechanic.

Primary record:
`UNFINISHED-DEBUG-AND-DEAD-CODE-CATALOG.md`.

## stdout coverage

All four active print hits are classified:

- `EntityMajoAIOktavia` ×2 — candidate false/true printing during Wheel spawn search.
- `EntityMajoAICharlotteWander` ×1 — position-search counter printing.
- `EntityGarnetTameable` ×1 — owner chat mirrored to stdout.

Records:
- `UNFINISHED-DEBUG-AND-DEAD-CODE-CATALOG.md`
- `STATIC-PERFORMANCE-AND-SAFETY-RISK-MAP.md`

## Explosion surfaces

All `createExplosion` source hits fall into known systems:

- Garnet Throwable critical impact;
- Nutcracker anti-air punishment;
- Walpurgis Attack anti-air punishment;
- Walpurgis Play anti-air punishment;
- Kriemhild terminal explosion;
- Homura Ultimate escalation.

Records:
- `PROJECTILE-TRAJECTORY-CATALOG.md`
- `DAMAGE-DEFENSE-AND-MULTIHIT-SEMANTICS.md`
- `BOSS-COMBAT-CATALOG.md`
- `STATIC-PERFORMANCE-AND-SAFETY-RISK-MAP.md`

## Primed-TNT surfaces

The 25 literal `EntityTNTPrimed` references across 11 files reduce to already mapped families:

- Homura teleport/TNT attack;
- Homulilly retaliation/attack;
- Walpurgis terrain→TNT attack;
- Yuri terrain→TNT attack;
- companion TNT avoidance;
- registration/type checks around those systems.

No additional independent TNT combat family was found in this retrieval pass.

## Direct-health mutation

The six `setHealth` hits are classified as:

- LightArrow3 percentage-health pre-impact mutation;
- Homura Ultimate 95% / 1 HP / 0 HP execution ladder;
- Kriemhild constructor/init health setup;
- Ophelia phantom self-health clamp to 1.

The dangerous target-health mutations are documented in:
- `CHARACTER-COMBAT-CATALOG.md`
- `PROJECTILE-TRAJECTORY-CATALOG.md`
- `DAMAGE-DEFENSE-AND-MULTIHIT-SEMANTICS.md`
- `ANCHOR-PORTABILITY-MATRIX.md`

## World-write surface

The `setBlock`-family hits span:

- Fire Lance block cutting;
- Charlotte second-form collision destruction;
- Walpurgis body/attack terrain destruction;
- Nutcracker collision destruction;
- Anthony flower planting;
- Grief Seed forced hatch clearance;
- Yuri terrain conversion;
- magical-girl witch-transformation clearance;
- magical-girl torch placement;
- Sayaka Ultimate collision destruction;
- Garnet ItemBreaker;
- Garnet Arrow/Throwable impact-face fire ignition;
- Throwable TNT removal.

Every family now has a destination in the block-edit / encounter-risk analysis.

Primary records:
- `STATIC-PERFORMANCE-AND-SAFETY-RISK-MAP.md`
- `ANCHOR-PORTABILITY-MATRIX.md`
- `PROJECTILE-TRAJECTORY-CATALOG.md`
- `WITCH-ECOLOGY-AND-GRIEF-SEED.md`

## Direct-position movement

The 20 `setPosition` hits across 12 files include:

- teleports;
- summon/replacement placement;
- Rosso Fantasma hard target relocation;
- Servant Oktavia 3-block positional-step flight;
- entity placement during transformations/rituals.

The nontrivial combat movement cases are now separated from ordinary spawn placement in:
`AI-GOAL-AND-COMBAT-INTENT-CATALOG.md`.

## Entity-query surface

The 18 AABB-query hits across 12 files cover:

- Garnet target acquisition;
- staged Musket/Cutlass lookup;
- Kriemhild absorb pulse;
- boss death cleanup;
- witch/familiar local population;
- Soul Gem threat detection;
- item/world-interaction searches.

The large/recurring query paths are classified in:
`STATIC-PERFORMANCE-AND-SAFETY-RISK-MAP.md`.

## Persistence and synchronization surface

NBT override counts:
- writes: 14 occurrences / 8 files;
- reads: 14 occurrences / 8 files.

DataWatcher references:
- 83 occurrences / 11 files.

These surfaces drove the explicit state-boundary review in:
`NETWORK-PERSISTENCE-AND-STATE-BOUNDARIES.md`.

Known missing-persistence candidates include:
- Grief Seed Homulilly ritual flag;
- Charlotte second-form flag;
- witch ecology age;
- raw master/encounter links;
- process-local Walpurgis encounter gate.

## Legacy networking surface

All `Packet250CustomPayload` references occur in the already mapped Garnet gun client/server path.

Server handler's byte-zero read without visible length check has also been selected for distributed-bytecode correspondence.

Records:
- `GARNET-FRAMEWORK-ANALYSIS.md`
- `NETWORK-PERSISTENCE-AND-STATE-BOUNDARIES.md`
- `BINARY-SOURCE-CORRESPONDENCE.md`

## Firework / lightning presentation surface

Firework references reduce to:
- Homura-vs-Walpurgis attack tracer/cue;
- Walpurgis death celebration.

Lightning/weather-effect hit reduces to:
- Kriemhild's periodic absorb-cycle presentation branch.

These are classified in:
- `ATTACK-TELEGRAPH-AND-VFX-CATALOG.md`
- `BOSS-COMBAT-CATALOG.md`

## Additional archaeology found by this audit

The abstract `ItemMadomagiWeapon` still contains an older generic right-click implementation, but every concrete current descendant:
- Sayaka Cutlass;
- Kyouko Spear;
- Kirika Claw;

overrides `onItemRightClick` and does not call super.

It is therefore preserved as an **implemented-but-shadowed legacy implementation fossil**, not active player behavior.

Record:
`UNFINISHED-DEBUG-AND-DEAD-CODE-CATALOG.md`.

## Interpretation

This audit materially strengthens the claim:

**STATIC WHOLE-TREE MAPPED**

because a second, mechanically broad retrieval pass over all 193 Java files did not expose an unclassified high-risk surface among the selected categories.

It does **not** establish:
- semantic completeness of every ordinary method;
- runtime reachability of every branch;
- exact source↔bytecode equivalence;
- runtime performance;
- save/reload correctness;
- historical failure/repair provenance;
- ANCHOR equivalence.

Those remain separate evidence gates.

The correct target status therefore remains:

**STATIC WHOLE-TREE MAPPED, NOT COMPLETE**.
