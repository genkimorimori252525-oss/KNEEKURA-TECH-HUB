# Raids: Enhanced — network, rendering and risk audit

**Anchor:** [FINDERFEED/raidsenhanced `6354ebf97faaeba79affaf7e71d01ed5ae651e85`](https://github.com/FINDERFEED/raidsenhanced/tree/6354ebf97faaeba79affaf7e71d01ed5ae651e85) (Minecraft 1.20.1 + Forge). All behavior below is static-source inference; runtime tests are **NOT_RUN**.

## Network and authority

| Sender / lane | Class / packet ID | Data and receiver | Audit finding |
|---|---|---|---|
| Client → server | `PlayerBlimpRotatingPacket` / `raidsenhanced:player_blimp_rotating` | `int entityId`, `byte direction`; server looks up `PlayerBlimpEntity` and updates rotation state | **AUTHORIZATION REVIEW:** in the observed `serverAction` branch there is no explicit check that `getSender()` currently rides/owns/controls this target blimp |
| Server → client | `REPosEventPacket` / `raidsenhanced:pos_event` | 3 doubles (position) + 2 ints (event, data), dispatched to `REClientUtil.handlePosEvent` | compact positional visual event protocol |
| FDLib system | animation/entity attachments, screen shake and effects | mod delegates to FDLib implementations | protocol and compatibility depend on a **separate** FDLib artifact/snapshot; not fully audited here |

The first row identifies a **potential input spoofing/authority gap** visible in the source. It is **not a validated exploit**, especially without FDLib's server-side packet dispatch and live permissions examined. Independent implementation should validate sender membership/control, entity dimension/proximity, enum range, and rate.

Primary locators: [content/entities/player_blimp/PlayerBlimpRotatingPacket.java](https://github.com/FINDERFEED/raidsenhanced/blob/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/content/entities/player_blimp/PlayerBlimpRotatingPacket.java), [content/packets/REPosEventPacket.java](https://github.com/FINDERFEED/raidsenhanced/blob/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/content/packets/REPosEventPacket.java), [content/entities/FDRaider.java](https://github.com/FINDERFEED/raidsenhanced/blob/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/content/entities/FDRaider.java), [mixin/LocalPlayerMixin.java](https://github.com/FINDERFEED/raidsenhanced/blob/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/mixin/LocalPlayerMixin.java).

## Renderer, assets and animation

The renderer registry [REClientEvents.java](https://github.com/FINDERFEED/raidsenhanced/blob/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/REClientEvents.java) installs:
- customized FDLib `FDEntityRendererBuilder` instances for airship, golem, drill, Zapper and player vehicle;
- specialized renderers for lightning, projectiles and particles;
- a bone transformation controller for six independently aimed cannons.

`init/REModels.java` resolves FDLib `FDModelInfo`; `init/REAnimations.java` selects Bedrock-style animation records. Resource inventory in pinned 1.20.1 source: 113 resources, including **9 Bedrock `.geo.json`** models, **5 primary Bedrock animation JSON** files, PNG sprite/entity textures and 15 sound OGGs. Shader/visual parity and cross-client frame cost remain UNMEASURED.

Primary locators: [init/REModels.java](https://github.com/FINDERFEED/raidsenhanced/blob/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/init/REModels.java), [init/REAnimations.java](https://github.com/FINDERFEED/raidsenhanced/blob/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/init/REAnimations.java), [content/entities/raid_blimp/cannons/RaidBlimpCannonBonesController.java](https://github.com/FINDERFEED/raidsenhanced/blob/6354ebf97faaeba79affaf7e71d01ed5ae651e85/src/main/java/com/finderfeed/raids_enhanced/content/entities/raid_blimp/cannons/RaidBlimpCannonBonesController.java).

## Cost surfaces requiring measured data

1. Airship cannon targeting: shared `getEntitiesInCylinder` is called from `RaidBlimpCannonsController.tick`; six cannons then each filter potential living targets by range/angle, ray obstruction and assignment. Complexity grows with nearby entity count and six guns. **No ms/TPS observed**.
2. Flying path navigation: node selection uses repeated `level.clip` ray checks; observe obstacle-dense environments and delayed path recomputation.
3. Drill destination selection: enumerates X/Z candidate offsets over a 51 × 51 square before height/solid/air/fluids validation; check performance near complex modded terrain and chunk boundaries.
4. Golem heavy attacks: scans and spawns custom falling block effect entities; block destruction can trigger claim-mod hooks and neighbor update load.
5. Zapper laser: block clipping plus entity trace on alternate attack ticks; particle/radial lightning spam may produce client/network burst cost.
6. Renderer: FDLib attachment animation and per-gun bone movement should be checked in scenes with many simultaneous Blimps and multiple clients.

Do not promote any of the above to 'slow' or 'fast' without profiler evidence.

## Discovered upstream reports (not independently reproduced)

| Reference | Upstream reported symptom | Why it matters / status |
|---|---|---|
| [#1](https://github.com/FINDERFEED/raidsenhanced/issues/1) | Golem may break blocks protected by Flan | open report; check `onEntityDestroyBlock` compatibility, protected blocks, mobGriefing |
| [#2](https://github.com/FINDERFEED/raidsenhanced/issues/2) | raider tag/bell/Johnny alignment issues; only Omen-corresponding boss at highest level; Zapper invulnerability-bypass crash; non-stackable spawn eggs | open collection of user reports; wave selection matches source; other symptoms need reproduction |
| [#3](https://github.com/FINDERFEED/raidsenhanced/issues/3) | dedicated server join disconnect with FDLib `CutsceneData` serialization (1.20.1/Forge), while singleplayer works | open report; severity high for multiplayer, but not independently reproduced |
| [#4](https://github.com/FINDERFEED/raidsenhanced/issues/4) | crash with Raider Blimp | issue closed, root cause/fix not established by this review |

Do not infer closure = proven fix.

## LAB acceptance scenarios (proposed)

- **R1 wave matrix:** Bad Omen 1..5, final vs interim waves, save/reload, mixed raid mods, bell/glowing/raider tags.
- **R2 aerial census:** single and 4 simultaneous airships, 0/10/100 villagers, turrets acquiring distinct targets, projectile effects, movement traces, 20 TPS budget instrumentation.
- **R3 terrain:** Drill across open plains, water, ceilings, ungenerated chunks, solid ground, protected claims, chunk exits, max repeated burrows.
- **R4 attack phases:** Golem friendly/civilian exclusion, block claims, Zapper shield/laser/low armor/immune damage, death mid-attack.
- **R5 dedicated multiplayer:** Forge 1.20.1 with exact mod/FDLib binaries, 2 clients, packet replay/unauthorized blimp steering attempts in isolated test world.
- **R6 rendering:** cosmetic correctness, frame timing, FDLib event bursts, low vs high visual settings.
- **R7 restoration:** disposable worlds, explicit test authority, export evidence, teardown, private saves excluded from Git.

All scenarios currently `NOT_RUN`. The active KNEEKURA LAB run authority, evidence and restoration gates apply.
